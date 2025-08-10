"""
Chatbot Interface Tool for AutoGen SME platform.
Provides conversational AI capabilities for customer interactions.
"""

import json
import uuid
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import httpx

from .base import BaseTool, ToolResult, ToolStatus, ToolMetadata, ToolCapability
from ..log_service import get_logger
from ..config import get_tool_config, ChatbotConfig


class MessageRole(str, Enum):
    """Chat message roles."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ConversationStatus(str, Enum):
    """Conversation status."""
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"
    ESCALATED = "escalated"


@dataclass
class ChatMessage:
    """Represents a single chat message."""
    role: MessageRole
    content: str
    timestamp: datetime
    message_id: str = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Conversation:
    """Represents a conversation session."""
    conversation_id: str
    tenant_id: str
    user_id: Optional[str]
    status: ConversationStatus
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime
    context: Dict[str, Any]
    
    def add_message(self, role: MessageRole, content: str, metadata: Dict[str, Any] = None) -> ChatMessage:
        """Add a message to the conversation."""
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.updated_at = datetime.now()
        return message
    
    def get_recent_messages(self, limit: int = 10) -> List[ChatMessage]:
        """Get the most recent messages."""
        return self.messages[-limit:] if self.messages else []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary."""
        return {
            "conversation_id": self.conversation_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "status": self.status.value,
            "messages": [asdict(msg) for msg in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "context": self.context
        }


class ChatbotInterfaceTool(BaseTool):
    """Tool for managing conversational AI interactions with customers."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the chatbot interface tool.
        
        Args:
            config: Tool configuration
        """
        super().__init__(config)
        self.chatbot_config = ChatbotConfig(**config)
        self.logger = get_logger("chatbot_interface_tool")
        
        # In-memory conversation storage (in production, use Redis or database)
        self._conversations: Dict[str, Conversation] = {}
        
        # API endpoint for the language model
        self.api_endpoint = "https://api.openai.com/v1/chat/completions"
        if self.chatbot_config.model_provider == "anthropic":
            self.api_endpoint = "https://api.anthropic.com/v1/messages"
    
    @property
    def metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        if self._metadata is None:
            self._metadata = ToolMetadata(
                name="chatbot_interface",
                description="Provide conversational AI interface for customer interactions",
                version="1.0.0",
                capabilities=[ToolCapability.COMMUNICATION],
                input_schema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["start_conversation", "send_message", "get_conversation", "end_conversation"],
                            "description": "Action to perform"
                        },
                        "conversation_id": {
                            "type": "string",
                            "description": "Unique conversation identifier"
                        },
                        "user_message": {
                            "type": "string",
                            "description": "User's message content"
                        },
                        "user_id": {
                            "type": "string",
                            "description": "Optional user identifier"
                        },
                        "business_context": {
                            "type": "object",
                            "description": "Business-specific context",
                            "properties": {
                                "business_name": {"type": "string"},
                                "business_type": {"type": "string"},
                                "support_hours": {"type": "string"},
                                "escalation_info": {"type": "string"}
                            }
                        },
                        "conversation_context": {
                            "type": "object",
                            "description": "Additional conversation context"
                        }
                    },
                    "required": ["action"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "conversation_id": {"type": "string"},
                        "bot_response": {"type": "string"},
                        "conversation_status": {"type": "string"},
                        "should_escalate": {"type": "boolean"},
                        "escalation_reason": {"type": "string"},
                        "conversation_summary": {"type": "object"}
                    }
                },
                rate_limits={
                    "per_minute": self.chatbot_config.rate_limit_per_minute,
                    "per_hour": self.chatbot_config.rate_limit_per_hour
                },
                dependencies=["httpx"],
                tags=["chatbot", "conversation", "customer-service", "ai"]
            )
        return self._metadata
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate chatbot input data.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            action = input_data.get("action")
            if action not in ["start_conversation", "send_message", "get_conversation", "end_conversation"]:
                self.logger.warning(f"Invalid action: {action}")
                return False
            
            # Validate action-specific requirements
            if action in ["send_message", "get_conversation", "end_conversation"]:
                if not input_data.get("conversation_id"):
                    self.logger.warning("conversation_id is required for this action")
                    return False
            
            if action == "send_message":
                user_message = input_data.get("user_message", "").strip()
                if not user_message:
                    self.logger.warning("user_message is required for send_message action")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Input validation failed: {e}")
            return False
    
    async def _do_execute(
        self, 
        input_data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> ToolResult:
        """
        Execute chatbot interface action.
        
        Args:
            input_data: Action parameters
            context: Execution context
            
        Returns:
            Chatbot interaction result
        """
        action = input_data["action"]
        tenant_id = context.get("tenant_id", "unknown")
        
        self.logger.info(f"Executing chatbot action: {action}")
        
        try:
            if action == "start_conversation":
                return await self._start_conversation(input_data, tenant_id)
            elif action == "send_message":
                return await self._send_message(input_data, tenant_id)
            elif action == "get_conversation":
                return await self._get_conversation(input_data, tenant_id)
            elif action == "end_conversation":
                return await self._end_conversation(input_data, tenant_id)
            else:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"Unknown action: {action}"
                )
                
        except Exception as e:
            self.logger.error(f"Chatbot action {action} failed: {e}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Action failed: {str(e)}"
            )
    
    async def _start_conversation(
        self, 
        input_data: Dict[str, Any], 
        tenant_id: str
    ) -> ToolResult:
        """Start a new conversation."""
        conversation_id = str(uuid.uuid4())
        user_id = input_data.get("user_id")
        business_context = input_data.get("business_context", {})
        conversation_context = input_data.get("conversation_context", {})
        
        # Create conversation
        conversation = Conversation(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            status=ConversationStatus.ACTIVE,
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            context={**business_context, **conversation_context}
        )
        
        # Add system message
        business_name = business_context.get("business_name", "our company")
        system_prompt = self.chatbot_config.system_prompt_template.format(
            business_name=business_name
        )
        
        conversation.add_message(
            MessageRole.SYSTEM, 
            system_prompt,
            {"type": "system_initialization"}
        )
        
        # Generate welcome message
        welcome_message = await self._generate_response(
            conversation,
            "Generate a friendly welcome message for a customer visiting our website."
        )
        
        conversation.add_message(
            MessageRole.ASSISTANT,
            welcome_message,
            {"type": "welcome_message"}
        )
        
        # Store conversation
        self._conversations[conversation_id] = conversation
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data={
                "conversation_id": conversation_id,
                "bot_response": welcome_message,
                "conversation_status": ConversationStatus.ACTIVE.value,
                "should_escalate": False
            },
            metadata={
                "tenant_id": tenant_id,
                "user_id": user_id,
                "message_count": len(conversation.messages)
            }
        )
    
    async def _send_message(
        self, 
        input_data: Dict[str, Any], 
        tenant_id: str
    ) -> ToolResult:
        """Send a message and get bot response."""
        conversation_id = input_data["conversation_id"]
        user_message = input_data["user_message"]
        
        # Get conversation
        conversation = self._conversations.get(conversation_id)
        if not conversation:
            return ToolResult(
                status=ToolStatus.ERROR,
                error="Conversation not found"
            )
        
        if conversation.tenant_id != tenant_id:
            return ToolResult(
                status=ToolStatus.ERROR,
                error="Unauthorized access to conversation"
            )
        
        # Check if conversation is active
        if conversation.status != ConversationStatus.ACTIVE:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Conversation is {conversation.status.value}"
            )
        
        # Add user message
        conversation.add_message(
            MessageRole.USER,
            user_message,
            {"user_id": input_data.get("user_id")}
        )
        
        # Check conversation length limit
        if len(conversation.messages) > self.chatbot_config.max_conversation_length:
            # Remove oldest non-system messages
            system_messages = [msg for msg in conversation.messages if msg.role == MessageRole.SYSTEM]
            other_messages = [msg for msg in conversation.messages if msg.role != MessageRole.SYSTEM]
            
            # Keep recent messages within limit
            keep_count = self.chatbot_config.max_conversation_length - len(system_messages)
            conversation.messages = system_messages + other_messages[-keep_count:]
        
        # Generate bot response
        bot_response = await self._generate_response(conversation, user_message)
        
        # Check if escalation is needed
        should_escalate, escalation_reason = await self._check_escalation(
            conversation, user_message, bot_response
        )
        
        if should_escalate:
            conversation.status = ConversationStatus.ESCALATED
            # Add escalation message
            escalation_message = (
                "Let me connect you with a human agent who can better assist you with this request. "
                "Please hold on for a moment."
            )
            conversation.add_message(
                MessageRole.ASSISTANT,
                escalation_message,
                {"type": "escalation", "reason": escalation_reason}
            )
            bot_response = escalation_message
        else:
            # Add bot response
            conversation.add_message(
                MessageRole.ASSISTANT,
                bot_response,
                {"type": "response"}
            )
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data={
                "conversation_id": conversation_id,
                "bot_response": bot_response,
                "conversation_status": conversation.status.value,
                "should_escalate": should_escalate,
                "escalation_reason": escalation_reason if should_escalate else None
            },
            metadata={
                "tenant_id": tenant_id,
                "message_count": len(conversation.messages),
                "response_generated": True
            }
        )
    
    async def _generate_response(
        self, 
        conversation: Conversation, 
        user_message: str
    ) -> str:
        """Generate AI response for the conversation."""
        try:
            # Prepare messages for API
            messages = []
            recent_messages = conversation.get_recent_messages(10)
            
            for msg in recent_messages:
                if msg.role == MessageRole.SYSTEM:
                    messages.append({"role": "system", "content": msg.content})
                elif msg.role == MessageRole.USER:
                    messages.append({"role": "user", "content": msg.content})
                elif msg.role == MessageRole.ASSISTANT:
                    messages.append({"role": "assistant", "content": msg.content})
            
            # Generate response using configured provider
            if self.chatbot_config.model_provider == "openai":
                response = await self._generate_openai_response(messages)
            elif self.chatbot_config.model_provider == "anthropic":
                response = await self._generate_anthropic_response(messages)
            else:
                raise ValueError(f"Unsupported model provider: {self.chatbot_config.model_provider}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Response generation failed: {e}")
            # Return fallback response
            import random
            return random.choice(self.chatbot_config.fallback_responses)
    
    async def _generate_openai_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate response using OpenAI API."""
        headers = {
            "Authorization": f"Bearer {self.chatbot_config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.chatbot_config.model_name,
            "messages": messages,
            "max_tokens": min(self.chatbot_config.context_window_tokens // 4, 1000),
            "temperature": 0.7,
            "top_p": 1.0
        }
        
        async with self.http_client as client:
            response = await client.post(
                self.api_endpoint,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        
        return data["choices"][0]["message"]["content"].strip()
    
    async def _generate_anthropic_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate response using Anthropic API."""
        # Separate system message from conversation
        system_message = ""
        conversation_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                conversation_messages.append(msg)
        
        headers = {
            "x-api-key": self.chatbot_config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": self.chatbot_config.model_name,
            "system": system_message,
            "messages": conversation_messages,
            "max_tokens": min(self.chatbot_config.context_window_tokens // 4, 1000),
            "temperature": 0.7
        }
        
        async with self.http_client as client:
            response = await client.post(
                self.api_endpoint,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        
        return data["content"][0]["text"].strip()
    
    async def _check_escalation(
        self, 
        conversation: Conversation, 
        user_message: str, 
        bot_response: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check if conversation should be escalated to human agent.
        
        Returns:
            Tuple of (should_escalate, escalation_reason)
        """
        # Simple escalation rules (in production, use more sophisticated logic)
        escalation_keywords = [
            "speak to human", "human agent", "transfer to agent", "escalate",
            "manager", "supervisor", "complaint", "angry", "frustrated",
            "legal", "lawsuit", "refund", "cancel", "billing issue"
        ]
        
        user_message_lower = user_message.lower()
        
        for keyword in escalation_keywords:
            if keyword in user_message_lower:
                return True, f"User requested escalation: {keyword}"
        
        # Check for repeated similar messages (user seems stuck)
        recent_user_messages = [
            msg.content for msg in conversation.get_recent_messages(6)
            if msg.role == MessageRole.USER
        ]
        
        if len(recent_user_messages) >= 3:
            # Simple similarity check (in production, use better similarity metrics)
            similar_count = 0
            for i in range(len(recent_user_messages) - 1):
                if len(set(recent_user_messages[i].split()) & set(recent_user_messages[i + 1].split())) > 2:
                    similar_count += 1
            
            if similar_count >= 2:
                return True, "User seems stuck with similar repeated queries"
        
        # Check conversation length for potential frustration
        if len(conversation.messages) > 20:
            return True, "Long conversation may require human assistance"
        
        return False, None
    
    async def _get_conversation(
        self, 
        input_data: Dict[str, Any], 
        tenant_id: str
    ) -> ToolResult:
        """Get conversation details."""
        conversation_id = input_data["conversation_id"]
        
        conversation = self._conversations.get(conversation_id)
        if not conversation:
            return ToolResult(
                status=ToolStatus.ERROR,
                error="Conversation not found"
            )
        
        if conversation.tenant_id != tenant_id:
            return ToolResult(
                status=ToolStatus.ERROR,
                error="Unauthorized access to conversation"
            )
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data={
                "conversation_summary": conversation.to_dict(),
                "conversation_status": conversation.status.value,
                "message_count": len(conversation.messages)
            }
        )
    
    async def _end_conversation(
        self, 
        input_data: Dict[str, Any], 
        tenant_id: str
    ) -> ToolResult:
        """End a conversation."""
        conversation_id = input_data["conversation_id"]
        
        conversation = self._conversations.get(conversation_id)
        if not conversation:
            return ToolResult(
                status=ToolStatus.ERROR,
                error="Conversation not found"
            )
        
        if conversation.tenant_id != tenant_id:
            return ToolResult(
                status=ToolStatus.ERROR,
                error="Unauthorized access to conversation"
            )
        
        conversation.status = ConversationStatus.ENDED
        conversation.updated_at = datetime.now()
        
        # Add closing message
        closing_message = "Thank you for contacting us! Have a great day."
        conversation.add_message(
            MessageRole.ASSISTANT,
            closing_message,
            {"type": "conversation_end"}
        )
        
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data={
                "conversation_id": conversation_id,
                "bot_response": closing_message,
                "conversation_status": ConversationStatus.ENDED.value,
                "final_message_count": len(conversation.messages)
            }
        )
    
    async def health_check(self) -> bool:
        """
        Check if the chatbot service is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try a simple conversation simulation
            test_conversation = Conversation(
                conversation_id="health_check",
                tenant_id="test",
                user_id=None,
                status=ConversationStatus.ACTIVE,
                messages=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                context={"business_name": "Test Business"}
            )
            
            test_conversation.add_message(MessageRole.SYSTEM, "You are a helpful assistant.")
            response = await self._generate_response(test_conversation, "Hello")
            
            return len(response) > 0
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False