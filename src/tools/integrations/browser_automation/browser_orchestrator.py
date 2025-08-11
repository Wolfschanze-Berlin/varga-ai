"""
Browser Orchestrator for coordinating browser automation tasks.
Manages integration between browser-use and playwright MCP agents.
"""

from __future__ import annotations
import asyncio
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

from loguru import logger
from pydantic import BaseModel, Field

from ....log_service import get_logger
from ...base.base_tool import BaseTool, ToolResult, ToolStatus
from ...base.tool_interface import ToolMetadata, ToolCapability
from .browser_use_wrapper import BrowserUseWrapper
from .session_manager import BrowserSessionManager
from .task_classifier import TaskClassifier, TaskType, TaskComplexity


class RoutingStrategy(str, Enum):
    """Browser automation routing strategies."""
    
    BROWSER_USE_FIRST = "browser_use_first"
    PLAYWRIGHT_FIRST = "playwright_first"
    BEST_FIT = "best_fit"
    PARALLEL = "parallel"


@dataclass
class BrowserTask:
    """Represents a browser automation task."""
    
    id: str
    description: str
    url: Optional[str]
    parameters: Dict[str, Any]
    task_type: TaskType
    complexity: TaskComplexity
    priority: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3


class BrowserTaskResult(BaseModel):
    """Result of browser automation task execution."""
    
    task_id: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: float
    tool_used: str
    screenshots: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BrowserOrchestrator(BaseTool):
    """
    Orchestrates browser automation tasks between browser-use and playwright MCP.
    Provides intelligent routing and coordination of browser operations.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the browser orchestrator.
        
        Args:
            config: Configuration dictionary containing routing and tool settings
        """
        super().__init__(config)
        self.logger = get_logger("browser_orchestrator")
        
        # Configuration
        self.routing_strategy = RoutingStrategy(
            config.get("routing_strategy", RoutingStrategy.BEST_FIT)
        )
        self.default_timeout = config.get("default_timeout_seconds", 300)
        self.max_concurrent_sessions = config.get("max_concurrent_sessions", 5)
        self.enable_screenshots = config.get("enable_screenshots", True)
        self.screenshot_on_error = config.get("screenshot_on_error", True)
        
        # Components
        self.browser_use_wrapper = BrowserUseWrapper(
            config.get("browser_use", {})
        )
        self.session_manager = BrowserSessionManager(
            config.get("session_manager", {})
        )
        self.task_classifier = TaskClassifier(
            config.get("task_classifier", {})
        )
        
        # State tracking
        self._active_tasks: Dict[str, BrowserTask] = {}
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._workers: List[asyncio.Task] = []
        self._is_running = False
        
        # Performance metrics
        self._metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "avg_execution_time": 0.0,
            "browser_use_successes": 0,
            "playwright_successes": 0,
            "routing_decisions": {}
        }
    
    @property
    def metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="browser_orchestrator",
            version="0.1.0",
            description="Orchestrates browser automation tasks between browser-use and playwright",
            capabilities=[ToolCapability.AUTOMATION, ToolCapability.ANALYSIS],
            input_schema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Natural language description of the browser task"
                    },
                    "url": {
                        "type": "string",
                        "description": "Optional starting URL for the task"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Additional parameters for task execution"
                    },
                    "timeout_seconds": {
                        "type": "integer",
                        "description": "Task timeout in seconds",
                        "default": 300
                    }
                },
                "required": ["description"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "data": {"type": "object"},
                    "error": {"type": "string"},
                    "execution_time_ms": {"type": "number"},
                    "tool_used": {"type": "string"},
                    "screenshots": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            },
            tags=["browser", "automation", "orchestrator"]
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
            if not input_data.get("description"):
                self.logger.error("Missing required field: description")
                return False
            
            # Validate description is string and not empty
            description = input_data.get("description")
            if not isinstance(description, str) or len(description.strip()) == 0:
                self.logger.error("Description must be a non-empty string")
                return False
            
            # Validate URL if provided
            url = input_data.get("url")
            if url is not None:
                if not isinstance(url, str):
                    self.logger.error("URL must be a string")
                    return False
                
                # Basic URL format validation
                if not (url.startswith("http://") or url.startswith("https://")):
                    self.logger.error("URL must start with http:// or https://")
                    return False
            
            # Validate parameters if provided
            parameters = input_data.get("parameters")
            if parameters is not None and not isinstance(parameters, dict):
                self.logger.error("Parameters must be a dictionary")
                return False
            
            # Validate timeout if provided
            timeout = input_data.get("timeout_seconds")
            if timeout is not None:
                if not isinstance(timeout, int) or timeout <= 0 or timeout > 3600:
                    self.logger.error("Timeout must be a positive integer <= 3600 seconds")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Input validation error: {e}")
            return False
    
    async def setup(self) -> bool:
        """Setup the browser orchestrator and all components."""
        try:
            self.logger.info("Setting up browser orchestrator")
            
            # Setup components
            await self.browser_use_wrapper.setup()
            await self.session_manager.setup()
            await self.task_classifier.setup()
            
            # Start worker tasks
            self._is_running = True
            for i in range(min(3, self.max_concurrent_sessions)):
                worker = asyncio.create_task(self._task_worker(f"worker-{i}"))
                self._workers.append(worker)
            
            self.logger.info("Browser orchestrator setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup browser orchestrator: {e}")
            return False
    
    async def _do_execute(
        self, 
        input_data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> ToolResult:
        """
        Execute browser automation task.
        
        Args:
            input_data: Task parameters including description, url, and options
            context: Execution context with tenant and correlation info
            
        Returns:
            Tool execution result with task completion data
        """
        try:
            # Create browser task
            task = await self._create_task(input_data, context)
            
            # Add to queue for processing
            await self._task_queue.put(task)
            
            # Wait for task completion with timeout
            timeout = task.timeout_seconds
            start_time = datetime.utcnow()
            
            while (datetime.utcnow() - start_time).total_seconds() < timeout:
                if task.id not in self._active_tasks:
                    # Task completed, get result from session manager
                    result = await self.session_manager.get_task_result(task.id)
                    if result:
                        return ToolResult(
                            status=ToolStatus.SUCCESS if result.success else ToolStatus.ERROR,
                            data=result.data,
                            error=result.error,
                            execution_time_ms=result.execution_time_ms
                        )
                
                await asyncio.sleep(0.5)
            
            # Task timed out
            await self._handle_task_timeout(task)
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Task {task.id} timed out after {timeout} seconds"
            )
            
        except Exception as e:
            self.logger.error(f"Error executing browser task: {e}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e)
            )
    
    async def _create_task(
        self, 
        input_data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> BrowserTask:
        """Create a browser task from input data."""
        task_id = str(uuid.uuid4())
        description = input_data.get("description", "")
        url = input_data.get("url")
        parameters = input_data.get("parameters", {})
        
        # Classify the task
        classification = await self.task_classifier.classify_task(
            description=description,
            url=url,
            parameters=parameters
        )
        
        task = BrowserTask(
            id=task_id,
            description=description,
            url=url,
            parameters=parameters,
            task_type=classification["task_type"],
            complexity=classification["complexity"],
            timeout_seconds=input_data.get("timeout_seconds", self.default_timeout)
        )
        
        self._active_tasks[task_id] = task
        
        self.logger.info(
            f"Created browser task {task_id}",
            extra={
                "task_type": task.task_type.value,
                "complexity": task.complexity.value,
                "url": url
            }
        )
        
        return task
    
    async def _task_worker(self, worker_name: str) -> None:
        """Worker coroutine that processes tasks from the queue."""
        self.logger.debug(f"Starting task worker: {worker_name}")
        
        while self._is_running:
            try:
                # Wait for task with timeout
                task = await asyncio.wait_for(
                    self._task_queue.get(), 
                    timeout=1.0
                )
                
                await self._execute_task(task, worker_name)
                
            except asyncio.TimeoutError:
                # No task available, continue polling
                continue
            except Exception as e:
                self.logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(1.0)
        
        self.logger.debug(f"Task worker {worker_name} stopped")
    
    async def _execute_task(self, task: BrowserTask, worker_name: str) -> None:
        """Execute a single browser task."""
        start_time = datetime.utcnow()
        
        try:
            self.logger.info(
                f"Worker {worker_name} executing task {task.id}",
                extra={"task_type": task.task_type.value}
            )
            
            # Determine routing strategy
            tool_choice = await self._route_task(task)
            
            # Execute with chosen tool
            if tool_choice == "browser_use":
                result = await self._execute_with_browser_use(task)
            else:
                result = await self._execute_with_playwright(task)
            
            # Store result
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.execution_time_ms = execution_time
            result.tool_used = tool_choice
            
            await self.session_manager.store_task_result(task.id, result)
            
            # Update metrics
            self._update_metrics(result, tool_choice)
            
            self.logger.info(
                f"Task {task.id} completed successfully",
                extra={
                    "tool_used": tool_choice,
                    "execution_time_ms": execution_time
                }
            )
            
        except Exception as e:
            # Handle task failure
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            result = BrowserTaskResult(
                task_id=task.id,
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
                tool_used="unknown"
            )
            
            await self.session_manager.store_task_result(task.id, result)
            
            self.logger.error(
                f"Task {task.id} failed: {e}",
                extra={"execution_time_ms": execution_time}
            )
            
        finally:
            # Remove from active tasks
            self._active_tasks.pop(task.id, None)
    
    async def _route_task(self, task: BrowserTask) -> str:
        """
        Determine which tool should handle the task.
        
        Args:
            task: The browser task to route
            
        Returns:
            Tool name: "browser_use" or "playwright"
        """
        if self.routing_strategy == RoutingStrategy.BROWSER_USE_FIRST:
            return "browser_use"
        elif self.routing_strategy == RoutingStrategy.PLAYWRIGHT_FIRST:
            return "playwright"
        elif self.routing_strategy == RoutingStrategy.BEST_FIT:
            return await self._determine_best_fit(task)
        else:
            # Default to best fit
            return await self._determine_best_fit(task)
    
    async def _determine_best_fit(self, task: BrowserTask) -> str:
        """Determine the best tool for the task based on characteristics."""
        # Rules-based routing logic
        
        # High complexity tasks or data extraction -> browser-use
        if task.complexity in [TaskComplexity.HIGH, TaskComplexity.VERY_HIGH]:
            return "browser_use"
        
        # Simple navigation or form filling -> playwright for speed
        if task.task_type in [TaskType.NAVIGATION, TaskType.FORM_SUBMISSION]:
            if task.complexity == TaskComplexity.LOW:
                return "playwright"
        
        # Data extraction and complex interactions -> browser-use
        if task.task_type in [TaskType.DATA_EXTRACTION, TaskType.COMPLEX_INTERACTION]:
            return "browser_use"
        
        # Default to browser-use for unknown cases
        return "browser_use"
    
    async def _execute_with_browser_use(self, task: BrowserTask) -> BrowserTaskResult:
        """Execute task using browser-use wrapper."""
        try:
            result = await self.browser_use_wrapper.execute_task(
                description=task.description,
                url=task.url,
                parameters=task.parameters,
                timeout_seconds=task.timeout_seconds
            )
            
            return BrowserTaskResult(
                task_id=task.id,
                success=True,
                data=result.get("data"),
                screenshots=result.get("screenshots", []),
                metadata=result.get("metadata", {})
            )
            
        except Exception as e:
            return BrowserTaskResult(
                task_id=task.id,
                success=False,
                error=str(e)
            )
    
    async def _execute_with_playwright(self, task: BrowserTask) -> BrowserTaskResult:
        """Execute task using playwright MCP integration."""
        try:
            # This would integrate with the existing playwright MCP
            # For now, we'll simulate the call
            # TODO: Integrate with actual playwright MCP agent
            
            result_data = {
                "message": "Playwright execution simulated",
                "task_description": task.description,
                "url": task.url
            }
            
            return BrowserTaskResult(
                task_id=task.id,
                success=True,
                data=result_data,
                metadata={"simulated": True}
            )
            
        except Exception as e:
            return BrowserTaskResult(
                task_id=task.id,
                success=False,
                error=str(e)
            )
    
    async def _handle_task_timeout(self, task: BrowserTask) -> None:
        """Handle task timeout by cleaning up resources."""
        try:
            # Cancel any ongoing operations
            await self.session_manager.cleanup_task_session(task.id)
            
            # Remove from active tasks
            self._active_tasks.pop(task.id, None)
            
            self.logger.warning(
                f"Task {task.id} timed out and was cleaned up",
                extra={"timeout_seconds": task.timeout_seconds}
            )
            
        except Exception as e:
            self.logger.error(f"Error handling task timeout: {e}")
    
    def _update_metrics(self, result: BrowserTaskResult, tool_used: str) -> None:
        """Update performance metrics."""
        if result.success:
            self._metrics["tasks_completed"] += 1
            if tool_used == "browser_use":
                self._metrics["browser_use_successes"] += 1
            else:
                self._metrics["playwright_successes"] += 1
        else:
            self._metrics["tasks_failed"] += 1
        
        # Update routing decisions
        routing_key = f"{tool_used}_chosen"
        self._metrics["routing_decisions"][routing_key] = (
            self._metrics["routing_decisions"].get(routing_key, 0) + 1
        )
        
        # Update average execution time
        total_tasks = self._metrics["tasks_completed"] + self._metrics["tasks_failed"]
        if total_tasks > 0:
            current_avg = self._metrics["avg_execution_time"]
            self._metrics["avg_execution_time"] = (
                (current_avg * (total_tasks - 1) + result.execution_time_ms) / total_tasks
            )
    
    async def health_check(self) -> bool:
        """Check health of orchestrator and all components."""
        try:
            # Check if workers are running
            if not self._is_running or not self._workers:
                return False
            
            # Check component health
            browser_use_healthy = await self.browser_use_wrapper.health_check()
            session_manager_healthy = await self.session_manager.health_check()
            
            return browser_use_healthy and session_manager_healthy
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """Cleanup orchestrator and all components."""
        try:
            self.logger.info("Cleaning up browser orchestrator")
            
            # Stop workers
            self._is_running = False
            
            # Cancel all worker tasks
            for worker in self._workers:
                worker.cancel()
            
            # Wait for workers to finish
            if self._workers:
                await asyncio.gather(*self._workers, return_exceptions=True)
            
            # Cleanup components
            await self.browser_use_wrapper.cleanup()
            await self.session_manager.cleanup()
            
            # Clear state
            self._active_tasks.clear()
            self._workers.clear()
            
            self.logger.info("Browser orchestrator cleanup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            return False
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            **self._metrics,
            "active_tasks": len(self._active_tasks),
            "queue_size": self._task_queue.qsize(),
            "workers_running": len(self._workers),
            "is_healthy": await self.health_check()
        }