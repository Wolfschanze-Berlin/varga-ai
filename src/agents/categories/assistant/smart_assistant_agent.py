"""
Smart Assistant Agent implementation.
Handles general queries, research, and intelligent responses.
"""

import json
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import re

from autogen import ConversableAgent, Agent, AssistantAgent, UserProxyAgent
from autogen.agentchat import GroupChat, GroupChatManager

from agents.base.base_agent import BaseAgent, AgentConfig, AgentResponse
from src.log_service import get_logger
from src.tools.integrations.communication.telegram_tool import TelegramBot, TelegramMessage


class SmartAssistantAgent(BaseAgent):
    """
    Smart assistant agent that can answer questions, do research, and handle general inquiries.
    Uses AutoGen's conversational capabilities for intelligent responses.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the smart assistant agent.
        
        Args:
            config: Optional agent configuration
        """
        if not config:
            config = self._get_default_config()
        
        super().__init__(config)
        
        # Assistant components
        self._assistant: Optional[AssistantAgent] = None
        self._user_proxy: Optional[UserProxyAgent] = None
        self._researcher: Optional[AssistantAgent] = None
        self._group_chat: Optional[GroupChat] = None
        self._manager: Optional[GroupChatManager] = None
        
        # Conversation state
        self._conversations: Dict[int, List[Dict]] = {}  # chat_id -> conversation history
        self._active_tasks: Dict[int, str] = {}  # chat_id -> current task
        
        # Research capabilities
        self.enable_research = config.custom_config.get("enable_research", True)
        self.enable_web_search = config.custom_config.get("enable_web_search", False)
        
    def _get_default_config(self) -> AgentConfig:
        """Get default configuration for the smart assistant."""
        return AgentConfig(
            name="smart_assistant",
            description="Intelligent assistant for answering questions and doing research",
            category="assistant",
            system_message="""You are a helpful and intelligent assistant that can:
1. Answer general questions with accurate and detailed information
2. Perform research and analysis on various topics
3. Provide step-by-step explanations when needed
4. Admit when you don't know something and suggest alternatives
5. Maintain context throughout the conversation
6. Be concise yet comprehensive in your responses

Always aim to be helpful, accurate, and user-friendly. Format your responses clearly using markdown when appropriate.""",
            model="gpt-4",
            temperature=0.7,
            max_tokens=2000,
            enable_code_execution=False,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=5,
            custom_config={
                "enable_research": True,
                "enable_web_search": False,
                "max_conversation_length": 20
            }
        )
    
    async def setup(self) -> None:
        """Set up the assistant agent components."""
        try:
            # Create the main assistant
            self._assistant = AssistantAgent(
                name="assistant",
                system_message=self.config.system_message,
                llm_config=self.llm_config,
                max_consecutive_auto_reply=self.config.max_consecutive_auto_reply
            )
            
            # Create a user proxy for interaction
            self._user_proxy = UserProxyAgent(
                name="user",
                human_input_mode="NEVER",
                max_consecutive_auto_reply=0,
                code_execution_config=False
            )
            
            # Create a researcher agent if enabled
            if self.enable_research:
                researcher_system_message = """You are a research specialist that helps find detailed information.
When asked to research a topic:
1. Break down the query into key components
2. Provide comprehensive information from your knowledge
3. Structure the response with clear sections
4. Include relevant examples and explanations
5. Cite sources when possible"""
                
                self._researcher = AssistantAgent(
                    name="researcher",
                    system_message=researcher_system_message,
                    llm_config=self.llm_config,
                    max_consecutive_auto_reply=3
                )
                
                # Create group chat for multi-agent collaboration
                self._group_chat = GroupChat(
                    agents=[self._user_proxy, self._assistant, self._researcher],
                    messages=[],
                    max_round=10,
                    speaker_selection_method="auto"
                )
                
                self._manager = GroupChatManager(
                    groupchat=self._group_chat,
                    llm_config=self.llm_config
                )
            
            self.logger.info("Smart assistant agent setup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to setup smart assistant: {e}")
            raise
    
    async def process_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        sender: Optional[Agent] = None
    ) -> str:
        """
        Process a message and return the response.
        
        Args:
            message: Input message
            context: Optional context including chat_id
            sender: Optional sender agent
            
        Returns:
            Response message
        """
        chat_id = context.get("chat_id", 0) if context else 0
        
        # Maintain conversation history
        if chat_id not in self._conversations:
            self._conversations[chat_id] = []
        
        # Add user message to history
        self._conversations[chat_id].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Determine if research is needed
        needs_research = self._needs_research(message)
        
        try:
            if needs_research and self.enable_research and self._researcher:
                # Use group chat for research tasks
                response = await self._handle_research_query(message, chat_id)
            else:
                # Use direct assistant for simple queries
                response = await self._handle_simple_query(message, chat_id)
            
            # Add assistant response to history
            self._conversations[chat_id].append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Trim conversation history if too long
            max_length = self.config.custom_config.get("max_conversation_length", 20)
            if len(self._conversations[chat_id]) > max_length:
                self._conversations[chat_id] = self._conversations[chat_id][-max_length:]
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return "I apologize, but I encountered an error while processing your request. Please try again."
    
    def _needs_research(self, message: str) -> bool:
        """
        Determine if a message requires research capabilities.
        
        Args:
            message: Input message
            
        Returns:
            True if research is needed
        """
        research_keywords = [
            "research", "analyze", "investigate", "explore", "study",
            "find information", "tell me about", "explain in detail",
            "comprehensive", "detailed", "in-depth", "thorough"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in research_keywords)
    
    async def _handle_simple_query(self, message: str, chat_id: int) -> str:
        """
        Handle a simple query using the main assistant.
        
        Args:
            message: User message
            chat_id: Chat identifier
            
        Returns:
            Assistant response
        """
        try:
            # Build context from conversation history
            context_messages = self._build_context_messages(chat_id)
            
            # Get response from assistant
            # initiate_chat is synchronous in pyautogen 0.2.35
            self._user_proxy.initiate_chat(
                self._assistant,
                message=message,
                clear_history=False
            )
            
            # Extract the last assistant message
            last_message = self._assistant.last_message()
            if last_message and isinstance(last_message, dict):
                return last_message.get("content", "I couldn't generate a response.")
            elif isinstance(last_message, str):
                return last_message
            else:
                return "I couldn't generate a response."
            
        except Exception as e:
            self.logger.error(f"Error in simple query handler: {e}")
            return "I encountered an error while processing your request."
    
    async def _handle_research_query(self, message: str, chat_id: int) -> str:
        """
        Handle a research query using multi-agent collaboration.
        
        Args:
            message: User message
            chat_id: Chat identifier
            
        Returns:
            Research response
        """
        try:
            # Create research prompt
            research_prompt = f"""Research Request: {message}

Please provide a comprehensive response that includes:
1. Key information and facts
2. Relevant context and background
3. Different perspectives if applicable
4. Practical implications or applications
5. Summary of findings"""
            
            # Initiate group chat (synchronous in pyautogen 0.2.35)
            self._user_proxy.initiate_chat(
                self._manager,
                message=research_prompt,
                clear_history=True
            )
            
            # Get the conversation summary
            messages = self._group_chat.messages
            
            # Extract and combine responses
            response_parts = []
            for msg in messages:
                if isinstance(msg, dict) and msg.get("name") in ["assistant", "researcher"]:
                    content = msg.get("content", "")
                    if content and content != research_prompt:
                        response_parts.append(content)
            
            if response_parts:
                # Combine and format the responses
                combined_response = "\n\n".join(response_parts)
                return self._format_research_response(combined_response)
            else:
                return "I couldn't generate a comprehensive research response. Please try rephrasing your question."
            
        except Exception as e:
            self.logger.error(f"Error in research query handler: {e}")
            return "I encountered an error while researching your request."
    
    def _build_context_messages(self, chat_id: int) -> List[Dict[str, str]]:
        """
        Build context messages from conversation history.
        
        Args:
            chat_id: Chat identifier
            
        Returns:
            List of context messages
        """
        if chat_id not in self._conversations:
            return []
        
        # Get last few messages for context
        recent_messages = self._conversations[chat_id][-6:]  # Last 3 exchanges
        
        context_messages = []
        for msg in recent_messages:
            context_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return context_messages
    
    def _format_research_response(self, response: str) -> str:
        """
        Format a research response for better readability.
        
        Args:
            response: Raw research response
            
        Returns:
            Formatted response
        """
        # Remove duplicate information
        lines = response.split("\n")
        unique_lines = []
        seen = set()
        
        for line in lines:
            line_clean = line.strip()
            if line_clean and line_clean not in seen:
                unique_lines.append(line)
                seen.add(line_clean)
        
        formatted = "\n".join(unique_lines)
        
        # Add section markers if not present
        if "##" not in formatted and len(formatted) > 500:
            # Try to add structure
            paragraphs = formatted.split("\n\n")
            if len(paragraphs) > 2:
                formatted = "## Overview\n\n" + paragraphs[0]
                formatted += "\n\n## Details\n\n" + "\n\n".join(paragraphs[1:-1])
                if paragraphs[-1]:
                    formatted += "\n\n## Summary\n\n" + paragraphs[-1]
        
        return formatted
    
    async def handle_telegram_message(self, message: TelegramMessage) -> str:
        """
        Handle a Telegram message specifically.
        
        Args:
            message: TelegramMessage object
            
        Returns:
            Response to send back
        """
        # Extract context
        context = {
            "chat_id": message.chat_id,
            "user_id": message.from_user.get("id") if message.from_user else None,
            "username": message.from_user.get("username") if message.from_user else None,
            "message_id": message.message_id
        }
        
        # Handle different message types
        if message.text:
            # Handle commands
            if message.text.startswith("/"):
                return await self._handle_command(message.text, context)
            else:
                # Process as regular message
                response = await self.execute(message.text, context)
                return response.message if response.success else "I encountered an error processing your message."
        else:
            return "I can currently only process text messages. Please send me a text message or question."
    
    async def _handle_command(self, command: str, context: Dict[str, Any]) -> str:
        """
        Handle Telegram commands.
        
        Args:
            command: Command string
            context: Message context
            
        Returns:
            Command response
        """
        cmd_parts = command.split()
        cmd_name = cmd_parts[0].lower()
        
        if cmd_name == "/start":
            return """Welcome to the Smart Assistant! 

I'm here to help you with:
• Answering questions on various topics
• Providing detailed explanations
• Researching information
• General assistance

Just send me your questions or requests, and I'll do my best to help!

Available commands:
/help - Show this help message
/clear - Clear conversation history
/status - Show current status"""
        
        elif cmd_name == "/help":
            return """Smart Assistant Commands:

/start - Welcome message
/help - Show this help
/clear - Clear conversation history
/status - Show bot status
/research <topic> - Research a specific topic

Just type your questions naturally, and I'll respond with helpful information!"""
        
        elif cmd_name == "/clear":
            chat_id = context.get("chat_id", 0)
            if chat_id in self._conversations:
                self._conversations[chat_id] = []
            return "Conversation history cleared."
        
        elif cmd_name == "/status":
            metrics = self.get_metrics()
            return f"""Bot Status:
• Total executions: {metrics['total_executions']}
• Success rate: {metrics['success_rate']:.1%}
• Active conversations: {len(self._conversations)}
• Research enabled: {self.enable_research}"""
        
        elif cmd_name == "/research":
            if len(cmd_parts) > 1:
                topic = " ".join(cmd_parts[1:])
                response = await self.execute(f"Please research the following topic in detail: {topic}", context)
                return response.message if response.success else "Research failed."
            else:
                return "Please provide a topic to research. Example: /research artificial intelligence"
        
        else:
            return f"Unknown command: {cmd_name}. Use /help to see available commands."
    
    def clear_conversation(self, chat_id: int) -> None:
        """
        Clear conversation history for a specific chat.
        
        Args:
            chat_id: Chat identifier
        """
        if chat_id in self._conversations:
            del self._conversations[chat_id]
    
    def get_conversation_history(self, chat_id: int) -> List[Dict]:
        """
        Get conversation history for a specific chat.
        
        Args:
            chat_id: Chat identifier
            
        Returns:
            Conversation history
        """
        return self._conversations.get(chat_id, [])
    
    async def cleanup(self) -> None:
        """Clean up agent resources."""
        try:
            # Clear conversation histories
            self._conversations.clear()
            self._active_tasks.clear()
            
            # Clean up AutoGen agents
            self._assistant = None
            self._user_proxy = None
            self._researcher = None
            self._group_chat = None
            self._manager = None
            
            await super().cleanup()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")