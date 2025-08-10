"""
Tool initializer for AutoGen SME platform.
Handles registration and setup of all available tools.
"""

from typing import Dict, Any, List
import asyncio

from .base import get_tool_registry, ToolRegistry
from .web_search_tool import WebSearchTool
from .text_generation_tool import TextGenerationTool
from .chatbot_interface_tool import ChatbotInterfaceTool
from .utilities import add_rate_limit_rule, RateLimitScope, RateLimitStrategy
from ..config import get_settings, get_tool_config
from ..log_service import get_logger


class ToolInitializer:
    """Handles initialization and registration of platform tools."""
    
    def __init__(self):
        """Initialize the tool initializer."""
        self.logger = get_logger("tool_initializer")
        self.registry = get_tool_registry()
        self.settings = get_settings()
    
    async def initialize_all_tools(self) -> Dict[str, Any]:
        """
        Initialize and register all platform tools.
        
        Returns:
            Dictionary with initialization results
        """
        self.logger.info("Starting tool initialization")
        
        results = {
            "initialized_tools": [],
            "failed_tools": [],
            "rate_limits_configured": 0,
            "errors": []
        }
        
        try:
            # Setup global rate limits
            await self._setup_rate_limits()
            results["rate_limits_configured"] = 3
            
            # Initialize individual tools
            tools_to_initialize = [
                ("web_search", WebSearchTool, self.settings.web_search),
                ("text_generation", TextGenerationTool, self.settings.text_generation),
                ("chatbot_interface", ChatbotInterfaceTool, self.settings.chatbot)
            ]
            
            for tool_name, tool_class, tool_config in tools_to_initialize:
                try:
                    await self._initialize_tool(tool_name, tool_class, tool_config.dict())
                    results["initialized_tools"].append(tool_name)
                    self.logger.info(f"Successfully initialized tool: {tool_name}")
                
                except Exception as e:
                    error_msg = f"Failed to initialize {tool_name}: {str(e)}"
                    self.logger.error(error_msg)
                    results["failed_tools"].append(tool_name)
                    results["errors"].append(error_msg)
            
            # Auto-discover additional tools
            try:
                discovered_count = self.registry.auto_discover_tools("src.tools.integrations")
                self.logger.info(f"Auto-discovered {discovered_count} integration tools")
            except Exception as e:
                self.logger.warning(f"Auto-discovery failed: {e}")
            
            self.logger.info(
                f"Tool initialization completed: "
                f"{len(results['initialized_tools'])} success, "
                f"{len(results['failed_tools'])} failed"
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Tool initialization failed: {e}")
            results["errors"].append(str(e))
            return results
    
    async def _setup_rate_limits(self) -> None:
        """Setup global rate limiting rules."""
        # Global rate limits
        add_rate_limit_rule(
            scope=RateLimitScope.GLOBAL,
            max_requests=self.settings.global_rate_limit_per_minute,
            window_seconds=60,
            strategy=RateLimitStrategy.SLIDING_WINDOW,
            priority=10
        )
        
        add_rate_limit_rule(
            scope=RateLimitScope.GLOBAL,
            max_requests=self.settings.global_rate_limit_per_hour,
            window_seconds=3600,
            strategy=RateLimitStrategy.SLIDING_WINDOW,
            priority=10
        )
        
        # Tenant-level rate limits (more restrictive)
        add_rate_limit_rule(
            scope=RateLimitScope.TENANT,
            max_requests=100,
            window_seconds=60,
            strategy=RateLimitStrategy.TOKEN_BUCKET,
            priority=20
        )
        
        self.logger.info("Configured global rate limiting rules")
    
    async def _initialize_tool(
        self, 
        tool_name: str, 
        tool_class, 
        config: Dict[str, Any]
    ) -> None:
        """Initialize and register a specific tool."""
        # Validate configuration
        if not config.get("enabled", True):
            self.logger.info(f"Tool {tool_name} is disabled, skipping initialization")
            return
        
        # Check required configuration
        if tool_name in ["web_search", "text_generation", "chatbot_interface"]:
            if not config.get("api_key"):
                raise ValueError(f"API key is required for {tool_name}")
        
        # Register the tool
        self.registry.register_tool(tool_class, config)
        
        # Create instance and test health
        instance = self.registry.get_tool_instance(tool_name)
        if instance:
            # Setup the tool
            setup_success = await instance.setup()
            if not setup_success:
                raise ValueError(f"Tool setup failed for {tool_name}")
            
            # Health check
            health_ok = await instance.health_check()
            if not health_ok:
                self.logger.warning(f"Health check failed for {tool_name}")
    
    async def shutdown_all_tools(self) -> None:
        """Shutdown and cleanup all tools."""
        self.logger.info("Shutting down all tools")
        
        try:
            await self.registry.cleanup_all_instances()
            self.logger.info("All tools shut down successfully")
        except Exception as e:
            self.logger.error(f"Tool shutdown failed: {e}")
    
    def get_tool_status(self) -> Dict[str, Any]:
        """
        Get status of all registered tools.
        
        Returns:
            Dictionary with tool status information
        """
        tools = self.registry.list_tools(enabled_only=False)
        registry_stats = self.registry.get_registry_stats()
        
        return {
            "total_tools": len(tools),
            "enabled_tools": len([t for t in tools if self.registry._tool_configs.get(t.name, {}).get("enabled", True)]),
            "registry_stats": registry_stats,
            "tools": [
                {
                    "name": tool.name,
                    "version": tool.version,
                    "capabilities": [c.value for c in tool.capabilities],
                    "enabled": self.registry._tool_configs.get(tool.name, {}).get("enabled", True)
                }
                for tool in tools
            ]
        }


# Global initializer instance
_tool_initializer = ToolInitializer()

async def initialize_tools() -> Dict[str, Any]:
    """Initialize all platform tools."""
    return await _tool_initializer.initialize_all_tools()

async def shutdown_tools() -> None:
    """Shutdown all platform tools."""
    await _tool_initializer.shutdown_all_tools()

def get_tool_status() -> Dict[str, Any]:
    """Get status of all tools."""
    return _tool_initializer.get_tool_status()

def get_initializer() -> ToolInitializer:
    """Get the tool initializer instance."""
    return _tool_initializer