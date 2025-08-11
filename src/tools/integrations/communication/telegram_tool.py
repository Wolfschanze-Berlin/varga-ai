"""
Telegram bot integration tool.
Provides base functionality for Telegram bot communication.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
from collections import deque

from src.tools.base import BaseTool, ToolResult, ToolStatus, ToolMetadata, ToolCapability
from src.log_service import get_logger
from src.config import settings


class MessageType(Enum):
    """Telegram message types."""
    TEXT = "text"
    PHOTO = "photo"
    DOCUMENT = "document"
    VOICE = "voice"
    VIDEO = "video"
    LOCATION = "location"
    CONTACT = "contact"
    CALLBACK_QUERY = "callback_query"
    INLINE_QUERY = "inline_query"


@dataclass
class TelegramMessage:
    """Represents a Telegram message."""
    
    message_id: int
    chat_id: int
    text: Optional[str] = None
    from_user: Optional[Dict[str, Any]] = None
    date: Optional[datetime] = None
    message_type: MessageType = MessageType.TEXT
    media: Optional[Dict[str, Any]] = None
    reply_to_message_id: Optional[int] = None
    thread_id: Optional[int] = None  # For topics in groups
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TelegramResponse:
    """Response from Telegram API."""
    
    success: bool
    message_id: Optional[int] = None
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class TelegramBot(BaseTool):
    """
    Base Telegram bot integration tool.
    Handles polling, message processing, and sending responses.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Telegram bot.
        
        Args:
            config: Bot configuration including token
        """
        super().__init__(config)
        
        # Bot configuration
        self.bot_token = config.get("bot_token") or settings.TELEGRAM_BOT_TOKEN
        self.default_chat_id = config.get("default_chat_id") or settings.TELEGRAM_CHAT_ID
        self.polling_interval = config.get("polling_interval", 1)  # seconds
        self.webhook_enabled = config.get("webhook_enabled", False)
        
        if not self.bot_token:
            raise ValueError("Telegram bot token not provided")
        
        # API configuration
        self.api_base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # State management
        self.last_update_id = 0
        self.is_polling = False
        self._polling_task: Optional[asyncio.Task] = None
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Bot info (populated during setup)
        self.bot_username: Optional[str] = None
        self.bot_id: Optional[int] = None
        
        # Message handlers
        self._message_handlers: List[Callable] = []
        self._command_handlers: Dict[str, Callable] = {}
        self._callback_handlers: Dict[str, Callable] = {}
        
        # Message queue for processing
        self._message_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._processing_task: Optional[asyncio.Task] = None
        
        # Processed message tracking (to avoid duplicates)
        self._processed_messages: Set[int] = set()
        self._processed_messages_cache: deque = deque(maxlen=10000)
        
        # Metrics
        self.messages_received = 0
        self.messages_sent = 0
        self.errors_count = 0
        
        self.logger = get_logger("telegram_bot")
        
        # Tool metadata
        self._metadata = ToolMetadata(
            name="telegram_bot",
            version="1.0.0",
            description="Telegram bot integration for sending and receiving messages through the Telegram Bot API",
            capabilities=[
                ToolCapability.COMMUNICATION,
                ToolCapability.INTEGRATION
            ],
            input_schema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["send_message", "start_polling", "stop_polling"]},
                    "text": {"type": "string"},
                    "chat_id": {"type": "integer"}
                },
                "required": ["action"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message_id": {"type": "integer"},
                    "error": {"type": "string"}
                }
            },
            rate_limits={
                "messages_per_minute": 30,
                "messages_per_second": 1
            },
            dependencies=["aiohttp"],
            tags=["telegram", "messaging", "bot", "communication"]
        )
    
    @property
    def metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return self._metadata
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data for the tool.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        action = input_data.get("action")
        
        if not action:
            self.logger.error("No action specified in input data")
            return False
        
        if action == "send_message":
            if not input_data.get("text"):
                self.logger.error("No text provided for send_message action")
                return False
        
        return True
    
    async def setup(self) -> bool:
        """Set up the Telegram bot."""
        try:
            # Create aiohttp session
            if not self._session:
                self._session = aiohttp.ClientSession()
            
            # Test bot connection
            bot_info = await self._api_call("getMe")
            if bot_info and bot_info.get("ok"):
                self.bot_username = bot_info['result']['username']
                self.bot_id = bot_info['result']['id']
                self.logger.info(f"Telegram bot connected: @{self.bot_username}")
                return True
            else:
                self.logger.error("Failed to connect to Telegram bot")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to setup Telegram bot: {e}")
            return False
    
    async def _api_call(
        self,
        method: str,
        data: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        Make an API call to Telegram.
        
        Args:
            method: API method name
            data: Optional request data
            timeout: Request timeout in seconds
            
        Returns:
            API response data
        """
        url = f"{self.api_base_url}/{method}"
        
        try:
            async with self._session.post(
                url,
                json=data,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                result = await response.json()
                
                if not result.get("ok"):
                    self.logger.error(f"Telegram API error: {result.get('description')}")
                    self.errors_count += 1
                
                return result
                
        except asyncio.TimeoutError:
            self.logger.error(f"Telegram API timeout for method {method}")
            self.errors_count += 1
            return None
        except Exception as e:
            self.logger.error(f"Telegram API call failed: {e}")
            self.errors_count += 1
            return None
    
    async def send_message(
        self,
        text: str,
        chat_id: Optional[int] = None,
        reply_to_message_id: Optional[int] = None,
        message_thread_id: Optional[int] = None,
        parse_mode: str = "HTML",
        disable_notification: bool = False,
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> TelegramResponse:
        """
        Send a text message.
        
        Args:
            text: Message text
            chat_id: Target chat ID (uses default if not provided)
            reply_to_message_id: Message ID to reply to
            parse_mode: Parse mode (HTML, Markdown, MarkdownV2)
            disable_notification: Disable notification
            reply_markup: Reply markup (keyboard, inline keyboard, etc.)
            
        Returns:
            TelegramResponse with result
        """
        if not chat_id:
            chat_id = self.default_chat_id
        
        if not chat_id:
            return TelegramResponse(
                success=False,
                error="No chat_id provided and no default chat_id configured"
            )
        
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_notification": disable_notification
        }
        
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id
        
        if message_thread_id:
            data["message_thread_id"] = message_thread_id
        
        if reply_markup:
            data["reply_markup"] = reply_markup
        
        result = await self._api_call("sendMessage", data)
        
        if result and result.get("ok"):
            self.messages_sent += 1
            message_id = result["result"]["message_id"]
            
            self.logger.debug(f"Message sent to chat {chat_id}: {text[:50]}...")
            
            return TelegramResponse(
                success=True,
                message_id=message_id,
                data=result["result"]
            )
        else:
            return TelegramResponse(
                success=False,
                error=result.get("description") if result else "Failed to send message"
            )
    
    async def send_typing_action(self, chat_id: Optional[int] = None) -> bool:
        """
        Send typing action to show bot is processing.
        
        Args:
            chat_id: Target chat ID
            
        Returns:
            True if successful
        """
        if not chat_id:
            chat_id = self.default_chat_id
        
        if not chat_id:
            self.logger.warning("No chat_id provided for typing action")
            return False
        
        self.logger.debug(f"Sending typing action to chat {chat_id}")
        
        result = await self._api_call("sendChatAction", {
            "chat_id": chat_id,
            "action": "typing"
        })
        
        success = result and result.get("ok", False)
        if success:
            self.logger.debug(f"Typing action sent successfully to chat {chat_id}")
        else:
            self.logger.warning(f"Typing action failed for chat {chat_id}: {result}")
        
        return success
    
    async def get_updates(self, timeout: int = 30) -> List[TelegramMessage]:
        """
        Get updates using long polling.
        
        Args:
            timeout: Long polling timeout
            
        Returns:
            List of new messages
        """
        data = {
            "offset": self.last_update_id + 1,
            "timeout": timeout,
            "allowed_updates": ["message", "edited_message", "channel_post", "edited_channel_post", "callback_query", "inline_query", "message_reaction", "message_reaction_count"]
        }
        
        result = await self._api_call("getUpdates", data, timeout=timeout + 5)
        
        messages = []
        if result and result.get("ok"):
            updates = result.get("result", [])
            if updates:
                self.logger.info(f"Got {len(updates)} updates from Telegram")
                for update in updates[:3]:  # Log first 3 for debugging
                    self.logger.debug(f"Update type: {list(update.keys())}")
                    if "message" in update:
                        msg = update["message"]
                        self.logger.debug(f"Message from chat {msg.get('chat', {}).get('id')}, type: {msg.get('chat', {}).get('type')}")
                        if "text" in msg:
                            self.logger.debug(f"Update text: {msg['text'][:100]}")
                        if "entities" in msg:
                            self.logger.debug(f"Message entities: {msg['entities']}")
            
            for update in updates:
                update_id = update.get("update_id", 0)
                
                # Skip if already processed
                if update_id in self._processed_messages:
                    continue
                
                # Track update ID
                if update_id > self.last_update_id:
                    self.last_update_id = update_id
                
                # Mark as processed
                self._processed_messages.add(update_id)
                self._processed_messages_cache.append(update_id)
                
                # Clean old processed messages
                if len(self._processed_messages) > 20000:
                    self._processed_messages = set(self._processed_messages_cache)
                
                # Parse message
                message = self._parse_update(update)
                if message:
                    self.logger.info(f"Parsed message from chat {message.chat_id}: {message.text[:100] if message.text else 'No text'}")
                    messages.append(message)
                    self.messages_received += 1
                else:
                    self.logger.warning(f"Could not parse update: {update}")
        
        return messages
    
    def _parse_update(self, update: Dict[str, Any]) -> Optional[TelegramMessage]:
        """
        Parse a Telegram update into a TelegramMessage.
        
        Args:
            update: Raw update data
            
        Returns:
            Parsed TelegramMessage or None
        """
        try:
            # Handle different types of messages
            msg = None
            if "message" in update:
                msg = update["message"]
            elif "edited_message" in update:
                msg = update["edited_message"]
                self.logger.debug("Processing edited message")
            elif "channel_post" in update:
                msg = update["channel_post"]
                self.logger.debug("Processing channel post")
            elif "edited_channel_post" in update:
                msg = update["edited_channel_post"]
                self.logger.debug("Processing edited channel post")
            
            if msg:
                # Log message details for debugging
                self.logger.debug(f"Parsing message from chat {msg.get('chat', {}).get('id')}, type: {msg.get('chat', {}).get('type')}")
                
                # Extract thread_id for topics in groups
                thread_id = None
                if msg.get("reply_to_message"):
                    thread_id = msg["reply_to_message"].get("message_thread_id")
                elif msg.get("message_thread_id"):
                    thread_id = msg.get("message_thread_id")
                
                return TelegramMessage(
                    message_id=msg.get("message_id"),
                    chat_id=msg["chat"]["id"],
                    text=msg.get("text"),
                    from_user=msg.get("from"),
                    date=datetime.fromtimestamp(msg.get("date", 0)),
                    message_type=self._get_message_type(msg),
                    media=self._extract_media(msg),
                    reply_to_message_id=msg.get("reply_to_message", {}).get("message_id"),
                    thread_id=thread_id,
                    raw_data=msg
                )
            
            # Handle callback queries
            elif "callback_query" in update:
                query = update["callback_query"]
                
                return TelegramMessage(
                    message_id=query.get("id"),
                    chat_id=query["message"]["chat"]["id"],
                    text=query.get("data"),
                    from_user=query.get("from"),
                    date=datetime.now(),
                    message_type=MessageType.CALLBACK_QUERY,
                    raw_data=query
                )
            
            # Handle inline queries
            elif "inline_query" in update:
                query = update["inline_query"]
                
                return TelegramMessage(
                    message_id=query.get("id"),
                    chat_id=0,  # Inline queries don't have chat_id
                    text=query.get("query"),
                    from_user=query.get("from"),
                    date=datetime.now(),
                    message_type=MessageType.INLINE_QUERY,
                    raw_data=query
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to parse update: {e}")
            return None
    
    def _get_message_type(self, message: Dict[str, Any]) -> MessageType:
        """Determine message type."""
        if "text" in message:
            return MessageType.TEXT
        elif "photo" in message:
            return MessageType.PHOTO
        elif "document" in message:
            return MessageType.DOCUMENT
        elif "voice" in message:
            return MessageType.VOICE
        elif "video" in message:
            return MessageType.VIDEO
        elif "location" in message:
            return MessageType.LOCATION
        elif "contact" in message:
            return MessageType.CONTACT
        else:
            return MessageType.TEXT
    
    def _extract_media(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract media information from message."""
        media_types = ["photo", "document", "voice", "video", "location", "contact"]
        
        for media_type in media_types:
            if media_type in message:
                return {
                    "type": media_type,
                    "data": message[media_type]
                }
        
        return None
    
    def add_message_handler(self, handler: Callable) -> None:
        """
        Add a message handler.
        
        Args:
            handler: Async function to handle messages
        """
        self._message_handlers.append(handler)
    
    def add_command_handler(self, command: str, handler: Callable) -> None:
        """
        Add a command handler.
        
        Args:
            command: Command name (without /)
            handler: Async function to handle the command
        """
        self._command_handlers[command] = handler
    
    async def start_polling(self) -> None:
        """Start polling for messages."""
        if self.is_polling:
            self.logger.warning("Polling already started")
            return
        
        self.is_polling = True
        self._polling_task = asyncio.create_task(self._polling_loop())
        self._processing_task = asyncio.create_task(self._process_message_queue())
        
        self.logger.info("Telegram bot polling started")
    
    async def stop_polling(self) -> None:
        """Stop polling for messages."""
        self.is_polling = False
        
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
        
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Telegram bot polling stopped")
    
    async def _polling_loop(self) -> None:
        """Main polling loop."""
        self.logger.info("Starting polling loop")
        poll_count = 0
        while self.is_polling:
            try:
                poll_count += 1
                if poll_count % 10 == 1:  # Log every 10th poll
                    self.logger.info(f"Polling for updates (offset: {self.last_update_id + 1}, poll #{poll_count})")
                messages = await self.get_updates(timeout=30)
                
                if messages:
                    self.logger.info(f"Received {len(messages)} new messages")
                    for message in messages:
                        await self._message_queue.put(message)
                
                # Short delay between polls
                await asyncio.sleep(self.polling_interval)
                
            except Exception as e:
                self.logger.error(f"Error in polling loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _process_message_queue(self) -> None:
        """Process messages from the queue."""
        while self.is_polling:
            try:
                # Get message with timeout
                message = await asyncio.wait_for(
                    self._message_queue.get(),
                    timeout=1.0
                )
                
                # Process the message
                await self._handle_message(message)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error processing message: {e}")
    
    async def _handle_message(self, message: TelegramMessage) -> None:
        """
        Handle an incoming message.
        
        Args:
            message: TelegramMessage to handle
        """
        try:
            # Check for commands
            if message.text and message.text.startswith("/"):
                command = message.text.split()[0][1:].split("@")[0]
                if command in self._command_handlers:
                    await self._command_handlers[command](message)
                    return
            
            # Process with general handlers
            for handler in self._message_handlers:
                try:
                    await handler(message)
                except Exception as e:
                    self.logger.error(f"Error in message handler: {e}")
            
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
    
    async def _do_execute(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ToolResult:
        """
        Execute the Telegram tool.
        
        Args:
            input_data: Input parameters
            context: Execution context
            
        Returns:
            Tool execution result
        """
        action = input_data.get("action", "send_message")
        
        if action == "send_message":
            text = input_data.get("text", "")
            chat_id = input_data.get("chat_id")
            
            response = await self.send_message(text, chat_id)
            
            return ToolResult(
                status=ToolStatus.SUCCESS if response.success else ToolStatus.ERROR,
                data={"message_id": response.message_id} if response.success else None,
                error=response.error
            )
        
        elif action == "start_polling":
            await self.start_polling()
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={"polling": True}
            )
        
        elif action == "stop_polling":
            await self.stop_polling()
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={"polling": False}
            )
        
        else:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Unknown action: {action}"
            )
    
    async def cleanup(self) -> bool:
        """Clean up resources."""
        try:
            # Stop polling
            if self.is_polling:
                await self.stop_polling()
            
            # Close session
            if self._session:
                await self._session.close()
                self._session = None
            
            return await super().cleanup()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get bot metrics."""
        base_metrics = self.get_performance_metrics()
        
        return {
            **base_metrics,
            "telegram_metrics": {
                "messages_received": self.messages_received,
                "messages_sent": self.messages_sent,
                "errors_count": self.errors_count,
                "is_polling": self.is_polling,
                "last_update_id": self.last_update_id,
                "queue_size": self._message_queue.qsize(),
                "processed_messages_count": len(self._processed_messages)
            }
        }