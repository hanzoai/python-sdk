"""Test helper classes for MCP tools testing."""

from typing import Any, Dict, List, Optional


class PaginatedResponseWrapper:
    """Wrapper class for paginated responses to support tests."""

    def __init__(
        self,
        items: Optional[List[Any]] = None,
        next_cursor: Optional[str] = None,
        has_more: bool = False,
        total_items: Optional[int] = None,
    ) -> None:
        """Initialize paginated response."""
        self.items: List[Any] = items or []
        self.next_cursor: Optional[str] = next_cursor
        self.has_more: bool = has_more
        self.total_items: int = total_items or len(self.items)

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
def PaginatedResponse(
    items: Optional[List[Any]] = None,
    next_cursor: Optional[str] = None,
    has_more: bool = False,
    total_items: Optional[int] = None,
) -> PaginatedResponseWrapper:
    """Create a paginated response for testing."""
    return PaginatedResponseWrapper(items, next_cursor, has_more, total_items)
