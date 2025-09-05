"""Test helper classes for MCP tools testing."""

from typing import Any, Dict, List, Optional


class PaginatedResponseWrapper:
    """Wrapper class for paginated responses to support tests."""

    def __init__(self, items=None, next_cursor=None, has_more=False, total_items=None):
        """Initialize paginated response."""
        self.items = items or []
        self.next_cursor = next_cursor
        self.has_more = has_more
        self.total_items = total_items or len(self.items)

    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "items": self.items,
            "_meta": {
                "next_cursor": self.next_cursor,
                "has_more": self.has_more,
                "total_items": self.total_items,
            },
        }


# Export a convenience constructor
def PaginatedResponse(items=None, next_cursor=None, has_more=False, total_items=None):
    """Create a paginated response for testing."""
    return PaginatedResponseWrapper(items, next_cursor, has_more, total_items)
