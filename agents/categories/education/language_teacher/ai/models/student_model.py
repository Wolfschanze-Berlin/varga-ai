"""
Student Model for tracking individual learner characteristics and progress.
"""

import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import numpy as np

from src.log_service import get_logger


class LearningStyle(Enum):
    """Learning style preferences."""
    VISUAL = "visual"
    AUDITORY = "auditory" 
    KINESTHETIC = "kinesthetic"
    READING = "reading"


class ProficiencyLevel(Enum):
    """Language proficiency levels."""
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    UPPER_INTERMEDIATE = "upper_intermediate"
    ADVANCED = "advanced"
    PROFICIENT = "proficient"


@dataclass
class LearningPreferences:
    """Student learning preferences and settings."""
    learning_style: LearningStyle = LearningStyle.VISUAL
    difficulty_preference: float = 0.7  # 0-1 scale
    session_length: int = 15  # minutes
    review_frequency: str = "daily"
    focus_areas: List[str] = None
    
    def __post_init__(self):
        if self.focus_areas is None:
            self.focus_areas = ["vocabulary", "grammar", "conversation"]


@dataclass
class PerformanceMetrics:
    """Student performance tracking."""
    accuracy_rate: float = 0.0
    completion_rate: float = 0.0
    engagement_score: float = 0.0
    learning_velocity: float = 0.0  # concepts per hour
    retention_rate: float = 0.0
    
    # Response time metrics
    avg_response_time: float = 0.0
    response_time_variance: float = 0.0
    
    # Streak tracking
    current_streak: int = 0
    max_streak: int = 0
    
    # Error analysis
    common_errors: Dict[str, int] = None
    improvement_areas: List[str] = None
    
    def __post_init__(self):
        if self.common_errors is None:
            self.common_errors = {}
        if self.improvement_areas is None:
            self.improvement_areas = []


@dataclass
class KnowledgeState:
    """Student's knowledge state per topic/skill."""
    topic: str
    mastery_level: float = 0.0  # 0-1 scale
    confidence_level: float = 0.0
    last_practiced: Optional[datetime] = None
    practice_count: int = 0
    correct_answers: int = 0
    total_attempts: int = 0
    forgetting_rate: float = 0.1  # For spaced repetition
    next_review: Optional[datetime] = None


class StudentModel:
    """
    Comprehensive student model for personalized learning.
    
    This model tracks:
    - Learning preferences and style
    - Performance metrics and progress
    - Knowledge state per topic
    - Behavioral patterns
    - Optimal learning parameters
    """
    
    def __init__(self, student_id: str, target_language: str = "english"):
        """
        Initialize student model.
        
        Args:
            student_id: Unique identifier for student
            target_language: Language being learned
        """
        self.logger = get_logger(f"student_model_{student_id}")
        
        # Basic info
        self.student_id = student_id
        self.target_language = target_language
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        
        # Learning profile
        self.proficiency_level = ProficiencyLevel.BEGINNER
        self.preferences = LearningPreferences()
        self.performance = PerformanceMetrics()
        
        # Knowledge tracking
        self.knowledge_states: Dict[str, KnowledgeState] = {}
        self.mastered_concepts: List[str] = []
        self.struggling_concepts: List[str] = []
        
        # Learning history
        self.session_history: List[Dict[str, Any]] = []
        self.total_study_time: timedelta = timedelta()
        self.total_sessions: int = 0
        
        # Adaptive parameters
        self.optimal_difficulty: float = 0.7
        self.learning_rate: float = 0.1
        self.forgetting_curve_params: Dict[str, float] = {
            'initial_strength': 1.0,
            'decay_rate': 0.05
        }
        
        self.logger.info(f"Initialized student model for {student_id}")
    
    def update_performance(self, session_data: Dict[str, Any]) -> None:
        """
        Update performance metrics based on session data.
        
        Args:
            session_data: Dictionary containing session performance data
        """
        try:
            # Extract metrics from session
            accuracy = session_data.get('accuracy', 0.0)
            completion = session_data.get('completion_rate', 0.0)
            engagement = session_data.get('engagement_score', 0.0)
            response_times = session_data.get('response_times', [])
            
            # Update performance with exponential moving average
            alpha = 0.3  # Learning rate
            self.performance.accuracy_rate = (
                alpha * accuracy + (1 - alpha) * self.performance.accuracy_rate
            )
            self.performance.completion_rate = (
                alpha * completion + (1 - alpha) * self.performance.completion_rate
            )
            self.performance.engagement_score = (
                alpha * engagement + (1 - alpha) * self.performance.engagement_score
            )
            
            # Update response time metrics
            if response_times:
                avg_time = np.mean(response_times)
                self.performance.avg_response_time = (
                    alpha * avg_time + (1 - alpha) * self.performance.avg_response_time
                )
                self.performance.response_time_variance = np.var(response_times)
            
            # Update streak
            if accuracy > 0.8:  # Good session threshold
                self.performance.current_streak += 1
                self.performance.max_streak = max(
                    self.performance.max_streak, 
                    self.performance.current_streak
                )
            else:
                self.performance.current_streak = 0
            
            # Track common errors
            errors = session_data.get('errors', [])
            for error in errors:
                error_type = error.get('type', 'unknown')
                self.performance.common_errors[error_type] = (
                    self.performance.common_errors.get(error_type, 0) + 1
                )
            
            # Update learning velocity
            concepts_learned = len(session_data.get('new_concepts', []))
            session_duration = session_data.get('duration_minutes', 0)
            if session_duration > 0:
                velocity = concepts_learned / (session_duration / 60)  # concepts per hour
                self.performance.learning_velocity = (
                    alpha * velocity + (1 - alpha) * self.performance.learning_velocity
                )
            
            self.last_updated = datetime.now()
            self.logger.info(f"Updated performance for student {self.student_id}")
            
        except Exception as e:
            self.logger.error(f"Error updating performance: {e}")
    
    def update_knowledge_state(self, topic: str, correct: bool, 
                             response_time: float = None) -> None:
        """
        Update knowledge state for a specific topic.
        
        Args:
            topic: Topic/skill being practiced
            correct: Whether the response was correct
            response_time: Time taken to respond (optional)
        """
        try:
            # Get or create knowledge state
            if topic not in self.knowledge_states:
                self.knowledge_states[topic] = KnowledgeState(topic=topic)
            
            state = self.knowledge_states[topic]
            
            # Update attempt counts
            state.total_attempts += 1
            if correct:
                state.correct_answers += 1
            
            # Calculate new mastery level using IRT-inspired approach
            success_rate = state.correct_answers / state.total_attempts
            
            # Adjust for response time if available
            time_factor = 1.0
            if response_time is not None and response_time > 0:
                # Faster responses indicate better mastery
                avg_time = self.performance.avg_response_time
                if avg_time > 0:
                    time_factor = min(2.0, avg_time / response_time)
            
            # Update mastery with exponential moving average
            new_mastery = success_rate * time_factor
            alpha = 0.2
            state.mastery_level = (
                alpha * new_mastery + (1 - alpha) * state.mastery_level
            )
            
            # Update confidence based on consistency
            if state.total_attempts >= 5:
                recent_performance = state.correct_answers / state.total_attempts
                variance = abs(recent_performance - state.mastery_level)
                state.confidence_level = max(0.0, 1.0 - variance)
            
            # Calculate forgetting rate based on performance
            if correct:
                state.forgetting_rate *= 0.95  # Decrease forgetting rate
            else:
                state.forgetting_rate = min(0.3, state.forgetting_rate * 1.05)
            
            state.last_practiced = datetime.now()
            state.practice_count += 1
            
            # Schedule next review using spaced repetition
            self._schedule_next_review(state)
            
            # Update concept lists
            self._update_concept_lists(topic, state.mastery_level)
            
            self.logger.debug(
                f"Updated knowledge state for {topic}: "
                f"mastery={state.mastery_level:.2f}, "
                f"confidence={state.confidence_level:.2f}"
            )
            
        except Exception as e:
            self.logger.error(f"Error updating knowledge state for {topic}: {e}")
    
    def _schedule_next_review(self, state: KnowledgeState) -> None:
        """Schedule next review based on spaced repetition algorithm."""
        try:
            base_interval = 1  # days
            
            # Adjust interval based on mastery and forgetting rate
            mastery_factor = max(1.0, state.mastery_level * 3)
            forgetting_factor = 1 / (state.forgetting_rate + 0.1)
            
            interval_days = base_interval * mastery_factor * forgetting_factor
            interval_days = min(30, max(1, interval_days))  # Clamp between 1-30 days
            
            state.next_review = datetime.now() + timedelta(days=interval_days)
            
        except Exception as e:
            self.logger.error(f"Error scheduling review: {e}")
    
    def _update_concept_lists(self, topic: str, mastery_level: float) -> None:
        """Update mastered and struggling concept lists."""
        try:
            # Remove from both lists first
            if topic in self.mastered_concepts:
                self.mastered_concepts.remove(topic)
            if topic in self.struggling_concepts:
                self.struggling_concepts.remove(topic)
            
            # Add to appropriate list
            if mastery_level >= 0.85:
                self.mastered_concepts.append(topic)
            elif mastery_level < 0.5:
                self.struggling_concepts.append(topic)
                
        except Exception as e:
            self.logger.error(f"Error updating concept lists: {e}")
    
    def get_optimal_difficulty(self, topic: str = None) -> float:
        """
        Get optimal difficulty level for student.
        
        Args:
            topic: Specific topic (optional)
            
        Returns:
            Optimal difficulty level (0-1)
        """
        try:
            if topic and topic in self.knowledge_states:
                state = self.knowledge_states[topic]
                # Adjust difficulty based on mastery
                if state.mastery_level > 0.8:
                    return min(1.0, self.optimal_difficulty + 0.1)
                elif state.mastery_level < 0.5:
                    return max(0.3, self.optimal_difficulty - 0.2)
            
            return self.optimal_difficulty
            
        except Exception as e:
            self.logger.error(f"Error getting optimal difficulty: {e}")
            return 0.7
    
    def get_next_topics(self, limit: int = 5) -> List[str]:
        """
        Get next topics for practice based on spaced repetition.
        
        Args:
            limit: Maximum number of topics to return
            
        Returns:
            List of topic names
        """
        try:
            now = datetime.now()
            due_topics = []
            
            for topic, state in self.knowledge_states.items():
                if state.next_review and state.next_review <= now:
                    priority = self._calculate_topic_priority(state)
                    due_topics.append((topic, priority))
            
            # Sort by priority (higher first)
            due_topics.sort(key=lambda x: x[1], reverse=True)
            
            return [topic for topic, _ in due_topics[:limit]]
            
        except Exception as e:
            self.logger.error(f"Error getting next topics: {e}")
            return []
    
    def _calculate_topic_priority(self, state: KnowledgeState) -> float:
        """Calculate priority score for a topic."""
        try:
            # Base priority on mastery level (lower mastery = higher priority)
            mastery_priority = 1.0 - state.mastery_level
            
            # Add time-based urgency
            if state.next_review:
                days_overdue = (datetime.now() - state.next_review).days
                time_priority = max(0, days_overdue * 0.1)
            else:
                time_priority = 1.0  # New topics have high priority
            
            # Add forgetting curve factor
            forgetting_priority = state.forgetting_rate
            
            return mastery_priority + time_priority + forgetting_priority
            
        except Exception as e:
            self.logger.error(f"Error calculating topic priority: {e}")
            return 0.5
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """
        Get insights about student's learning progress.
        
        Returns:
            Dictionary of learning insights
        """
        try:
            insights = {
                'proficiency_level': self.proficiency_level.value,
                'overall_progress': {
                    'accuracy': self.performance.accuracy_rate,
                    'completion': self.performance.completion_rate,
                    'engagement': self.performance.engagement_score,
                    'streak': self.performance.current_streak
                },
                'knowledge_summary': {
                    'total_topics': len(self.knowledge_states),
                    'mastered_topics': len(self.mastered_concepts),
                    'struggling_topics': len(self.struggling_concepts)
                },
                'learning_style': self.preferences.learning_style.value,
                'optimal_difficulty': self.optimal_difficulty,
                'study_time': str(self.total_study_time),
                'sessions_completed': self.total_sessions
            }
            
            # Add recommendations
            insights['recommendations'] = self._generate_recommendations()
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error getting learning insights: {e}")
            return {}
    
    def _generate_recommendations(self) -> List[str]:
        """Generate personalized learning recommendations."""
        recommendations = []
        
        try:
            # Performance-based recommendations
            if self.performance.accuracy_rate < 0.6:
                recommendations.append("Consider reviewing fundamentals and reducing difficulty")
            elif self.performance.accuracy_rate > 0.9:
                recommendations.append("Try more challenging content to accelerate learning")
            
            if self.performance.engagement_score < 0.5:
                recommendations.append("Consider shorter sessions or different content types")
            
            # Knowledge-based recommendations
            if len(self.struggling_concepts) > 5:
                recommendations.append("Focus on struggling concepts before learning new material")
            
            if len(self.mastered_concepts) > len(self.struggling_concepts) * 2:
                recommendations.append("Ready for more advanced topics")
            
            # Streak-based recommendations
            if self.performance.current_streak > 7:
                recommendations.append("Great consistency! Consider increasing session difficulty")
            elif self.performance.current_streak == 0:
                recommendations.append("Take a break or try easier content to rebuild confidence")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return ["Continue practicing regularly for best results"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert student model to dictionary for serialization."""
        try:
            return {
                'student_id': self.student_id,
                'target_language': self.target_language,
                'created_at': self.created_at.isoformat(),
                'last_updated': self.last_updated.isoformat(),
                'proficiency_level': self.proficiency_level.value,
                'preferences': asdict(self.preferences),
                'performance': asdict(self.performance),
                'knowledge_states': {
                    topic: {
                        'topic': state.topic,
                        'mastery_level': state.mastery_level,
                        'confidence_level': state.confidence_level,
                        'last_practiced': state.last_practiced.isoformat() if state.last_practiced else None,
                        'practice_count': state.practice_count,
                        'correct_answers': state.correct_answers,
                        'total_attempts': state.total_attempts,
                        'forgetting_rate': state.forgetting_rate,
                        'next_review': state.next_review.isoformat() if state.next_review else None
                    }
                    for topic, state in self.knowledge_states.items()
                },
                'mastered_concepts': self.mastered_concepts,
                'struggling_concepts': self.struggling_concepts,
                'total_study_time': str(self.total_study_time),
                'total_sessions': self.total_sessions,
                'optimal_difficulty': self.optimal_difficulty
            }
            
        except Exception as e:
            self.logger.error(f"Error converting to dict: {e}")
            return {}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StudentModel':
        """Create StudentModel from dictionary."""
        try:
            model = cls(
                student_id=data['student_id'],
                target_language=data.get('target_language', 'english')
            )
            
            # Restore basic info
            model.created_at = datetime.fromisoformat(data['created_at'])
            model.last_updated = datetime.fromisoformat(data['last_updated'])
            model.proficiency_level = ProficiencyLevel(data['proficiency_level'])
            
            # Restore preferences
            prefs_data = data.get('preferences', {})
            model.preferences = LearningPreferences(
                learning_style=LearningStyle(prefs_data.get('learning_style', 'visual')),
                difficulty_preference=prefs_data.get('difficulty_preference', 0.7),
                session_length=prefs_data.get('session_length', 15),
                review_frequency=prefs_data.get('review_frequency', 'daily'),
                focus_areas=prefs_data.get('focus_areas', ['vocabulary', 'grammar'])
            )
            
            # Restore performance (this is complex due to nested structure)
            perf_data = data.get('performance', {})
            model.performance = PerformanceMetrics()
            for key, value in perf_data.items():
                if hasattr(model.performance, key):
                    setattr(model.performance, key, value)
            
            # Restore knowledge states
            for topic, state_data in data.get('knowledge_states', {}).items():
                state = KnowledgeState(topic=topic)
                for key, value in state_data.items():
                    if key in ['last_practiced', 'next_review'] and value:
                        setattr(state, key, datetime.fromisoformat(value))
                    else:
                        setattr(state, key, value)
                model.knowledge_states[topic] = state
            
            # Restore lists and other attributes
            model.mastered_concepts = data.get('mastered_concepts', [])
            model.struggling_concepts = data.get('struggling_concepts', [])
            model.total_sessions = data.get('total_sessions', 0)
            model.optimal_difficulty = data.get('optimal_difficulty', 0.7)
            
            return model
            
        except Exception as e:
            get_logger("student_model").error(f"Error loading from dict: {e}")
            # Return basic model if loading fails
            return cls(data.get('student_id', 'unknown'))