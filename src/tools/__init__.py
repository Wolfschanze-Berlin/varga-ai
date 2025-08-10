"""
Tools module for AutoGen SME platform.
Provides generic tools for web search, text generation, and chatbot interface.
"""

from .base import (
    BaseToolInterface,
    ToolResult,
    ToolStatus,
    ToolCapability,
    ToolMetadata,
    BaseTool,
    ToolRegistry,
    get_tool_registry,
    register_tool,
    get_tool
)

from .web_search_tool import WebSearchTool
from .text_generation_tool import TextGenerationTool, ContentType
from .chatbot_interface_tool import ChatbotInterfaceTool, MessageRole, ConversationStatus

from .utilities import (
    ErrorHandler,
    ToolError,
    get_rate_limiter,
    add_rate_limit_rule
)

__all__ = [
    # Base classes and interfaces
    "BaseToolInterface",
    "ToolResult",
    "ToolStatus", 
    "ToolCapability",
    "ToolMetadata",
    "BaseTool",
    "ToolRegistry",
    "get_tool_registry",
    "register_tool",
    "get_tool",
    
    # Concrete tools
    "WebSearchTool",
    "TextGenerationTool",
    "ContentType",
    "ChatbotInterfaceTool", 
    "MessageRole",
    "ConversationStatus",
    
    # Utilities
    "ErrorHandler",
    "ToolError",
    "get_rate_limiter",
    "add_rate_limit_rule"
]