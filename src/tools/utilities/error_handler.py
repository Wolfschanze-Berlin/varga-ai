"""
Error handling utilities for AutoGen SME platform tools.
Provides centralized error handling and recovery mechanisms.
"""

import traceback
from typing import Any, Dict, Optional, Callable, Type, Union, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import httpx

from ...log_service import get_logger


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories."""
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    VALIDATION = "validation"
    EXTERNAL_SERVICE = "external_service"
    INTERNAL = "internal"
    CONFIGURATION = "configuration"
    TIMEOUT = "timeout"


@dataclass
class ErrorDetails:
    """Detailed error information."""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    stacktrace: Optional[str] = None
    recoverable: bool = True
    retry_after_seconds: Optional[int] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.details is None:
            self.details = {}


class ToolError(Exception):
    """Base exception for tool errors."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.INTERNAL,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True,
        retry_after_seconds: Optional[int] = None
    ):
        super().__init__(message)
        self.error_details = ErrorDetails(
            category=category,
            severity=severity,
            message=message,
            code=code,
            details=details or {},
            stacktrace=traceback.format_exc(),
            recoverable=recoverable,
            retry_after_seconds=retry_after_seconds
        )


class NetworkError(ToolError):
    """Network-related errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class AuthenticationError(ToolError):
    """Authentication-related errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            recoverable=False,
            **kwargs
        )


class RateLimitError(ToolError):
    """Rate limiting errors."""
    
    def __init__(self, message: str, retry_after_seconds: int = 60, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            retry_after_seconds=retry_after_seconds,
            **kwargs
        )


class ValidationError(ToolError):
    """Input validation errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            recoverable=False,
            **kwargs
        )


class ExternalServiceError(ToolError):
    """External service errors."""
    
    def __init__(self, message: str, service_name: str = None, **kwargs):
        details = kwargs.get("details", {})
        if service_name:
            details["service_name"] = service_name
        
        super().__init__(
            message,
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            **kwargs
        )


class ConfigurationError(ToolError):
    """Configuration-related errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            recoverable=False,
            **kwargs
        )


class TimeoutError(ToolError):
    """Timeout errors."""
    
    def __init__(self, message: str, timeout_seconds: float = None, **kwargs):
        details = kwargs.get("details", {})
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        
        super().__init__(
            message,
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            **kwargs
        )


class ErrorHandler:
    """Centralized error handling and recovery system."""
    
    def __init__(self, tool_name: str):
        """
        Initialize error handler.
        
        Args:
            tool_name: Name of the tool using this error handler
        """
        self.tool_name = tool_name
        self.logger = get_logger(f"error_handler.{tool_name}")
        self._error_callbacks: List[Callable[[ErrorDetails], None]] = []
    
    def add_error_callback(self, callback: Callable[[ErrorDetails], None]) -> None:
        """
        Add a callback to be called when errors occur.
        
        Args:
            callback: Function to call with error details
        """
        self._error_callbacks.append(callback)
    
    def handle_exception(
        self,
        exc: Exception,
        context: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> ErrorDetails:
        """
        Handle and categorize an exception.
        
        Args:
            exc: Exception to handle
            context: Optional context information
            tenant_id: Optional tenant ID
            correlation_id: Optional correlation ID
            
        Returns:
            ErrorDetails object
        """
        context = context or {}
        
        # Convert common exceptions to ToolError
        if isinstance(exc, ToolError):
            error_details = exc.error_details
        else:
            error_details = self._categorize_exception(exc)
        
        # Add context information
        error_details.details.update({
            "tool_name": self.tool_name,
            "context": context,
            "tenant_id": tenant_id,
            "correlation_id": correlation_id
        })
        
        # Log the error
        self._log_error(error_details, tenant_id, correlation_id)
        
        # Call error callbacks
        for callback in self._error_callbacks:
            try:
                callback(error_details)
            except Exception as callback_exc:
                self.logger.error(f"Error callback failed: {callback_exc}")
        
        return error_details
    
    def _categorize_exception(self, exc: Exception) -> ErrorDetails:
        """
        Categorize a generic exception into a ToolError.
        
        Args:
            exc: Exception to categorize
            
        Returns:
            ErrorDetails object
        """
        exc_type = type(exc)
        message = str(exc)
        
        # HTTP errors
        if isinstance(exc, httpx.HTTPStatusError):
            status_code = exc.response.status_code
            
            if status_code == 401:
                return ErrorDetails(
                    category=ErrorCategory.AUTHENTICATION,
                    severity=ErrorSeverity.HIGH,
                    message=f"Authentication failed: {message}",
                    code=str(status_code),
                    recoverable=False
                )
            elif status_code == 429:
                # Extract retry-after header if available
                retry_after = None
                if hasattr(exc, 'response') and exc.response.headers.get('retry-after'):
                    try:
                        retry_after = int(exc.response.headers['retry-after'])
                    except ValueError:
                        retry_after = 60
                
                return ErrorDetails(
                    category=ErrorCategory.RATE_LIMIT,
                    severity=ErrorSeverity.MEDIUM,
                    message=f"Rate limited: {message}",
                    code=str(status_code),
                    retry_after_seconds=retry_after
                )
            elif 500 <= status_code < 600:
                return ErrorDetails(
                    category=ErrorCategory.EXTERNAL_SERVICE,
                    severity=ErrorSeverity.HIGH,
                    message=f"External service error: {message}",
                    code=str(status_code)
                )
            else:
                return ErrorDetails(
                    category=ErrorCategory.NETWORK,
                    severity=ErrorSeverity.MEDIUM,
                    message=f"HTTP error: {message}",
                    code=str(status_code)
                )
        
        # Timeout errors
        elif isinstance(exc, (httpx.TimeoutException, TimeoutError)):
            return ErrorDetails(
                category=ErrorCategory.TIMEOUT,
                severity=ErrorSeverity.MEDIUM,
                message=f"Operation timed out: {message}"
            )
        
        # Connection errors
        elif isinstance(exc, (httpx.ConnectError, httpx.NetworkError)):
            return ErrorDetails(
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                message=f"Network error: {message}"
            )
        
        # Validation errors
        elif isinstance(exc, (ValueError, TypeError)) and "validation" in message.lower():
            return ErrorDetails(
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.LOW,
                message=f"Validation error: {message}",
                recoverable=False
            )
        
        # Configuration errors
        elif isinstance(exc, (KeyError, AttributeError)) and any(
            keyword in message.lower() for keyword in ["config", "setting", "key", "env"]
        ):
            return ErrorDetails(
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.HIGH,
                message=f"Configuration error: {message}",
                recoverable=False
            )
        
        # Generic internal error
        else:
            return ErrorDetails(
                category=ErrorCategory.INTERNAL,
                severity=ErrorSeverity.MEDIUM,
                message=f"Internal error: {message}",
                details={"exception_type": exc_type.__name__}
            )
    
    def _log_error(
        self,
        error_details: ErrorDetails,
        tenant_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Log error details.
        
        Args:
            error_details: Error details to log
            tenant_id: Optional tenant ID
            correlation_id: Optional correlation ID
        """
        log_data = {
            "tool_name": self.tool_name,
            "error_category": error_details.category.value,
            "error_severity": error_details.severity.value,
            "error_code": error_details.code,
            "recoverable": error_details.recoverable,
            "tenant_id": tenant_id,
            "correlation_id": correlation_id,
            "error_details": error_details.details
        }
        
        if error_details.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(
                f"Critical error: {error_details.message}",
                extra=log_data
            )
        elif error_details.severity == ErrorSeverity.HIGH:
            self.logger.error(
                f"High severity error: {error_details.message}",
                extra=log_data
            )
        elif error_details.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(
                f"Medium severity error: {error_details.message}",
                extra=log_data
            )
        else:
            self.logger.info(
                f"Low severity error: {error_details.message}",
                extra=log_data
            )
        
        # Log stack trace for internal errors
        if error_details.category == ErrorCategory.INTERNAL and error_details.stacktrace:
            self.logger.debug(f"Stack trace: {error_details.stacktrace}")
    
    def create_recovery_strategy(self, error_details: ErrorDetails) -> Optional[Dict[str, Any]]:
        """
        Create a recovery strategy for an error.
        
        Args:
            error_details: Error details
            
        Returns:
            Recovery strategy or None if not recoverable
        """
        if not error_details.recoverable:
            return None
        
        strategy = {
            "can_retry": True,
            "max_retries": 3,
            "backoff_factor": 1.0,
            "retry_after_seconds": error_details.retry_after_seconds or 1
        }
        
        # Adjust strategy based on error category
        if error_details.category == ErrorCategory.RATE_LIMIT:
            strategy.update({
                "max_retries": 1,
                "retry_after_seconds": error_details.retry_after_seconds or 60,
                "backoff_factor": 0  # Don't use exponential backoff for rate limits
            })
        elif error_details.category == ErrorCategory.NETWORK:
            strategy.update({
                "max_retries": 5,
                "backoff_factor": 2.0
            })
        elif error_details.category == ErrorCategory.TIMEOUT:
            strategy.update({
                "max_retries": 2,
                "retry_after_seconds": 5
            })
        elif error_details.category == ErrorCategory.EXTERNAL_SERVICE:
            strategy.update({
                "max_retries": 3,
                "backoff_factor": 1.5
            })
        
        return strategy


def handle_tool_errors(tool_name: str):
    """
    Decorator to handle tool errors automatically.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        Decorated function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            error_handler = ErrorHandler(tool_name)
            
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                error_details = error_handler.handle_exception(
                    exc,
                    context=kwargs.get("context", {}),
                    tenant_id=kwargs.get("tenant_id"),
                    correlation_id=kwargs.get("correlation_id")
                )
                
                # Re-raise as ToolError for consistent handling
                raise ToolError(
                    error_details.message,
                    category=error_details.category,
                    severity=error_details.severity,
                    code=error_details.code,
                    details=error_details.details,
                    recoverable=error_details.recoverable,
                    retry_after_seconds=error_details.retry_after_seconds
                )
        
        return wrapper
    return decorator