"""
Browser Automation Tool for the AutoGen SME platform.
Provides a unified interface to browser automation using browser-use MCP integration.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import asyncio

from ....log_service import get_logger
from ...base.base_tool import BaseTool, ToolResult, ToolStatus
from ...base.tool_interface import ToolMetadata, ToolCapability

from .browser_orchestrator import BrowserOrchestrator
from .config import get_browser_automation_config, BrowserAutomationConfig


class BrowserAutomationTool(BaseTool):
    """
    Browser automation tool that provides unified access to browser-use and playwright MCP.
    Handles intelligent task routing and execution coordination.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize browser automation tool.
        
        Args:
            config: Tool configuration dictionary
        """
        super().__init__(config)
        self.logger = get_logger("browser_automation_tool")
        
        # Load browser automation configuration
        try:
            self._browser_config = get_browser_automation_config()
        except Exception as e:
            self.logger.error(f"Failed to load browser automation config: {e}")
            self._browser_config = None
        
        # Browser orchestrator instance
        self._orchestrator: Optional[BrowserOrchestrator] = None
        
        # Tool configuration
        self.enabled = config.get("enabled", True) and (self._browser_config is not None)
        self.max_concurrent_tasks = config.get("max_concurrent_tasks", 5)
        self.default_timeout_seconds = config.get("default_timeout_seconds", 300)
        
        # Performance tracking
        self._metrics = {
            "tasks_executed": 0,
            "tasks_successful": 0,
            "tasks_failed": 0,
            "total_execution_time_ms": 0.0,
            "browser_use_tasks": 0,
            "playwright_tasks": 0
        }
    
    @property
    def metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="browser_automation",
            version="1.0.0",
            description="Automated browser interaction using browser-use and playwright MCP",
            capabilities=[
                ToolCapability.AUTOMATION,
                ToolCapability.ANALYSIS,
                ToolCapability.DATA_EXTRACTION
            ],
            input_schema={
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "Natural language description of the browser task to perform",
                        "minLength": 5,
                        "maxLength": 1000
                    },
                    "url": {
                        "type": "string",
                        "description": "Optional starting URL for the browser task",
                        "format": "uri"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Additional parameters for task execution",
                        "properties": {
                            "wait_time": {
                                "type": "number",
                                "description": "Time to wait after navigation (seconds)",
                                "minimum": 0,
                                "maximum": 30
                            },
                            "take_screenshot": {
                                "type": "boolean",
                                "description": "Whether to take screenshot after task completion"
                            },
                            "extract_data": {
                                "type": "object",
                                "description": "Data extraction specifications",
                                "properties": {
                                    "selectors": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "CSS selectors for data extraction"
                                    },
                                    "attributes": {
                                        "type": "array", 
                                        "items": {"type": "string"},
                                        "description": "HTML attributes to extract"
                                    }
                                }
                            }
                        }
                    },
                    "timeout_seconds": {
                        "type": "integer",
                        "description": "Task timeout in seconds",
                        "minimum": 10,
                        "maximum": 600,
                        "default": 300
                    },
                    "preferred_tool": {
                        "type": "string",
                        "description": "Preferred automation tool (browser_use or playwright)",
                        "enum": ["browser_use", "playwright", "auto"]
                    }
                },
                "required": ["task_description"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "task_id": {"type": "string"},
                    "tool_used": {"type": "string"},
                    "execution_time_ms": {"type": "number"},
                    "data": {
                        "type": "object",
                        "description": "Extracted or processed data from the task"
                    },
                    "screenshots": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Paths to captured screenshots"
                    },
                    "page_info": {
                        "type": "object",
                        "description": "Information about the final page state"
                    },
                    "error": {"type": "string"},
                    "warnings": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["success", "task_id", "execution_time_ms"]
            },
            tags=["browser", "automation", "web", "scraping", "interaction"]
        )
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data for browser automation tasks.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if input is valid, False otherwise
        """
        try:
            # Check required fields
            if not input_data.get("task_description"):
                self.logger.error("Missing required field: task_description")
                return False
            
            # Validate task description
            task_description = input_data.get("task_description")
            if not isinstance(task_description, str) or len(task_description.strip()) < 5:
                self.logger.error("task_description must be a string with at least 5 characters")
                return False
            
            if len(task_description) > 1000:
                self.logger.error("task_description must be less than 1000 characters")
                return False
            
            # Validate URL if provided
            url = input_data.get("url")
            if url is not None:
                if not isinstance(url, str):
                    self.logger.error("url must be a string")
                    return False
                
                # Basic URL validation
                if not (url.startswith("http://") or url.startswith("https://")):
                    self.logger.error("url must start with http:// or https://")
                    return False
            
            # Validate timeout
            timeout = input_data.get("timeout_seconds")
            if timeout is not None:
                if not isinstance(timeout, int) or timeout < 10 or timeout > 600:
                    self.logger.error("timeout_seconds must be an integer between 10 and 600")
                    return False
            
            # Validate preferred_tool
            preferred_tool = input_data.get("preferred_tool")
            if preferred_tool is not None:
                allowed_tools = ["browser_use", "playwright", "auto"]
                if preferred_tool not in allowed_tools:
                    self.logger.error(f"preferred_tool must be one of {allowed_tools}")
                    return False
            
            # Validate parameters if provided
            parameters = input_data.get("parameters")
            if parameters is not None:
                if not isinstance(parameters, dict):
                    self.logger.error("parameters must be a dictionary")
                    return False
                
                # Validate wait_time
                wait_time = parameters.get("wait_time")
                if wait_time is not None:
                    if not isinstance(wait_time, (int, float)) or wait_time < 0 or wait_time > 30:
                        self.logger.error("wait_time must be a number between 0 and 30")
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Input validation error: {e}")
            return False
    
    async def setup(self) -> bool:
        """Setup the browser automation tool."""
        try:
            if not self.enabled:
                self.logger.info("Browser automation tool is disabled")
                return True
            
            if not self._browser_config:
                self.logger.error("Browser automation configuration not available")
                return False
            
            self.logger.info("Setting up browser automation tool")
            
            # Create orchestrator configuration
            orchestrator_config = self._browser_config.orchestrator.model_dump()
            orchestrator_config.update({
                'browser_use': self._browser_config.browser_use.model_dump(),
                'session_manager': self._browser_config.session_manager.model_dump(),
                'task_classifier': self._browser_config.task_classifier.model_dump()
            })
            
            # Initialize orchestrator
            self._orchestrator = BrowserOrchestrator(orchestrator_config)
            
            # Setup orchestrator
            setup_success = await self._orchestrator.setup()
            if not setup_success:
                self.logger.error("Failed to setup browser orchestrator")
                return False
            
            self.logger.info("Browser automation tool setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup browser automation tool: {e}")
            return False
    
    async def _do_execute(
        self, 
        input_data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> ToolResult:
        """
        Execute browser automation task.
        
        Args:
            input_data: Task parameters
            context: Execution context
            
        Returns:
            Tool execution result
        """
        if not self.enabled:
            return ToolResult(
                status=ToolStatus.ERROR,
                error="Browser automation tool is disabled"
            )
        
        if not self._orchestrator:
            return ToolResult(
                status=ToolStatus.ERROR,
                error="Browser orchestrator not initialized"
            )
        
        try:
            self._metrics["tasks_executed"] += 1
            
            # Prepare orchestrator input
            orchestrator_input = {
                "description": input_data["task_description"],
                "url": input_data.get("url"),
                "parameters": input_data.get("parameters", {}),
                "timeout_seconds": input_data.get("timeout_seconds", self.default_timeout_seconds)
            }
            
            # Add preferred tool hint to routing context
            execution_context = {
                **context,
                "preferred_tool": input_data.get("preferred_tool", "auto")
            }
            
            self.logger.info(
                f"Executing browser automation task",
                extra={
                    "description": input_data["task_description"][:100] + "...",
                    "url": input_data.get("url"),
                    "timeout": orchestrator_input["timeout_seconds"],
                    "tenant_id": context.get("tenant_id")
                }
            )
            
            # Execute via orchestrator
            result = await self._orchestrator.execute(orchestrator_input, execution_context)
            
            # Update metrics
            if result.status == ToolStatus.SUCCESS:
                self._metrics["tasks_successful"] += 1
            else:
                self._metrics["tasks_failed"] += 1
            
            if result.execution_time_ms:
                self._metrics["total_execution_time_ms"] += result.execution_time_ms
            
            # Track tool usage from result metadata
            if result.data and isinstance(result.data, dict):
                tool_used = result.data.get("tool_used", "unknown")
                if tool_used == "browser_use":
                    self._metrics["browser_use_tasks"] += 1
                elif tool_used == "playwright":
                    self._metrics["playwright_tasks"] += 1
            
            self.logger.info(
                f"Browser automation task completed",
                extra={
                    "status": result.status.value,
                    "execution_time_ms": result.execution_time_ms,
                    "tenant_id": context.get("tenant_id")
                }
            )
            
            return result
            
        except Exception as e:
            self._metrics["tasks_failed"] += 1
            error_msg = f"Browser automation task failed: {str(e)}"
            self.logger.error(error_msg)
            
            return ToolResult(
                status=ToolStatus.ERROR,
                error=error_msg
            )
    
    async def health_check(self) -> bool:
        """Check health of browser automation tool."""
        try:
            if not self.enabled:
                return True
            
            if not self._orchestrator:
                return False
            
            # Check orchestrator health
            orchestrator_healthy = await self._orchestrator.health_check()
            
            return orchestrator_healthy
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """Cleanup browser automation tool resources."""
        try:
            success = await super().cleanup()
            
            if self._orchestrator:
                orchestrator_cleanup = await self._orchestrator.cleanup()
                success = success and orchestrator_cleanup
                self._orchestrator = None
            
            return success
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
            return False
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the browser automation tool."""
        base_metrics = await super().get_performance_metrics()
        
        # Add browser automation specific metrics
        browser_metrics = {
            **self._metrics,
            "avg_execution_time_ms": (
                self._metrics["total_execution_time_ms"] / max(1, self._metrics["tasks_executed"])
            ),
            "success_rate": (
                self._metrics["tasks_successful"] / max(1, self._metrics["tasks_executed"]) * 100
            )
        }
        
        # Add orchestrator metrics if available
        if self._orchestrator:
            try:
                orchestrator_metrics = await self._orchestrator.get_metrics()
                browser_metrics["orchestrator"] = orchestrator_metrics
            except Exception as e:
                self.logger.debug(f"Failed to get orchestrator metrics: {e}")
        
        return {
            **base_metrics,
            "browser_automation": browser_metrics
        }
    
    async def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List active browser sessions."""
        if not self._orchestrator:
            return []
        
        try:
            # Get session info from session manager
            sessions = await self._orchestrator.session_manager.list_sessions(limit=50)
            
            return [
                {
                    "session_id": session.id,
                    "task_id": session.task_id,
                    "state": session.state.value,
                    "created_at": session.created_at.isoformat(),
                    "description": session.description,
                    "url": session.url
                }
                for session in sessions
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to list active sessions: {e}")
            return []
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel an active browser automation task.
        
        Args:
            task_id: Task identifier to cancel
            
        Returns:
            True if cancellation successful, False otherwise
        """
        if not self._orchestrator:
            return False
        
        try:
            # Use session manager to cleanup task session
            success = await self._orchestrator.session_manager.cleanup_task_session(task_id)
            
            if success:
                self.logger.info(f"Successfully cancelled task {task_id}")
            else:
                self.logger.warning(f"Failed to cancel task {task_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error cancelling task {task_id}: {e}")
            return False