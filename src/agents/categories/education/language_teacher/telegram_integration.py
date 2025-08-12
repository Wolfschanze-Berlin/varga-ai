"""
Telegram Integration for Language Teacher Agent.
Handles all Telegram bot functionality for language learning.
"""

import asyncio
import json
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum

from src.log_service import get_logger
from src.tools.integrations.communication.telegram_tool import TelegramBot, TelegramMessage, MessageType

# Import Language Teacher components
from .agent import LanguageTeacherAgent
from .teachers.conversation_teacher import ConversationTeacher
from .teachers.homework_teacher import HomeworkTeacher
from .modules.progress_tracker import ProgressTracker
from .modules.achievement_system import AchievementSystem
from .database_manager import DatabaseManager
from .voice_handler import VoiceMessageHandler


class BotState(Enum):
    """Bot conversation states."""
    START = "start"
    LANGUAGE_SELECTION = "language_selection"
    LEVEL_ASSESSMENT = "level_assessment"
    MAIN_MENU = "main_menu"
    CONVERSATION_PRACTICE = "conversation_practice"
    HOMEWORK_MODE = "homework_mode"
    PROGRESS_VIEW = "progress_view"
    SETTINGS = "settings"


class TelegramLanguageBot:
    """
    Telegram Bot integration for Language Teacher Agent.
    Provides complete language learning experience through Telegram.
    """
    
    SUPPORTED_LANGUAGES = {
        'english': {'name': 'English', 'flag': '🇺🇸'},
        'spanish': {'name': 'Spanish', 'flag': '🇪🇸'}, 
        'french': {'name': 'French', 'flag': '🇫🇷'},
        'german': {'name': 'German', 'flag': '🇩🇪'},
        'italian': {'name': 'Italian', 'flag': '🇮🇹'},
        'portuguese': {'name': 'Portuguese', 'flag': '🇵🇹'}
    }
    
    PROFICIENCY_LEVELS = {
        'beginner': {'name': 'Beginner', 'icon': '🌱'},
        'elementary': {'name': 'Elementary', 'icon': '🌿'},
        'intermediate': {'name': 'Intermediate', 'icon': '🌳'},
        'upper_intermediate': {'name': 'Upper Intermediate', 'icon': '🌲'},
        'advanced': {'name': 'Advanced', 'icon': '🏔️'},
        'proficient': {'name': 'Proficient', 'icon': '⭐'}
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Language Learning Telegram Bot."""
        self.logger = get_logger("telegram_language_bot")
        self.config = config
        
        # Initialize components
        self.telegram_bot: Optional[TelegramBot] = None
        self.language_agent: Optional[LanguageTeacherAgent] = None
        self.conversation_teacher: Optional[ConversationTeacher] = None
        self.homework_teacher: Optional[HomeworkTeacher] = None
        self.progress_tracker: Optional[ProgressTracker] = None
        self.achievement_system: Optional[AchievementSystem] = None
        self.db_manager: Optional[DatabaseManager] = None
        self.voice_handler: Optional[VoiceMessageHandler] = None
        
        # User session management
        self.user_sessions: Dict[int, Dict[str, Any]] = {}
        self.user_states: Dict[int, BotState] = {}
        
        # Performance tracking
        self.total_users = 0
        self.active_sessions = 0
        self.messages_processed = 0
        
        self.logger.info("TelegramLanguageBot initialized")
    
    async def initialize(self) -> bool:
        """Initialize all bot components."""
        try:
            self.logger.info("Initializing Telegram Language Bot...")
            
            # Initialize database manager
            self.db_manager = DatabaseManager(self.config.get('database', {}))
            await self.db_manager.initialize()
            
            # Initialize Language Teacher Agent
            self.language_agent = LanguageTeacherAgent(self.config.get('language_teacher', {}))
            
            # Initialize specialized teachers
            self.conversation_teacher = ConversationTeacher()
            self.homework_teacher = HomeworkTeacher()
            
            # Initialize tracking systems
            self.progress_tracker = ProgressTracker(self.db_manager)
            self.achievement_system = AchievementSystem(self.db_manager)
            
            # Initialize voice handler
            self.voice_handler = VoiceMessageHandler(self.config.get('voice_processing', {}))
            
            # Initialize Telegram bot
            telegram_config = self.config.get('telegram', {})
            self.telegram_bot = TelegramBot(telegram_config)
            
            if not await self.telegram_bot.setup():
                self.logger.error("Failed to setup Telegram bot")
                return False
            
            # Register handlers
            self._register_handlers()
            
            self.logger.info("Telegram Language Bot initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize bot: {e}")
            return False
    
    def _register_handlers(self) -> None:
        """Register all Telegram message and command handlers."""
        # Command handlers
        self.telegram_bot.add_command_handler("start", self.handle_start_command)
        self.telegram_bot.add_command_handler("help", self.handle_help_command)
        self.telegram_bot.add_command_handler("language", self.handle_language_command)
        self.telegram_bot.add_command_handler("practice", self.handle_practice_command)
        self.telegram_bot.add_command_handler("homework", self.handle_homework_command)
        self.telegram_bot.add_command_handler("progress", self.handle_progress_command)
        self.telegram_bot.add_command_handler("achievements", self.handle_achievements_command)
        self.telegram_bot.add_command_handler("settings", self.handle_settings_command)
        self.telegram_bot.add_command_handler("menu", self.handle_menu_command)
        self.telegram_bot.add_command_handler("pronunciation", self.handle_pronunciation_command)
        self.telegram_bot.add_command_handler("voice", self.handle_voice_command)
        
        # Message handler for all other messages
        self.telegram_bot.add_message_handler(self.handle_message)
        
        # Voice message handler
        self.telegram_bot.add_voice_handler(self.handle_voice_message)
    
    async def handle_start_command(self, message: TelegramMessage) -> None:
        """Handle /start command - onboarding flow."""
        try:
            user_id = message.from_user.get("id") if message.from_user else message.chat_id
            
            # Check if user exists
            user_profile = await self.db_manager.get_user_profile(user_id)
            
            if user_profile:
                # Returning user
                await self._send_returning_user_welcome(message, user_profile)
            else:
                # New user - start onboarding
                await self._start_onboarding(message, user_id)
                
        except Exception as e:
            self.logger.error(f"Error in start command: {e}")
            await self.telegram_bot.send_message(
                text="Sorry, I encountered an error. Please try again.",
                chat_id=message.chat_id
            )
    
    async def _start_onboarding(self, message: TelegramMessage, user_id: int) -> None:
        """Start onboarding flow for new users."""
        welcome_text = """🌟 Welcome to AI Language Teacher! 🌟

I'm your personal AI language tutor, powered by advanced adaptive learning technology. I'll help you learn languages through:

🗣️ **Natural Conversations** - Practice speaking naturally
📚 **Personalized Homework** - Exercises tailored to your level
📈 **Progress Tracking** - See your improvement over time
🏆 **Achievements** - Celebrate your milestones
🎯 **Adaptive Learning** - Difficulty adjusts to your progress

Let's start by choosing your target language! 🌍"""
        
        # Send welcome message with language selection
        keyboard = self._create_language_selection_keyboard()
        
        await self.telegram_bot.send_message(
            text=welcome_text,
            chat_id=message.chat_id,
            reply_markup=keyboard
        )
        
        # Set user state
        self.user_states[user_id] = BotState.LANGUAGE_SELECTION
        self.logger.info(f"Started onboarding for user {user_id}")
    
    async def _send_returning_user_welcome(self, message: TelegramMessage, user_profile: Dict[str, Any]) -> None:
        """Send welcome message for returning users."""
        user_id = user_profile['user_id']
        language = user_profile.get('target_language', 'english')
        level = user_profile.get('proficiency_level', 'beginner')
        
        # Get user stats
        stats = await self.progress_tracker.get_user_stats(user_id)
        streak = stats.get('learning_streak', 0)
        
        lang_info = self.SUPPORTED_LANGUAGES.get(language, {'name': language, 'flag': '🌍'})
        level_info = self.PROFICIENCY_LEVELS.get(level, {'name': level, 'icon': '📚'})
        
        welcome_text = f"""Welcome back! {lang_info['flag']} Ready to continue your {lang_info['name']} journey?

📊 **Your Progress:**
🎯 Level: {level_info['icon']} {level_info['name']}
🔥 Streak: {streak} days
📈 Total Sessions: {stats.get('total_sessions', 0)}
⭐ Achievement Points: {stats.get('achievement_points', 0)}

What would you like to do today?"""
        
        keyboard = self._create_main_menu_keyboard()
        
        await self.telegram_bot.send_message(
            text=welcome_text,
            chat_id=message.chat_id,
            reply_markup=keyboard
        )
        
        # Set user state to main menu
        self.user_states[user_id] = BotState.MAIN_MENU
    
    def _create_language_selection_keyboard(self) -> Dict[str, Any]:
        """Create inline keyboard for language selection."""
        keyboard = {
            "inline_keyboard": []
        }
        
        # Create rows of 2 languages each
        row = []
        for lang_code, lang_info in self.SUPPORTED_LANGUAGES.items():
            button = {
                "text": f"{lang_info['flag']} {lang_info['name']}",
                "callback_data": f"select_language:{lang_code}"
            }
            row.append(button)
            
            if len(row) == 2:
                keyboard["inline_keyboard"].append(row)
                row = []
        
        # Add remaining button if any
        if row:
            keyboard["inline_keyboard"].append(row)
        
        return keyboard
    
    def _create_level_assessment_keyboard(self) -> Dict[str, Any]:
        """Create keyboard for level assessment."""
        keyboard = {
            "inline_keyboard": []
        }
        
        for level_code, level_info in self.PROFICIENCY_LEVELS.items():
            button = {
                "text": f"{level_info['icon']} {level_info['name']}",
                "callback_data": f"select_level:{level_code}"
            }
            keyboard["inline_keyboard"].append([button])
        
        # Add assessment option
        keyboard["inline_keyboard"].append([{
            "text": "🧠 Take Assessment Test",
            "callback_data": "take_assessment"
        }])
        
        return keyboard
    
    def _create_main_menu_keyboard(self) -> Dict[str, Any]:
        """Create main menu keyboard."""
        return {
            "inline_keyboard": [
                [
                    {"text": "🗣️ Conversation Practice", "callback_data": "menu:conversation"},
                    {"text": "📚 Homework Exercises", "callback_data": "menu:homework"}
                ],
                [
                    {"text": "🎤 Pronunciation Practice", "callback_data": "menu:pronunciation"},
                    {"text": "📈 View Progress", "callback_data": "menu:progress"}
                ],
                [
                    {"text": "🏆 Achievements", "callback_data": "menu:achievements"},
                    {"text": "⚙️ Settings", "callback_data": "menu:settings"}
                ],
                [
                    {"text": "❓ Help", "callback_data": "menu:help"}
                ]
            ]
        }
    
    async def handle_callback_query(self, callback_query: Dict[str, Any]) -> None:
        """Handle callback queries from inline keyboards."""
        try:
            data = callback_query.get("data", "")
            chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
            user_id = callback_query.get("from", {}).get("id", chat_id)
            
            if data.startswith("select_language:"):
                await self._handle_language_selection(chat_id, user_id, data.split(":")[1])
            elif data.startswith("select_level:"):
                await self._handle_level_selection(chat_id, user_id, data.split(":")[1])
            elif data.startswith("menu:"):
                await self._handle_menu_selection(chat_id, user_id, data.split(":")[1])
            elif data == "take_assessment":
                await self._start_level_assessment(chat_id, user_id)
            
            # Answer callback query to remove loading state
            await self.telegram_bot.answer_callback_query(callback_query["id"])
            
        except Exception as e:
            self.logger.error(f"Error handling callback query: {e}")
    
    async def _handle_language_selection(self, chat_id: int, user_id: int, language: str) -> None:
        """Handle language selection from keyboard."""
        try:
            # Store language selection temporarily
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = {}
            
            self.user_sessions[user_id]['selected_language'] = language
            lang_info = self.SUPPORTED_LANGUAGES[language]
            
            # Ask for proficiency level
            level_text = f"""Great choice! {lang_info['flag']} You've selected **{lang_info['name']}**.

Now, what's your current proficiency level? This helps me personalize your learning experience.

If you're not sure, I recommend taking the assessment test for the most accurate placement."""
            
            keyboard = self._create_level_assessment_keyboard()
            
            await self.telegram_bot.send_message(
                text=level_text,
                chat_id=chat_id,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
            self.user_states[user_id] = BotState.LEVEL_ASSESSMENT
            
        except Exception as e:
            self.logger.error(f"Error handling language selection: {e}")
    
    async def _handle_level_selection(self, chat_id: int, user_id: int, level: str) -> None:
        """Handle proficiency level selection."""
        try:
            session = self.user_sessions.get(user_id, {})
            language = session.get('selected_language', 'english')
            
            # Create user profile
            user_profile = {
                'user_id': user_id,
                'target_language': language,
                'proficiency_level': level,
                'created_at': datetime.now(),
                'learning_preferences': {
                    'session_length': 15,
                    'focus_areas': [],
                    'reminder_time': None
                }
            }
            
            # Save to database
            await self.db_manager.create_user_profile(user_profile)
            
            # Initialize user with language agent
            await self.language_agent.start_learning_session(str(user_id), {
                'target_language': language,
                'proficiency_level': level
            })
            
            # Send completion message
            lang_info = self.SUPPORTED_LANGUAGES[language]
            level_info = self.PROFICIENCY_LEVELS[level]
            
            completion_text = f"""🎉 **Setup Complete!**

📊 **Your Profile:**
🎯 Language: {lang_info['flag']} {lang_info['name']}
📚 Level: {level_info['icon']} {level_info['name']}

You're all set to start learning! I've prepared personalized content based on your level. Let's begin with some conversation practice to get warmed up!

Ready to start? Choose what you'd like to do:"""
            
            keyboard = self._create_main_menu_keyboard()
            
            await self.telegram_bot.send_message(
                text=completion_text,
                chat_id=chat_id,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
            # Update state and clean up session
            self.user_states[user_id] = BotState.MAIN_MENU
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
            
            self.total_users += 1
            
        except Exception as e:
            self.logger.error(f"Error handling level selection: {e}")
    
    async def _handle_menu_selection(self, chat_id: int, user_id: int, menu_item: str) -> None:
        """Handle main menu selections."""
        try:
            if menu_item == "conversation":
                await self._start_conversation_practice(chat_id, user_id)
            elif menu_item == "homework":
                await self._start_homework_mode(chat_id, user_id)
            elif menu_item == "progress":
                await self._show_progress_report(chat_id, user_id)
            elif menu_item == "achievements":
                await self._show_achievements(chat_id, user_id)
            elif menu_item == "pronunciation":
                await self._start_pronunciation_practice(chat_id, user_id)
            elif menu_item == "settings":
                await self._show_settings(chat_id, user_id)
            elif menu_item == "help":
                await self._show_help(chat_id, user_id)
                
        except Exception as e:
            self.logger.error(f"Error handling menu selection: {e}")
    
    async def _start_conversation_practice(self, chat_id: int, user_id: int) -> None:
        """Start conversation practice mode."""
        try:
            # Get user profile
            user_profile = await self.db_manager.get_user_profile(user_id)
            if not user_profile:
                await self._handle_unregistered_user(chat_id)
                return
            
            # Set state
            self.user_states[user_id] = BotState.CONVERSATION_PRACTICE
            
            # Start conversation with teacher
            start_text = """🗣️ **Conversation Practice Mode**

Great! Let's practice natural conversation. I'll chat with you in a friendly, supportive way and help you improve as we talk.

💡 **Tips:**
• Don't worry about mistakes - they help you learn!
• Try to respond naturally, like talking to a friend
• I'll give gentle corrections and introduce new vocabulary
• Type /menu anytime to return to the main menu

Ready? Let's start! 😊"""
            
            await self.telegram_bot.send_message(
                text=start_text,
                chat_id=chat_id,
                parse_mode="Markdown"
            )
            
            # Initialize conversation with teacher
            context = {
                "user_profile": user_profile,
                "language": user_profile.get('target_language', 'english'),
                "level": user_profile.get('proficiency_level', 'beginner'),
                "mode": "conversation_practice"
            }
            
            # Send first conversation prompt
            response = await self.conversation_teacher.process_message("Let's start talking!", context)
            
            await self.telegram_bot.send_message(
                text=response,
                chat_id=chat_id,
                parse_mode="Markdown"
            )
            
            self.active_sessions += 1
            
        except Exception as e:
            self.logger.error(f"Error starting conversation practice: {e}")
    
    async def _start_homework_mode(self, chat_id: int, user_id: int) -> None:
        """Start homework/exercise mode."""
        try:
            user_profile = await self.db_manager.get_user_profile(user_id)
            if not user_profile:
                await self._handle_unregistered_user(chat_id)
                return
            
            self.user_states[user_id] = BotState.HOMEWORK_MODE
            
            homework_text = """📚 **Homework & Exercises**

Perfect! Let's work on some structured exercises tailored to your level. I'll give you various types of practice:

📝 **What you'll get:**
• Grammar exercises
• Vocabulary building
• Reading comprehension
• Writing practice
• Listening exercises (when supported)

Ready for your first exercise? Let me prepare something perfect for your level! 🎯"""
            
            await self.telegram_bot.send_message(
                text=homework_text,
                chat_id=chat_id,
                parse_mode="Markdown"
            )
            
            # Get homework from teacher
            context = {
                "user_profile": user_profile,
                "language": user_profile.get('target_language', 'english'),
                "level": user_profile.get('proficiency_level', 'beginner'),
                "mode": "homework_practice"
            }
            
            homework_response = await self.homework_teacher.process_message("Give me an exercise", context)
            
            await self.telegram_bot.send_message(
                text=homework_response,
                chat_id=chat_id,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            self.logger.error(f"Error starting homework mode: {e}")
    
    async def _start_pronunciation_practice(self, chat_id: int, user_id: int) -> None:
        """Start pronunciation practice mode."""
        try:
            user_profile = await self.db_manager.get_user_profile(user_id)
            if not user_profile:
                await self._handle_unregistered_user(chat_id)
                return
            
            language = user_profile.get('target_language', 'english')
            level = user_profile.get('proficiency_level', 'beginner')
            
            # Check if voice is supported
            language_config = self.SUPPORTED_LANGUAGES.get(language, {})
            
            if not language_config.get('voice_enabled', False):
                await self.telegram_bot.send_message(
                    text=f"🎤 Voice practice is not yet available for {language_config.get('name', language)}. Coming soon!",
                    chat_id=chat_id
                )
                return
            
            pronunciation_text = f"""🎤 **Pronunciation Practice Mode**

Welcome to pronunciation practice! Here's how it works:

**Current Settings:**
🎯 Language: {language_config.get('flag', '')} {language_config.get('name', language)}
📚 Level: {level.title()}

**How to practice:**
1. I'll give you phrases to practice
2. Record yourself saying them using voice messages
3. Get instant feedback on your pronunciation!

**Voice Message Tips:**
• Speak clearly and at normal pace
• Find a quiet environment
• Hold the microphone close to your mouth
• Don't rush - take your time

Ready to start? Let me give you your first pronunciation exercise! 🚀"""
            
            await self.telegram_bot.send_message(
                text=pronunciation_text,
                chat_id=chat_id,
                parse_mode="Markdown"
            )
            
            # Get and send first exercise
            exercise = self.voice_handler.get_pronunciation_exercise(level)
            formatted_exercise = self.voice_handler.format_pronunciation_exercise(exercise)
            
            # Store current exercise text for voice processing
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = {}
            self.user_sessions[user_id]['current_pronunciation_text'] = exercise.get('text', '')
            
            await self.telegram_bot.send_message(
                text=formatted_exercise,
                chat_id=chat_id,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            self.logger.error(f"Error starting pronunciation practice: {e}")
            await self.telegram_bot.send_message(
                text="Sorry, I couldn't start pronunciation practice right now. Please try again.",
                chat_id=chat_id
            )
    
    async def _show_progress_report(self, chat_id: int, user_id: int) -> None:
        """Show detailed progress report."""
        try:
            # Get comprehensive progress data
            progress_data = await self.progress_tracker.get_comprehensive_report(user_id)
            
            if not progress_data:
                await self.telegram_bot.send_message(
                    text="📊 No progress data available yet. Complete some lessons to see your progress!",
                    chat_id=chat_id
                )
                return
            
            # Format progress report
            report_text = f"""📈 **Your Learning Progress**

🎯 **Overall Stats:**
📚 Level: {progress_data.get('current_level', 'Beginner')}
🔥 Streak: {progress_data.get('learning_streak', 0)} days
⏱️ Total Study Time: {progress_data.get('total_study_time', '0m')}
✅ Sessions Completed: {progress_data.get('total_sessions', 0)}

📊 **Performance:**
🎯 Average Accuracy: {progress_data.get('average_accuracy', 0):.1%}
⚡ Response Speed: {progress_data.get('avg_response_time', 0):.1f}s
📈 Improvement Rate: {progress_data.get('improvement_rate', 0):.1%}

🏆 **Achievements:**
⭐ Points Earned: {progress_data.get('achievement_points', 0)}
🏅 Badges Unlocked: {progress_data.get('badges_count', 0)}
🎖️ Milestones Reached: {progress_data.get('milestones_count', 0)}

💪 **Areas of Strength:**
{self._format_strengths(progress_data.get('strengths', []))}

🎯 **Focus Areas:**
{self._format_focus_areas(progress_data.get('focus_areas', []))}"""
            
            keyboard = {
                "inline_keyboard": [
                    [{"text": "📊 Detailed Analytics", "callback_data": "show_detailed_analytics"}],
                    [{"text": "🔙 Back to Menu", "callback_data": "menu:main"}]
                ]
            }
            
            await self.telegram_bot.send_message(
                text=report_text,
                chat_id=chat_id,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            self.logger.error(f"Error showing progress report: {e}")
    
    def _format_strengths(self, strengths: List[str]) -> str:
        """Format strengths list."""
        if not strengths:
            return "• Building foundation skills"
        return "\n".join([f"• {strength}" for strength in strengths[:3]])
    
    def _format_focus_areas(self, focus_areas: List[str]) -> str:
        """Format focus areas list."""
        if not focus_areas:
            return "• Continue regular practice"
        return "\n".join([f"• {area}" for area in focus_areas[:3]])
    
    async def _show_achievements(self, chat_id: int, user_id: int) -> None:
        """Show user achievements and badges."""
        try:
            achievements = await self.achievement_system.get_user_achievements(user_id)
            
            if not achievements.get('unlocked_achievements'):
                await self.telegram_bot.send_message(
                    text="🏆 Start learning to unlock achievements! Complete lessons, maintain streaks, and master skills to earn badges.",
                    chat_id=chat_id
                )
                return
            
            # Format achievements
            achievement_text = f"""🏆 **Your Achievements**

✨ **Achievement Points:** {achievements.get('total_points', 0)}
🎯 **Progress to Next Level:** {achievements.get('progress_to_next', 0):.0%}

🏅 **Unlocked Badges:**
{self._format_achievements(achievements.get('unlocked_achievements', []))}

🎖️ **Recent Milestones:**
{self._format_recent_milestones(achievements.get('recent_milestones', []))}

🎯 **Next Goals:**
{self._format_next_goals(achievements.get('next_goals', []))}"""
            
            await self.telegram_bot.send_message(
                text=achievement_text,
                chat_id=chat_id,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            self.logger.error(f"Error showing achievements: {e}")
    
    def _format_achievements(self, achievements: List[Dict]) -> str:
        """Format achievements list."""
        if not achievements:
            return "• No badges unlocked yet"
        
        formatted = []
        for achievement in achievements[:5]:
            formatted.append(f"🏅 {achievement.get('name', 'Achievement')} - {achievement.get('description', '')}")
        
        return "\n".join(formatted)
    
    def _format_recent_milestones(self, milestones: List[Dict]) -> str:
        """Format recent milestones."""
        if not milestones:
            return "• Complete activities to reach milestones"
        
        formatted = []
        for milestone in milestones[:3]:
            formatted.append(f"🎖️ {milestone.get('name', 'Milestone')}")
        
        return "\n".join(formatted)
    
    def _format_next_goals(self, goals: List[Dict]) -> str:
        """Format next goals."""
        if not goals:
            return "• Continue learning to set new goals"
        
        formatted = []
        for goal in goals[:3]:
            progress = goal.get('progress', 0)
            formatted.append(f"🎯 {goal.get('name', 'Goal')} ({progress:.0%})")
        
        return "\n".join(formatted)
    
    async def handle_message(self, message: TelegramMessage) -> None:
        """Handle all non-command messages."""
        try:
            user_id = message.from_user.get("id") if message.from_user else message.chat_id
            chat_id = message.chat_id
            
            # Check if user exists
            user_profile = await self.db_manager.get_user_profile(user_id)
            if not user_profile:
                await self._handle_unregistered_user(chat_id)
                return
            
            # Get user state
            user_state = self.user_states.get(user_id, BotState.MAIN_MENU)
            
            # Handle based on current state
            if user_state == BotState.CONVERSATION_PRACTICE:
                await self._handle_conversation_message(message, user_profile)
            elif user_state == BotState.HOMEWORK_MODE:
                await self._handle_homework_message(message, user_profile)
            else:
                # Default to conversation practice for any text message
                await self._handle_conversation_message(message, user_profile)
            
            self.messages_processed += 1
            
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
            await self.telegram_bot.send_message(
                text="Sorry, I encountered an error. Please try again or use /menu to return to the main menu.",
                chat_id=message.chat_id
            )
    
    async def _handle_conversation_message(self, message: TelegramMessage, user_profile: Dict[str, Any]) -> None:
        """Handle message in conversation practice mode."""
        try:
            user_id = user_profile['user_id']
            
            # Send typing indicator
            await self.telegram_bot.send_typing_action(message.chat_id)
            
            # Process with conversation teacher
            context = {
                "user_profile": user_profile,
                "language": user_profile.get('target_language', 'english'),
                "level": user_profile.get('proficiency_level', 'beginner'),
                "mode": "conversation_practice"
            }
            
            response = await self.conversation_teacher.process_message(message.text or "No text", context)
            
            # Send response
            await self.telegram_bot.send_message(
                text=response,
                chat_id=message.chat_id,
                parse_mode="Markdown"
            )
            
            # Update progress
            await self.progress_tracker.record_interaction(user_id, {
                'type': 'conversation',
                'message_length': len(message.text or ""),
                'response_time': None  # Would be calculated with timing
            })
            
        except Exception as e:
            self.logger.error(f"Error handling conversation message: {e}")
    
    async def _handle_homework_message(self, message: TelegramMessage, user_profile: Dict[str, Any]) -> None:
        """Handle message in homework mode."""
        try:
            user_id = user_profile['user_id']
            
            await self.telegram_bot.send_typing_action(message.chat_id)
            
            # Process with homework teacher
            context = {
                "user_profile": user_profile,
                "language": user_profile.get('target_language', 'english'),
                "level": user_profile.get('proficiency_level', 'beginner'),
                "mode": "homework_practice"
            }
            
            response = await self.homework_teacher.process_message(message.text or "No text", context)
            
            await self.telegram_bot.send_message(
                text=response,
                chat_id=message.chat_id,
                parse_mode="Markdown"
            )
            
            # Update progress
            await self.progress_tracker.record_interaction(user_id, {
                'type': 'homework',
                'message_length': len(message.text or ""),
                'exercise_completed': True
            })
            
        except Exception as e:
            self.logger.error(f"Error handling homework message: {e}")
    
    async def _handle_unregistered_user(self, chat_id: int) -> None:
        """Handle messages from unregistered users."""
        await self.telegram_bot.send_message(
            text="🌟 Welcome! Please start with /start to set up your language learning profile first.",
            chat_id=chat_id
        )
    
    async def handle_help_command(self, message: TelegramMessage) -> None:
        """Handle /help command."""
        help_text = """🤖 **AI Language Teacher Help**

**Available Commands:**
/start - Set up your profile or return to main menu
/practice - Start conversation practice
/homework - Get structured exercises
/progress - View your learning progress
/achievements - See your badges and milestones
/settings - Adjust your preferences
/menu - Show main menu
/help - Show this help message

**Learning Modes:**
🗣️ **Conversation Practice** - Natural dialogue with AI teacher
📚 **Homework Mode** - Structured exercises and assessments
📈 **Progress Tracking** - Monitor your improvement
🏆 **Achievement System** - Earn badges and reach milestones

**Tips:**
• Practice daily for best results
• Don't worry about mistakes - they help you learn!
• Use voice messages for pronunciation practice
• Check your progress regularly to stay motivated

**Supported Languages:**
🇺🇸 English • 🇪🇸 Spanish • 🇫🇷 French • 🇩🇪 German • 🇮🇹 Italian • 🇵🇹 Portuguese

Need more help? Just ask me anything! 😊"""
        
        await self.telegram_bot.send_message(
            text=help_text,
            chat_id=message.chat_id,
            parse_mode="Markdown"
        )
    
    async def handle_language_command(self, message: TelegramMessage) -> None:
        """Handle /language command to change target language."""
        try:
            user_id = message.from_user.get("id") if message.from_user else message.chat_id
            
            language_text = "🌍 **Change Your Target Language**\n\nSelect a new language to learn:"
            keyboard = self._create_language_selection_keyboard()
            
            await self.telegram_bot.send_message(
                text=language_text,
                chat_id=message.chat_id,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
            self.user_states[user_id] = BotState.LANGUAGE_SELECTION
            
        except Exception as e:
            self.logger.error(f"Error in language command: {e}")
    
    async def handle_practice_command(self, message: TelegramMessage) -> None:
        """Handle /practice command."""
        user_id = message.from_user.get("id") if message.from_user else message.chat_id
        await self._start_conversation_practice(message.chat_id, user_id)
    
    async def handle_homework_command(self, message: TelegramMessage) -> None:
        """Handle /homework command."""
        user_id = message.from_user.get("id") if message.from_user else message.chat_id
        await self._start_homework_mode(message.chat_id, user_id)
    
    async def handle_progress_command(self, message: TelegramMessage) -> None:
        """Handle /progress command."""
        user_id = message.from_user.get("id") if message.from_user else message.chat_id
        await self._show_progress_report(message.chat_id, user_id)
    
    async def handle_achievements_command(self, message: TelegramMessage) -> None:
        """Handle /achievements command."""
        user_id = message.from_user.get("id") if message.from_user else message.chat_id
        await self._show_achievements(message.chat_id, user_id)
    
    async def handle_settings_command(self, message: TelegramMessage) -> None:
        """Handle /settings command."""
        await self._show_settings(message.chat_id, message.from_user.get("id") if message.from_user else message.chat_id)
    
    async def _show_settings(self, chat_id: int, user_id: int) -> None:
        """Show user settings menu."""
        settings_text = """⚙️ **Settings**

Customize your learning experience:"""
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "🌍 Change Language", "callback_data": "settings:language"}],
                [{"text": "📊 Change Level", "callback_data": "settings:level"}],
                [{"text": "⏰ Study Reminders", "callback_data": "settings:reminders"}],
                [{"text": "🎯 Learning Goals", "callback_data": "settings:goals"}],
                [{"text": "🔙 Back to Menu", "callback_data": "menu:main"}]
            ]
        }
        
        await self.telegram_bot.send_message(
            text=settings_text,
            chat_id=chat_id,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    async def _show_help(self, chat_id: int, user_id: int) -> None:
        """Show help information."""
        help_text = """❓ **Quick Help**

**Current Mode:** Choose from conversation practice or homework exercises
**Commands:** Use /menu to see all options
**Progress:** Check /progress to see your improvement
**Achievements:** Use /achievements to see your badges

**Tips for Better Learning:**
• Practice daily, even if just for 5 minutes
• Don't be afraid to make mistakes
• Ask questions if you don't understand
• Use voice messages to practice pronunciation

**Having Issues?**
• Use /start to reset your profile
• Use /menu to return to main options
• Contact support if problems persist

Ready to continue learning? 🚀"""
        
        await self.telegram_bot.send_message(
            text=help_text,
            chat_id=chat_id,
            parse_mode="Markdown"
        )
    
    async def handle_menu_command(self, message: TelegramMessage) -> None:
        """Handle /menu command."""
        keyboard = self._create_main_menu_keyboard()
        
        await self.telegram_bot.send_message(
            text="📱 **Main Menu**\n\nWhat would you like to do?",
            chat_id=message.chat_id,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    async def handle_pronunciation_command(self, message: TelegramMessage) -> None:
        """Handle /pronunciation command."""
        try:
            user_id = message.from_user.get("id") if message.from_user else message.chat_id
            user_profile = await self.db_manager.get_user_profile(user_id)
            
            if not user_profile:
                await self._handle_unregistered_user(message.chat_id)
                return
            
            level = user_profile.get('proficiency_level', 'beginner')
            
            # Get pronunciation exercise
            exercise = self.voice_handler.get_pronunciation_exercise(level)
            formatted_exercise = self.voice_handler.format_pronunciation_exercise(exercise)
            
            await self.telegram_bot.send_message(
                text=formatted_exercise,
                chat_id=message.chat_id,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            self.logger.error(f"Error in pronunciation command: {e}")
            await self.telegram_bot.send_message(
                text="Sorry, I couldn't create a pronunciation exercise right now. Please try again.",
                chat_id=message.chat_id
            )
    
    async def handle_voice_command(self, message: TelegramMessage) -> None:
        """Handle /voice command."""
        voice_info = """🎤 **Voice Message Practice**

**How to use voice messages for pronunciation practice:**

1️⃣ **Request an exercise:** Use /pronunciation to get a practice phrase
2️⃣ **Record your voice:** Press and hold the microphone button in Telegram
3️⃣ **Speak clearly:** Say the given phrase or sentence
4️⃣ **Send the message:** Release the button to send your voice message
5️⃣ **Get feedback:** I'll analyze your pronunciation and give you detailed feedback!

**Features:**
🎯 **Pronunciation scoring** - Get accuracy ratings
🗣️ **Speech recognition** - I'll transcribe what you said
💡 **Improvement tips** - Personalized suggestions
📈 **Progress tracking** - Monitor your pronunciation improvement

**Supported formats:** Voice messages, audio files (up to 60 seconds)

Ready to practice? Send me a voice message or use /pronunciation to get started! 🚀"""
        
        await self.telegram_bot.send_message(
            text=voice_info,
            chat_id=message.chat_id,
            parse_mode="Markdown"
        )
    
    async def handle_voice_message(self, message: TelegramMessage) -> None:
        """Handle voice message for pronunciation practice."""
        try:
            user_id = message.from_user.get("id") if message.from_user else message.chat_id
            user_profile = await self.db_manager.get_user_profile(user_id)
            
            if not user_profile:
                await self.telegram_bot.send_message(
                    text="Please use /start to set up your profile before using voice messages.",
                    chat_id=message.chat_id
                )
                return
            
            # Check if voice is supported for user's language
            language = user_profile.get('target_language', 'english')
            language_config = self.SUPPORTED_LANGUAGES.get(language, {})
            
            if not language_config.get('voice_enabled', False):
                await self.telegram_bot.send_message(
                    text=f"Voice practice is not yet available for {language_config.get('name', language)}. Coming soon! 🎤",
                    chat_id=message.chat_id
                )
                return
            
            # Send processing message
            processing_msg = await self.telegram_bot.send_message(
                text="🎤 Processing your voice message... This may take a few seconds.",
                chat_id=message.chat_id
            )
            
            # Download and process voice file
            # Note: This is a simplified version - actual implementation would download the file
            voice_file_path = f"/tmp/voice_{user_id}_{datetime.now().timestamp()}.ogg"
            
            # Simulate voice file processing
            try:
                # Process voice message
                context = {
                    'expected_text': self.user_sessions.get(user_id, {}).get('current_pronunciation_text'),
                    'exercise_type': 'pronunciation_practice'
                }
                
                processing_result = await self.voice_handler.process_voice_message(
                    voice_file_path, 
                    user_profile, 
                    context
                )
                
                # Delete processing message (if telegram bot supports it)
                try:
                    if hasattr(self.telegram_bot, 'delete_message'):
                        await self.telegram_bot.delete_message(message.chat_id, processing_msg.message_id)
                except:
                    pass  # Ignore deletion errors
                
                if processing_result.get('success'):
                    # Send detailed feedback
                    feedback_text = processing_result.get('feedback', 'Good effort!')
                    
                    # Add score and transcription if available
                    if 'pronunciation_score' in processing_result:
                        score_percent = int(processing_result['pronunciation_score'] * 100)
                        feedback_text += f"\n\n📊 **Pronunciation Score: {score_percent}%**"
                    
                    if processing_result.get('transcription'):
                        feedback_text += f"\n🎯 **What I heard:** \"{processing_result['transcription']}\""
                    
                    # Send feedback
                    await self.telegram_bot.send_message(
                        text=feedback_text,
                        chat_id=message.chat_id,
                        parse_mode="Markdown"
                    )
                    
                    # Record progress
                    await self.progress_tracker.record_interaction(user_id, {
                        'type': 'pronunciation_practice',
                        'score': processing_result.get('pronunciation_score', 0),
                        'duration': processing_result.get('duration_seconds', 0)
                    })
                    
                    # Check for achievements
                    achievements = await self.achievement_system.check_achievements(user_id, {
                        'activity_type': 'pronunciation',
                        'score': processing_result.get('pronunciation_score', 0)
                    })
                    
                    # Send achievement notifications
                    for achievement in achievements:
                        achievement_msg = self.achievement_system.format_achievement_notification(achievement)
                        await self.telegram_bot.send_message(
                            text=achievement_msg,
                            chat_id=message.chat_id,
                            parse_mode="Markdown"
                        )
                    
                else:
                    error_msg = processing_result.get('error', 'Could not process voice message')
                    await self.telegram_bot.send_message(
                        text=f"❌ {error_msg}\n\nPlease try again with a shorter, clearer recording.",
                        chat_id=message.chat_id
                    )
            
            finally:
                # Cleanup temp file
                await self.voice_handler.cleanup_temp_files(voice_file_path)
            
        except Exception as e:
            self.logger.error(f"Error processing voice message: {e}")
            await self.telegram_bot.send_message(
                text="Sorry, I had trouble processing your voice message. Please try again or contact support if the problem continues.",
                chat_id=message.chat_id
            )
    
    async def start_polling(self) -> None:
        """Start the Telegram bot polling."""
        try:
            self.logger.info("Starting Language Learning Bot polling...")
            await self.telegram_bot.start_polling()
            
        except Exception as e:
            self.logger.error(f"Error starting polling: {e}")
    
    async def stop_polling(self) -> None:
        """Stop the Telegram bot polling."""
        try:
            if self.telegram_bot:
                await self.telegram_bot.stop_polling()
            self.logger.info("Stopped Language Learning Bot polling")
            
        except Exception as e:
            self.logger.error(f"Error stopping polling: {e}")
    
    async def cleanup(self) -> None:
        """Clean up bot resources."""
        try:
            await self.stop_polling()
            
            if self.telegram_bot:
                await self.telegram_bot.cleanup()
            
            if self.db_manager:
                await self.db_manager.cleanup()
            
            # Clear session data
            self.user_sessions.clear()
            self.user_states.clear()
            
            self.logger.info("Language Learning Bot cleaned up successfully")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def get_bot_stats(self) -> Dict[str, Any]:
        """Get bot statistics."""
        return {
            'total_users': self.total_users,
            'active_sessions': self.active_sessions,
            'messages_processed': self.messages_processed,
            'supported_languages': len(self.SUPPORTED_LANGUAGES),
            'proficiency_levels': len(self.PROFICIENCY_LEVELS),
            'active_conversations': len([s for s in self.user_states.values() 
                                       if s == BotState.CONVERSATION_PRACTICE]),
            'active_homework_sessions': len([s for s in self.user_states.values() 
                                           if s == BotState.HOMEWORK_MODE])
        }