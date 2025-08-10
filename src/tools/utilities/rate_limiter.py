"""
Advanced rate limiting utilities for AutoGen SME platform tools.
Provides sophisticated rate limiting strategies and quota management.
"""

import asyncio
import time
from typing import Dict, Optional, Any, List, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from collections import deque, defaultdict
import hashlib

from ...log_service import get_logger


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies."""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"


class RateLimitScope(str, Enum):
    """Rate limit scopes."""
    GLOBAL = "global"
    TENANT = "tenant"
    USER = "user"
    TOOL = "tool"
    ENDPOINT = "endpoint"


@dataclass
class RateLimitRule:
    """Rate limiting rule definition."""
    max_requests: int
    window_seconds: int
    scope: RateLimitScope
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    burst_limit: Optional[int] = None
    quota_reset_interval: Optional[int] = None
    priority: int = 0  # Higher priority rules are checked first
    
    def get_key(self, identifier: str) -> str:
        """Generate a unique key for this rule and identifier."""
        rule_hash = hashlib.md5(
            f"{self.scope}:{self.max_requests}:{self.window_seconds}".encode()
        ).hexdigest()[:8]
        return f"{rule_hash}:{identifier}"


class RateLimitResult:
    """Result of a rate limit check."""
    
    def __init__(
        self,
        allowed: bool,
        remaining: int = 0,
        reset_time: Optional[datetime] = None,
        retry_after_seconds: Optional[int] = None,
        rule_matched: Optional[RateLimitRule] = None
    ):
        self.allowed = allowed
        self.remaining = remaining
        self.reset_time = reset_time
        self.retry_after_seconds = retry_after_seconds
        self.rule_matched = rule_matched


class TokenBucketLimiter:
    """Token bucket rate limiter implementation."""
    
    def __init__(self, max_tokens: int, refill_rate: float, refill_period: float = 1.0):
        """
        Initialize token bucket limiter.
        
        Args:
            max_tokens: Maximum tokens in the bucket
            refill_rate: Tokens added per refill_period
            refill_period: Time period for refill in seconds
        """
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.refill_period = refill_period
        self.tokens = max_tokens
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False if not enough tokens
        """
        async with self._lock:
            now = time.time()
            time_passed = now - self.last_refill
            
            # Refill tokens based on time passed
            new_tokens = (time_passed / self.refill_period) * self.refill_rate
            self.tokens = min(self.max_tokens, self.tokens + new_tokens)
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def get_remaining(self) -> int:
        """Get remaining tokens."""
        return max(0, int(self.tokens))
    
    def get_reset_time(self) -> datetime:
        """Get time when bucket will be full again."""
        if self.tokens >= self.max_tokens:
            return datetime.now()
        
        time_to_full = ((self.max_tokens - self.tokens) / self.refill_rate) * self.refill_period
        return datetime.now() + timedelta(seconds=time_to_full)


class SlidingWindowLimiter:
    """Sliding window rate limiter implementation."""
    
    def __init__(self, max_requests: int, window_seconds: int):
        """
        Initialize sliding window limiter.
        
        Args:
            max_requests: Maximum requests in the window
            window_seconds: Window size in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: deque = deque()
        self._lock = asyncio.Lock()
    
    async def is_allowed(self) -> bool:
        """
        Check if a request is allowed.
        
        Returns:
            True if request is allowed, False otherwise
        """
        async with self._lock:
            now = time.time()
            cutoff_time = now - self.window_seconds
            
            # Remove old requests outside the window
            while self.requests and self.requests[0] <= cutoff_time:
                self.requests.popleft()
            
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            return False
    
    def get_remaining(self) -> int:
        """Get remaining requests in the current window."""
        return max(0, self.max_requests - len(self.requests))
    
    def get_reset_time(self) -> datetime:
        """Get time when the oldest request will expire."""
        if not self.requests:
            return datetime.now()
        
        oldest_request = self.requests[0]
        reset_time = oldest_request + self.window_seconds
        return datetime.fromtimestamp(reset_time)


class AdvancedRateLimiter:
    """Advanced rate limiter with multiple strategies and scopes."""
    
    def __init__(self):
        """Initialize the advanced rate limiter."""
        self.logger = get_logger("rate_limiter")
        self.rules: List[RateLimitRule] = []
        self.limiters: Dict[str, Union[TokenBucketLimiter, SlidingWindowLimiter]] = {}
        self.quotas: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._lock = asyncio.Lock()
    
    def add_rule(self, rule: RateLimitRule) -> None:
        """
        Add a rate limiting rule.
        
        Args:
            rule: Rate limit rule to add
        """
        self.rules.append(rule)
        # Sort rules by priority (higher priority first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        self.logger.info(f"Added rate limit rule: {rule.scope.value} - {rule.max_requests}/{rule.window_seconds}s")
    
    def remove_rule(self, scope: RateLimitScope, max_requests: int, window_seconds: int) -> bool:
        """
        Remove a rate limiting rule.
        
        Args:
            scope: Rule scope
            max_requests: Maximum requests
            window_seconds: Window size
            
        Returns:
            True if rule was removed, False if not found
        """
        for i, rule in enumerate(self.rules):
            if (rule.scope == scope and 
                rule.max_requests == max_requests and 
                rule.window_seconds == window_seconds):
                del self.rules[i]
                self.logger.info(f"Removed rate limit rule: {scope.value}")
                return True
        return False
    
    async def check_rate_limit(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        endpoint: Optional[str] = None,
        tokens_requested: int = 1
    ) -> RateLimitResult:
        """
        Check if a request should be rate limited.
        
        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            tool_name: Tool name
            endpoint: Endpoint identifier
            tokens_requested: Number of tokens requested
            
        Returns:
            Rate limit check result
        """
        async with self._lock:
            # Check each rule in priority order
            for rule in self.rules:
                identifier = self._get_identifier(rule.scope, tenant_id, user_id, tool_name, endpoint)
                if identifier is None:
                    continue
                
                result = await self._check_rule(rule, identifier, tokens_requested)
                if not result.allowed:
                    self.logger.warning(
                        f"Rate limit exceeded for {rule.scope.value}: {identifier}",
                        extra={
                            "tenant_id": tenant_id,
                            "user_id": user_id,
                            "tool_name": tool_name,
                            "rule_scope": rule.scope.value,
                            "max_requests": rule.max_requests,
                            "window_seconds": rule.window_seconds
                        }
                    )
                    return result
            
            # All rules passed
            return RateLimitResult(allowed=True)
    
    def _get_identifier(
        self,
        scope: RateLimitScope,
        tenant_id: Optional[str],
        user_id: Optional[str],
        tool_name: Optional[str],
        endpoint: Optional[str]
    ) -> Optional[str]:
        """Get identifier for the given scope."""
        if scope == RateLimitScope.GLOBAL:
            return "global"
        elif scope == RateLimitScope.TENANT and tenant_id:
            return f"tenant:{tenant_id}"
        elif scope == RateLimitScope.USER and user_id:
            return f"user:{user_id}"
        elif scope == RateLimitScope.TOOL and tool_name:
            return f"tool:{tool_name}"
        elif scope == RateLimitScope.ENDPOINT and endpoint:
            return f"endpoint:{endpoint}"
        return None
    
    async def _check_rule(
        self,
        rule: RateLimitRule,
        identifier: str,
        tokens_requested: int
    ) -> RateLimitResult:
        """Check a specific rule against an identifier."""
        limiter_key = rule.get_key(identifier)
        
        # Get or create limiter for this rule and identifier
        if limiter_key not in self.limiters:
            self.limiters[limiter_key] = self._create_limiter(rule)
        
        limiter = self.limiters[limiter_key]
        
        if rule.strategy == RateLimitStrategy.TOKEN_BUCKET:
            allowed = await limiter.consume(tokens_requested)
            remaining = limiter.get_remaining()
            reset_time = limiter.get_reset_time()
        elif rule.strategy == RateLimitStrategy.SLIDING_WINDOW:
            allowed = await limiter.is_allowed()
            remaining = limiter.get_remaining()
            reset_time = limiter.get_reset_time()
        else:
            # Default to sliding window
            allowed = await limiter.is_allowed()
            remaining = limiter.get_remaining()
            reset_time = limiter.get_reset_time()
        
        retry_after_seconds = None
        if not allowed:
            retry_after_seconds = int((reset_time - datetime.now()).total_seconds())
            retry_after_seconds = max(1, retry_after_seconds)
        
        return RateLimitResult(
            allowed=allowed,
            remaining=remaining,
            reset_time=reset_time,
            retry_after_seconds=retry_after_seconds,
            rule_matched=rule
        )
    
    def _create_limiter(self, rule: RateLimitRule) -> Union[TokenBucketLimiter, SlidingWindowLimiter]:
        """Create a limiter instance based on the rule strategy."""
        if rule.strategy == RateLimitStrategy.TOKEN_BUCKET:
            refill_rate = rule.max_requests / rule.window_seconds
            return TokenBucketLimiter(
                max_tokens=rule.max_requests,
                refill_rate=refill_rate,
                refill_period=1.0
            )
        elif rule.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return SlidingWindowLimiter(
                max_requests=rule.max_requests,
                window_seconds=rule.window_seconds
            )
        else:
            # Default to sliding window
            return SlidingWindowLimiter(
                max_requests=rule.max_requests,
                window_seconds=rule.window_seconds
            )
    
    async def reset_limits(self, identifier_pattern: str = None) -> int:
        """
        Reset rate limits for identifiers matching the pattern.
        
        Args:
            identifier_pattern: Pattern to match identifiers (None = reset all)
            
        Returns:
            Number of limiters reset
        """
        async with self._lock:
            if identifier_pattern is None:
                count = len(self.limiters)
                self.limiters.clear()
                self.logger.info("Reset all rate limiters")
                return count
            
            keys_to_remove = [
                key for key in self.limiters.keys()
                if identifier_pattern in key
            ]
            
            for key in keys_to_remove:
                del self.limiters[key]
            
            self.logger.info(f"Reset {len(keys_to_remove)} rate limiters matching '{identifier_pattern}'")
            return len(keys_to_remove)
    
    def get_limiter_stats(self) -> Dict[str, Any]:
        """
        Get statistics about active rate limiters.
        
        Returns:
            Dictionary with limiter statistics
        """
        stats = {
            "total_rules": len(self.rules),
            "active_limiters": len(self.limiters),
            "rules_by_scope": defaultdict(int),
            "rules_by_strategy": defaultdict(int)
        }
        
        for rule in self.rules:
            stats["rules_by_scope"][rule.scope.value] += 1
            stats["rules_by_strategy"][rule.strategy.value] += 1
        
        return dict(stats)


# Global rate limiter instance
_rate_limiter = AdvancedRateLimiter()

def get_rate_limiter() -> AdvancedRateLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter

def add_rate_limit_rule(
    scope: RateLimitScope,
    max_requests: int,
    window_seconds: int,
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW,
    priority: int = 0
) -> None:
    """Add a rate limit rule to the global limiter."""
    rule = RateLimitRule(
        max_requests=max_requests,
        window_seconds=window_seconds,
        scope=scope,
        strategy=strategy,
        priority=priority
    )
    _rate_limiter.add_rule(rule)

async def check_rate_limit(
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    endpoint: Optional[str] = None,
    tokens_requested: int = 1
) -> RateLimitResult:
    """Check rate limits using the global limiter."""
    return await _rate_limiter.check_rate_limit(
        tenant_id=tenant_id,
        user_id=user_id,
        tool_name=tool_name,
        endpoint=endpoint,
        tokens_requested=tokens_requested
    )