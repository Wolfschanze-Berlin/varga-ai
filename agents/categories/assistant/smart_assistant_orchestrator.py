"""
Smart Assistant Orchestrator for Telegram Bot.
Coordinates multiple specialized agents for different tasks.
"""

import asyncio
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from autogen import AssistantAgent, UserProxyAgent, ConversableAgent

from agents.base.base_agent import BaseAgent, AgentConfig, AgentResponse
from src.log_service import get_logger
from src.config import settings


class TaskType(Enum):
    """Types of tasks the orchestrator can handle."""
    GENERAL = "general"
    RESEARCH = "research"
    CODING = "coding"
    ANALYSIS = "analysis"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    BUSINESS = "business"
    SIMPLE = "simple"
    COMPLEX = "complex"


@dataclass
class TaskContext:
    """Context for a task being processed."""
    task_type: TaskType
    user_message: str
    chat_id: int
    thread_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=dict)


class SmartAssistantOrchestrator(BaseAgent):
    """
    Orchestrates multiple specialized agents to handle complex tasks.
    """
    
    # Model configurations with pricing
    # Using actual OpenAI models with appropriate naming
    MODELS = {
        "complex": {
            "name": "gpt-4-turbo",  # Most capable model for complex tasks
            "input_cost": 0.01,  # per 1k tokens
            "output_cost": 0.03   # per 1k tokens
        },
        "standard": {
            "name": "gpt-4o-mini",  # Standard model for general use (GPT-4 Omni Mini)
            "input_cost": 0.00015,  # per 1k tokens
            "output_cost": 0.0006   # per 1k tokens
        },
        "budget": {
            "name": "gpt-4o-mini",  # Budget model same as standard
            "input_cost": 0.00015,
            "output_cost": 0.0006
        }
    }
    
    def __init__(self):
        """Initialize the orchestrator."""
        # Default to standard model for general tasks
        default_model = self.MODELS["standard"]["name"]
        
        config = AgentConfig(
            name="smart_orchestrator",
            description="Intelligent orchestrator for multi-agent coordination",
            category="assistant",
            model=default_model,
            temperature=0.7,
            max_tokens=2000,
            system_message="""You are an intelligent orchestrator that coordinates multiple specialized agents.
            
Your responsibilities:
1. Analyze user requests to determine the best approach
2. Select and coordinate appropriate specialized agents
3. Ensure comprehensive and accurate responses
4. Maintain context across conversations
5. Learn from interactions to improve over time

You have access to:
- Research agents for in-depth information gathering
- Technical agents for coding and technical tasks
- Creative agents for content generation
- Analysis agents for data and business insights
- Web search and browser capabilities
- Memory system for context retention

Always strive to provide the most helpful, accurate, and comprehensive response possible."""
        )
        
        super().__init__(config)
        
        # Specialized agents
        self.agents: Dict[str, BaseAgent] = {}
        self.assistant_agent: Optional[AssistantAgent] = None
        
        # Conversation memory
        self.conversation_memory: Dict[int, List[Dict[str, Any]]] = {}
        self.max_memory_items = 50
        
        # Performance tracking
        self.task_metrics: Dict[TaskType, Dict[str, int]] = {
            task_type: {"total": 0, "successful": 0}
            for task_type in TaskType
        }
        
        # Cost tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        
        self.logger = get_logger("smart_orchestrator")
    
    async def setup(self) -> bool:
        """Set up the orchestrator and specialized agents."""
        try:
            self.logger.info("Setting up Smart Assistant Orchestrator...")
            
            # Initialize main assistant agent
            llm_config = {
                "model": self.config.model,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "config_list": [{
                    "model": self.config.model,
                    "api_key": os.getenv("OPENAI_API_KEY")
                }]
            }
            
            self.assistant_agent = AssistantAgent(
                name="orchestrator",
                llm_config=llm_config,
                system_message=self.config.system_message
            )
            
            # Initialize specialized agents
            await self._initialize_specialized_agents()
            
            self.logger.info("Smart Assistant Orchestrator setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup orchestrator: {e}")
            return False
    
    async def _initialize_specialized_agents(self) -> None:
        """Initialize specialized agents for different tasks."""
        # Import specialized agents as they're created
        try:
            # Research Agent
            from agents.categories.research.research_agent import ResearchAgent
            research_agent = ResearchAgent()
            if await research_agent.initialize():
                self.agents["research"] = research_agent
                self.logger.info("Research agent initialized")
        except ImportError:
            self.logger.debug("Research agent not available")
        
        try:
            # Technical Agent
            from agents.categories.technical.technical_agent import TechnicalAgent
            technical_agent = TechnicalAgent()
            if await technical_agent.initialize():
                self.agents["technical"] = technical_agent
                self.logger.info("Technical agent initialized")
        except ImportError:
            self.logger.debug("Technical agent not available")
        
        try:
            # Creative Agent
            from agents.categories.creative.creative_agent import CreativeAgent
            creative_agent = CreativeAgent()
            if await creative_agent.initialize():
                self.agents["creative"] = creative_agent
                self.logger.info("Creative agent initialized")
        except ImportError:
            self.logger.debug("Creative agent not available")
    
    async def _get_available_tools(self) -> List[Any]:
        """Get list of available tools for the agent."""
        tools = []
        
        # Add web search tool if available
        try:
            from src.tools.integrations.web.web_search_tool import WebSearchTool
            web_search = WebSearchTool({})
            if await web_search.setup():
                tools.append(web_search)
                self.logger.info("Web search tool added")
        except ImportError:
            pass
        
        # Add browser tool if available
        try:
            from src.tools.integrations.browser_automation.browser_automation_tool import BrowserAutomationTool
            browser = BrowserAutomationTool({})
            if await browser.setup():
                tools.append(browser)
                self.logger.info("Browser automation tool added")
        except ImportError:
            pass
        
        return tools
    
    def _select_model_for_task(self, task_type: TaskType, message: str) -> str:
        """
        Select the appropriate model based on task complexity.
        
        Args:
            task_type: Type of task
            message: User message
            
        Returns:
            Model name to use
        """
        # Complex tasks that need GPT-4.1
        if task_type in [TaskType.RESEARCH, TaskType.ANALYSIS, TaskType.TECHNICAL, TaskType.CODING]:
            return self.MODELS["complex"]["name"]
        
        # Very simple tasks can still use budget model
        if len(message) < 30 and task_type == TaskType.GENERAL:
            # Very simple like "hello" or "thanks"
            return self.MODELS["budget"]["name"]
        
        # Check for keywords indicating complexity
        complex_keywords = ["explain", "analyze", "compare", "detailed", "comprehensive", "research", "implement"]
        if any(keyword in message.lower() for keyword in complex_keywords):
            return self.MODELS["complex"]["name"]
        
        simple_keywords = ["what", "when", "where", "who", "yes", "no", "thanks", "hello"]
        if any(message.lower().startswith(keyword) for keyword in simple_keywords):
            return self.MODELS["budget"]["name"]
        
        # Default to standard model
        return self.MODELS["standard"]["name"]
    
    def _estimate_cost(self, input_tokens: int, output_tokens: int, model_name: str) -> float:
        """
        Estimate cost for model usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model_name: Model being used
            
        Returns:
            Estimated cost in dollars
        """
        for model_config in self.MODELS.values():
            if model_config["name"] == model_name:
                input_cost = (input_tokens / 1000) * model_config["input_cost"]
                output_cost = (output_tokens / 1000) * model_config["output_cost"]
                return input_cost + output_cost
        return 0.0
    
    def _classify_task(self, message: str) -> TaskType:
        """
        Classify the task type based on the message content.
        
        Args:
            message: User message
            
        Returns:
            TaskType classification
        """
        message_lower = message.lower()
        
        # Keywords for classification
        research_keywords = ["research", "find", "search", "investigate", "explore", "study"]
        coding_keywords = ["code", "program", "function", "class", "debug", "implement", "develop"]
        analysis_keywords = ["analyze", "compare", "evaluate", "assess", "metrics", "data"]
        creative_keywords = ["write", "create", "design", "compose", "generate", "story", "article"]
        technical_keywords = ["technical", "system", "architecture", "infrastructure", "deploy"]
        business_keywords = ["business", "strategy", "market", "revenue", "customer", "sales"]
        
        # Check for keywords
        if any(keyword in message_lower for keyword in research_keywords):
            return TaskType.RESEARCH
        elif any(keyword in message_lower for keyword in coding_keywords):
            return TaskType.CODING
        elif any(keyword in message_lower for keyword in analysis_keywords):
            return TaskType.ANALYSIS
        elif any(keyword in message_lower for keyword in creative_keywords):
            return TaskType.CREATIVE
        elif any(keyword in message_lower for keyword in technical_keywords):
            return TaskType.TECHNICAL
        elif any(keyword in message_lower for keyword in business_keywords):
            return TaskType.BUSINESS
        else:
            return TaskType.GENERAL
    
    def _get_conversation_context(self, chat_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent conversation context for a chat.
        
        Args:
            chat_id: Chat ID
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of recent messages
        """
        if chat_id not in self.conversation_memory:
            return []
        
        return self.conversation_memory[chat_id][-limit:]
    
    def _update_conversation_memory(
        self,
        chat_id: int,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update conversation memory for a chat.
        
        Args:
            chat_id: Chat ID
            role: Message role (user/assistant)
            content: Message content
            metadata: Optional metadata
        """
        if chat_id not in self.conversation_memory:
            self.conversation_memory[chat_id] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.conversation_memory[chat_id].append(message)
        
        # Trim memory if too long
        if len(self.conversation_memory[chat_id]) > self.max_memory_items:
            self.conversation_memory[chat_id] = self.conversation_memory[chat_id][-self.max_memory_items:]
    
    async def process_message(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> AgentResponse:
        """
        Process a message through the orchestrator.
        
        Args:
            message: User message
            context: Message context
            
        Returns:
            Processing result
        """
        try:
            chat_id = context.get("chat_id", 0)
            thread_id = context.get("thread_id")
            
            # Classify the task
            task_type = self._classify_task(message)
            self.logger.info(f"Task classified as: {task_type.value}")
            
            # Select appropriate model
            selected_model = self._select_model_for_task(task_type, message)
            self.logger.info(f"Selected model: {selected_model}")
            
            # Update assistant with selected model
            await self._update_assistant_model(selected_model)
            
            # Create task context
            # Get conversation history from context or fallback to existing method
            conversation_history = context.get("conversation_history", self._get_conversation_context(chat_id))
            
            task_context = TaskContext(
                task_type=task_type,
                user_message=message,
                chat_id=chat_id,
                thread_id=thread_id,
                history=conversation_history,
                metadata={"model": selected_model}
            )
            
            # Update conversation memory
            self._update_conversation_memory(chat_id, "user", message)
            
            # Process based on task type
            response = await self._process_task(task_context)
            
            # Update conversation memory with response
            self._update_conversation_memory(chat_id, "assistant", response)
            
            # Update metrics
            self.task_metrics[task_type]["total"] += 1
            self.task_metrics[task_type]["successful"] += 1
            
            return AgentResponse(
                success=True,
                message=response,
                data={
                    "task_type": task_type.value,
                    "chat_id": chat_id
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return AgentResponse(
                success=False,
                message="I encountered an error processing your request. Please try again.",
                error=str(e)
            )
    
    async def _process_task(self, context: TaskContext) -> str:
        """
        Process a task based on its type.
        
        Args:
            context: Task context
            
        Returns:
            Response message
        """
        # Build context-aware prompt
        prompt = self._build_prompt(context)
        
        # For research tasks, enhance the prompt
        if context.task_type == TaskType.RESEARCH:
            prompt = f"""Please provide a comprehensive research report on the following topic:

{context.user_message}

Your response should include:
1. Overview and basic principles
2. Current state of technology
3. Key advantages and benefits
4. Main challenges and limitations
5. Recent developments and breakthroughs
6. Future prospects and timeline
7. Key players and projects in the field

Please provide detailed, accurate, and up-to-date information."""
        
        # Select appropriate agent(s) if available
        if context.task_type == TaskType.RESEARCH and "research" in self.agents:
            # Use research agent for in-depth research
            result = await self.agents["research"].execute(
                {"message": context.user_message},
                {"chat_id": context.chat_id}
            )
            return result.message
        
        elif context.task_type == TaskType.CODING and "technical" in self.agents:
            # Use technical agent for coding tasks
            result = await self.agents["technical"].execute(
                {"message": context.user_message},
                {"chat_id": context.chat_id}
            )
            return result.message
        
        elif context.task_type == TaskType.CREATIVE and "creative" in self.agents:
            # Use creative agent for content generation
            result = await self.agents["creative"].execute(
                {"message": context.user_message},
                {"chat_id": context.chat_id}
            )
            return result.message
        
        else:
            # Use main assistant for all tasks (including research when no specialized agent)
            return await self._process_with_assistant(prompt)
    
    def _build_prompt(self, context: TaskContext) -> str:
        """
        Build a context-aware prompt.
        
        Args:
            context: Task context
            
        Returns:
            Enhanced prompt
        """
        prompt = context.user_message
        
        # Check if this is a follow-up/elaboration request
        if self._is_elaboration_request(prompt) and context.history:
            # Get the last assistant response to provide context
            last_assistant_response = self._get_last_assistant_response(context.history)
            if last_assistant_response:
                prompt = f"""The user is asking for more details about your previous response.

Your previous response was:
{last_assistant_response[:500]}...

User's follow-up request: {prompt}

Please provide a more detailed, easy-to-read explanation of the topic you previously discussed."""
        
        # Add general conversation context if available
        elif context.history:
            context_summary = self._summarize_context(context.history)
            if context_summary:
                prompt = f"Previous context: {context_summary}\n\nCurrent request: {prompt}"
        
        return prompt
    
    def _is_elaboration_request(self, message: str) -> bool:
        """
        Check if the message is asking for elaboration on a previous topic.
        
        Args:
            message: User message
            
        Returns:
            True if this is an elaboration request
        """
        message_lower = message.lower()
        
        # Keywords that indicate asking for more details
        elaboration_keywords = [
            "explain", "more details", "more detail", "elaborate", "expand", 
            "tell me more", "can you explain", "what do you mean", "clarify",
            "break it down", "in more detail", "go deeper", "more about",
            "how does", "why does", "what exactly", "easy to read", "simpler"
        ]
        
        return any(keyword in message_lower for keyword in elaboration_keywords)
    
    def _get_last_assistant_response(self, history: List[Dict[str, Any]]) -> Optional[str]:
        """
        Get the last assistant response from history.
        
        Args:
            history: Conversation history
            
        Returns:
            Last assistant message content or None
        """
        # Look through history in reverse to find last assistant message
        for msg in reversed(history):
            if msg.get("role") == "assistant" and msg.get("content"):
                return msg["content"]
        return None
    
    def _summarize_context(self, history: List[Dict[str, Any]]) -> str:
        """
        Summarize conversation history.
        
        Args:
            history: Conversation history
            
        Returns:
            Summary string
        """
        if not history:
            return ""
        
        # Take last 3 exchanges
        recent = history[-6:] if len(history) >= 6 else history
        
        summary_parts = []
        for msg in recent:
            role = msg["role"]
            content = msg["content"][:100]  # Truncate long messages
            summary_parts.append(f"{role}: {content}")
        
        return " | ".join(summary_parts)
    
    async def _update_assistant_model(self, model_name: str) -> None:
        """
        Update the assistant's model configuration.
        
        Args:
            model_name: Name of the model to use
        """
        if self.assistant_agent:
            # Update the LLM config with new model
            self.assistant_agent.llm_config["model"] = model_name
            self.assistant_agent.llm_config["config_list"][0]["model"] = model_name
            self.logger.debug(f"Updated assistant model to: {model_name}")
    
    async def _process_with_assistant(self, prompt: str) -> str:
        """
        Process a prompt with the main assistant.
        
        Args:
            prompt: User prompt
            
        Returns:
            Assistant response
        """
        try:
            # Create a unique user proxy for this conversation
            import uuid
            user_id = f"user_{uuid.uuid4().hex[:8]}"
            
            user_proxy = UserProxyAgent(
                name=user_id,
                human_input_mode="NEVER",
                max_consecutive_auto_reply=0,
                code_execution_config=False
            )
            
            # Clear history to avoid confusion
            self.assistant_agent.reset()
            
            # Initiate chat
            await user_proxy.a_initiate_chat(
                self.assistant_agent,
                message=prompt,
                clear_history=True
            )
            
            # Get the last message from the assistant
            try:
                last_msg = self.assistant_agent.last_message(agent=user_proxy)
                if last_msg and last_msg.get("content"):
                    return last_msg["content"]
            except:
                # Fallback: try to get from chat messages directly
                if hasattr(self.assistant_agent, 'chat_messages'):
                    for sender in self.assistant_agent.chat_messages:
                        if user_id in sender:
                            messages = self.assistant_agent.chat_messages[sender]
                            if messages and len(messages) > 0:
                                # Find the last assistant message
                                for msg in reversed(messages):
                                    if msg.get("name") == "orchestrator" or msg.get("role") == "assistant":
                                        return msg.get("content", "")
            
            return "I'm here to help! Could you please provide more details about what you need?"
            
        except Exception as e:
            self.logger.error(f"Error in assistant processing: {e}")
            return "I encountered an issue processing your request. Please try rephrasing or breaking it down into smaller parts."
    
    def clear_conversation(self, chat_id: int) -> None:
        """
        Clear conversation history for a chat.
        
        Args:
            chat_id: Chat ID
        """
        if chat_id in self.conversation_memory:
            del self.conversation_memory[chat_id]
            self.logger.info(f"Cleared conversation for chat {chat_id}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get orchestrator metrics."""
        base_metrics = super().get_metrics()
        
        return {
            **base_metrics,
            "task_metrics": self.task_metrics,
            "active_conversations": len(self.conversation_memory),
            "total_messages_in_memory": sum(
                len(msgs) for msgs in self.conversation_memory.values()
            ),
            "available_agents": list(self.agents.keys()),
            "cost_tracking": {
                "total_input_tokens": self.total_input_tokens,
                "total_output_tokens": self.total_output_tokens,
                "total_cost_usd": round(self.total_cost, 4),
                "models_used": {
                    "complex": self.MODELS["complex"]["name"],
                    "standard": self.MODELS["standard"]["name"],
                    "budget": self.MODELS["budget"]["name"]
                }
            }
        }
    
    async def cleanup(self) -> bool:
        """Clean up orchestrator resources."""
        try:
            # Cleanup specialized agents
            for agent_name, agent in self.agents.items():
                try:
                    await agent.cleanup()
                    self.logger.info(f"Cleaned up {agent_name} agent")
                except Exception as e:
                    self.logger.error(f"Error cleaning up {agent_name}: {e}")
            
            self.agents.clear()
            self.conversation_memory.clear()
            
            return await super().cleanup()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            return False