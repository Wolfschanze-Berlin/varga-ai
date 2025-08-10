"""
Browser Session Manager for coordinating browser automation sessions.
Handles session lifecycle, result storage, and resource management.
"""

from __future__ import annotations
import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

import aiofiles
from pydantic import BaseModel, Field

from ....log_service import get_logger


class SessionState(str, Enum):
    """Browser session states."""
    
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class SessionInfo:
    """Information about a browser session."""
    
    id: str
    tenant_id: str
    task_id: str
    state: SessionState
    created_at: datetime
    updated_at: datetime
    url: Optional[str] = None
    description: Optional[str] = None
    tool_used: Optional[str] = None
    execution_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskResultStorage(BaseModel):
    """Storage model for task results."""
    
    task_id: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: float
    tool_used: str
    screenshots: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BrowserSessionManager:
    """
    Manages browser automation sessions and task results.
    Provides session tracking, result storage, and cleanup coordination.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize browser session manager.
        
        Args:
            config: Configuration dictionary for session management
        """
        self.logger = get_logger("browser_session_manager")
        
        # Configuration
        self.storage_dir = Path(config.get("storage_dir", "browser_sessions"))
        self.max_sessions = config.get("max_sessions", 100)
        self.session_timeout_minutes = config.get("session_timeout_minutes", 60)
        self.cleanup_interval_seconds = config.get("cleanup_interval_seconds", 300)  # 5 minutes
        self.enable_persistence = config.get("enable_persistence", True)
        self.max_result_age_days = config.get("max_result_age_days", 7)
        
        # Storage paths
        self.sessions_dir = self.storage_dir / "sessions"
        self.results_dir = self.storage_dir / "results"
        self.temp_dir = self.storage_dir / "temp"
        
        # In-memory storage
        self._sessions: Dict[str, SessionInfo] = {}
        self._task_results: Dict[str, TaskResultStorage] = {}
        self._session_lock = asyncio.Lock()
        self._result_lock = asyncio.Lock()
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._is_running = False
        
        # Performance metrics
        self._metrics = {
            "sessions_created": 0,
            "sessions_completed": 0,
            "sessions_failed": 0,
            "sessions_timeout": 0,
            "results_stored": 0,
            "results_retrieved": 0,
            "cleanup_runs": 0
        }
        
        # Ensure directories exist
        self._setup_storage()
    
    def _setup_storage(self) -> None:
        """Setup storage directories."""
        try:
            for directory in [self.sessions_dir, self.results_dir, self.temp_dir]:
                directory.mkdir(parents=True, exist_ok=True)
            
            self.logger.debug("Storage directories created")
            
        except Exception as e:
            self.logger.error(f"Failed to setup storage directories: {e}")
            raise
    
    async def setup(self) -> bool:
        """Setup session manager and load persisted data."""
        try:
            self.logger.info("Setting up browser session manager")
            
            # Load persisted sessions and results if enabled
            if self.enable_persistence:
                await self._load_persisted_data()
            
            # Start background cleanup task
            self._is_running = True
            self._cleanup_task = asyncio.create_task(self._cleanup_worker())
            
            self.logger.info("Browser session manager setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup session manager: {e}")
            return False
    
    async def create_session(
        self,
        task_id: str,
        tenant_id: str,
        url: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new browser session.
        
        Args:
            task_id: Associated task identifier
            tenant_id: Tenant identifier for isolation
            url: Optional starting URL
            description: Session description
            metadata: Additional session metadata
            
        Returns:
            Session identifier
        """
        async with self._session_lock:
            session_id = str(uuid.uuid4())
            
            # Check session limits
            if len(self._sessions) >= self.max_sessions:
                await self._cleanup_expired_sessions()
                
                if len(self._sessions) >= self.max_sessions:
                    raise RuntimeError("Maximum number of sessions reached")
            
            # Create session info
            session_info = SessionInfo(
                id=session_id,
                tenant_id=tenant_id,
                task_id=task_id,
                state=SessionState.PENDING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                url=url,
                description=description,
                metadata=metadata or {}
            )
            
            # Store in memory
            self._sessions[session_id] = session_info
            
            # Persist if enabled
            if self.enable_persistence:
                await self._persist_session(session_info)
            
            self._metrics["sessions_created"] += 1
            
            self.logger.info(
                f"Created session {session_id}",
                extra={
                    "tenant_id": tenant_id,
                    "task_id": task_id,
                    "url": url
                }
            )
            
            return session_id
    
    async def update_session_state(
        self,
        session_id: str,
        state: SessionState,
        tool_used: Optional[str] = None,
        execution_time_ms: Optional[float] = None,
        error_message: Optional[str] = None,
        metadata_update: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update session state and information.
        
        Args:
            session_id: Session identifier
            state: New session state
            tool_used: Tool that was used for execution
            execution_time_ms: Execution time in milliseconds
            error_message: Error message if state is FAILED
            metadata_update: Additional metadata to merge
            
        Returns:
            True if update successful, False otherwise
        """
        async with self._session_lock:
            session = self._sessions.get(session_id)
            if not session:
                self.logger.warning(f"Session {session_id} not found for update")
                return False
            
            # Update session information
            session.state = state
            session.updated_at = datetime.utcnow()
            
            if tool_used:
                session.tool_used = tool_used
            if execution_time_ms is not None:
                session.execution_time_ms = execution_time_ms
            if error_message:
                session.error_message = error_message
            if metadata_update:
                session.metadata.update(metadata_update)
            
            # Update metrics
            if state == SessionState.COMPLETED:
                self._metrics["sessions_completed"] += 1
            elif state == SessionState.FAILED:
                self._metrics["sessions_failed"] += 1
            elif state == SessionState.TIMEOUT:
                self._metrics["sessions_timeout"] += 1
            
            # Persist if enabled
            if self.enable_persistence:
                await self._persist_session(session)
            
            self.logger.debug(
                f"Updated session {session_id} to state {state.value}",
                extra={
                    "tool_used": tool_used,
                    "execution_time_ms": execution_time_ms
                }
            )
            
            return True
    
    async def store_task_result(
        self,
        task_id: str,
        result: Any  # BrowserTaskResult from orchestrator
    ) -> bool:
        """
        Store task execution result.
        
        Args:
            task_id: Task identifier
            result: Task result object
            
        Returns:
            True if storage successful, False otherwise
        """
        async with self._result_lock:
            try:
                # Convert result to storage model
                result_storage = TaskResultStorage(
                    task_id=task_id,
                    success=result.success,
                    data=result.data,
                    error=result.error,
                    execution_time_ms=result.execution_time_ms,
                    tool_used=result.tool_used,
                    screenshots=result.screenshots,
                    metadata=result.metadata
                )
                
                # Store in memory
                self._task_results[task_id] = result_storage
                
                # Persist if enabled
                if self.enable_persistence:
                    await self._persist_task_result(result_storage)
                
                self._metrics["results_stored"] += 1
                
                self.logger.debug(
                    f"Stored result for task {task_id}",
                    extra={
                        "success": result.success,
                        "tool_used": result.tool_used
                    }
                )
                
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to store task result {task_id}: {e}")
                return False
    
    async def get_task_result(self, task_id: str) -> Optional[TaskResultStorage]:
        """
        Retrieve task execution result.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task result if found, None otherwise
        """
        async with self._result_lock:
            result = self._task_results.get(task_id)
            
            if result:
                self._metrics["results_retrieved"] += 1
                self.logger.debug(f"Retrieved result for task {task_id}")
            
            return result
    
    async def get_session_info(self, session_id: str) -> Optional[SessionInfo]:
        """
        Get session information.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session information if found, None otherwise
        """
        async with self._session_lock:
            return self._sessions.get(session_id)
    
    async def list_sessions(
        self,
        tenant_id: Optional[str] = None,
        state: Optional[SessionState] = None,
        limit: Optional[int] = None
    ) -> List[SessionInfo]:
        """
        List sessions with optional filtering.
        
        Args:
            tenant_id: Filter by tenant ID
            state: Filter by session state
            limit: Maximum number of sessions to return
            
        Returns:
            List of session information
        """
        async with self._session_lock:
            sessions = list(self._sessions.values())
            
            # Apply filters
            if tenant_id:
                sessions = [s for s in sessions if s.tenant_id == tenant_id]
            if state:
                sessions = [s for s in sessions if s.state == state]
            
            # Sort by creation time (newest first)
            sessions.sort(key=lambda s: s.created_at, reverse=True)
            
            # Apply limit
            if limit:
                sessions = sessions[:limit]
            
            return sessions
    
    async def cleanup_task_session(self, task_id: str) -> bool:
        """
        Clean up session associated with a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if cleanup successful, False otherwise
        """
        async with self._session_lock:
            # Find session by task_id
            session_id = None
            for sid, session in self._sessions.items():
                if session.task_id == task_id:
                    session_id = sid
                    break
            
            if not session_id:
                return False
            
            # Update session state to cancelled
            await self.update_session_state(session_id, SessionState.CANCELLED)
            
            self.logger.debug(f"Cleaned up session for task {task_id}")
            return True
    
    async def _cleanup_worker(self) -> None:
        """Background worker for cleaning up expired sessions and results."""
        while self._is_running:
            try:
                await asyncio.sleep(self.cleanup_interval_seconds)
                await self._cleanup_expired_sessions()
                await self._cleanup_old_results()
                self._metrics["cleanup_runs"] += 1
                
            except Exception as e:
                self.logger.error(f"Error in cleanup worker: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions."""
        async with self._session_lock:
            current_time = datetime.utcnow()
            expired_sessions = []
            
            for session_id, session in self._sessions.items():
                time_since_update = (current_time - session.updated_at).total_seconds() / 60
                
                # Mark as timeout if session has been active too long
                if (session.state == SessionState.ACTIVE and 
                    time_since_update > self.session_timeout_minutes):
                    
                    session.state = SessionState.TIMEOUT
                    session.updated_at = current_time
                    self._metrics["sessions_timeout"] += 1
                    
                    if self.enable_persistence:
                        await self._persist_session(session)
                
                # Mark for removal if completed/failed sessions are old
                if (session.state in [SessionState.COMPLETED, SessionState.FAILED, SessionState.TIMEOUT] and
                    time_since_update > self.session_timeout_minutes * 2):  # Keep completed for 2x timeout
                    
                    expired_sessions.append(session_id)
            
            # Remove expired sessions
            for session_id in expired_sessions:
                del self._sessions[session_id]
                
                # Remove persisted files
                if self.enable_persistence:
                    session_file = self.sessions_dir / f"{session_id}.json"
                    if session_file.exists():
                        session_file.unlink()
            
            if expired_sessions:
                self.logger.debug(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    async def _cleanup_old_results(self) -> None:
        """Clean up old task results."""
        async with self._result_lock:
            current_time = datetime.utcnow()
            cutoff_time = current_time - timedelta(days=self.max_result_age_days)
            
            old_results = []
            for task_id, result in self._task_results.items():
                if result.timestamp < cutoff_time:
                    old_results.append(task_id)
            
            # Remove old results
            for task_id in old_results:
                del self._task_results[task_id]
                
                # Remove persisted files
                if self.enable_persistence:
                    result_file = self.results_dir / f"{task_id}.json"
                    if result_file.exists():
                        result_file.unlink()
            
            if old_results:
                self.logger.debug(f"Cleaned up {len(old_results)} old results")
    
    async def _persist_session(self, session: SessionInfo) -> None:
        """Persist session to storage."""
        try:
            session_file = self.sessions_dir / f"{session.id}.json"
            session_data = asdict(session)
            
            # Convert datetime objects to ISO strings
            session_data["created_at"] = session.created_at.isoformat()
            session_data["updated_at"] = session.updated_at.isoformat()
            session_data["state"] = session.state.value
            
            async with aiofiles.open(session_file, 'w') as f:
                await f.write(json.dumps(session_data, indent=2))
                
        except Exception as e:
            self.logger.error(f"Failed to persist session {session.id}: {e}")
    
    async def _persist_task_result(self, result: TaskResultStorage) -> None:
        """Persist task result to storage."""
        try:
            result_file = self.results_dir / f"{result.task_id}.json"
            result_data = result.dict()
            
            # Convert datetime to ISO string
            result_data["timestamp"] = result.timestamp.isoformat()
            
            async with aiofiles.open(result_file, 'w') as f:
                await f.write(json.dumps(result_data, indent=2))
                
        except Exception as e:
            self.logger.error(f"Failed to persist result {result.task_id}: {e}")
    
    async def _load_persisted_data(self) -> None:
        """Load persisted sessions and results."""
        try:
            # Load sessions
            if self.sessions_dir.exists():
                for session_file in self.sessions_dir.glob("*.json"):
                    try:
                        async with aiofiles.open(session_file, 'r') as f:
                            data = json.loads(await f.read())
                        
                        # Convert back to SessionInfo
                        session = SessionInfo(
                            id=data["id"],
                            tenant_id=data["tenant_id"],
                            task_id=data["task_id"],
                            state=SessionState(data["state"]),
                            created_at=datetime.fromisoformat(data["created_at"]),
                            updated_at=datetime.fromisoformat(data["updated_at"]),
                            url=data.get("url"),
                            description=data.get("description"),
                            tool_used=data.get("tool_used"),
                            execution_time_ms=data.get("execution_time_ms"),
                            error_message=data.get("error_message"),
                            metadata=data.get("metadata", {})
                        )
                        
                        self._sessions[session.id] = session
                        
                    except Exception as e:
                        self.logger.error(f"Failed to load session from {session_file}: {e}")
            
            # Load results
            if self.results_dir.exists():
                for result_file in self.results_dir.glob("*.json"):
                    try:
                        async with aiofiles.open(result_file, 'r') as f:
                            data = json.loads(await f.read())
                        
                        # Convert back to TaskResultStorage
                        result = TaskResultStorage(
                            task_id=data["task_id"],
                            success=data["success"],
                            data=data.get("data"),
                            error=data.get("error"),
                            execution_time_ms=data["execution_time_ms"],
                            tool_used=data["tool_used"],
                            screenshots=data.get("screenshots", []),
                            metadata=data.get("metadata", {}),
                            timestamp=datetime.fromisoformat(data["timestamp"])
                        )
                        
                        self._task_results[result.task_id] = result
                        
                    except Exception as e:
                        self.logger.error(f"Failed to load result from {result_file}: {e}")
            
            self.logger.info(
                f"Loaded {len(self._sessions)} sessions and {len(self._task_results)} results"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to load persisted data: {e}")
    
    async def health_check(self) -> bool:
        """Check health of session manager."""
        try:
            # Check if cleanup worker is running
            if not self._is_running or not self._cleanup_task:
                return False
            
            # Check storage directories
            for directory in [self.sessions_dir, self.results_dir, self.temp_dir]:
                if not directory.exists():
                    return False
            
            # Check session and result counts are reasonable
            if len(self._sessions) > self.max_sessions * 1.2:  # 20% buffer
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """Cleanup session manager and resources."""
        try:
            self.logger.info("Cleaning up browser session manager")
            
            # Stop background tasks
            self._is_running = False
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Final cleanup of expired sessions
            await self._cleanup_expired_sessions()
            
            # Clear in-memory data
            self._sessions.clear()
            self._task_results.clear()
            
            self.logger.info("Browser session manager cleanup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            return False
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get session manager metrics."""
        return {
            **self._metrics,
            "active_sessions": len(self._sessions),
            "stored_results": len(self._task_results),
            "config": {
                "max_sessions": self.max_sessions,
                "session_timeout_minutes": self.session_timeout_minutes,
                "cleanup_interval_seconds": self.cleanup_interval_seconds,
                "enable_persistence": self.enable_persistence
            }
        }