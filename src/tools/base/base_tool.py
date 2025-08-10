"""
Base tool implementation with common functionality.
Provides rate limiting, error handling, and logging for all tools.
"""

from __future__ import annotations
import time
import asyncio
from typing import Any, Dict, Optional, Final, TYPE_CHECKING
from datetime import datetime, timedelta
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

from .tool_interface import BaseToolInterface, ToolResult, ToolStatus
from ...log_service import get_logger
from ...config import get_tool_config

if TYPE_CHECKING:
    from collections.abc import Mapping


class RateLimiter:
    """Async-optimized rate limiter implementation."""
    
    __slots__ = ('max_calls_per_minute', 'max_calls_per_hour', 'minute_calls', 'hour_calls', '_lock')
    
    def __init__(self, max_calls_per_minute: int, max_calls_per_hour: int):
        """
        Initialize rate limiter.
        
        Args:
            max_calls_per_minute: Maximum calls per minute
            max_calls_per_hour: Maximum calls per hour
        """
        self.max_calls_per_minute: Final[int] = max_calls_per_minute
        self.max_calls_per_hour: Final[int] = max_calls_per_hour
        self.minute_calls: deque[float] = deque()
        self.hour_calls: deque[float] = deque()
        self._lock = asyncio.Lock()
    
    async def can_proceed(self) -> bool:
        """
        Check if a call can proceed without exceeding rate limits.
        
        Returns:
            True if call can proceed, False if rate limited
        """
        async with self._lock:
            now = time.time()
            
            # Clean old entries using efficient batch removal
            self._cleanup_old_calls(now)
            
            # Check limits
            if len(self.minute_calls) >= self.max_calls_per_minute:
                return False
            if len(self.hour_calls) >= self.max_calls_per_hour:
                return False
            
            # Record the call
            self.minute_calls.append(now)
            self.hour_calls.append(now)
            return True
    
    def _cleanup_old_calls(self, now: float) -> None:
        """Efficiently clean up old call records."""
        minute_ago = now - 60
        hour_ago = now - 3600
        
        # Use more efficient bulk removal for minute calls
        while self.minute_calls and self.minute_calls[0] < minute_ago:
            self.minute_calls.popleft()
        
        # Use more efficient bulk removal for hour calls
        while self.hour_calls and self.hour_calls[0] < hour_ago:
            self.hour_calls.popleft()
    
    async def wait_for_slot(self, timeout_seconds: float = 60.0) -> bool:
        """
        Wait for an available rate limit slot with exponential backoff.
        
        Args:
            timeout_seconds: Maximum time to wait
            
        Returns:
            True if slot became available, False if timeout
        """
        start_time = time.time()
        backoff = 0.1
        
        while time.time() - start_time < timeout_seconds:
            if await self.can_proceed():
                return True
            
            # Exponential backoff with jitter
            await asyncio.sleep(backoff + (backoff * 0.1 * asyncio.get_event_loop().time() % 1))
            backoff = min(backoff * 1.5, 5.0)  # Cap at 5 seconds
        
        return False
    
    def get_stats(self) -> Dict[str, int]:
        """Get current rate limiter statistics."""
        return {
            'calls_last_minute': len(self.minute_calls),
            'calls_last_hour': len(self.hour_calls),
            'max_per_minute': self.max_calls_per_minute,
            'max_per_hour': self.max_calls_per_hour
        }


class BaseTool(BaseToolInterface):
    """Base implementation for all platform tools with enhanced async support."""
    
    def __init__(self, config: Mapping[str, Any]):
        """
        Initialize the base tool.
        
        Args:
            config: Tool configuration
        """
        super().__init__(config)
        self.logger = get_logger(f"tool.{self.__class__.__name__.lower()}")
        
        # Rate limiting with validation
        rate_limit_per_minute = max(1, config.get("rate_limit_per_minute", 60))
        rate_limit_per_hour = max(1, config.get("rate_limit_per_hour", 1000))
        self.rate_limiter = RateLimiter(rate_limit_per_minute, rate_limit_per_hour)
        
        # Configuration with validation
        self.timeout_seconds = max(1, min(300, config.get("timeout_seconds", 30)))
        self.retry_attempts = max(0, min(10, config.get("retry_attempts", 3)))
        self.retry_delay_seconds = max(0.1, min(60.0, config.get("retry_delay_seconds", 1.0)))
        self.enabled = config.get("enabled", True)
        
        # State tracking with thread safety
        self._is_setup = False
        self._setup_lock = asyncio.Lock()
        self._health_status = True
        self._last_health_check: Optional[datetime] = None
        
        # HTTP client with connection pooling
        self._http_client: Optional[httpx.AsyncClient] = None
        self._client_lock = asyncio.Lock()
    
    @property
    async def http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with connection pooling."""
        if self._http_client is None:
            async with self._client_lock:
                if self._http_client is None:  # Double-check pattern
                    self._http_client = httpx.AsyncClient(
                        timeout=httpx.Timeout(self.timeout_seconds),
                        limits=httpx.Limits(
                            max_keepalive_connections=20,
                            max_connections=100,
                            keepalive_expiry=30.0
                        ),
                        http2=True,  # Enable HTTP/2 for better performance
                        verify=True  # Always verify SSL certificates
                    )
        return self._http_client
    
    @asynccontextmanager
    async def _http_session(self):
        """Async context manager for HTTP sessions."""
        client = await self.http_client
        try:
            yield client
        except Exception:
            # Log but don't re-raise to allow for cleanup
            self.logger.debug("HTTP session error occurred")
            raise
    
    async def execute(
        self, 
        input_data: Mapping[str, Any], 
        context: Optional[Mapping[str, Any]] = None
    ) -> ToolResult:
        """
        Execute the tool with enhanced error handling and monitoring.
        
        Args:
            input_data: Input parameters for the tool
            context: Optional execution context
            
        Returns:
            Tool execution result
        """
        start_time = time.perf_counter()  # More precise timing
        context = dict(context) if context else {}
        tenant_id = context.get("tenant_id", "unknown")
        correlation_id = context.get("correlation_id")
        
        # Create immutable copies for safety
        input_data = dict(input_data)
        
        try:
            # Pre-execution checks
            if not self.enabled:
                return self._create_error_result("Tool is disabled", start_time)
            
            # Thread-safe setup
            await self._ensure_setup()
            
            # Health check with caching
            if not await self._cached_health_check():
                return self._create_error_result("Tool health check failed", start_time)
            
            # Input validation
            if not await self.validate_input(input_data):
                return self._create_error_result("Invalid input data", start_time)
            
            # Rate limiting with waiting
            if not await self.rate_limiter.can_proceed():
                # Try to wait for a slot briefly
                if not await self.rate_limiter.wait_for_slot(5.0):
                    return ToolResult(
                        status=ToolStatus.RATE_LIMITED,
                        error="Rate limit exceeded",
                        execution_time_ms=(time.perf_counter() - start_time) * 1000
                    )
            
            # Execute with comprehensive monitoring
            result = await self._execute_with_retry(input_data, context)
            result.execution_time_ms = (time.perf_counter() - start_time) * 1000
            
            # Enhanced logging with structured data
            self.logger.info(
                f"Tool executed successfully",
                extra={
                    "tenant_id": tenant_id,
                    "tool_name": self.metadata.name,
                    "status": result.status.value,
                    "duration_ms": result.execution_time_ms,
                    "correlation_id": correlation_id,
                    "input_size": len(str(input_data)),
                    "rate_limiter_stats": self.rate_limiter.get_stats()
                }
            )
            
            return result
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            error_msg = str(e)[:1000]  # Truncate very long errors
            
            self.logger.error(
                f"Tool execution failed",
                extra={
                    "tenant_id": tenant_id,
                    "tool_name": self.metadata.name,
                    "error": error_msg,
                    "error_type": type(e).__name__,
                    "duration_ms": execution_time,
                    "correlation_id": correlation_id
                },
                exc_info=True  # Include stack trace
            )
            
            return ToolResult(
                status=ToolStatus.ERROR,
                error=error_msg,
                execution_time_ms=execution_time
            )
    
    def _create_error_result(self, error: str, start_time: float) -> ToolResult:
        """Helper to create error results consistently."""
        return ToolResult(
            status=ToolStatus.ERROR,
            error=error,
            execution_time_ms=(time.perf_counter() - start_time) * 1000
        )
    
    async def _ensure_setup(self) -> None:
        """Ensure tool is set up with thread safety."""
        if not self._is_setup:
            async with self._setup_lock:
                if not self._is_setup:  # Double-check pattern
                    setup_success = await self.setup()
                    if not setup_success:
                        raise RuntimeError("Tool setup failed")
                    self._is_setup = True
    
    async def _cached_health_check(self) -> bool:
        """Health check with caching to avoid excessive checks."""
        now = datetime.now()
        
        # Use cached result if recent (within 30 seconds)
        if (self._last_health_check and 
            (now - self._last_health_check).total_seconds() < 30 and 
            self._health_status):
            return self._health_status
        
        # Perform actual health check
        self._health_status = await self.health_check()
        self._last_health_check = now
        return self._health_status
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError))
    )
    async def _execute_with_retry(
        self, 
        input_data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> ToolResult:
        """
        Execute the tool with sophisticated retry logic.
        
        Args:
            input_data: Input parameters
            context: Execution context
            
        Returns:
            Tool execution result
        """
        return await self._do_execute(input_data, context)
    
    async def _do_execute(
        self, 
        input_data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> ToolResult:
        """
        Actual tool execution logic. Override this in concrete implementations.
        
        Args:
            input_data: Input parameters
            context: Execution context
            
        Returns:
            Tool execution result
        """
        raise NotImplementedError("Subclasses must implement _do_execute")
    
    async def health_check(self) -> bool:
        """
        Enhanced health check implementation.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # More comprehensive health check
            client = await self.http_client
            
            # Test basic connectivity with a HEAD request to a reliable endpoint
            async with asyncio.timeout(5.0):  # Python 3.11+ timeout
                response = await client.head("https://httpbin.org/status/200")
                is_healthy = 200 <= response.status_code < 300
            
            self._health_status = is_healthy
            self._last_health_check = datetime.now()
            
            return is_healthy
            
        except Exception as e:
            self.logger.debug(f"Health check failed: {e}")
            self._health_status = False
            return False
    
    async def cleanup(self) -> bool:
        """
        Enhanced cleanup with proper resource management.
        
        Returns:
            True if cleanup successful
        """
        success = True
        
        try:
            # Notify observers first
            await super().cleanup()
            
            # Close HTTP client
            if self._http_client:
                async with self._client_lock:
                    if self._http_client:
                        await self._http_client.aclose()
                        self._http_client = None
            
            # Reset state
            self._is_setup = False
            self._health_status = False
            self._last_health_check = None
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
            success = False
        
        return success
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance and health metrics for monitoring."""
        return {
            'is_setup': self._is_setup,
            'is_healthy': self._health_status,
            'last_health_check': self._last_health_check.isoformat() if self._last_health_check else None,
            'rate_limiter_stats': self.rate_limiter.get_stats(),
            'has_http_client': self._http_client is not None,
            'config': {
                'enabled': self.enabled,
                'timeout_seconds': self.timeout_seconds,
                'retry_attempts': self.retry_attempts,
                'retry_delay_seconds': self.retry_delay_seconds
            }
        }
    
    def __del__(self):
        """Enhanced destructor with better cleanup handling."""
        if self._http_client:
            # Schedule cleanup in the event loop if running
            try:
                loop = asyncio.get_running_loop()
                if not loop.is_closed():
                    loop.create_task(self._http_client.aclose())
            except RuntimeError:
                # No running loop, try to create one for cleanup
                try:
                    asyncio.run(self._http_client.aclose())
                except Exception:
                    pass  # Best effort cleanup