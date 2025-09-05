"""Pagination utilities for MCP tools.

This module provides utilities for implementing cursor-based pagination
according to the MCP pagination protocol.
"""

import json
import base64
from typing import Any, Dict, List, Generic, TypeVar, Optional
from dataclasses import dataclass

T = TypeVar("T")


@dataclass
class PaginationParams:
    """Parameters for pagination."""

    cursor: Optional[str] = None
    page_size: int = 100  # Default page size


@dataclass
class PaginatedResponse(Generic[T]):
    """A paginated response containing items and optional next cursor."""

    items: List[T]
    next_cursor: Optional[str] = None

    def to_dict(self, items_key: str = "items") -> Dict[str, Any]:
        """Convert to dictionary format for MCP response.

        Args:
            items_key: The key to use for items in the response

        Returns:
            Dictionary with items and optional nextCursor
        """
        result = {items_key: self.items}
        if self.next_cursor:
            result["nextCursor"] = self.next_cursor
        return result


class CursorManager:
    """Manages cursor creation and parsing for pagination."""

    @staticmethod
    def create_cursor(data: Dict[str, Any]) -> str:
        """Create an opaque cursor from data.

        Args:
            data: Data to encode in the cursor

        Returns:
            Base64-encoded cursor string
        """
        json_data = json.dumps(data, separators=(",", ":"))
        return base64.b64encode(json_data.encode()).decode()

    @staticmethod
    def parse_cursor(cursor: str) -> Optional[Dict[str, Any]]:
        """Parse a cursor string back to data.

        Args:
            cursor: Base64-encoded cursor string

        Returns:
            Decoded data or None if invalid
        """
        try:
            decoded = base64.b64decode(cursor.encode()).decode()
            return json.loads(decoded)
        except (ValueError, json.JSONDecodeError):
            return None

    @staticmethod
    def create_offset_cursor(offset: int) -> str:
        """Create a cursor for offset-based pagination.

        Args:
            offset: The offset for the next page

        Returns:
            Cursor string
        """
        return CursorManager.create_cursor({"offset": offset})

    @staticmethod
    def parse_offset_cursor(cursor: Optional[str]) -> int:
        """Parse an offset cursor.

        Args:
            cursor: Cursor string or None

        Returns:
            Offset value (0 if cursor is None or invalid)
        """
        if not cursor:
            return 0

        data = CursorManager.parse_cursor(cursor)
        if not data or "offset" not in data:
            return 0

        return int(data["offset"])


class Paginator(Generic[T]):
    """Generic paginator for any list of items."""

    def __init__(self, items: List[T], page_size: int = 100):
        """Initialize paginator.

        Args:
            items: List of items to paginate
            page_size: Number of items per page
        """
        self.items = items
        self.page_size = page_size

    def get_page(self, cursor: Optional[str] = None) -> PaginatedResponse[T]:
        """Get a page of results.

        Args:
            cursor: Optional cursor for the page

        Returns:
            Paginated response with items and next cursor
        """
        offset = CursorManager.parse_offset_cursor(cursor)

        # Get the page of items
        start = offset
        end = min(start + self.page_size, len(self.items))
        page_items = self.items[start:end]

        # Create next cursor if there are more items
        next_cursor = None
        if end < len(self.items):
            next_cursor = CursorManager.create_offset_cursor(end)

        return PaginatedResponse(items=page_items, next_cursor=next_cursor)


class StreamPaginator(Generic[T]):
    """Paginator for streaming/generator-based results."""

    def __init__(self, page_size: int = 100):
        """Initialize stream paginator.

        Args:
            page_size: Number of items per page
        """
        self.page_size = page_size

    def paginate_stream(self, stream_generator, cursor: Optional[str] = None) -> PaginatedResponse[T]:
        """Paginate results from a stream/generator.

        Args:
            stream_generator: Generator function that yields items
            cursor: Optional cursor for resuming

        Returns:
            Paginated response
        """
        items = []
        skip_count = 0

        # Parse cursor to get skip count
        if cursor:
            cursor_data = CursorManager.parse_cursor(cursor)
            if cursor_data and "skip" in cursor_data:
                skip_count = cursor_data["skip"]

        # Skip items based on cursor
        item_count = 0
        for item in stream_generator():
            if item_count < skip_count:
                item_count += 1
                continue

            items.append(item)
            if len(items) >= self.page_size:
                # We have a full page, create cursor for next page
                next_cursor = CursorManager.create_cursor({"skip": skip_count + len(items)})
                return PaginatedResponse(items=items, next_cursor=next_cursor)

        # No more items
        return PaginatedResponse(items=items, next_cursor=None)


def paginate_list(items: List[T], cursor: Optional[str] = None, page_size: int = 100) -> PaginatedResponse[T]:
    """Convenience function to paginate a list.

    Args:
        items: List to paginate
        cursor: Optional cursor
        page_size: Items per page

    Returns:
        Paginated response
    """
    paginator = Paginator(items, page_size)
    return paginator.get_page(cursor)


def validate_cursor(cursor: str) -> bool:
    """Validate that a cursor is properly formatted.

    Args:
        cursor: Cursor string to validate

    Returns:
        True if valid, False otherwise
    """
    return CursorManager.parse_cursor(cursor) is not None
