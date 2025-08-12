"""
Complete Language Learning Telegram Bot Implementation.
Integrates all language teacher components for comprehensive language learning experience.
"""

import asyncio
import signal
import sys
from typing import Optional
from datetime import datetime
import os

from src.log_service import get_logger
from src.config import settings
from src.config.config_manager import get_config
from agents.categories.education.language_teacher.telegram_integration import TelegramLanguageBot


class LanguageTeacherBotOrchestrator:
    """
    Main orchestrator for the Language Teacher Telegram Bot.
    Coordinates all language learning components and provides a complete learning experience.
    """
    
    def __init__(self):
        """Initialize the Language Teacher Bot Orchestrator."""
        self.logger = get_logger("language_teacher_bot")
        
        # Get configuration
        self.config = get_config()
        
        # Initialize components
        self.language_bot: Optional[TelegramLanguageBot] = None
        
        # State management
        self.is_running = False
        self.start_time = datetime.now()
        
        # Performance tracking
        self.total_learning_interactions = 0
        self.active_learners = 0
        
        self.logger.info("Language Teacher Bot Orchestrator initialized")
    
    async def initialize(self) -> bool:
        """
        Initialize all components for the language learning bot.
        
        Returns:
            True if initialization successful
        """
        try:
            self.logger.info("Initializing Language Teacher Bot...")
            
            # Build language teacher configuration
            language_config = self._build_language_config()
            
            # Initialize Language Learning Bot
            self.language_bot = TelegramLanguageBot(language_config)
            
            if not await self.language_bot.initialize():
                self.logger.error("Failed to initialize language learning bot")
                return False
            
            # Register callback query handler for inline keyboards
            if hasattr(self.language_bot.telegram_bot, 'add_callback_query_handler'):
                self.language_bot.telegram_bot.add_callback_query_handler(
                    self.language_bot.handle_callback_query
                )
            
            self.logger.info("Language Teacher Bot initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize language teacher bot: {e}")
            return False
    
    def _build_language_config(self) -> dict:
        """Build comprehensive configuration for language learning bot."""
        
        # Get base configuration
        base_config = self.config.to_dict() if hasattr(self.config, 'to_dict') else {}
        
        # Build language-specific configuration
        language_config = {
            # Telegram bot configuration
            'telegram': {
                'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
                'polling_interval': 1,
                'rate_limit_per_minute': 100,
                'rate_limit_per_hour': 2000,
                'webhook_url': os.getenv('TELEGRAM_WEBHOOK_URL'),
                'allowed_updates': ['message', 'callback_query', 'voice']
            },
            
            # Language teacher configuration
            'language_teacher': {
                'target_language': 'english',  # Default language
                'adaptation_strategy': 'irt_based',
                'max_session_duration': 60,  # minutes
                'difficulty_range': (0.1, 1.0),
                'enable_voice_practice': True,
                'enable_achievement_system': True
            },
            
            # Database configuration
            'database': {
                'sqlite_path': 'language_learners.db',
                'enable_migrations': True,
                'connection_timeout': 30
            },
            
            # AI and NLP configuration
            'adaptive_learning': {
                'algorithm': 'irt',
                'difficulty_adjustment_factor': 0.1,
                'performance_window': 10,
                'adaptation_threshold': 0.7
            },
            
            'spaced_repetition': {
                'algorithm': 'sm2_plus',
                'initial_interval': 1,
                'ease_factor': 2.5,
                'max_interval': 365
            },
            
            'analytics': {
                'track_detailed_metrics': True,
                'generate_insights': True,
                'retention_days': 90
            },
            
            'content_generation': {
                'enable_dynamic_content': True,
                'content_difficulty_levels': ['beginner', 'elementary', 'intermediate', 'upper_intermediate', 'advanced'],
                'content_types': ['vocabulary', 'grammar', 'conversation', 'reading', 'listening']
            },
            
            # Voice processing configuration
            'voice_processing': {
                'enabled': True,
                'supported_languages': ['english', 'spanish', 'french'],
                'max_audio_duration': 60,  # seconds
                'speech_recognition_provider': 'openai_whisper',
                'pronunciation_scoring': True
            },
            
            # Achievement system configuration
            'achievements': {
                'enabled': True,
                'point_system': True,
                'badges': True,
                'streaks': True,
                'leaderboards': False  # Privacy-focused
            }
        }
        
        # Merge with base configuration
        if base_config:
            language_config.update(base_config)
        
        return language_config
    
    async def start(self) -> None:
        """Start the language learning bot."""
        try:
            self.logger.info("Starting Language Teacher Bot...")
            
            if not await self.initialize():
                self.logger.error("Failed to initialize bot")
                return
            
            self.is_running = True
            
            # Start the language bot polling
            await self.language_bot.start_polling()
            
            self.logger.info("Language Teacher Bot started successfully. Ready for learning sessions!")
            
            # Keep running and provide periodic status updates
            while self.is_running:
                await asyncio.sleep(60)  # Check every minute
                
                # Log periodic stats
                if int(datetime.now().timestamp()) % 300 == 0:  # Every 5 minutes
                    stats = self.get_comprehensive_stats()
                    self.logger.info(
                        f"Bot Status - Users: {stats['total_users']}, "
                        f"Active Sessions: {stats['active_sessions']}, "
                        f"Messages: {stats['messages_processed']}"
                    )
            
        except Exception as e:
            self.logger.error(f"Error in bot main loop: {e}")
        finally:
            await self.stop()
    
    async def stop(self) -> None:
        """Stop the language learning bot."""
        self.logger.info("Stopping Language Teacher Bot...")
        self.is_running = False
        
        try:
            if self.language_bot:
                await self.language_bot.cleanup()
            
            self.logger.info("Language Teacher Bot stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping bot: {e}")
    
    def get_comprehensive_stats(self) -> dict:
        """Get comprehensive statistics for the language learning bot."""
        try:
            base_stats = {
                'uptime_minutes': int((datetime.now() - self.start_time).total_seconds() / 60),
                'total_learning_interactions': self.total_learning_interactions,
                'active_learners': self.active_learners
            }
            
            if self.language_bot:
                bot_stats = self.language_bot.get_bot_stats()
                base_stats.update(bot_stats)
            
            return base_stats
            
        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return {'error': 'Failed to retrieve stats'}
    
    async def handle_emergency_stop(self) -> None:
        """Handle emergency stop procedures."""
        self.logger.warning("Emergency stop initiated")
        await self.stop()


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    print("\nShutdown signal received. Stopping Language Teacher Bot...")
    
    # Create a new event loop for cleanup if needed
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, schedule the stop
            asyncio.create_task(bot.stop())
        else:
            # If loop is not running, run the stop
            loop.run_until_complete(bot.stop())
    except RuntimeError:
        # Create new loop for cleanup
        asyncio.run(bot.stop())
    
    sys.exit(0)


async def main():
    """Main entry point for the Language Teacher Bot."""
    global bot
    
    # Create bot instance
    bot = LanguageTeacherBotOrchestrator()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start bot
    await bot.start()


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                🎓 AI Language Teacher Bot 🎓                 ║
    ║                                                              ║
    ║   • Adaptive Learning with Personalized Difficulty          ║
    ║   • Natural Conversation Practice                           ║
    ║   • Structured Homework & Exercises                         ║
    ║   • Voice Pronunciation Practice                            ║
    ║   • Progress Tracking & Analytics                           ║
    ║   • Achievement System & Gamification                       ║
    ║   • Spaced Repetition for Long-term Retention              ║
    ║                                                              ║
    ║   Supported Languages: English, Spanish, French, German     ║
    ║   Levels: Beginner → Advanced                               ║
    ║                                                              ║
    ║   Powered by AutoGen AI & Advanced NLP                      ║
    ╚══════════════════════════════════════════════════════════════╝
    
    🚀 Starting AI Language Teacher Bot...
    📚 Preparing personalized learning experiences...
    🎯 Ready to help users master new languages!
    
    Press Ctrl+C to stop
    """)
    
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Language Teacher Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting Language Teacher Bot: {e}")
        sys.exit(1)