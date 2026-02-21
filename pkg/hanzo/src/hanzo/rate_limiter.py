"""
Rate limiting and error recovery for Hanzo Dev.
Prevents API overuse and handles failures gracefully.
"""

import time
import random
import asyncio
from typing import Any, Dict, Callable, Optional
from datetime import datetime, timedelta
from collections import deque
from dataclasses import field, dataclass


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests_per_minute: int = 20
    requests_per_hour: int = 100
    burst_size: int = 5
    cooldown_seconds: int = 60
    max_retries: int = 3
    backoff_base: float = 2.0
    jitter: bool = True


@dataclass
class RateLimitState:
    """Current state of rate limiter."""

    minute_requests: deque = field(default_factory=lambda: deque(maxlen=60))
    hour_requests: deque = field(default_factory=lambda: deque(maxlen=3600))
    last_request: Optional[datetime] = None
    consecutive_errors: int = 0
    total_requests: int = 0
    total_errors: int = 0
    is_throttled: bool = False
    throttle_until: Optional[datetime] = None


class RateLimiter:
    """Rate limiter with error recovery."""

    def __init__(self, config: RateLimitConfig = None):
        """Initialize rate limiter."""
        self.config = config or RateLimitConfig()
        self.states: Dict[str, RateLimitState] = {}

    def get_state(self, key: str = "default") -> RateLimitState:
        """Get or create state for a key."""
        if key not in self.states:
            self.states[key] = RateLimitState()
        return self.states[key]

    async def check_rate_limit(self, key: str = "default") -> tuple[bool, float]:
        """
        Check if request is allowed.
        Returns (allowed, wait_seconds).
        """
        state = self.get_state(key)
        now = datetime.now()

        # Check if throttled
        if state.is_throttled and state.throttle_until:
            if now < state.throttle_until:
                wait_seconds = (state.throttle_until - now).total_seconds()
                return False, wait_seconds
            else:
                # Throttle period ended
                state.is_throttled = False
                state.throttle_until = None

        # Clean old requests
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)

        # Remove old requests from queues
        while state.minute_requests and state.minute_requests[0] < minute_ago:
            state.minute_requests.popleft()

        while state.hour_requests and state.hour_requests[0] < hour_ago:
            state.hour_requests.popleft()

        # Check minute limit
        if len(state.minute_requests) >= self.config.requests_per_minute:
            # Calculate wait time
            oldest = state.minute_requests[0]
            wait_seconds = (oldest + timedelta(minutes=1) - now).total_seconds()
            return False, max(0, wait_seconds)

        # Check hour limit
        if len(state.hour_requests) >= self.config.requests_per_hour:
            # Calculate wait time
            oldest = state.hour_requests[0]
            wait_seconds = (oldest + timedelta(hours=1) - now).total_seconds()
            return False, max(0, wait_seconds)

        # Check burst limit
        if state.last_request:
            time_since_last = (now - state.last_request).total_seconds()
            if time_since_last < 1.0 / self.config.burst_size:
                wait_seconds = (1.0 / self.config.burst_size) - time_since_last
                return False, wait_seconds

        return True, 0

    async def acquire(self, key: str = "default") -> bool:
        """
        Acquire a rate limit slot.
        Waits if necessary.
        """
        while True:
            allowed, wait_seconds = await self.check_rate_limit(key)

            if allowed:
                # Record request
                state = self.get_state(key)
                now = datetime.now()
                state.minute_requests.append(now)
                state.hour_requests.append(now)
                state.last_request = now
                state.total_requests += 1
                return True

            # Wait before retrying
            if wait_seconds > 0:
                await asyncio.sleep(min(wait_seconds, 5))  # Check every 5 seconds max

    def record_error(self, key: str = "default", error: Exception = None):
        """Record an error for the key."""
        state = self.get_state(key)
        state.consecutive_errors += 1
        state.total_errors += 1

        # Implement exponential backoff on errors
        if state.consecutive_errors >= 3:
            # Throttle for increasing periods
            backoff_minutes = min(
                self.config.backoff_base ** (state.consecutive_errors - 2),
                60,  # Max 1 hour
            )
            state.is_throttled = True
            state.throttle_until = datetime.now() + timedelta(minutes=backoff_minutes)

    def record_success(self, key: str = "default"):
        """Record a successful request."""
        state = self.get_state(key)
        state.consecutive_errors = 0

    def get_status(self, key: str = "default") -> Dict[str, Any]:
        """Get current status for monitoring."""
        state = self.get_state(key)
        now = datetime.now()

        return {
            "requests_last_minute": len(state.minute_requests),
            "requests_last_hour": len(state.hour_requests),
            "total_requests": state.total_requests,
            "total_errors": state.total_errors,
            "consecutive_errors": state.consecutive_errors,
            "is_throttled": state.is_throttled,
            "throttle_remaining": (
                (state.throttle_until - now).total_seconds()
                if state.throttle_until and now < state.throttle_until
                else 0
            ),
            "minute_limit": self.config.requests_per_minute,
            "hour_limit": self.config.requests_per_hour,
        }


class ErrorRecovery:
    """Error recovery with retries and fallback."""

    def __init__(self, rate_limiter: RateLimiter = None):
        """Initialize error recovery."""
        self.rate_limiter = rate_limiter or RateLimiter()
        self.fallback_handlers: Dict[type, Callable] = {}

    def register_fallback(self, error_type: type, handler: Callable):
        """Register a fallback handler for an error type."""
        self.fallback_handlers[error_type] = handler

    async def with_retry(
        self,
        func: Callable,
        *args,
        key: str = "default",
        max_retries: Optional[int] = None,
        **kwargs,
    ) -> Any:
        """
        Execute function with retry logic.
        """
        max_retries = max_retries or self.rate_limiter.config.max_retries
        last_error = None

        for attempt in range(max_retries):
            try:
                # Check rate limit
                await self.rate_limiter.acquire(key)

                # Execute function
                result = await func(*args, **kwargs)

                # Record success
                self.rate_limiter.record_success(key)

                return result

            except Exception as e:
                last_error = e
                self.rate_limiter.record_error(key, e)

                # Check for fallback handler
                for error_type, handler in self.fallback_handlers.items():
                    if isinstance(e, error_type):
                        try:
                            return await handler(*args, **kwargs)
                        except Exception:
                            pass  # Fallback failed, continue with retry

                # Calculate backoff
                if attempt < max_retries - 1:
                    backoff = self.rate_limiter.config.backoff_base**attempt

                    # Add jitter if configured
                    if self.rate_limiter.config.jitter:
                        backoff *= 0.5 + random.random()

                    await asyncio.sleep(min(backoff, 60))  # Max 60 seconds

        # All retries failed
        raise last_error or Exception("All retry attempts failed")

    async def with_circuit_breaker(
        self,
        func: Callable,
        *args,
        key: str = "default",
        threshold: int = 5,
        timeout: int = 60,
        **kwargs,
    ) -> Any:
        """
        Execute function with circuit breaker pattern.
        """
        state = self.rate_limiter.get_state(key)

        # Check if circuit is open
        if state.is_throttled:
            raise Exception(f"Circuit breaker open for {key}")

        try:
            result = await self.with_retry(func, *args, key=key, **kwargs)
            return result

        except Exception as e:
            # Check if we should open the circuit
            if state.consecutive_errors >= threshold:
                state.is_throttled = True
                state.throttle_until = datetime.now() + timedelta(seconds=timeout)
                raise Exception(f"Circuit breaker triggered for {key}: {e}")
            raise


class SmartRateLimiter:
    """Smart rate limiter that adapts to API responses."""

    def __init__(self):
        """Initialize smart rate limiter."""
        self.limiters: Dict[str, RateLimiter] = {}
        self.recovery = ErrorRecovery()

        # Default configs for known APIs
        self.configs = {
            "openai": RateLimitConfig(
                requests_per_minute=60, requests_per_hour=1000, burst_size=10
            ),
            "anthropic": RateLimitConfig(
                requests_per_minute=50, requests_per_hour=1000, burst_size=5
            ),
            "local": RateLimitConfig(
                requests_per_minute=100, requests_per_hour=10000, burst_size=20
            ),
            "free": RateLimitConfig(
                requests_per_minute=10, requests_per_hour=100, burst_size=2
            ),
        }

    def get_limiter(self, api_type: str) -> RateLimiter:
        """Get or create limiter for API type."""
        if api_type not in self.limiters:
            config = self.configs.get(api_type, RateLimitConfig())
            self.limiters[api_type] = RateLimiter(config)
        return self.limiters[api_type]

    async def execute_with_limit(
        self, api_type: str, func: Callable, *args, **kwargs
    ) -> Any:
        """Execute function with appropriate rate limiting."""
        limiter = self.get_limiter(api_type)
        recovery = ErrorRecovery(limiter)

        return await recovery.with_retry(func, *args, key=api_type, **kwargs)

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all limiters."""
        return {
            api_type: limiter.get_status()
            for api_type, limiter in self.limiters.items()
        }


# Global instance for easy use
smart_limiter = SmartRateLimiter()
