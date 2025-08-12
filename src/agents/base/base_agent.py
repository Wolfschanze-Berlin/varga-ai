"""
Base agent implementation for AutoGen-based agents.
Provides core functionality for all platform agents.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import json

import autogen
from autogen import ConversableAgent, Agent
from loguru import logger

from src.log_service import get_logger


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    
    name: str
    description: str
    category: str
    system_message: str
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000
    tools: List[str] = field(default_factory=list)
    enable_code_execution: bool = False
    human_input_mode: str = "NEVER"
    max_consecutive_auto_reply: int = 10
    custom_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResponse:
    """Response from an agent execution."""
    
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    execution_time_ms: Optional[float] = None


class BaseAgent(ABC):
    """Base class for all AutoGen-based agents in the platform."""
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the base agent.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.logger = get_logger(f"agent.{config.name}")
        self._agent: Optional[ConversableAgent] = None
        self._is_initialized = False
        
        # LLM configuration
        self.llm_config = self._create_llm_config()
        
        # Agent metrics
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.total_tokens_used = 0
        
    def _create_llm_config(self) -> Dict[str, Any]:
        """Create LLM configuration for the agent."""
        from src.config.config_manager import get_config
        
        # Get centralized configuration
        config_manager = get_config()
        llm_config = config_manager.get_llm_config()
        
        # Override with agent-specific settings if provided
        if self.config.model:
            llm_config["model"] = self.config.model
            llm_config["config_list"][0]["model"] = self.config.model
        
        if self.config.temperature is not None:
            llm_config["temperature"] = self.config.temperature
        
        if self.config.max_tokens is not None:
            llm_config["max_tokens"] = self.config.max_tokens
        
        return llm_config
    
    async def initialize(self) -> bool:
        """
        Initialize the agent.
        
        Returns:
            True if initialization successful
        """
        try:
            if self._is_initialized:
                self.logger.info(f"Agent {self.config.name} already initialized")
                return True
            
            # Create the AutoGen agent
            self._agent = self._create_autogen_agent()
            
            # Perform any additional setup
            await self.setup()
            
            self._is_initialized = True
            self.logger.info(f"Agent {self.config.name} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agent {self.config.name}: {e}")
            return False
    
    def _create_autogen_agent(self) -> ConversableAgent:
        """Create the AutoGen ConversableAgent."""
        code_execution_config = False
        if self.config.enable_code_execution:
            code_execution_config = {
                "work_dir": f"./work_dir/{self.config.name}",
                "use_docker": False,
            }
        
        return ConversableAgent(
            name=self.config.name,
            system_message=self.config.system_message,
            llm_config=self.llm_config,
            code_execution_config=code_execution_config,
            human_input_mode=self.config.human_input_mode,
            max_consecutive_auto_reply=self.config.max_consecutive_auto_reply,
        )
    
    @abstractmethod
    async def setup(self) -> None:
        """
        Perform any additional setup required by the specific agent.
        Override in subclasses.
        """
        pass
    
    async def execute(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        sender: Optional[Agent] = None
    ) -> AgentResponse:
        """
        Execute the agent with a message.
        
        Args:
            message: Input message to process
            context: Optional execution context
            sender: Optional sender agent for conversations
            
        Returns:
            Agent response
        """
        start_time = datetime.now()
        
        try:
            if not self._is_initialized:
                await self.initialize()
            
            if not self._agent:
                raise RuntimeError(f"Agent {self.config.name} not properly initialized")
            
            self.total_executions += 1
            
            # Process the message
            response = await self.process_message(message, context, sender)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Update metrics
            self.successful_executions += 1
            
            self.logger.info(
                f"Agent {self.config.name} executed successfully",
                extra={
                    "execution_time_ms": execution_time,
                    "message_length": len(message),
                    "has_context": context is not None
                }
            )
            
            return AgentResponse(
                success=True,
                message=response,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self.failed_executions += 1
            
            self.logger.error(
                f"Agent {self.config.name} execution failed: {e}",
                exc_info=True
            )
            
            return AgentResponse(
                success=False,
                message="Agent execution failed",
                error=str(e),
                execution_time_ms=execution_time
            )
    
    @abstractmethod
    async def process_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        sender: Optional[Agent] = None
    ) -> str:
        """
        Process a message and return the response.
        Override in subclasses to implement specific behavior.
        
        Args:
            message: Input message
            context: Optional context
            sender: Optional sender agent
            
        Returns:
            Response message
        """
        pass
    
    def get_agent(self) -> Optional[ConversableAgent]:
        """Get the underlying AutoGen agent."""
        return self._agent
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics."""
        return {
            "name": self.config.name,
            "category": self.config.category,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "success_rate": (
                self.successful_executions / self.total_executions 
                if self.total_executions > 0 else 0
            ),
            "total_tokens_used": self.total_tokens_used,
            "is_initialized": self._is_initialized
        }
    
    async def cleanup(self) -> None:
        """Clean up agent resources."""
        try:
            self._agent = None
            self._is_initialized = False
            self.logger.info(f"Agent {self.config.name} cleaned up")
        except Exception as e:
            self.logger.error(f"Error cleaning up agent {self.config.name}: {e}")
    
    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"<{self.__class__.__name__}(name={self.config.name}, initialized={self._is_initialized})>"