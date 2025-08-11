"""
Integration module for Language Teacher Agent with Telegram bot and other systems.
"""

import asyncio
import json
import yaml
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from src.log_service import get_logger
from .agent import LanguageTeacherAgent


class LanguageTeacherIntegration:
    """
    Integration layer for Language Teacher Agent.
    
    Provides interfaces for:
    - Telegram bot integration
    - Configuration management
    - Session persistence
    - Metrics collection
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize integration layer.
        
        Args:
            config_path: Path to configuration file
        """
        self.logger = get_logger("language_teacher_integration")
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize agent
        self.agent = LanguageTeacherAgent(self.config)
        
        # Integration state
        self.active_telegram_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_persistence: Dict[str, Any] = {}
        
        self.logger.info("Initialized Language Teacher Integration")
    
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            if config_path is None:
                config_path = Path(__file__).parent / "config" / "default_config.yaml"
            
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
            
            self.logger.debug(f"Loaded configuration from {config_path}")
            return config
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return {}
    
    async def handle_telegram_message(self, user_id: str, message: str,
                                    chat_context: Dict[str, Any] = None) -> str:
        """
        Handle incoming Telegram message.
        
        Args:
            user_id: Telegram user ID
            message: User message text
            chat_context: Additional chat context
            
        Returns:
            Response message for Telegram
        """
        try:
            self.logger.info(f"Processing Telegram message from user {user_id}: {message[:50]}")
            
            # Check for commands
            if message.startswith('/'):
                return await self._handle_telegram_command(user_id, message, chat_context)
            
            # Check if user has active learning session
            if user_id not in self.active_telegram_sessions:
                # Start new learning session
                session_prefs = {
                    'duration_minutes': 15,
                    'max_items': 5,
                    'focus_areas': []
                }
                
                session_result = await self.agent.start_learning_session(
                    user_id, session_prefs
                )
                
                if 'error' in session_result:
                    return f"Sorry, I couldn't start a learning session: {session_result['error']}"
                
                # Store session info
                self.active_telegram_sessions[user_id] = {
                    'session_id': session_result['session_id'],
                    'start_time': datetime.now(),
                    'activity_count': 0
                }
                
                # Return welcome message and first activity
                welcome = session_result.get('welcome_message', 'Welcome!')
                first_activity = session_result.get('first_activity', {})
                
                activity_text = self._format_activity_for_telegram(first_activity)
                
                return f"{welcome}\n\n{activity_text}"
            
            else:
                # Process response to current activity
                session_info = self.active_telegram_sessions[user_id]
                
                # Calculate response time
                response_time = (datetime.now() - session_info.get('last_activity_time', datetime.now())).total_seconds()
                
                result = await self.agent.process_student_response(
                    user_id, 
                    message,
                    response_time=response_time
                )
                
                if 'error' in result:
                    return f"Sorry, I encountered an error: {result['error']}"
                
                # Update session info
                session_info['activity_count'] += 1
                session_info['last_activity_time'] = datetime.now()
                
                # Format response
                feedback = result.get('feedback', 'Good effort!')
                next_activity = result.get('next_activity', {})
                progress = result.get('progress', {})
                
                response = f"{feedback}\n\n"
                
                # Add progress info
                if progress:
                    accuracy = progress.get('correct_answers', 0) / max(1, progress.get('total_attempts', 1))
                    response += f"📊 Progress: {progress.get('items_completed', 0)} completed, {accuracy:.0%} accuracy\n\n"
                
                # Add next activity
                if next_activity:
                    activity_text = self._format_activity_for_telegram(next_activity)
                    response += activity_text
                
                # Check if session should end
                if session_info['activity_count'] >= 10:  # Max activities
                    end_result = await self.agent.end_learning_session(user_id)
                    del self.active_telegram_sessions[user_id]
                    
                    summary = end_result.get('summary', {})
                    goodbye = end_result.get('goodbye_message', 'Great session!')
                    
                    response += f"\n\n{goodbye}\n"
                    response += f"📈 Session Summary:\n"
                    response += f"• {summary.get('activities_completed', 0)} activities completed\n"
                    response += f"• {summary.get('accuracy_rate', 0):.0%} accuracy rate\n"
                    response += f"• {summary.get('duration_minutes', 0):.1f} minutes\n"
                
                return response
        
        except Exception as e:
            self.logger.error(f"Error handling Telegram message: {e}")
            return "Sorry, I encountered an error. Please try again or use /help for assistance."
    
    async def _handle_telegram_command(self, user_id: str, command: str,
                                     context: Dict[str, Any] = None) -> str:
        """Handle Telegram commands."""
        try:
            command = command.lower().strip()
            
            if command == '/start':
                return self._get_start_message()
            
            elif command == '/help':
                return self._get_help_message()
            
            elif command == '/end' or command == '/stop':
                if user_id in self.active_telegram_sessions:
                    end_result = await self.agent.end_learning_session(user_id)
                    del self.active_telegram_sessions[user_id]
                    
                    goodbye = end_result.get('goodbye_message', 'Session ended!')
                    return f"{goodbye}\n\nUse /start to begin a new learning session."
                else:
                    return "You don't have an active learning session. Use /start to begin one!"
            
            elif command == '/progress':
                progress_report = self.agent.get_student_progress(user_id)
                return self._format_progress_for_telegram(progress_report)
            
            elif command == '/status':
                if user_id in self.active_telegram_sessions:
                    session = self.active_telegram_sessions[user_id]
                    duration = (datetime.now() - session['start_time']).total_seconds() / 60
                    return (
                        f"📚 Active Learning Session\n"
                        f"• Duration: {duration:.1f} minutes\n"
                        f"• Activities completed: {session['activity_count']}\n"
                        f"• Session ID: {session['session_id'][:8]}...\n\n"
                        f"Continue with your current activity or use /end to finish."
                    )
                else:
                    return "No active learning session. Use /start to begin learning!"
            
            elif command.startswith('/focus'):
                # Extract focus areas from command
                parts = command.split()[1:] if len(command.split()) > 1 else []
                focus_areas = [area.strip() for area in parts]
                
                if not focus_areas:
                    return (
                        "Specify focus areas for your learning session:\n"
                        "/focus vocabulary grammar\n"
                        "/focus conversation reading\n\n"
                        "Available areas: vocabulary, grammar, conversation, reading, writing, pronunciation"
                    )
                
                # Store focus preference and start session
                session_prefs = {
                    'duration_minutes': 15,
                    'max_items': 5,
                    'focus_areas': focus_areas
                }
                
                session_result = await self.agent.start_learning_session(user_id, session_prefs)
                
                if 'error' in session_result:
                    return f"Sorry, I couldn't start a focused session: {session_result['error']}"
                
                self.active_telegram_sessions[user_id] = {
                    'session_id': session_result['session_id'],
                    'start_time': datetime.now(),
                    'activity_count': 0
                }
                
                welcome = session_result.get('welcome_message', 'Welcome!')
                first_activity = session_result.get('first_activity', {})
                activity_text = self._format_activity_for_telegram(first_activity)
                
                return f"🎯 Focused Session: {', '.join(focus_areas)}\n\n{welcome}\n\n{activity_text}"
            
            else:
                return (
                    "Unknown command. Available commands:\n"
                    "/start - Begin learning session\n"
                    "/help - Show help information\n"
                    "/end - End current session\n"
                    "/progress - View your progress\n"
                    "/status - Check session status\n"
                    "/focus <areas> - Start focused session"
                )
        
        except Exception as e:
            self.logger.error(f"Error handling command {command}: {e}")
            return "Sorry, I couldn't process that command. Use /help for available commands."
    
    def _get_start_message(self) -> str:
        """Get welcome/start message."""
        return (
            "🎓 Welcome to AI Language Learning!\n\n"
            "I'm your personal language teacher powered by advanced AI. "
            "I provide adaptive, personalized language learning experiences.\n\n"
            "🌟 Features:\n"
            "• Adaptive difficulty adjustment\n"
            "• Grammar error detection & correction\n"
            "• Spaced repetition for retention\n"
            "• Progress tracking & analytics\n"
            "• Personalized content generation\n\n"
            "Just send me any message to start learning, or use:\n"
            "/help - Get help and commands\n"
            "/focus vocabulary - Start focused practice\n\n"
            "Let's begin your language learning journey! 🚀"
        )
    
    def _get_help_message(self) -> str:
        """Get help message."""
        return (
            "🎓 AI Language Teacher Help\n\n"
            "💬 **Learning:**\n"
            "Just send any message to start or continue learning!\n"
            "I'll adapt to your level and provide personalized exercises.\n\n"
            "📝 **Commands:**\n"
            "/start - Begin new learning session\n"
            "/end - End current session\n"
            "/progress - View detailed progress\n"
            "/status - Check current session\n"
            "/focus <areas> - Start focused practice\n\n"
            "🎯 **Focus Areas:**\n"
            "vocabulary, grammar, conversation, reading, writing, pronunciation\n\n"
            "📊 **Features:**\n"
            "• Real-time error correction\n"
            "• Adaptive difficulty\n"
            "• Spaced repetition\n"
            "• Progress analytics\n"
            "• Personalized content\n\n"
            "Need more help? Just ask me anything!"
        )
    
    def _format_activity_for_telegram(self, activity: Dict[str, Any]) -> str:
        """Format learning activity for Telegram display."""
        try:
            if not activity:
                return "No activity available."
            
            title = activity.get('title', 'Practice Activity')
            content_type = activity.get('content_type', 'practice')
            instructions = activity.get('instructions', '')
            content = activity.get('content', {})
            hints = activity.get('hints', [])
            
            # Format based on content type
            formatted = f"📚 **{title}**\n\n"
            
            if content_type == 'vocabulary':
                word = content.get('word', '')
                definition = content.get('definition', '')
                example = content.get('example_sentence', '')
                
                formatted += f"🔤 **Word:** {word}\n"
                if definition:
                    formatted += f"📖 **Definition:** {definition}\n"
                if example:
                    formatted += f"💬 **Example:** {example}\n"
            
            elif content_type == 'grammar':
                rule = content.get('rule', '')
                exercise = content.get('exercise', '')
                options = content.get('options', [])
                
                if rule:
                    formatted += f"📏 **Rule:** {rule}\n"
                if exercise:
                    formatted += f"✏️ **Exercise:** {exercise}\n"
                if options:
                    formatted += f"**Options:**\n"
                    for i, option in enumerate(options, 1):
                        formatted += f"{i}. {option}\n"
            
            elif content_type == 'conversation':
                scenario = content.get('scenario', '')
                dialogue = content.get('dialogue', [])
                your_turn = content.get('your_turn', '')
                
                if scenario:
                    formatted += f"🎭 **Scenario:** {scenario}\n\n"
                if dialogue:
                    formatted += "**Dialogue:**\n"
                    for line in dialogue:
                        formatted += f"{line}\n"
                if your_turn:
                    formatted += f"\n{your_turn}\n"
            
            elif content_type == 'reading':
                passage = content.get('passage', '')
                questions = content.get('questions', [])
                
                if passage:
                    formatted += f"📄 **Reading Passage:**\n{passage}\n\n"
                if questions:
                    formatted += "❓ **Questions:**\n"
                    for i, q in enumerate(questions, 1):
                        question_text = q.get('question', '') if isinstance(q, dict) else str(q)
                        formatted += f"{i}. {question_text}\n"
            
            else:
                # Generic content
                if isinstance(content, dict):
                    for key, value in content.items():
                        formatted += f"**{key.title()}:** {value}\n"
                else:
                    formatted += f"{content}\n"
            
            # Add instructions
            if instructions:
                formatted += f"\n💡 **Instructions:** {instructions}"
            
            # Add hints
            if hints:
                formatted += f"\n\n💭 **Hints:**\n"
                for hint in hints[:2]:  # Limit to 2 hints
                    formatted += f"• {hint}\n"
            
            # Add estimated time
            estimated_time = activity.get('estimated_time', 0)
            if estimated_time:
                formatted += f"\n⏱️ Estimated time: {estimated_time} minutes"
            
            return formatted
            
        except Exception as e:
            self.logger.error(f"Error formatting activity for Telegram: {e}")
            return "Activity available - please respond to continue learning."
    
    def _format_progress_for_telegram(self, progress_report: Dict[str, Any]) -> str:
        """Format progress report for Telegram display."""
        try:
            if 'error' in progress_report:
                return "Unable to generate progress report at this time."
            
            overall = progress_report.get('overall_assessment', {})
            adaptive = progress_report.get('adaptive_learning', {})
            srs_stats = progress_report.get('spaced_repetition', {})
            
            formatted = "📈 **Your Learning Progress**\n\n"
            
            # Overall assessment
            level = overall.get('proficiency_level', 'beginner')
            study_time = overall.get('total_study_time', '0:00:00')
            sessions = overall.get('sessions_completed', 0)
            retention = overall.get('retention_rate', 0)
            
            formatted += f"🎯 **Level:** {level.title()}\n"
            formatted += f"⏰ **Study Time:** {study_time}\n"
            formatted += f"📚 **Sessions:** {sessions}\n"
            formatted += f"🧠 **Retention Rate:** {retention:.0%}\n\n"
            
            # Recent performance
            recent_progress = adaptive.get('overall_progress', {})
            if recent_progress:
                accuracy = recent_progress.get('accuracy', 0)
                engagement = recent_progress.get('engagement', 0)
                
                formatted += "📊 **Recent Performance:**\n"
                formatted += f"• Accuracy: {accuracy:.0%}\n"
                formatted += f"• Engagement: {engagement:.0%}\n\n"
            
            # Spaced repetition stats
            if srs_stats and srs_stats.get('total_cards', 0) > 0:
                total_cards = srs_stats.get('total_cards', 0)
                due_cards = srs_stats.get('cards_due', 0)
                mature_cards = srs_stats.get('mature_cards', 0)
                
                formatted += "🗂️ **Spaced Repetition:**\n"
                formatted += f"• Total Cards: {total_cards}\n"
                formatted += f"• Due for Review: {due_cards}\n"
                formatted += f"• Mastered: {mature_cards}\n\n"
            
            # Recommendations
            recommendations = adaptive.get('recommendations', [])
            if recommendations:
                formatted += "💡 **Recommendations:**\n"
                for rec in recommendations[:3]:
                    formatted += f"• {rec}\n"
            
            formatted += "\nKeep up the great work! 🌟"
            
            return formatted
            
        except Exception as e:
            self.logger.error(f"Error formatting progress for Telegram: {e}")
            return "📈 Progress tracking is available - continue learning to see your improvements!"
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get integration status and metrics."""
        try:
            agent_metrics = self.agent.get_agent_metrics()
            
            return {
                'integration_status': 'active',
                'active_telegram_sessions': len(self.active_telegram_sessions),
                'agent_metrics': agent_metrics,
                'config_loaded': bool(self.config),
                'components': {
                    'language_teacher_agent': 'active',
                    'adaptive_learning': agent_metrics.get('components_status', {}).get('adaptive_learning', 'unknown'),
                    'nlp_processor': agent_metrics.get('components_status', {}).get('nlp_processor', 'unknown'),
                    'spaced_repetition': agent_metrics.get('components_status', {}).get('spaced_repetition', 'unknown'),
                    'learning_analytics': agent_metrics.get('components_status', {}).get('learning_analytics', 'unknown'),
                    'content_generator': agent_metrics.get('components_status', {}).get('content_generator', 'unknown')
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting integration status: {e}")
            return {'integration_status': 'error', 'error': str(e)}