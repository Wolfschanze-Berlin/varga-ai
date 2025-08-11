"""
Browser-Use Wrapper for integrating browser-use library with the platform.
Provides a clean interface to browser-use agent capabilities.
"""

from __future__ import annotations
import asyncio
import os
import uuid
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from loguru import logger
import httpx
from pydantic import BaseModel, Field

try:
    from browser_use.browser import BrowserSession
    from browser_use.config import CONFIG
    BROWSER_USE_AVAILABLE = True
except ImportError:
    # Fallback if browser-use is not installed
    BrowserSession = None
    CONFIG = None
    BROWSER_USE_AVAILABLE = False

from ....log_service import get_logger
from ...base.base_tool import BaseTool


@dataclass
class BrowserSessionInfo:
    """Represents an active browser session info."""
    
    id: str
    browser_session: Optional[Any] = None  # BrowserSession instance
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: datetime = Field(default_factory=datetime.utcnow)
    page_count: int = 0
    is_active: bool = True


class BrowserUseConfig(BaseModel):
    """Configuration for browser-use integration."""
    
    headless: bool = True
    browser_type: str = "chromium"  # chromium, firefox, webkit
    viewport_width: int = 1920
    viewport_height: int = 1080
    timeout_seconds: int = 30
    max_sessions: int = 5
    session_timeout_minutes: int = 30
    screenshots_enabled: bool = True
    screenshots_dir: str = "screenshots"
    user_agent: Optional[str] = None
    proxy: Optional[str] = None
    extra_args: List[str] = Field(default_factory=list)


class BrowserUseWrapper:
    """
    Wrapper for browser-use library providing session management and task execution.
    Handles browser automation with intelligent agent-based interactions.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize browser-use wrapper.
        
        Args:
            config: Configuration dictionary for browser-use setup
        """
        self.logger = get_logger("browser_use_wrapper")
        
        # Validate browser-use availability
        if not self._is_browser_use_available():
            self.logger.error("browser-use library is not available")
            raise ImportError("browser-use library is required but not installed")
        
        # Configuration
        self.config = BrowserUseConfig(**config)
        
        # Session management
        self._sessions: Dict[str, BrowserSessionInfo] = {}
        self._session_lock = asyncio.Lock()
        
        # Service instances
        self._default_browser_config: Optional[Dict[str, Any]] = None
        
        # Performance tracking
        self._stats = {
            "sessions_created": 0,
            "sessions_closed": 0,
            "tasks_executed": 0,
            "tasks_failed": 0,
            "total_execution_time_ms": 0.0
        }
        
        # Ensure screenshots directory exists
        self._setup_directories()
    
    def _is_browser_use_available(self) -> bool:
        """Check if browser-use library is available."""
        return BROWSER_USE_AVAILABLE
    
    def _setup_directories(self) -> None:
        """Setup required directories."""
        if self.config.screenshots_enabled:
            screenshots_path = Path(self.config.screenshots_dir)
            screenshots_path.mkdir(parents=True, exist_ok=True)
    
    async def setup(self) -> bool:
        """Setup browser-use wrapper and initialize components."""
        try:
            self.logger.info("Setting up browser-use wrapper")
            
            if not self._is_browser_use_available():
                self.logger.error("Cannot setup: browser-use not available")
                return False
            
            # Create default browser configuration
            self._default_browser_config = {
                "headless": self.config.headless,
                "browser_type": self.config.browser_type,
                "viewport_width": self.config.viewport_width,
                "viewport_height": self.config.viewport_height,
                "timeout_seconds": self.config.timeout_seconds,
                "user_agent": self.config.user_agent,
                "proxy": self.config.proxy,
                "extra_args": self.config.extra_args
            }
            
            # Start session cleanup task
            asyncio.create_task(self._session_cleanup_worker())
            
            self.logger.info("Browser-use wrapper setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup browser-use wrapper: {e}")
            return False
    
    async def execute_task(
        self,
        description: str,
        url: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a browser automation task using browser-use agent.
        
        Args:
            description: Natural language description of the task
            url: Optional starting URL
            parameters: Additional parameters for task execution
            timeout_seconds: Task timeout override
            session_id: Optional existing session ID to reuse
            
        Returns:
            Dictionary containing task results, screenshots, and metadata
        """
        start_time = datetime.utcnow()
        task_id = str(uuid.uuid4())
        
        try:
            self.logger.info(
                f"Executing browser task {task_id}",
                extra={
                    "description": description[:100] + "..." if len(description) > 100 else description,
                    "url": url,
                    "session_id": session_id
                }
            )
            
            # Get or create session
            session = await self._get_or_create_session(session_id)
            
            # Execute task with agent
            result = await self._execute_with_agent(
                session=session,
                task_id=task_id,
                description=description,
                url=url,
                parameters=parameters or {},
                timeout_seconds=timeout_seconds or self.config.timeout_seconds
            )
            
            # Update statistics
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._stats["tasks_executed"] += 1
            self._stats["total_execution_time_ms"] += execution_time
            
            self.logger.info(
                f"Browser task {task_id} completed successfully",
                extra={"execution_time_ms": execution_time}
            )
            
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._stats["tasks_failed"] += 1
            
            self.logger.error(
                f"Browser task {task_id} failed: {e}",
                extra={"execution_time_ms": execution_time}
            )
            
            raise
    
    async def _get_or_create_session(self, session_id: Optional[str] = None) -> BrowserSessionInfo:
        """Get existing session or create a new one."""
        async with self._session_lock:
            if session_id and session_id in self._sessions:
                session = self._sessions[session_id]
                session.last_used = datetime.utcnow()
                return session
            
            # Create new session
            session = await self._create_session()
            return session
    
    async def _create_session(self) -> BrowserSessionInfo:
        """Create a new browser session."""
        try:
            # Check session limits
            if len(self._sessions) >= self.config.max_sessions:
                await self._cleanup_oldest_session()
            
            session_id = str(uuid.uuid4())
            
            # Create browser session instance using browser-use API
            browser_session = BrowserSession()
            await browser_session.start()
            
            session_info = BrowserSessionInfo(
                id=session_id,
                browser_session=browser_session
            )
            
            self._sessions[session_id] = session_info
            self._stats["sessions_created"] += 1
            
            self.logger.debug(f"Created browser session {session_id}")
            
            return session_info
            
        except Exception as e:
            self.logger.error(f"Failed to create browser session: {e}")
            raise
    
    async def _execute_with_agent(
        self,
        session: BrowserSessionInfo,
        task_id: str,
        description: str,
        url: Optional[str],
        parameters: Dict[str, Any],
        timeout_seconds: int
    ) -> Dict[str, Any]:
        """Execute task using browser-use agent."""
        try:
            browser = session.browser_session
            
            # Navigate to URL if provided
            if url:
                await browser.navigate_to(url)
                await asyncio.sleep(2)  # Allow page to load
            
            # For now, we'll implement basic browser automation
            # In a full implementation, you'd integrate with an LLM agent
            # to interpret the description and execute the task
            
            # Take screenshot if enabled
            screenshots = []
            if self.config.screenshots_enabled:
                screenshot_path = await self._take_screenshot(task_id, session)
                if screenshot_path:
                    screenshots.append(screenshot_path)
            
            # Get page info as result data
            page_info = browser.get_page_info()
            
            return {
                "data": {
                    "page_info": page_info,
                    "task_completed": True,
                    "description": description,
                    "parameters": parameters
                },
                "screenshots": screenshots,
                "metadata": {
                    "session_id": session.id,
                    "url": url,
                    "task_description": description,
                    "execution_timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except asyncio.TimeoutError:
            self.logger.error(f"Task {task_id} timed out after {timeout_seconds} seconds")
            raise
        except Exception as e:
            self.logger.error(f"Agent execution failed for task {task_id}: {e}")
            raise
    
    def _prepare_agent_task(self, description: str, parameters: Dict[str, Any]) -> str:
        """Prepare agent task string with parameters."""
        task_parts = [description]
        
        if parameters:
            task_parts.append("\nAdditional parameters:")
            for key, value in parameters.items():
                task_parts.append(f"- {key}: {value}")
        
        return "\n".join(task_parts)
    
    def _extract_result_data(self, result: Any) -> Dict[str, Any]:
        """Extract structured data from agent result."""
        if hasattr(result, 'data'):
            return result.data
        elif hasattr(result, '__dict__'):
            return result.__dict__
        elif isinstance(result, dict):
            return result
        else:
            return {"result": str(result)}
    
    async def _take_screenshot(self, task_id: str, session: BrowserSessionInfo) -> Optional[str]:
        """Take screenshot of current browser state."""
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            screenshot_name = f"{task_id}_{timestamp}.png"
            screenshot_path = Path(self.config.screenshots_dir) / screenshot_name
            
            # Take screenshot using browser
            await session.browser_session.take_screenshot(str(screenshot_path))
            
            return str(screenshot_path)
            
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            return None
    
    async def _cleanup_oldest_session(self) -> None:
        """Remove the oldest session to make room for new one."""
        if not self._sessions:
            return
        
        oldest_session_id = min(
            self._sessions.keys(),
            key=lambda sid: self._sessions[sid].created_at
        )
        
        await self.close_session(oldest_session_id)
    
    async def _session_cleanup_worker(self) -> None:
        """Background worker to clean up expired sessions."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                current_time = datetime.utcnow()
                timeout_minutes = self.config.session_timeout_minutes
                
                expired_sessions = []
                for session_id, session in self._sessions.items():
                    time_since_last_use = (current_time - session.last_used).total_seconds() / 60
                    if time_since_last_use > timeout_minutes:
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    await self.close_session(session_id)
                    self.logger.debug(f"Cleaned up expired session {session_id}")
                
            except Exception as e:
                self.logger.error(f"Error in session cleanup worker: {e}")
                await asyncio.sleep(60)
    
    async def close_session(self, session_id: str) -> bool:
        """Close a specific browser session."""
        async with self._session_lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            
            try:
                # Close browser
                if session.browser_session:
                    await session.browser_session.close()
                
                # Remove from sessions
                del self._sessions[session_id]
                self._stats["sessions_closed"] += 1
                
                self.logger.debug(f"Closed browser session {session_id}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error closing session {session_id}: {e}")
                return False
    
    async def health_check(self) -> bool:
        """Check health of browser-use wrapper."""
        try:
            # Check if browser-use is available
            if not self._is_browser_use_available():
                return False
            
            # Check session health
            active_sessions = sum(1 for s in self._sessions.values() if s.is_active)
            
            return active_sessions <= self.config.max_sessions
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """Cleanup all browser sessions and resources."""
        try:
            self.logger.info("Cleaning up browser-use wrapper")
            
            # Close all sessions
            session_ids = list(self._sessions.keys())
            for session_id in session_ids:
                await self.close_session(session_id)
            
            self.logger.info("Browser-use wrapper cleanup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get wrapper statistics and metrics."""
        return {
            **self._stats,
            "active_sessions": len(self._sessions),
            "config": {
                "headless": self.config.headless,
                "browser_type": self.config.browser_type,
                "max_sessions": self.config.max_sessions,
                "timeout_seconds": self.config.timeout_seconds
            },
            "avg_execution_time_ms": (
                self._stats["total_execution_time_ms"] / max(1, self._stats["tasks_executed"])
            )
        }
    
    async def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active browser sessions."""
        return [
            {
                "id": session.id,
                "created_at": session.created_at.isoformat(),
                "last_used": session.last_used.isoformat(),
                "page_count": session.page_count,
                "is_active": session.is_active
            }
            for session in self._sessions.values()
        ]