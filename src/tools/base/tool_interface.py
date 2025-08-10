"""
Base tool interface for AutoGen SME platform tools.
Defines the contract that all tools must implement.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Protocol, runtime_checkable
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
import weakref
from collections.abc import Awaitable, Mapping


class ToolStatus(str, Enum):
    """Tool execution status."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"


class ToolResult(BaseModel):
    """Standard tool execution result."""
    model_config = ConfigDict(frozen=True, extra='forbid')
    
    status: ToolStatus
    data: Optional[Any] = None
    error: Optional[str] = Field(None, max_length=1000)  # Limit error message length
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: Optional[float] = Field(None, ge=0.0)
    
    @property
    def is_success(self) -> bool:
        """Check if the tool execution was successful."""
        return self.status == ToolStatus.SUCCESS
    
    @property
    def is_error(self) -> bool:
        """Check if the tool execution failed."""
        return self.status == ToolStatus.ERROR


class ToolCapability(str, Enum):
    """Tool capability types."""
    SEARCH = "search"
    GENERATION = "generation"
    COMMUNICATION = "communication"
    INTEGRATION = "integration"
    ANALYSIS = "analysis"
    AUTOMATION = "automation"


@runtime_checkable
class ExecutionContext(Protocol):
    """Protocol for execution context."""
    tenant_id: Optional[str]
    correlation_id: Optional[str]
    user_id: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]: ...


@runtime_checkable
class ToolObserver(Protocol):
    """Protocol for tool lifecycle observers."""
    
    async def on_tool_cleanup(self, tool: BaseToolInterface) -> None:
        """Called when a tool is being cleaned up."""
        ...


class ToolMetadata(BaseModel):
    """Tool metadata and description."""
    model_config = ConfigDict(frozen=True, extra='forbid')
    
    name: str = Field(min_length=1, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$')
    description: str = Field(min_length=10, max_length=500)
    version: str = Field(pattern=r'^\d+\.\d+\.\d+$')
    capabilities: List[ToolCapability] = Field(min_length=1)
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    rate_limits: Dict[str, int] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class BaseToolInterface(ABC):
    """Abstract base class for all platform tools."""
    
    def __init__(self, config: Mapping[str, Any]) -> None:
        """
        Initialize the tool with configuration.
        
        Args:
            config: Tool configuration dictionary
        """
        self.config = dict(config)  # Create a copy for safety
        self._metadata: Optional[ToolMetadata] = None
        self._observers: weakref.WeakSet = weakref.WeakSet()  # For cleanup notifications
    
    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        ...
    
    @abstractmethod
    async def execute(
        self, 
        input_data: Mapping[str, Any], 
        context: Optional[Mapping[str, Any]] = None
    ) -> ToolResult:
        """
        Execute the tool with given input data.
        
        Args:
            input_data: Input parameters for the tool
            context: Optional execution context (tenant_id, user_id, etc.)
            
        Returns:
            Tool execution result
        """
        ...
    
    @abstractmethod
    async def validate_input(self, input_data: Mapping[str, Any]) -> bool:
        """
        Validate input data against the tool's schema.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        ...
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the tool is healthy and ready to execute.
        
        Returns:
            True if healthy, False otherwise
        """
        ...
    
    async def setup(self) -> bool:
        """
        Setup/initialize the tool. Called before first use.
        
        Returns:
            True if setup successful, False otherwise
        """
        return True
    
    async def cleanup(self) -> bool:
        """
        Cleanup resources when tool is no longer needed.
        
        Returns:
            True if cleanup successful, False otherwise
        """
        # Notify observers about cleanup
        for observer in self._observers:
            try:
                await observer.on_tool_cleanup(self)
            except Exception:
                pass  # Ignore observer errors during cleanup
        return True
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get the tool's input/output schema for AutoGen integration.
        
        Returns:
            Schema definition for AutoGen function calling
        """
        metadata = self.metadata
        return {
            "name": metadata.name,
            "description": metadata.description,
            "parameters": metadata.input_schema,
            "returns": metadata.output_schema
        }
    
    def add_observer(self, observer: ToolObserver) -> None:
        """Add an observer for tool lifecycle events."""
        self._observers.add(observer)
    
    def remove_observer(self, observer: ToolObserver) -> None:
        """Remove an observer."""
        self._observers.discard(observer)
    
    async def __aenter__(self) -> BaseToolInterface:
        """Async context manager entry."""
        if not await self.setup():
            raise RuntimeError(f"Failed to setup tool: {self.__class__.__name__}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.cleanup()
    
    def __str__(self) -> str:
        """String representation of the tool."""
        return f"{self.__class__.__name__}(name={self.metadata.name})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the tool."""
        return (
            f"{self.__class__.__name__}("
            f"name={self.metadata.name}, "
            f"version={self.metadata.version}, "
            f"capabilities={self.metadata.capabilities}"
            f")"
        )