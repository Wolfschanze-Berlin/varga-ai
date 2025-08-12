"""
Main script to run the Telegram bot with AutoGen smart assistant.
Orchestrates the integration between Telegram and the smart assistant agent.
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
from src.tools.integrations.communication.telegram_tool import TelegramBot, TelegramMessage
from src.tools.integrations.memory.conversation_memory import get_conversation_memory
from agents.categories.assistant.smart_assistant_orchestrator import SmartAssistantOrchestrator


class TelegramAssistantBot:
    """
    Main orchestrator for Telegram bot with AutoGen assistant.
    """
    
    def __init__(self):
        """Initialize the Telegram assistant bot."""
        self.logger = get_logger("telegram_assistant_bot")
        
        # Get centralized configuration
        self.config = get_config()
        
        # Initialize components
        self.telegram_bot: Optional[TelegramBot] = None
        self.assistant_agent: Optional[SmartAssistantOrchestrator] = None
        self.conversation_memory = get_conversation_memory()
        self.bot_username: Optional[str] = None  # Will be set during setup
        
        # State management
        self.is_running = False
        self.start_time = datetime.now()
        self.total_messages_processed = 0
        self.active_chats = set()
        
        # Rate limiting per chat
        self.chat_last_message = {}
        self.min_message_interval = 1.0  # seconds
    
    async def initialize(self) -> bool:
        """
        Initialize all components.
        
        Returns:
            True if initialization successful
        """
        try:
            self.logger.info("Initializing Telegram Assistant Bot...")
            
            # Initialize Telegram bot
            telegram_config = self.config.get_telegram_config()
            telegram_config.update({
                "polling_interval": 1,
                "rate_limit_per_minute": 60,
                "rate_limit_per_hour": 1000
            })
            
            self.telegram_bot = TelegramBot(telegram_config)
            
            # Setup Telegram bot
            if not await self.telegram_bot.setup():
                self.logger.error("Failed to setup Telegram bot")
                return False
            
            # Store bot username for mention detection
            self.bot_username = self.telegram_bot.bot_username
            
            # Initialize smart assistant orchestrator
            self.assistant_agent = SmartAssistantOrchestrator()
            
            if not await self.assistant_agent.initialize():
                self.logger.error("Failed to initialize assistant agent")
                return False
            
            # Register message handler
            self.telegram_bot.add_message_handler(self.handle_telegram_message)
            
            # Register command handlers
            self.telegram_bot.add_command_handler("start", self.handle_start_command)
            self.telegram_bot.add_command_handler("help", self.handle_help_command)
            self.telegram_bot.add_command_handler("status", self.handle_status_command)
            self.telegram_bot.add_command_handler("clear", self.handle_clear_command)
            
            self.logger.info("Telegram Assistant Bot initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize bot: {e}")
            return False
    
    async def handle_telegram_message(self, message: TelegramMessage) -> None:
        """
        Handle incoming Telegram message.
        
        Args:
            message: TelegramMessage to process
        """
        try:
            # Check rate limiting
            chat_id = message.chat_id
            current_time = datetime.now().timestamp()
            
            if chat_id in self.chat_last_message:
                time_since_last = current_time - self.chat_last_message[chat_id]
                if time_since_last < self.min_message_interval:
                    self.logger.warning(f"Rate limiting chat {chat_id}")
                    return
            
            self.chat_last_message[chat_id] = current_time
            
            # Check if this is a group message
            is_group = chat_id < 0  # Negative chat IDs are groups/channels
            
            # In groups, only respond if bot is mentioned OR it's a reply to the bot
            if is_group:
                self.logger.info(f"Group message from {chat_id}: {message.text[:50] if message.text else 'No text'}")
                self.logger.info(f"Bot username for mention detection: @{self.bot_username}")
                
                # Check if this is a reply to the bot's message
                is_reply_to_bot = message.reply_to_message_id is not None
                
                if message.text:
                    # Check if bot is mentioned (with or without @)
                    # Handle multiple mention formats
                    bot_mention_with_at = f"@{self.bot_username}".lower() if self.bot_username else None
                    bot_mention_without_at = self.bot_username.lower() if self.bot_username else None
                    
                    text_lower = message.text.lower()
                    is_mentioned = False
                    
                    if bot_mention_with_at:
                        is_mentioned = bot_mention_with_at in text_lower
                        self.logger.debug(f"Checking for '{bot_mention_with_at}' in '{text_lower[:100]}': {is_mentioned}")
                    
                    # Also check without @ symbol for partial mentions
                    if not is_mentioned and bot_mention_without_at:
                        # Check if bot username appears as a word (not part of another word)
                        words = text_lower.split()
                        is_mentioned = bot_mention_without_at in words or any(bot_mention_without_at in word for word in words)
                        self.logger.debug(f"Checking for '{bot_mention_without_at}' in words: {is_mentioned}")
                    
                    # Log the full detection result
                    self.logger.info(f"Mention detection - Text: '{message.text[:100]}', Bot: @{self.bot_username}, Mentioned: {is_mentioned}, Reply: {is_reply_to_bot}")
                    
                    if not is_mentioned and not is_reply_to_bot:
                        self.logger.info(f"Ignoring group message without mention in chat {chat_id}")
                        return
                    elif is_reply_to_bot:
                        self.logger.info(f"Processing reply to bot in group {chat_id}")
                    elif is_mentioned:
                        self.logger.info(f"Bot mentioned in group {chat_id}: {message.text[:50]}")
                else:
                    self.logger.info(f"Non-text message in group {chat_id}, ignoring")
                    return
            
            # Track active chat
            self.active_chats.add(chat_id)
            
            # Send typing indicator immediately with logging
            typing_sent = await self.telegram_bot.send_typing_action(chat_id)
            self.logger.info(f"Typing indicator sent to chat {chat_id}: {typing_sent}")
            
            # Start a background task to keep sending typing indicator
            typing_task = asyncio.create_task(self._keep_typing(chat_id))
            
            # Log incoming message
            self.logger.info(
                f"Processing message from chat {chat_id}",
                extra={
                    "chat_id": chat_id,
                    "user": message.from_user.get("username") if message.from_user else None,
                    "message_type": message.message_type.value,
                    "text_length": len(message.text) if message.text else 0
                }
            )
            
            # Add user message to conversation memory
            await self.conversation_memory.add_message(
                chat_id=message.chat_id,
                role="user",
                content=message.text if message.text else "No text",
                user_id=message.from_user.get("id") if message.from_user else None,
                message_id=message.message_id,
                thread_id=message.thread_id
            )
            
            # Get conversation history for context
            conversation_history = await self.conversation_memory.get_conversation_context(
                chat_id=message.chat_id,
                max_entries=20,
                include_thread_id=message.thread_id
            )
            
            # Process with assistant orchestrator - include reply context and conversation history
            context = {
                "chat_id": message.chat_id,
                "thread_id": message.thread_id,
                "from_user": message.from_user,
                "message_type": message.message_type.value,
                "reply_to_message_id": message.reply_to_message_id,
                "is_reply": message.reply_to_message_id is not None,
                "conversation_history": conversation_history
            }
            
            # Get the message text
            message_text = message.text if message.text else "No text"
            
            result = await self.assistant_agent.process_message(message_text, context)
            response = result.message if hasattr(result, 'message') else str(result)
            
            # Send response
            if response:
                self.logger.info(f"Sending response to chat {chat_id}: {response[:100]}...")
                # Split long responses
                max_message_length = 4096
                if len(response) > max_message_length:
                    # Split into chunks
                    chunks = self._split_message(response, max_message_length)
                    for chunk in chunks:
                        await self.telegram_bot.send_message(
                            text=chunk,
                            chat_id=chat_id,
                            reply_to_message_id=message.message_id if chunks.index(chunk) == 0 else None,
                            message_thread_id=message.thread_id,  # Support topics in groups
                            parse_mode="Markdown"
                        )
                        await asyncio.sleep(0.5)  # Small delay between messages
                else:
                    result = await self.telegram_bot.send_message(
                        text=response,
                        chat_id=chat_id,
                        reply_to_message_id=message.message_id,
                        message_thread_id=message.thread_id,  # Support topics in groups
                        parse_mode="Markdown"
                    )
                    if result.success:
                        self.logger.info(f"Response sent successfully to chat {chat_id}")
                        
                        # Add assistant response to conversation memory
                        await self.conversation_memory.add_message(
                            chat_id=message.chat_id,
                            role="assistant",
                            content=response,
                            message_id=result.message_id,
                            thread_id=message.thread_id
                        )
                    else:
                        self.logger.error(f"Failed to send response: {result.error}")
            
            # Update metrics
            self.total_messages_processed += 1
            
            # Stop typing indicator
            typing_task.cancel()
            
        except Exception as e:
            # Make sure to cancel typing task on error
            if 'typing_task' in locals():
                typing_task.cancel()
            self.logger.error(f"Error handling message: {e}", exc_info=True)
            
            # Send error message to user
            try:
                await self.telegram_bot.send_message(
                    text="Sorry, I encountered an error processing your message. Please try again.",
                    chat_id=message.chat_id,
                    reply_to_message_id=message.message_id,
                    message_thread_id=message.thread_id  # Support topics in groups
                )
            except:
                pass
    
    async def _keep_typing(self, chat_id: int) -> None:
        """
        Keep sending typing indicator while processing.
        
        Args:
            chat_id: Chat ID to send typing indicator to
        """
        try:
            while True:
                await asyncio.sleep(4)  # Send typing every 4 seconds
                typing_sent = await self.telegram_bot.send_typing_action(chat_id)
                self.logger.debug(f"Continuous typing indicator sent to chat {chat_id}: {typing_sent}")
        except asyncio.CancelledError:
            # Task was cancelled, stop typing
            self.logger.debug(f"Typing indicator task cancelled for chat {chat_id}")
            pass
        except Exception as e:
            self.logger.error(f"Error in typing indicator for chat {chat_id}: {e}")
    
    def _split_message(self, text: str, max_length: int) -> list:
        """
        Split a long message into chunks.
        
        Args:
            text: Text to split
            max_length: Maximum length per chunk
            
        Returns:
            List of text chunks
        """
        chunks = []
        
        # Try to split by paragraphs first
        paragraphs = text.split("\n\n")
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) + 2 <= max_length:
                if current_chunk:
                    current_chunk += "\n\n"
                current_chunk += paragraph
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                
                # If paragraph itself is too long, split it
                if len(paragraph) > max_length:
                    # Split by sentences
                    sentences = paragraph.split(". ")
                    current_chunk = ""
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) + 2 <= max_length:
                            if current_chunk:
                                current_chunk += ". "
                            current_chunk += sentence
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = sentence
                    if current_chunk:
                        current_chunk = current_chunk
                else:
                    current_chunk = paragraph
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    async def handle_start_command(self, message: TelegramMessage) -> None:
        """Handle /start command."""
        welcome_message = """Welcome to the Smart Assistant Bot! 

I'm powered by AutoGen and GPT-4 to help you with:
• Answering questions
• Research and analysis
• Information lookup
• General assistance

Just send me your questions and I'll do my best to help!

Commands:
/help - Show available commands
/status - Show bot status
/clear - Clear conversation history"""
        
        await self.telegram_bot.send_message(
            text=welcome_message,
            chat_id=message.chat_id,
            parse_mode="Markdown"
        )
    
    async def handle_help_command(self, message: TelegramMessage) -> None:
        """Handle /help command."""
        help_message = """Available Commands:

/start - Welcome message
/help - Show this help
/status - Show bot and system status
/clear - Clear your conversation history

You can also just send me any question or request directly!

Examples:
• "What is machine learning?"
• "Research the history of computers"
• "Explain quantum physics simply"
• "Help me understand Python decorators"

I'll provide detailed, helpful responses!"""
        
        await self.telegram_bot.send_message(
            text=help_message,
            chat_id=message.chat_id,
            parse_mode="Markdown"
        )
    
    async def handle_status_command(self, message: TelegramMessage) -> None:
        """Handle /status command."""
        uptime = datetime.now() - self.start_time
        hours = int(uptime.total_seconds() // 3600)
        minutes = int((uptime.total_seconds() % 3600) // 60)
        
        bot_metrics = self.telegram_bot.get_metrics()
        agent_metrics = self.assistant_agent.get_metrics()
        
        status_message = f"""Bot Status:

System:
• Uptime: {hours}h {minutes}m
• Messages processed: {self.total_messages_processed}
• Active chats: {len(self.active_chats)}

Telegram Bot:
• Messages received: {bot_metrics['telegram_metrics']['messages_received']}
• Messages sent: {bot_metrics['telegram_metrics']['messages_sent']}
• Queue size: {bot_metrics['telegram_metrics']['queue_size']}

Assistant Agent:
• Total executions: {agent_metrics['total_executions']}
• Success rate: {agent_metrics['success_rate']:.1%}
• Model: GPT-4
• Research enabled: Yes"""
        
        await self.telegram_bot.send_message(
            text=status_message,
            chat_id=message.chat_id,
            parse_mode="Markdown"
        )
    
    async def handle_clear_command(self, message: TelegramMessage) -> None:
        """Handle /clear command."""
        self.assistant_agent.clear_conversation(message.chat_id)
        
        await self.telegram_bot.send_message(
            text="Your conversation history has been cleared. Start fresh with your next message!",
            chat_id=message.chat_id
        )
    
    async def start(self) -> None:
        """Start the bot."""
        try:
            self.logger.info("Starting Telegram Assistant Bot...")
            
            if not await self.initialize():
                self.logger.error("Failed to initialize bot")
                return
            
            self.is_running = True
            
            # Start polling
            await self.telegram_bot.start_polling()
            
            self.logger.info("Bot started successfully. Listening for messages...")
            
            # Keep running
            while self.is_running:
                await asyncio.sleep(1)
                
                # Periodic health check
                if int(datetime.now().timestamp()) % 60 == 0:
                    self.logger.debug(
                        f"Health check - Messages: {self.total_messages_processed}, "
                        f"Active chats: {len(self.active_chats)}"
                    )
            
        except Exception as e:
            self.logger.error(f"Error in bot main loop: {e}")
        finally:
            await self.stop()
    
    async def stop(self) -> None:
        """Stop the bot."""
        self.logger.info("Stopping Telegram Assistant Bot...")
        self.is_running = False
        
        try:
            # Stop polling
            if self.telegram_bot:
                await self.telegram_bot.stop_polling()
                await self.telegram_bot.cleanup()
            
            # Cleanup assistant
            if self.assistant_agent:
                await self.assistant_agent.cleanup()
            
            self.logger.info("Bot stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping bot: {e}")


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    print("\nShutdown signal received. Stopping bot...")
    asyncio.create_task(bot.stop())
    sys.exit(0)


async def main():
    """Main entry point."""
    global bot
    
    # Create bot instance
    bot = TelegramAssistantBot()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start bot
    await bot.start()


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════╗
    ║   Telegram AutoGen Assistant Bot         ║
    ║   Powered by Microsoft AutoGen & GPT-4   ║
    ╚══════════════════════════════════════════╝
    
    Starting bot...
    Press Ctrl+C to stop
    """)
    
    # Run the bot
    asyncio.run(main())