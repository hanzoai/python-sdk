"""Decorators for tool functions."""

import asyncio
import functools
import os
from typing import Any, Callable, Optional
from collections.abc import Awaitable


# Default timeouts per tool (can be overridden via env vars)
DEFAULT_TIMEOUTS: dict[str, int] = {
    "read": 30,
    "write": 60,
    "edit": 60,
    "search": 120,
    "dag": 600,
    "browser": 300,
    "default": 120,
}


def get_timeout(tool_name: str) -> int:
    """Get timeout for a tool.
    
    Checks environment variable HANZO_TIMEOUT_{TOOL_NAME} first,
    then falls back to defaults.
    """
    env_key = f"HANZO_TIMEOUT_{tool_name.upper()}"
    if env_val := os.environ.get(env_key):
        try:
            return int(env_val)
        except ValueError:
            pass
    
    return DEFAULT_TIMEOUTS.get(tool_name, DEFAULT_TIMEOUTS["default"])


def auto_timeout(
    tool_name: str,
    timeout: Optional[int] = None,
) -> Callable:
    """Decorator to add automatic timeout to async tool functions.
    
    Args:
        tool_name: Name of the tool (for logging and config)
        timeout: Override timeout in seconds (optional)
        
    Returns:
        Decorator that wraps the function with timeout handling
    """
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            effective_timeout = timeout or get_timeout(tool_name)
            
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=effective_timeout,
                )
            except asyncio.TimeoutError:
                return f"Tool '{tool_name}' timed out after {effective_timeout}s"
        
        return wrapper
    
    return decorator


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """Decorator to add retry logic to async functions.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each attempt
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
            
            raise last_exception
        
        return wrapper
    
    return decorator
