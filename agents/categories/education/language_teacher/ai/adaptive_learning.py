"""
Adaptive Learning Engine - Core AI component for personalized language learning.
"""

import json
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from src.log_service import get_logger
from .models.student_model import StudentModel, ProficiencyLevel
from .models.learning_models import IRT_Model, BKT_Model, ItemParameters


class AdaptationStrategy(Enum):
    """Strategies for adaptive learning."""
    DIFFICULTY_BASED = "difficulty_based"  # Adjust based on performance
    MASTERY_BASED = "mastery_based"  # Focus on mastery
    MIXED = "mixed"  # Combination approach
    SPACED_REPETITION = "spaced_repetition"  # Focus on retention


@dataclass
class LearningRecommendation:
    """Recommendation for next learning activity."""
    item_id: str
    item_type: str  # "vocabulary", "grammar", "conversation", etc.
    difficulty: float  # 0-1 scale
    estimated_time: int  # minutes
    reasoning: str  # Why this item was recommended
    priority: float  # 0-1 priority score
    knowledge_components: List[str]
    success_probability: float


@dataclass
class AdaptiveSession:
    """Configuration for an adaptive learning session."""
    student_id: str
    target_duration: int  # minutes
    max_items: int
    focus_areas: List[str]
    difficulty_range: Tuple[float, float]  # min, max difficulty
    adaptation_strategy: AdaptationStrategy


class AdaptiveLearningEngine:
    """
    Core adaptive learning engine that personalizes content and difficulty.
    
    Features:
    - Student proficiency modeling
    - Dynamic difficulty adjustment  
    - Optimal next-item selection
    - Performance prediction
    - Learning path optimization
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize adaptive learning engine.
        
        Args:
            config: Configuration dictionary
        """
        self.logger = get_logger("adaptive_learning")
        
        # Configuration
        self.config = config or {}
        self.adaptation_strategy = AdaptationStrategy(
            self.config.get('adaptation_strategy', 'mixed')
        )
        
        # Models
        self.irt_model = IRT_Model()
        self.bkt_model = BKT_Model()
        
        # Student models
        self.student_models: Dict[str, StudentModel] = {}
        
        # Content library
        self.content_items: Dict[str, Dict[str, Any]] = {}
        self.item_difficulty_cache: Dict[str, float] = {}
        
        # Learning objectives and prerequisites
        self.learning_objectives: Dict[str, Dict[str, Any]] = {}
        self.prerequisites: Dict[str, List[str]] = {}
        
        # Adaptation parameters
        self.difficulty_adjustment_rate = 0.1
        self.min_items_for_adaptation = 3
        self.success_rate_target = 0.75
        self.mastery_threshold = 0.85
        
        # Performance tracking
        self.session_history: List[Dict[str, Any]] = []
        
        self._initialize_default_content()
        self.logger.info("Initialized Adaptive Learning Engine")
    
    def _initialize_default_content(self) -> None:
        """Initialize default content items and parameters."""
        try:
            # Default language learning topics
            default_topics = {
                'vocabulary_basic': {
                    'type': 'vocabulary',
                    'difficulty': 0.3,
                    'knowledge_components': ['basic_vocabulary'],
                    'estimated_time': 2
                },
                'vocabulary_intermediate': {
                    'type': 'vocabulary', 
                    'difficulty': 0.6,
                    'knowledge_components': ['intermediate_vocabulary'],
                    'estimated_time': 3
                },
                'grammar_present_tense': {
                    'type': 'grammar',
                    'difficulty': 0.4,
                    'knowledge_components': ['present_tense', 'verb_conjugation'],
                    'estimated_time': 5
                },
                'grammar_past_tense': {
                    'type': 'grammar',
                    'difficulty': 0.6,
                    'knowledge_components': ['past_tense', 'verb_conjugation'],
                    'estimated_time': 5
                },
                'conversation_basic': {
                    'type': 'conversation',
                    'difficulty': 0.5,
                    'knowledge_components': ['basic_conversation', 'pronunciation'],
                    'estimated_time': 10
                }
            }
            
            for item_id, item_data in default_topics.items():
                self.add_content_item(item_id, item_data)
                
                # Add to IRT model
                self.irt_model.add_item(
                    item_id, 
                    difficulty=item_data['difficulty'] * 4 - 2,  # Convert to IRT scale
                    topic=item_data['type']
                )
                
                # Add knowledge components to BKT model
                for kc in item_data['knowledge_components']:
                    self.bkt_model.add_knowledge_component(kc)
            
            self.logger.debug("Initialized default content items")
            
        except Exception as e:
            self.logger.error(f"Error initializing default content: {e}")
    
    def add_content_item(self, item_id: str, item_data: Dict[str, Any]) -> None:
        """
        Add content item to the engine.
        
        Args:
            item_id: Unique item identifier
            item_data: Item metadata and parameters
        """
        try:
            required_fields = ['type', 'difficulty', 'knowledge_components']
            if not all(field in item_data for field in required_fields):
                raise ValueError(f"Item missing required fields: {required_fields}")
            
            self.content_items[item_id] = {
                'id': item_id,
                'type': item_data['type'],
                'difficulty': max(0.1, min(1.0, item_data['difficulty'])),
                'knowledge_components': item_data['knowledge_components'],
                'estimated_time': item_data.get('estimated_time', 5),
                'prerequisites': item_data.get('prerequisites', []),
                'metadata': item_data.get('metadata', {}),
                'created_at': datetime.now()
            }
            
            self.item_difficulty_cache[item_id] = item_data['difficulty']
            
            self.logger.debug(f"Added content item: {item_id}")
            
        except Exception as e:
            self.logger.error(f"Error adding content item {item_id}: {e}")
    
    def get_student_model(self, student_id: str) -> StudentModel:
        """Get or create student model."""
        if student_id not in self.student_models:
            self.student_models[student_id] = StudentModel(student_id)
            self.logger.info(f"Created new student model for {student_id}")
        
        return self.student_models[student_id]
    
    def update_student_performance(self, student_id: str, item_id: str,
                                 correct: bool, response_time: float = None,
                                 additional_data: Dict[str, Any] = None) -> None:
        """
        Update student performance and models.
        
        Args:
            student_id: Student identifier
            item_id: Item identifier
            correct: Whether response was correct
            response_time: Time taken to respond (seconds)
            additional_data: Additional performance data
        """
        try:
            student_model = self.get_student_model(student_id)
            
            # Update student model
            if item_id in self.content_items:
                item = self.content_items[item_id]
                
                # Update knowledge state
                for kc in item['knowledge_components']:
                    student_model.update_knowledge_state(kc, correct, response_time)
            
            # Update IRT model
            self.irt_model.update_student_state(student_id, item_id, correct)
            
            # Update BKT model
            if item_id in self.content_items:
                knowledge_components = self.content_items[item_id]['knowledge_components']
                self.bkt_model.update_student_state(
                    student_id, item_id, correct, knowledge_components
                )
            
            # Update session performance
            session_data = {
                'student_id': student_id,
                'item_id': item_id,
                'correct': correct,
                'response_time': response_time,
                'timestamp': datetime.now(),
                'additional_data': additional_data or {}
            }
            
            # Update student model performance
            self._update_session_performance(student_model, session_data)
            
            self.logger.debug(
                f"Updated performance for {student_id} on {item_id}: "
                f"correct={correct}"
            )
            
        except Exception as e:
            self.logger.error(f"Error updating student performance: {e}")
    
    def _update_session_performance(self, student_model: StudentModel, 
                                   session_data: Dict[str, Any]) -> None:
        """Update student model with session performance data."""
        try:
            # Add to session history
            student_model.session_history.append(session_data)
            
            # Calculate session metrics from recent performance
            recent_sessions = student_model.session_history[-20:]  # Last 20 items
            
            if recent_sessions:
                accuracy = sum(1 for s in recent_sessions if s['correct']) / len(recent_sessions)
                completion = 1.0  # Assume completed if we have data
                
                # Calculate engagement based on response times
                response_times = [s.get('response_time', 0) for s in recent_sessions if s.get('response_time')]
                if response_times:
                    avg_time = np.mean(response_times)
                    # Lower variance in response time = higher engagement
                    time_variance = np.var(response_times)
                    engagement = max(0.1, 1.0 - (time_variance / (avg_time**2 + 1)))
                else:
                    engagement = 0.7  # Default engagement
                
                session_performance = {
                    'accuracy': accuracy,
                    'completion_rate': completion,
                    'engagement_score': engagement,
                    'response_times': response_times,
                    'errors': [],  # Would be populated with error analysis
                    'new_concepts': [],  # Would be populated with new concepts learned
                    'duration_minutes': len(recent_sessions) * 2  # Estimate
                }
                
                student_model.update_performance(session_performance)
            
        except Exception as e:
            self.logger.error(f"Error updating session performance: {e}")
    
    def get_next_recommendation(self, student_id: str, 
                               session_config: AdaptiveSession = None) -> LearningRecommendation:
        """
        Get next learning recommendation for student.
        
        Args:
            student_id: Student identifier
            session_config: Session configuration
            
        Returns:
            Learning recommendation
        """
        try:
            student_model = self.get_student_model(student_id)
            
            # Get available items
            available_items = list(self.content_items.keys())
            
            # Filter based on prerequisites and focus areas
            if session_config:
                available_items = self._filter_items(
                    available_items, student_model, session_config
                )
            
            if not available_items:
                # Fallback to basic items
                available_items = ['vocabulary_basic']
            
            # Select optimal item based on strategy
            if self.adaptation_strategy == AdaptationStrategy.DIFFICULTY_BASED:
                item_id = self._select_difficulty_based(student_id, available_items)
            elif self.adaptation_strategy == AdaptationStrategy.MASTERY_BASED:
                item_id = self._select_mastery_based(student_id, available_items)
            elif self.adaptation_strategy == AdaptationStrategy.SPACED_REPETITION:
                item_id = self._select_spaced_repetition_based(student_id, available_items)
            else:  # MIXED
                item_id = self._select_mixed_strategy(student_id, available_items)
            
            # Create recommendation
            if item_id and item_id in self.content_items:
                item = self.content_items[item_id]
                
                # Calculate success probability
                success_prob = self._calculate_success_probability(student_id, item_id)
                
                # Adjust difficulty for student
                adjusted_difficulty = self._adjust_difficulty_for_student(
                    student_id, item['difficulty']
                )
                
                recommendation = LearningRecommendation(
                    item_id=item_id,
                    item_type=item['type'],
                    difficulty=adjusted_difficulty,
                    estimated_time=item['estimated_time'],
                    reasoning=self._generate_recommendation_reasoning(
                        student_model, item, success_prob
                    ),
                    priority=self._calculate_item_priority(student_id, item_id),
                    knowledge_components=item['knowledge_components'],
                    success_probability=success_prob
                )
                
                self.logger.debug(f"Generated recommendation for {student_id}: {item_id}")
                return recommendation
            
            else:
                # Fallback recommendation
                return self._create_fallback_recommendation(student_id)
            
        except Exception as e:
            self.logger.error(f"Error generating recommendation: {e}")
            return self._create_fallback_recommendation(student_id)
    
    def _filter_items(self, available_items: List[str], student_model: StudentModel,
                     session_config: AdaptiveSession) -> List[str]:
        """Filter items based on session configuration and prerequisites."""
        try:
            filtered_items = []
            
            for item_id in available_items:
                if item_id not in self.content_items:
                    continue
                
                item = self.content_items[item_id]
                
                # Check focus areas
                if session_config.focus_areas:
                    if item['type'] not in session_config.focus_areas:
                        continue
                
                # Check difficulty range
                if session_config.difficulty_range:
                    min_diff, max_diff = session_config.difficulty_range
                    if not (min_diff <= item['difficulty'] <= max_diff):
                        continue
                
                # Check prerequisites
                prerequisites_met = True
                for prereq in item.get('prerequisites', []):
                    if prereq in student_model.knowledge_states:
                        if student_model.knowledge_states[prereq].mastery_level < 0.7:
                            prerequisites_met = False
                            break
                    else:
                        prerequisites_met = False
                        break
                
                if prerequisites_met:
                    filtered_items.append(item_id)
            
            return filtered_items
            
        except Exception as e:
            self.logger.error(f"Error filtering items: {e}")
            return available_items
    
    def _select_difficulty_based(self, student_id: str, 
                               available_items: List[str]) -> str:
        """Select item based on difficulty optimization."""
        try:
            student_model = self.get_student_model(student_id)
            optimal_difficulty = student_model.get_optimal_difficulty()
            
            best_item = ""
            min_difficulty_diff = float('inf')
            
            for item_id in available_items:
                if item_id not in self.content_items:
                    continue
                
                item_difficulty = self.content_items[item_id]['difficulty']
                difficulty_diff = abs(item_difficulty - optimal_difficulty)
                
                if difficulty_diff < min_difficulty_diff:
                    min_difficulty_diff = difficulty_diff
                    best_item = item_id
            
            return best_item or available_items[0]
            
        except Exception as e:
            self.logger.error(f"Error in difficulty-based selection: {e}")
            return available_items[0] if available_items else ""
    
    def _select_mastery_based(self, student_id: str, 
                            available_items: List[str]) -> str:
        """Select item to improve mastery."""
        try:
            student_model = self.get_student_model(student_id)
            
            # Find items with knowledge components that need work
            best_item = ""
            lowest_mastery = 1.0
            
            for item_id in available_items:
                if item_id not in self.content_items:
                    continue
                
                item = self.content_items[item_id]
                avg_mastery = 0.0
                
                for kc in item['knowledge_components']:
                    if kc in student_model.knowledge_states:
                        avg_mastery += student_model.knowledge_states[kc].mastery_level
                    else:
                        avg_mastery += 0.1  # Low mastery for unknown KC
                
                avg_mastery /= len(item['knowledge_components'])
                
                if avg_mastery < lowest_mastery:
                    lowest_mastery = avg_mastery
                    best_item = item_id
            
            return best_item or available_items[0]
            
        except Exception as e:
            self.logger.error(f"Error in mastery-based selection: {e}")
            return available_items[0] if available_items else ""
    
    def _select_spaced_repetition_based(self, student_id: str,
                                      available_items: List[str]) -> str:
        """Select item based on spaced repetition needs."""
        try:
            student_model = self.get_student_model(student_id)
            due_topics = student_model.get_next_topics(limit=10)
            
            # Find items that cover due topics
            for item_id in available_items:
                if item_id not in self.content_items:
                    continue
                
                item = self.content_items[item_id]
                for kc in item['knowledge_components']:
                    if kc in due_topics:
                        return item_id
            
            # Fallback to difficulty-based if no items are due
            return self._select_difficulty_based(student_id, available_items)
            
        except Exception as e:
            self.logger.error(f"Error in spaced repetition selection: {e}")
            return available_items[0] if available_items else ""
    
    def _select_mixed_strategy(self, student_id: str, 
                             available_items: List[str]) -> str:
        """Select item using mixed strategy (combination of approaches)."""
        try:
            # Get candidates from each strategy
            difficulty_item = self._select_difficulty_based(student_id, available_items)
            mastery_item = self._select_mastery_based(student_id, available_items)
            spaced_item = self._select_spaced_repetition_based(student_id, available_items)
            
            # Score each candidate
            candidates = {
                difficulty_item: 0.3,  # 30% weight for difficulty optimization
                mastery_item: 0.4,     # 40% weight for mastery improvement
                spaced_item: 0.3       # 30% weight for spaced repetition
            }
            
            # Select highest scoring item
            best_item = max(candidates.items(), key=lambda x: x[1])[0]
            return best_item
            
        except Exception as e:
            self.logger.error(f"Error in mixed strategy selection: {e}")
            return available_items[0] if available_items else ""
    
    def _calculate_success_probability(self, student_id: str, item_id: str) -> float:
        """Calculate probability of success for student on item."""
        try:
            # Use both IRT and BKT models
            irt_prob = self.irt_model.predict_success_probability(student_id, item_id)
            
            if item_id in self.content_items:
                kcs = self.content_items[item_id]['knowledge_components']
                bkt_prob = self.bkt_model.predict_success_probability(
                    student_id, item_id, kcs
                )
            else:
                bkt_prob = 0.5
            
            # Combine probabilities (weighted average)
            combined_prob = 0.6 * irt_prob + 0.4 * bkt_prob
            
            return max(0.01, min(0.99, combined_prob))
            
        except Exception as e:
            self.logger.error(f"Error calculating success probability: {e}")
            return 0.5
    
    def _adjust_difficulty_for_student(self, student_id: str, 
                                     base_difficulty: float) -> float:
        """Adjust item difficulty based on student's current state."""
        try:
            student_model = self.get_student_model(student_id)
            
            # Adjust based on recent performance
            if student_model.performance.accuracy_rate > 0.9:
                # Student doing very well, increase difficulty
                adjustment = 0.1
            elif student_model.performance.accuracy_rate < 0.6:
                # Student struggling, decrease difficulty
                adjustment = -0.2
            else:
                adjustment = 0.0
            
            # Adjust based on proficiency level
            proficiency_adjustments = {
                ProficiencyLevel.BEGINNER: -0.2,
                ProficiencyLevel.ELEMENTARY: -0.1,
                ProficiencyLevel.INTERMEDIATE: 0.0,
                ProficiencyLevel.UPPER_INTERMEDIATE: 0.1,
                ProficiencyLevel.ADVANCED: 0.2,
                ProficiencyLevel.PROFICIENT: 0.3
            }
            
            proficiency_adjustment = proficiency_adjustments.get(
                student_model.proficiency_level, 0.0
            )
            
            adjusted_difficulty = base_difficulty + adjustment + proficiency_adjustment
            return max(0.1, min(1.0, adjusted_difficulty))
            
        except Exception as e:
            self.logger.error(f"Error adjusting difficulty: {e}")
            return base_difficulty
    
    def _generate_recommendation_reasoning(self, student_model: StudentModel,
                                         item: Dict[str, Any], 
                                         success_prob: float) -> str:
        """Generate human-readable reasoning for recommendation."""
        try:
            reasoning_parts = []
            
            # Difficulty reasoning
            if success_prob > 0.8:
                reasoning_parts.append("This item matches your current skill level well")
            elif success_prob > 0.6:
                reasoning_parts.append("This item provides an appropriate challenge")
            else:
                reasoning_parts.append("This item will help you practice fundamental skills")
            
            # Knowledge component reasoning
            weak_kcs = []
            for kc in item['knowledge_components']:
                if kc in student_model.knowledge_states:
                    if student_model.knowledge_states[kc].mastery_level < 0.5:
                        weak_kcs.append(kc)
            
            if weak_kcs:
                reasoning_parts.append(f"Focuses on areas needing improvement: {', '.join(weak_kcs)}")
            
            # Performance reasoning
            if student_model.performance.current_streak > 3:
                reasoning_parts.append("Building on your current learning streak")
            elif student_model.performance.current_streak == 0:
                reasoning_parts.append("A good item to rebuild confidence")
            
            return ". ".join(reasoning_parts) + "."
            
        except Exception as e:
            self.logger.error(f"Error generating reasoning: {e}")
            return "Recommended based on your learning profile."
    
    def _calculate_item_priority(self, student_id: str, item_id: str) -> float:
        """Calculate priority score for an item."""
        try:
            if item_id not in self.content_items:
                return 0.5
            
            student_model = self.get_student_model(student_id)
            item = self.content_items[item_id]
            
            priority = 0.0
            
            # Priority based on knowledge component mastery
            for kc in item['knowledge_components']:
                if kc in student_model.knowledge_states:
                    # Lower mastery = higher priority
                    mastery = student_model.knowledge_states[kc].mastery_level
                    priority += (1.0 - mastery)
                else:
                    priority += 0.8  # High priority for new concepts
            
            # Average across knowledge components
            priority /= len(item['knowledge_components'])
            
            # Boost priority for items due for review
            due_topics = student_model.get_next_topics(limit=20)
            if any(kc in due_topics for kc in item['knowledge_components']):
                priority += 0.2
            
            return max(0.0, min(1.0, priority))
            
        except Exception as e:
            self.logger.error(f"Error calculating item priority: {e}")
            return 0.5
    
    def _create_fallback_recommendation(self, student_id: str) -> LearningRecommendation:
        """Create fallback recommendation when no suitable items found."""
        return LearningRecommendation(
            item_id="vocabulary_basic",
            item_type="vocabulary", 
            difficulty=0.5,
            estimated_time=5,
            reasoning="Basic vocabulary practice to start your learning journey.",
            priority=0.7,
            knowledge_components=["basic_vocabulary"],
            success_probability=0.7
        )
    
    def get_learning_path(self, student_id: str, target_items: int = 10) -> List[LearningRecommendation]:
        """
        Generate a sequence of learning recommendations.
        
        Args:
            student_id: Student identifier
            target_items: Number of items in the path
            
        Returns:
            List of learning recommendations in order
        """
        try:
            learning_path = []
            
            # Create session config for path generation
            session_config = AdaptiveSession(
                student_id=student_id,
                target_duration=target_items * 5,  # Estimate 5 min per item
                max_items=target_items,
                focus_areas=[],  # No restriction
                difficulty_range=(0.1, 1.0),  # Full range
                adaptation_strategy=self.adaptation_strategy
            )
            
            # Generate recommendations iteratively
            for i in range(target_items):
                recommendation = self.get_next_recommendation(student_id, session_config)
                learning_path.append(recommendation)
                
                # Simulate completing this item successfully for path planning
                # (This is a preview - actual performance would update models)
                
            self.logger.info(f"Generated learning path with {len(learning_path)} items")
            return learning_path
            
        except Exception as e:
            self.logger.error(f"Error generating learning path: {e}")
            return []
    
    def analyze_student_progress(self, student_id: str) -> Dict[str, Any]:
        """
        Analyze student's learning progress and provide insights.
        
        Args:
            student_id: Student identifier
            
        Returns:
            Progress analysis and insights
        """
        try:
            student_model = self.get_student_model(student_id)
            
            # Get basic insights from student model
            insights = student_model.get_learning_insights()
            
            # Add adaptive learning specific insights
            recent_sessions = student_model.session_history[-10:]  # Last 10 sessions
            
            if recent_sessions:
                # Learning velocity analysis
                recent_accuracy = [s['correct'] for s in recent_sessions]
                learning_trend = "improving" if sum(recent_accuracy[-5:]) > sum(recent_accuracy[:5]) else "stable"
                
                insights['learning_trend'] = learning_trend
                insights['recent_accuracy'] = sum(recent_accuracy) / len(recent_accuracy)
                
                # Difficulty optimization analysis
                optimal_difficulty = student_model.get_optimal_difficulty()
                insights['optimal_difficulty'] = optimal_difficulty
                insights['difficulty_recommendation'] = self._get_difficulty_recommendation(optimal_difficulty)
            
            # Knowledge component analysis
            kc_analysis = {}
            for kc, state in student_model.knowledge_states.items():
                kc_analysis[kc] = {
                    'mastery_level': state.mastery_level,
                    'confidence': state.confidence_level,
                    'practice_count': state.practice_count,
                    'needs_review': state.next_review and state.next_review <= datetime.now()
                }
            
            insights['knowledge_components'] = kc_analysis
            
            # Next steps recommendation
            next_recommendations = self.get_learning_path(student_id, 3)
            insights['next_steps'] = [
                {
                    'item': rec.item_id,
                    'type': rec.item_type,
                    'reasoning': rec.reasoning
                }
                for rec in next_recommendations
            ]
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error analyzing student progress: {e}")
            return {'error': str(e)}
    
    def _get_difficulty_recommendation(self, optimal_difficulty: float) -> str:
        """Get human-readable difficulty recommendation."""
        if optimal_difficulty < 0.3:
            return "Focus on easier content to build confidence"
        elif optimal_difficulty < 0.5:
            return "Continue with beginner-level content"
        elif optimal_difficulty < 0.7:
            return "Ready for intermediate content"
        elif optimal_difficulty < 0.85:
            return "Challenge yourself with advanced content"
        else:
            return "Explore expert-level materials"