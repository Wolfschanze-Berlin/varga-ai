"""
Utilities module for AutoGen SME platform tools.
Provides error handling, rate limiting, and other common utilities.
"""

from .error_handler import (
    ErrorHandler,
    ToolError,
    NetworkError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    ExternalServiceError,
    ConfigurationError,
    TimeoutError,
    ErrorSeverity,
    ErrorCategory,
    ErrorDetails,
    handle_tool_errors
)
from .rate_limiter import (
    AdvancedRateLimiter,
    RateLimitStrategy,
    RateLimitScope,
    RateLimitRule,
    RateLimitResult,
    TokenBucketLimiter,
    SlidingWindowLimiter,
    get_rate_limiter,
    add_rate_limit_rule,
    check_rate_limit
)

__all__ = [
    # Error handling
    "ErrorHandler",
    "ToolError",
    "NetworkError", 
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "ExternalServiceError",
    "ConfigurationError",
    "TimeoutError",
    "ErrorSeverity",
    "ErrorCategory", 
    "ErrorDetails",
    "handle_tool_errors",
    
    # Rate limiting
    "AdvancedRateLimiter",
    "RateLimitStrategy",
    "RateLimitScope",
    "RateLimitRule", 
    "RateLimitResult",
    "TokenBucketLimiter",
    "SlidingWindowLimiter",
    "get_rate_limiter",
    "add_rate_limit_rule",
    "check_rate_limit"
]