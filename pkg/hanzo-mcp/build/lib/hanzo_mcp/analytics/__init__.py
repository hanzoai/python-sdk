"""Analytics module for Hanzo MCP using PostHog."""

from .posthog_analytics import Analytics, track_error, track_event, track_tool_usage

__all__ = ["Analytics", "track_event", "track_tool_usage", "track_error"]
