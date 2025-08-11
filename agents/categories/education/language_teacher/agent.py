"""
Language Teacher Agent - AI-powered adaptive language learning agent.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import asdict

from autogen import ConversableAgent, GroupChat, GroupChatManager
from src.log_service import get_logger

# AI Components
from .ai.adaptive_learning import AdaptiveLearningEngine, AdaptiveSession, LearningRecommendation
from .ai.nlp_processor import NLPProcessor, SentenceAnalysis, ErrorType
from .ai.spaced_repetition import SpacedRepetitionSystem, ReviewResult, ReviewCard
from .ai.learning_analytics import LearningAnalytics, MetricType
from .ai.content_generator import ContentGenerator, ContentType, DifficultyLevel


class LanguageTeacherAgent:
    """
    AI-powered Language Teacher Agent using AutoGen framework.
    
    Features:
    - Adaptive learning with personalized difficulty adjustment
    - Natural language processing for error detection
    - Spaced repetition for optimal retention
    - Learning analytics and progress tracking
    - Dynamic content generation
    - Multi-agent conversation support
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Language Teacher Agent.
        
        Args:
            config: Configuration dictionary
        """
        self.logger = get_logger("language_teacher_agent")
        
        # Configuration
        self.config = config or {}
        self.target_language = self.config.get('target_language', 'english')
        self.agent_name = self.config.get('agent_name', 'LanguageTeacher')
        
        # Initialize AI components
        self.adaptive_engine = AdaptiveLearningEngine(self.config.get('adaptive_learning', {}))
        self.nlp_processor = NLPProcessor(self.target_language)
        self.spaced_repetition = SpacedRepetitionSystem(self.config.get('spaced_repetition', {}))
        self.learning_analytics = LearningAnalytics(self.config.get('analytics', {}))
        self.content_generator = ContentGenerator(self.config.get('content_generation', {}))
        
        # Student sessions
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.student_profiles: Dict[str, Dict[str, Any]] = {}
        
        # AutoGen agents
        self.teacher_agent: Optional[ConversableAgent] = None
        self.assessment_agent: Optional[ConversableAgent] = None
        self.content_agent: Optional[ConversableAgent] = None
        self.group_chat: Optional[GroupChat] = None
        self.group_chat_manager: Optional[GroupChatManager] = None
        
        # Performance tracking
        self.total_interactions = 0
        self.successful_lessons = 0
        self.avg_response_time = 0.0
        
        # Initialize AutoGen agents
        self._initialize_autogen_agents()
        
        self.logger.info(f"Initialized Language Teacher Agent for {self.target_language}")
    
    def _initialize_autogen_agents(self) -> None:
        """Initialize AutoGen agents for multi-agent conversation."""
        try:
            # Main teacher agent
            self.teacher_agent = ConversableAgent(
                name="LanguageTeacher",
                system_message=f"""
                You are an AI language teacher specializing in {self.target_language} instruction.
                You provide personalized, adaptive language learning experiences.
                
                Your capabilities include:
                - Assessing student proficiency and progress
                - Providing grammar and vocabulary instruction
                - Correcting errors with detailed explanations
                - Generating practice exercises
                - Offering encouragement and motivation
                
                Always be patient, encouraging, and adapt your teaching style to the student's level.
                Use the student's native language when necessary to explain complex concepts.
                Focus on practical, real-world language usage.
                """,
                llm_config={
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                human_input_mode="NEVER",
                code_execution_config=False
            )
            
            # Assessment specialist agent
            self.assessment_agent = ConversableAgent(
                name="AssessmentSpecialist",
                system_message="""
                You are an assessment specialist focused on evaluating language learning progress.
                Your role is to:
                - Analyze student responses for errors
                - Provide detailed feedback on grammar, vocabulary, and structure
                - Suggest specific areas for improvement
                - Track learning progress over time
                
                Be constructive and specific in your feedback.
                Always highlight what the student did well before addressing areas for improvement.
                """,
                llm_config={
                    "model": "gpt-4",
                    "temperature": 0.6,
                    "max_tokens": 800
                },
                human_input_mode="NEVER",
                code_execution_config=False
            )
            
            # Content generation agent
            self.content_agent = ConversableAgent(
                name="ContentCreator",
                system_message="""
                You are a content creation specialist for language learning.
                Your role is to:
                - Create engaging practice exercises
                - Generate relevant examples and scenarios
                - Adapt content difficulty to student level
                - Create conversation prompts and role-play scenarios
                
                Make content interesting, relevant, and appropriately challenging.
                Use real-world contexts that students can relate to.
                """,
                llm_config={
                    "model": "gpt-4",
                    "temperature": 0.8,
                    "max_tokens": 1200
                },
                human_input_mode="NEVER",
                code_execution_config=False
            )
            
            # Create group chat
            self.group_chat = GroupChat(
                agents=[self.teacher_agent, self.assessment_agent, self.content_agent],
                messages=[],
                max_round=6,
                speaker_selection_method="round_robin"
            )
            
            self.group_chat_manager = GroupChatManager(
                groupchat=self.group_chat,
                llm_config={
                    "model": "gpt-4",
                    "temperature": 0.5
                }
            )
            
            self.logger.debug("Initialized AutoGen agents")
            
        except Exception as e:
            self.logger.error(f"Error initializing AutoGen agents: {e}")
    
    async def start_learning_session(self, student_id: str, 
                                   session_preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Start a new learning session for a student.
        
        Args:
            student_id: Unique student identifier
            session_preferences: Session preferences and settings
            
        Returns:
            Session information and first activity
        """
        try:
            self.logger.info(f"Starting learning session for student {student_id}")
            
            # Get or create student profile
            if student_id not in self.student_profiles:
                self.student_profiles[student_id] = self._create_student_profile(student_id)
            
            student_profile = self.student_profiles[student_id]
            
            # Create adaptive session configuration
            session_config = AdaptiveSession(
                student_id=student_id,
                target_duration=session_preferences.get('duration_minutes', 15),
                max_items=session_preferences.get('max_items', 5),
                focus_areas=session_preferences.get('focus_areas', []),
                difficulty_range=(0.1, 1.0),
                adaptation_strategy=self.adaptive_engine.adaptation_strategy
            )
            
            # Start spaced repetition session
            srs_session_id = self.spaced_repetition.start_review_session(student_id)
            
            # Initialize session data
            session_data = {
                'session_id': f"session_{student_id}_{int(datetime.now().timestamp())}",
                'student_id': student_id,
                'start_time': datetime.now(),
                'session_config': session_config,
                'srs_session_id': srs_session_id,
                'completed_activities': [],
                'current_activity': None,
                'progress': {
                    'items_completed': 0,
                    'correct_answers': 0,
                    'total_attempts': 0,
                    'avg_response_time': 0.0
                }
            }
            
            self.active_sessions[student_id] = session_data
            
            # Get first learning recommendation
            first_activity = await self._get_next_activity(student_id)
            
            return {
                'session_id': session_data['session_id'],
                'welcome_message': self._generate_welcome_message(student_profile),
                'first_activity': first_activity,
                'session_info': {
                    'target_duration': session_config.target_duration,
                    'estimated_activities': session_config.max_items,
                    'focus_areas': session_config.focus_areas or ['general_practice']
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error starting learning session: {e}")
            return {
                'error': 'Failed to start learning session',
                'message': 'Please try again later'
            }
    
    async def process_student_response(self, student_id: str, response: str,
                                     activity_id: str = None,
                                     response_time: float = None) -> Dict[str, Any]:
        """
        Process student response and provide feedback.
        
        Args:
            student_id: Student identifier
            response: Student's response text
            activity_id: Current activity identifier
            response_time: Time taken to respond (seconds)
            
        Returns:
            Feedback and next activity
        """
        try:
            if student_id not in self.active_sessions:
                return {'error': 'No active session found'}
            
            session = self.active_sessions[student_id]
            current_activity = session.get('current_activity')
            
            if not current_activity:
                return {'error': 'No current activity'}
            
            start_time = datetime.now()
            
            # Analyze response with NLP processor
            analysis = self.nlp_processor.analyze_text(
                response, 
                current_activity.get('expected_response')
            )
            
            # Calculate correctness
            is_correct = self._evaluate_response_correctness(
                response, current_activity, analysis
            )
            
            # Update spaced repetition system
            if 'card_id' in current_activity:
                review_result = self._map_to_review_result(analysis, is_correct, response_time)
                self.spaced_repetition.review_card(
                    student_id, 
                    current_activity['card_id'], 
                    review_result,
                    response_time
                )
            
            # Update adaptive learning engine
            item_id = current_activity.get('content_id', activity_id or 'unknown')
            self.adaptive_engine.update_student_performance(
                student_id, item_id, is_correct, response_time
            )
            
            # Record learning analytics
            self.learning_analytics.record_metric(
                student_id, MetricType.ACCURACY, 1.0 if is_correct else 0.0
            )
            
            if response_time:
                speed_score = min(1.0, 10.0 / response_time)  # Normalize response time
                self.learning_analytics.record_metric(
                    student_id, MetricType.SPEED, speed_score
                )
            
            # Update session progress
            session['progress']['total_attempts'] += 1
            if is_correct:
                session['progress']['correct_answers'] += 1
            session['progress']['items_completed'] += 1
            
            # Generate feedback using multi-agent system
            feedback = await self._generate_feedback(
                student_id, response, analysis, current_activity, is_correct
            )
            
            # Get next activity
            next_activity = await self._get_next_activity(student_id)
            
            # Update current activity
            session['completed_activities'].append(current_activity)
            session['current_activity'] = next_activity
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self.avg_response_time = (
                (self.avg_response_time * self.total_interactions + processing_time) /
                (self.total_interactions + 1)
            )
            self.total_interactions += 1
            
            if is_correct:
                self.successful_lessons += 1
            
            return {
                'feedback': feedback,
                'next_activity': next_activity,
                'progress': session['progress'],
                'analysis': {
                    'is_correct': is_correct,
                    'errors_found': len(analysis.errors),
                    'complexity_score': analysis.complexity_score,
                    'vocabulary_level': analysis.vocabulary_level
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing student response: {e}")
            return {
                'error': 'Failed to process response',
                'feedback': 'Sorry, I encountered an error. Please try again.'
            }
    
    async def _get_next_activity(self, student_id: str) -> Dict[str, Any]:
        """Get next learning activity for student."""
        try:
            # Check for due spaced repetition cards first
            due_cards = self.spaced_repetition.get_due_cards(student_id, limit=1)
            
            if due_cards:
                # Create activity from due card
                card = due_cards[0]
                return self._create_activity_from_card(card)
            
            # Get adaptive learning recommendation
            recommendation = self.adaptive_engine.get_next_recommendation(student_id)
            
            if recommendation:
                # Generate content based on recommendation
                content = await self._generate_content_for_recommendation(recommendation)
                return content
            
            # Fallback: generate basic content
            return await self._generate_fallback_activity(student_id)
            
        except Exception as e:
            self.logger.error(f"Error getting next activity: {e}")
            return await self._generate_fallback_activity(student_id)
    
    def _create_activity_from_card(self, card: ReviewCard) -> Dict[str, Any]:
        """Create learning activity from spaced repetition card."""
        return {
            'activity_id': f"srs_{card.card_id}",
            'card_id': card.card_id,
            'type': 'spaced_repetition',
            'content_type': card.card_type,
            'title': f"Review: {card.content}",
            'content': json.loads(card.content) if isinstance(card.content, str) else card.content,
            'instructions': f"Review this {card.card_type} item from your spaced repetition deck.",
            'difficulty': card.difficulty_score,
            'estimated_time': 2,
            'knowledge_components': card.knowledge_components,
            'is_review': True
        }
    
    async def _generate_content_for_recommendation(self, recommendation: LearningRecommendation) -> Dict[str, Any]:
        """Generate content based on learning recommendation."""
        try:
            # Map recommendation to content type
            content_type_map = {
                'vocabulary': ContentType.VOCABULARY,
                'grammar': ContentType.GRAMMAR,
                'conversation': ContentType.CONVERSATION,
                'reading': ContentType.READING
            }
            
            content_type = content_type_map.get(
                recommendation.item_type,
                ContentType.VOCABULARY
            )
            
            # Map difficulty
            difficulty_map = {
                0.0: DifficultyLevel.BEGINNER,
                0.2: DifficultyLevel.ELEMENTARY,
                0.4: DifficultyLevel.INTERMEDIATE,
                0.6: DifficultyLevel.UPPER_INTERMEDIATE,
                0.8: DifficultyLevel.ADVANCED
            }
            
            difficulty_level = DifficultyLevel.INTERMEDIATE
            for threshold, level in difficulty_map.items():
                if recommendation.difficulty >= threshold:
                    difficulty_level = level
            
            # Generate content
            if content_type == ContentType.VOCABULARY:
                content_list = self.content_generator.generate_vocabulary_content(
                    difficulty_level, count=1
                )
                generated_content = content_list[0] if content_list else None
            elif content_type == ContentType.GRAMMAR:
                generated_content = self.content_generator.generate_grammar_content(difficulty_level)
            elif content_type == ContentType.CONVERSATION:
                generated_content = self.content_generator.generate_conversation_content(difficulty_level)
            elif content_type == ContentType.READING:
                generated_content = self.content_generator.generate_reading_content(difficulty_level)
            else:
                generated_content = None
            
            if generated_content:
                # Add to spaced repetition system if it's a vocabulary item
                if content_type == ContentType.VOCABULARY:
                    card = self.spaced_repetition.add_card(
                        generated_content.content_id,
                        json.dumps(generated_content.content),
                        content_type.value,
                        generated_content.knowledge_components
                    )
                    self.spaced_repetition.add_card_to_student_deck(
                        recommendation.item_id.split('_')[0],  # Extract student_id if present
                        card.card_id
                    )
                
                return {
                    'activity_id': generated_content.content_id,
                    'content_id': generated_content.content_id,
                    'type': 'adaptive_learning',
                    'content_type': content_type.value,
                    'title': generated_content.title,
                    'content': generated_content.content,
                    'instructions': generated_content.instructions,
                    'expected_response': generated_content.expected_response,
                    'hints': generated_content.hints,
                    'difficulty': recommendation.difficulty,
                    'estimated_time': generated_content.estimated_time,
                    'knowledge_components': generated_content.knowledge_components,
                    'reasoning': recommendation.reasoning,
                    'is_review': False
                }
            
            return await self._generate_fallback_activity('')
            
        except Exception as e:
            self.logger.error(f"Error generating content for recommendation: {e}")
            return await self._generate_fallback_activity('')
    
    async def _generate_fallback_activity(self, student_id: str) -> Dict[str, Any]:
        """Generate fallback activity when other methods fail."""
        return {
            'activity_id': f"fallback_{int(datetime.now().timestamp())}",
            'type': 'basic_practice',
            'content_type': 'vocabulary',
            'title': 'Basic Vocabulary Practice',
            'content': {
                'word': 'hello',
                'definition': 'A greeting used when meeting someone',
                'example': 'Hello, how are you today?'
            },
            'instructions': 'Practice using this word in a sentence.',
            'expected_response': 'hello',
            'hints': ['This is a common greeting', 'Used when you meet someone'],
            'difficulty': 0.3,
            'estimated_time': 3,
            'knowledge_components': ['basic_vocabulary', 'greetings'],
            'is_review': False
        }
    
    def _evaluate_response_correctness(self, response: str, activity: Dict[str, Any],
                                     analysis: SentenceAnalysis) -> bool:
        """Evaluate if student response is correct."""
        try:
            expected = activity.get('expected_response', '').lower().strip()
            actual = response.lower().strip()
            
            # Direct match
            if expected and actual == expected:
                return True
            
            # Semantic similarity for open-ended responses
            if expected and len(expected) > 0:
                similarity = self.nlp_processor.calculate_semantic_similarity(actual, expected)
                if similarity.similarity_score > 0.7:
                    return True
            
            # Check for major errors
            critical_errors = [
                error for error in analysis.errors 
                if error.error_type in [ErrorType.GRAMMAR, ErrorType.SEMANTIC] and error.severity > 0.7
            ]
            
            if critical_errors:
                return False
            
            # For practice activities without specific expected responses
            if not expected:
                # Consider correct if no major errors and reasonable complexity
                return len(analysis.errors) < 3 and len(actual.split()) >= 3
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error evaluating response correctness: {e}")
            return False
    
    def _map_to_review_result(self, analysis: SentenceAnalysis, is_correct: bool,
                            response_time: float = None) -> ReviewResult:
        """Map analysis results to spaced repetition review result."""
        try:
            if not is_correct:
                return ReviewResult.AGAIN
            
            # Consider response time and error count
            error_count = len(analysis.errors)
            
            if error_count == 0:
                if response_time and response_time < 5:  # Fast and correct
                    return ReviewResult.EASY
                else:
                    return ReviewResult.GOOD
            elif error_count <= 2:
                return ReviewResult.HARD
            else:
                return ReviewResult.AGAIN
                
        except Exception as e:
            self.logger.error(f"Error mapping to review result: {e}")
            return ReviewResult.GOOD
    
    async def _generate_feedback(self, student_id: str, response: str,
                               analysis: SentenceAnalysis, activity: Dict[str, Any],
                               is_correct: bool) -> str:
        """Generate feedback using multi-agent system."""
        try:
            # Prepare context for agents
            context = {
                'student_response': response,
                'expected_response': activity.get('expected_response', ''),
                'activity_type': activity.get('content_type', 'practice'),
                'is_correct': is_correct,
                'errors_found': [
                    {
                        'type': error.error_type.value,
                        'original': error.original_text,
                        'corrected': error.corrected_text,
                        'explanation': error.explanation
                    }
                    for error in analysis.errors[:3]  # Limit to 3 errors
                ],
                'complexity_score': analysis.complexity_score,
                'vocabulary_level': analysis.vocabulary_level
            }
            
            # Create feedback request message
            feedback_request = f"""
            Please provide feedback for this student response:
            
            Student Response: "{response}"
            Expected Response: "{activity.get('expected_response', 'Open-ended')}"
            Activity Type: {activity.get('content_type', 'practice')}
            Correctness: {'Correct' if is_correct else 'Incorrect'}
            
            Analysis Results:
            - Errors Found: {len(analysis.errors)}
            - Vocabulary Level: {analysis.vocabulary_level}
            - Complexity Score: {analysis.complexity_score:.2f}
            
            Error Details:
            {json.dumps(context['errors_found'], indent=2)}
            
            Please provide encouraging, constructive feedback that:
            1. Acknowledges what the student did well
            2. Addresses any errors with clear explanations
            3. Provides specific suggestions for improvement
            4. Encourages continued learning
            """
            
            # Use AutoGen agents to generate feedback
            if self.teacher_agent and self.group_chat_manager:
                # Start conversation with teacher agent
                response_msg = await self.teacher_agent.a_generate_reply(
                    messages=[{"role": "user", "content": feedback_request}]
                )
                
                if response_msg:
                    return response_msg.get('content', 'Great effort! Keep practicing.')
            
            # Fallback to NLP processor feedback
            return self.nlp_processor.generate_feedback(analysis)
            
        except Exception as e:
            self.logger.error(f"Error generating feedback: {e}")
            # Fallback feedback
            if is_correct:
                return "✅ Excellent work! Your response is correct. Keep up the great progress!"
            else:
                return "Good effort! Let's work on improving this together. Keep practicing!"
    
    def _generate_welcome_message(self, student_profile: Dict[str, Any]) -> str:
        """Generate personalized welcome message."""
        try:
            name = student_profile.get('name', 'there')
            level = student_profile.get('proficiency_level', 'beginner')
            
            messages = [
                f"Hello {name}! Ready for today's {self.target_language} practice?",
                f"Welcome back, {name}! Let's continue your {self.target_language} learning journey.",
                f"Hi {name}! Time for some engaging {self.target_language} exercises.",
                f"Great to see you, {name}! Let's practice {self.target_language} together."
            ]
            
            import random
            base_message = random.choice(messages)
            
            level_encouragement = {
                'beginner': "We'll start with the basics and build your confidence step by step.",
                'elementary': "You're making great progress! Let's continue building your skills.",
                'intermediate': "Your skills are developing well! Ready for some new challenges?",
                'advanced': "Impressive progress! Let's refine your advanced language abilities."
            }
            
            encouragement = level_encouragement.get(level, "Let's learn together!")
            
            return f"{base_message} {encouragement}"
            
        except Exception as e:
            self.logger.error(f"Error generating welcome message: {e}")
            return f"Welcome to your {self.target_language} learning session! Let's get started."
    
    def _create_student_profile(self, student_id: str) -> Dict[str, Any]:
        """Create initial student profile."""
        return {
            'student_id': student_id,
            'name': student_id,  # Use ID as default name
            'proficiency_level': 'beginner',
            'target_language': self.target_language,
            'learning_preferences': {
                'session_length': 15,
                'focus_areas': [],
                'learning_style': 'mixed'
            },
            'created_at': datetime.now(),
            'last_active': datetime.now()
        }
    
    async def end_learning_session(self, student_id: str) -> Dict[str, Any]:
        """End learning session and provide summary."""
        try:
            if student_id not in self.active_sessions:
                return {'error': 'No active session found'}
            
            session = self.active_sessions[student_id]
            
            # End spaced repetition session
            srs_stats = self.spaced_repetition.end_review_session(
                session['srs_session_id']
            )
            
            # Calculate session duration
            end_time = datetime.now()
            duration = end_time - session['start_time']
            
            # Record session in learning analytics
            session_data = {
                'session_id': session['session_id'],
                'duration_minutes': duration.total_seconds() / 60,
                'items_completed': session['progress']['items_completed'],
                'accuracy': (
                    session['progress']['correct_answers'] / 
                    max(1, session['progress']['total_attempts'])
                ),
                'engagement_score': min(1.0, session['progress']['items_completed'] / 5),
                'session_type': 'practice'
            }
            
            self.learning_analytics.record_session(student_id, session_data)
            
            # Generate session summary
            summary = {
                'session_id': session['session_id'],
                'duration_minutes': round(duration.total_seconds() / 60, 1),
                'activities_completed': len(session['completed_activities']),
                'accuracy_rate': round(session_data['accuracy'], 2),
                'time_per_activity': round(
                    duration.total_seconds() / max(1, len(session['completed_activities'])) / 60, 1
                ),
                'areas_practiced': list(set([
                    activity.get('content_type', 'unknown')
                    for activity in session['completed_activities']
                ])),
                'achievements': self._generate_session_achievements(session_data),
                'next_session_recommendations': await self._generate_next_session_recommendations(student_id)
            }
            
            # Clean up session
            del self.active_sessions[student_id]
            
            return {
                'summary': summary,
                'goodbye_message': self._generate_goodbye_message(session_data),
                'spaced_repetition_stats': srs_stats
            }
            
        except Exception as e:
            self.logger.error(f"Error ending learning session: {e}")
            return {'error': 'Failed to end session properly'}
    
    def _generate_session_achievements(self, session_data: Dict[str, Any]) -> List[str]:
        """Generate achievements for the session."""
        achievements = []
        
        try:
            accuracy = session_data.get('accuracy', 0)
            items_completed = session_data.get('items_completed', 0)
            duration = session_data.get('duration_minutes', 0)
            
            if accuracy >= 0.9:
                achievements.append("🎯 Excellent Accuracy - 90%+ correct!")
            elif accuracy >= 0.8:
                achievements.append("🎯 Great Accuracy - 80%+ correct!")
            elif accuracy >= 0.7:
                achievements.append("🎯 Good Accuracy - 70%+ correct!")
            
            if items_completed >= 10:
                achievements.append("🔥 High Productivity - 10+ activities completed!")
            elif items_completed >= 5:
                achievements.append("⚡ Good Progress - 5+ activities completed!")
            
            if duration >= 15:
                achievements.append("⏰ Dedicated Learner - 15+ minutes of practice!")
            elif duration >= 10:
                achievements.append("📚 Consistent Practice - 10+ minutes!")
            
            if not achievements:
                achievements.append("🌟 Practice Makes Perfect - Keep it up!")
            
            return achievements
            
        except Exception as e:
            self.logger.error(f"Error generating achievements: {e}")
            return ["🌟 Great effort in today's session!"]
    
    async def _generate_next_session_recommendations(self, student_id: str) -> List[str]:
        """Generate recommendations for next session."""
        try:
            # Get learning insights
            insights = self.learning_analytics.generate_insights(student_id)
            recommendations = []
            
            for insight in insights[:3]:  # Top 3 insights
                if insight.insight_type == "weakness":
                    recommendations.append(f"Focus on {insight.title}")
                elif insight.insight_type == "positive_trend":
                    recommendations.append(f"Continue working on {insight.title}")
                else:
                    recommendations.append(insight.recommendation[:100])
            
            # Add spaced repetition recommendations
            due_cards = self.spaced_repetition.get_due_cards(student_id, limit=5)
            if due_cards:
                recommendations.append(f"Review {len(due_cards)} items from your spaced repetition deck")
            
            if not recommendations:
                recommendations = [
                    "Continue regular practice to maintain progress",
                    "Try varying your practice topics for balanced learning",
                    "Focus on areas where you feel less confident"
                ]
            
            return recommendations[:3]  # Limit to 3 recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating next session recommendations: {e}")
            return ["Continue regular practice for best results"]
    
    def _generate_goodbye_message(self, session_data: Dict[str, Any]) -> str:
        """Generate personalized goodbye message."""
        try:
            accuracy = session_data.get('accuracy', 0)
            items_completed = session_data.get('items_completed', 0)
            
            if accuracy >= 0.8 and items_completed >= 5:
                message = "Outstanding session! Your hard work is really paying off. 🌟"
            elif accuracy >= 0.7:
                message = "Great job today! You're making excellent progress. 👏"
            elif items_completed >= 5:
                message = "Impressive dedication! You completed many activities today. 🔥"
            else:
                message = "Thank you for practicing today! Every session helps you improve. 💪"
            
            return f"{message} See you next time for more {self.target_language} learning!"
            
        except Exception as e:
            self.logger.error(f"Error generating goodbye message: {e}")
            return f"Thanks for practicing {self.target_language} today! See you next time! 👋"
    
    def get_student_progress(self, student_id: str) -> Dict[str, Any]:
        """Get comprehensive student progress report."""
        try:
            # Get analytics report
            analytics_report = self.learning_analytics.get_comprehensive_report(student_id)
            
            # Get spaced repetition statistics
            srs_stats = self.spaced_repetition.get_student_statistics(student_id)
            
            # Get adaptive learning progress
            student_model = self.adaptive_engine.get_student_model(student_id)
            learning_insights = student_model.get_learning_insights()
            
            return {
                'student_id': student_id,
                'generated_at': datetime.now().isoformat(),
                'learning_analytics': analytics_report,
                'spaced_repetition': srs_stats,
                'adaptive_learning': learning_insights,
                'overall_assessment': {
                    'proficiency_level': learning_insights.get('proficiency_level', 'beginner'),
                    'total_study_time': learning_insights.get('study_time', '0:00:00'),
                    'sessions_completed': learning_insights.get('sessions_completed', 0),
                    'retention_rate': srs_stats.get('retention_rate', 0),
                    'learning_velocity': learning_insights.get('overall_progress', {}).get('progress_rate', 0)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting student progress: {e}")
            return {'error': 'Failed to generate progress report'}
    
    def get_agent_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics."""
        try:
            success_rate = (
                self.successful_lessons / max(1, self.total_interactions)
            )
            
            return {
                'total_interactions': self.total_interactions,
                'successful_lessons': self.successful_lessons,
                'success_rate': round(success_rate, 3),
                'avg_response_time': round(self.avg_response_time, 3),
                'active_sessions': len(self.active_sessions),
                'total_students': len(self.student_profiles),
                'target_language': self.target_language,
                'agent_name': self.agent_name,
                'uptime': str(datetime.now() - datetime.now()),  # Placeholder
                'components_status': {
                    'adaptive_learning': 'active',
                    'nlp_processor': 'active', 
                    'spaced_repetition': 'active',
                    'learning_analytics': 'active',
                    'content_generator': 'active',
                    'autogen_agents': 'active' if self.teacher_agent else 'inactive'
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting agent metrics: {e}")
            return {'error': 'Failed to retrieve metrics'}