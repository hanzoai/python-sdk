"""PostHog analytics integration for Hanzo MCP.

This module provides analytics tracking for:
- Tool usage and performance
- Error tracking and debugging
- Feature adoption and user behavior
- A/B testing and feature flags
"""

import os
import time
import asyncio
import platform
import functools
import traceback
from typing import Any, Dict, TypeVar, Callable, Optional
from datetime import datetime
from dataclasses import dataclass

# Try to import PostHog, but make it optional
try:
    from posthog import Posthog

    POSTHOG_AVAILABLE = True
except ImportError:
    POSTHOG_AVAILABLE = False
    Posthog = None


F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class AnalyticsConfig:
    """Configuration for analytics."""

    api_key: Optional[str] = None
    host: str = "https://us.i.posthog.com"
    enabled: bool = True
    debug: bool = False
    capture_errors: bool = True
    capture_performance: bool = True
    distinct_id: Optional[str] = None


class Analytics:
    """Main analytics class for Hanzo MCP."""

    def __init__(self, config: Optional[AnalyticsConfig] = None):
        """Initialize analytics with configuration."""
        self.config = config or AnalyticsConfig()
        self._client = None

        # Load from environment if not provided
        if not self.config.api_key:
            self.config.api_key = os.environ.get("POSTHOG_API_KEY")

        if not self.config.distinct_id:
            # Use machine ID or generate one
            self.config.distinct_id = self._get_distinct_id()

        # Initialize PostHog if available and configured
        if POSTHOG_AVAILABLE and self.config.api_key and self.config.enabled:
            self._client = Posthog(
                self.config.api_key,
                host=self.config.host,
                debug=self.config.debug,
                enable_exception_autocapture=self.config.capture_errors,
            )

    def _get_distinct_id(self) -> str:
        """Get a distinct ID for this installation."""
        # Try to get from environment
        distinct_id = os.environ.get("HANZO_DISTINCT_ID")
        if distinct_id:
            return distinct_id

        # Use hostname + username as fallback
        import socket
        import getpass

        hostname = socket.gethostname()
        username = getpass.getuser()
        return f"{hostname}:{username}"

    def is_enabled(self) -> bool:
        """Check if analytics is enabled."""
        return bool(self._client and self.config.enabled)

    def capture(self, event: str, properties: Optional[Dict[str, Any]] = None) -> None:
        """Capture an analytics event."""
        if not self.is_enabled():
            return

        try:
            # Add common properties
            props = {
                "timestamp": datetime.utcnow().isoformat(),
                "platform": platform.system(),
                "python_version": platform.python_version(),
                "mcp_version": "0.6.13",  # TODO: Get from package
                **(properties or {}),
            }

            self._client.capture(self.config.distinct_id, event, properties=props)
        except Exception as e:
            if self.config.debug:
                print(f"Analytics error: {e}")

    def identify(self, properties: Optional[Dict[str, Any]] = None) -> None:
        """Identify the current user/installation."""
        if not self.is_enabled():
            return

        try:
            self._client.identify(self.config.distinct_id, properties=properties or {})
        except Exception as e:
            if self.config.debug:
                print(f"Analytics identify error: {e}")

    def track_tool_usage(
        self,
        tool_name: str,
        duration_ms: Optional[float] = None,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track tool usage event."""
        properties = {"tool_name": tool_name, "success": success, **(metadata or {})}

        if duration_ms is not None:
            properties["duration_ms"] = duration_ms

        if error:
            properties["error"] = str(error)

        self.capture("tool_used", properties)

    def track_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Track an error event."""
        if not self.config.capture_errors:
            return

        properties = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_traceback": traceback.format_exc(),
            **(context or {}),
        }

        self.capture("error_occurred", properties)

    def feature_enabled(self, flag_key: str, default: bool = False) -> bool:
        """Check if a feature flag is enabled."""
        if not self.is_enabled():
            return default

        try:
            return self._client.feature_enabled(flag_key, self.config.distinct_id, default=default)
        except Exception:
            return default

    def get_feature_flag(self, flag_key: str, default: Any = None) -> Any:
        """Get feature flag value."""
        if not self.is_enabled():
            return default

        try:
            return self._client.get_feature_flag(flag_key, self.config.distinct_id, default=default)
        except Exception:
            return default

    def flush(self) -> None:
        """Flush any pending events."""
        if self.is_enabled():
            try:
                self._client.flush()
            except Exception:
                pass

    def shutdown(self) -> None:
        """Shutdown analytics client."""
        if self.is_enabled():
            try:
                self._client.shutdown()
            except Exception:
                pass


# Global analytics instance
_analytics = None


def get_analytics() -> Analytics:
    """Get or create the global analytics instance."""
    global _analytics
    if _analytics is None:
        _analytics = Analytics()
    return _analytics


def track_event(event: str, properties: Optional[Dict[str, Any]] = None) -> None:
    """Track a custom event."""
    get_analytics().capture(event, properties)


def track_tool_usage(tool_name: str, **kwargs) -> None:
    """Track tool usage."""
    get_analytics().track_tool_usage(tool_name, **kwargs)


def track_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """Track an error."""
    get_analytics().track_error(error, context)


def with_analytics(tool_name: str):
    """Decorator to track tool usage with analytics."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            error = None
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                track_error(e, {"tool": tool_name})
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                track_tool_usage(
                    tool_name,
                    duration_ms=duration_ms,
                    success=error is None,
                    error=str(error) if error else None,
                )

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            error = None
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                track_error(e, {"tool": tool_name})
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                track_tool_usage(
                    tool_name,
                    duration_ms=duration_ms,
                    success=error is None,
                    error=str(error) if error else None,
                )

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def feature_flag(flag_key: str, default: bool = False):
    """Decorator to conditionally enable features based on flags."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if get_analytics().feature_enabled(flag_key, default):
                return func(*args, **kwargs)
            else:
                raise NotImplementedError(f"Feature '{flag_key}' is not enabled")

        return wrapper

    return decorator


# Tool usage context manager
class ToolUsageTracker:
    """Context manager for tracking tool usage."""

    def __init__(self, tool_name: str, metadata: Optional[Dict[str, Any]] = None):
        self.tool_name = tool_name
        self.metadata = metadata or {}
        self.start_time = None
        self.error = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        success = exc_type is None

        if exc_type:
            self.error = str(exc_val)
            track_error(exc_val, {"tool": self.tool_name, **self.metadata})

        track_tool_usage(
            self.tool_name,
            duration_ms=duration_ms,
            success=success,
            error=self.error,
            metadata=self.metadata,
        )

        # Don't suppress exceptions
        return False


# Async context manager version
class AsyncToolUsageTracker:
    """Async context manager for tracking tool usage."""

    def __init__(self, tool_name: str, metadata: Optional[Dict[str, Any]] = None):
        self.tool_name = tool_name
        self.metadata = metadata or {}
        self.start_time = None
        self.error = None

    async def __aenter__(self):
        self.start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        success = exc_type is None

        if exc_type:
            self.error = str(exc_val)
            track_error(exc_val, {"tool": self.tool_name, **self.metadata})

        track_tool_usage(
            self.tool_name,
            duration_ms=duration_ms,
            success=success,
            error=self.error,
            metadata=self.metadata,
        )

        # Don't suppress exceptions
        return False
