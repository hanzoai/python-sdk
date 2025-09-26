"""FastMCP-compatible pagination implementation.

This module provides pagination utilities optimized for FastMCP with minimal latency.
"""

import json
import time
import base64
import hashlib
from typing import Any, Dict, List, Union, Generic, TypeVar, Optional
from dataclasses import field, dataclass

T = TypeVar("T")


@dataclass
class CursorData:
    """Cursor data structure for efficient pagination."""

    # Primary cursor fields (indexed)
    last_id: Optional[str] = None
    last_timestamp: Optional[float] = None
    offset: int = 0

    # Metadata for validation and optimization
    page_size: int = 100
    sort_field: str = "id"
    sort_order: str = "asc"

    # Security and validation
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    checksum: Optional[str] = None

    def to_cursor(self) -> str:
        """Convert to opaque cursor string."""
        data = {
            "id": self.last_id,
            "ts": self.last_timestamp,
            "o": self.offset,
            "ps": self.page_size,
            "sf": self.sort_field,
            "so": self.sort_order,
            "ca": self.created_at,
        }
        if self.expires_at:
            data["ea"] = self.expires_at

        # Add checksum for integrity
        data_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
        data["cs"] = hashlib.md5(data_str.encode()).hexdigest()[:8]

        # Encode as base64
        final_str = json.dumps(data, separators=(",", ":"))
        return base64.urlsafe_b64encode(final_str.encode()).decode().rstrip("=")

    @classmethod
    def from_cursor(cls, cursor: str) -> Optional["CursorData"]:
        """Parse cursor string back to CursorData."""
        try:
            # Add padding if needed
            padding = 4 - (len(cursor) % 4)
            if padding != 4:
                cursor += "=" * padding

            decoded = base64.urlsafe_b64decode(cursor.encode())
            data = json.loads(decoded)

            # Validate checksum
            checksum = data.pop("cs", None)
            if checksum:
                data_str = json.dumps(
                    {k: v for k, v in data.items() if k != "cs"},
                    sort_keys=True,
                    separators=(",", ":"),
                )
                expected = hashlib.md5(data_str.encode()).hexdigest()[:8]
                if checksum != expected:
                    return None

            # Check expiration
            expires_at = data.get("ea")
            if expires_at and time.time() > expires_at:
                return None

            return cls(
                last_id=data.get("id"),
                last_timestamp=data.get("ts"),
                offset=data.get("o", 0),
                page_size=data.get("ps", 100),
                sort_field=data.get("sf", "id"),
                sort_order=data.get("so", "asc"),
                created_at=data.get("ca", time.time()),
                expires_at=expires_at,
            )
        except Exception:
            return None


class FastMCPPaginator(Generic[T]):
    """High-performance paginator for FastMCP responses."""

    def __init__(
        self,
        page_size: int = 100,
        max_page_size: int = 1000,
        cursor_ttl: int = 3600,  # 1 hour
        enable_prefetch: bool = False,
    ):
        """Initialize the paginator.

        Args:
            page_size: Default page size
            max_page_size: Maximum allowed page size
            cursor_ttl: Cursor time-to-live in seconds
            enable_prefetch: Enable prefetching for next page
        """
        self.page_size = page_size
        self.max_page_size = max_page_size
        self.cursor_ttl = cursor_ttl
        self.enable_prefetch = enable_prefetch
        self._cache: Dict[str, Any] = {}

    def paginate_list(
        self,
        items: List[T],
        cursor: Optional[str] = None,
        page_size: Optional[int] = None,
        sort_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Paginate a list with optimal performance.

        Args:
            items: List to paginate
            cursor: Optional cursor from previous request
            page_size: Override default page size
            sort_key: Sort field for consistent ordering

        Returns:
            Dict with items and optional nextCursor
        """
        # Parse cursor or create new
        cursor_data = CursorData.from_cursor(cursor) if cursor else CursorData()

        # Use provided page size or default
        actual_page_size = min(page_size or cursor_data.page_size or self.page_size, self.max_page_size)

        # Get starting position
        start_idx = cursor_data.offset

        # Validate bounds
        if start_idx >= len(items):
            return {"items": [], "hasMore": False}

        # Slice the page
        end_idx = min(start_idx + actual_page_size, len(items))
        page_items = items[start_idx:end_idx]

        # Build response
        response = {
            "items": page_items,
            "pageInfo": {
                "startIndex": start_idx,
                "endIndex": end_idx,
                "pageSize": len(page_items),
                "totalItems": len(items),
            },
        }

        # Create next cursor if more items exist
        if end_idx < len(items):
            next_cursor_data = CursorData(
                offset=end_idx,
                page_size=actual_page_size,
                expires_at=time.time() + self.cursor_ttl if self.cursor_ttl else None,
            )
            response["nextCursor"] = next_cursor_data.to_cursor()
            response["hasMore"] = True
        else:
            response["hasMore"] = False

        return response

    def paginate_query(
        self,
        query_func,
        cursor: Optional[str] = None,
        page_size: Optional[int] = None,
        **query_params,
    ) -> Dict[str, Any]:
        """Paginate results from a query function.

        This is optimized for database queries using indexed fields.

        Args:
            query_func: Function that accepts (last_id, last_timestamp, limit, **params)
            cursor: Optional cursor
            page_size: Override page size
            **query_params: Additional query parameters

        Returns:
            Paginated response
        """
        # Parse cursor
        cursor_data = CursorData.from_cursor(cursor) if cursor else CursorData()

        # Determine page size
        limit = min(page_size or cursor_data.page_size or self.page_size, self.max_page_size)

        # Execute query with cursor position
        results = query_func(
            last_id=cursor_data.last_id,
            last_timestamp=cursor_data.last_timestamp,
            limit=limit + 1,  # Fetch one extra to detect more
            **query_params,
        )

        # Check if there are more results
        has_more = len(results) > limit
        if has_more:
            results = results[:limit]  # Remove the extra item

        # Build response
        response = {
            "items": results,
            "pageInfo": {"pageSize": len(results), "hasMore": has_more},
        }

        # Create next cursor if needed
        if has_more and results:
            last_item = results[-1]
            next_cursor_data = CursorData(
                last_id=getattr(last_item, "id", None),
                last_timestamp=getattr(last_item, "timestamp", None),
                page_size=limit,
                sort_field=cursor_data.sort_field,
                sort_order=cursor_data.sort_order,
                expires_at=time.time() + self.cursor_ttl if self.cursor_ttl else None,
            )
            response["nextCursor"] = next_cursor_data.to_cursor()

        return response


class TokenAwarePaginator:
    """Paginator that respects token limits for LLM responses."""

    def __init__(self, max_tokens: int = 20000):
        """Initialize token-aware paginator.

        Args:
            max_tokens: Maximum tokens per response
        """
        self.max_tokens = max_tokens
        self.paginator = FastMCPPaginator()

    def paginate_by_tokens(self, items: List[Any], cursor: Optional[str] = None, estimate_func=None) -> Dict[str, Any]:
        """Paginate items based on token count.

        Args:
            items: Items to paginate
            cursor: Optional cursor
            estimate_func: Function to estimate tokens for an item

        Returns:
            Paginated response
        """
        from hanzo_mcp.tools.common.truncate import estimate_tokens

        # Default token estimation
        if not estimate_func:
            estimate_func = lambda x: estimate_tokens(json.dumps(x) if not isinstance(x, str) else x)

        # Parse cursor
        cursor_data = CursorData.from_cursor(cursor) if cursor else CursorData()
        start_idx = cursor_data.offset

        # Build page respecting token limit
        page_items = []
        current_tokens = 100  # Base overhead
        current_idx = start_idx

        while current_idx < len(items) and current_tokens < self.max_tokens:
            item = items[current_idx]
            item_tokens = estimate_func(item)

            # Check if adding this item would exceed limit
            if current_tokens + item_tokens > self.max_tokens and page_items:
                break

            page_items.append(item)
            current_tokens += item_tokens
            current_idx += 1

        # Build response
        response = {
            "items": page_items,
            "pageInfo": {
                "itemCount": len(page_items),
                "estimatedTokens": current_tokens,
                "hasMore": current_idx < len(items),
            },
        }

        # Add next cursor if needed
        if current_idx < len(items):
            next_cursor_data = CursorData(offset=current_idx)
            response["nextCursor"] = next_cursor_data.to_cursor()

        return response


# FastMCP integration helpers
def create_paginated_response(
    items: Union[List[Any], Dict[str, Any], str],
    cursor: Optional[str] = None,
    page_size: int = 100,
    use_token_limit: bool = True,
) -> Dict[str, Any]:
    """Create a paginated response compatible with FastMCP.

    Args:
        items: The items to paginate
        cursor: Optional cursor from request
        page_size: Items per page
        use_token_limit: Whether to use token-based pagination

    Returns:
        FastMCP-compatible paginated response
    """
    if use_token_limit:
        paginator = TokenAwarePaginator()

        # Convert different types to list
        if isinstance(items, str):
            # Split string by lines for pagination
            items = items.split("\n")
        elif isinstance(items, dict):
            # Convert dict to list of key-value pairs
            items = [{"key": k, "value": v} for k, v in items.items()]

        return paginator.paginate_by_tokens(items, cursor)
    else:
        paginator = FastMCPPaginator(page_size=page_size)

        # Handle different input types
        if isinstance(items, list):
            return paginator.paginate_list(items, cursor, page_size)
        else:
            # Convert to list first
            if isinstance(items, str):
                items = items.split("\n")
            elif isinstance(items, dict):
                items = [{"key": k, "value": v} for k, v in items.items()]
            else:
                items = [items]

            return paginator.paginate_list(items, cursor, page_size)
