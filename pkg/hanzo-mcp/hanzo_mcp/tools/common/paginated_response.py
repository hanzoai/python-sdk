"""Automatic pagination response wrapper for MCP tools.

This module provides utilities to automatically paginate tool responses
when they exceed token limits.
"""

import json
from typing import Any, Dict, List, Union, Optional

from hanzo_mcp.tools.common.truncate import estimate_tokens
from hanzo_mcp.tools.common.pagination import CursorManager


class AutoPaginatedResponse:
    """Automatically paginate responses that exceed token limits."""

    # MCP token limit with safety buffer
    MAX_TOKENS = 20000  # Leave 5k buffer from 25k limit

    @staticmethod
    def create_response(
        content: Union[str, Dict[str, Any], List[Any]],
        cursor: Optional[str] = None,
        max_tokens: int = MAX_TOKENS,
    ) -> Dict[str, Any]:
        """Create a response that automatically paginates if too large.

        Args:
            content: The content to return
            cursor: Optional cursor from request
            max_tokens: Maximum tokens allowed in response

        Returns:
            Dict with content and optional nextCursor
        """
        # Handle different content types
        if isinstance(content, str):
            return AutoPaginatedResponse._handle_string_response(
                content, cursor, max_tokens
            )
        elif isinstance(content, list):
            return AutoPaginatedResponse._handle_list_response(
                content, cursor, max_tokens
            )
        elif isinstance(content, dict):
            # If dict already has pagination info, return as-is
            if "nextCursor" in content or "cursor" in content:
                return content
            # Otherwise treat as single item
            return AutoPaginatedResponse._handle_dict_response(
                content, cursor, max_tokens
            )
        else:
            # Convert to string for other types
            return AutoPaginatedResponse._handle_string_response(
                str(content), cursor, max_tokens
            )

    @staticmethod
    def _handle_string_response(
        content: str, cursor: Optional[str], max_tokens: int
    ) -> Dict[str, Any]:
        """Handle pagination for string responses."""
        # Parse cursor to get offset
        offset = 0
        if cursor:
            cursor_data = CursorManager.parse_cursor(cursor)
            if cursor_data and "offset" in cursor_data:
                offset = cursor_data["offset"]

        # For strings, paginate by lines
        lines = content.split("\n")

        if offset >= len(lines):
            return {"content": "", "message": "No more content"}

        # Build response line by line, checking tokens
        result_lines = []
        current_tokens = 0
        line_index = offset

        # Add header if this is a continuation
        if offset > 0:
            header = f"[Continued from line {offset + 1}]\n"
            current_tokens = estimate_tokens(header)
            result_lines.append(header)

        while line_index < len(lines):
            line = lines[line_index]
            line_tokens = estimate_tokens(line + "\n")

            # Check if adding this line would exceed limit
            if current_tokens + line_tokens > max_tokens:
                # Need to paginate
                if not result_lines:
                    # Single line too long, truncate it
                    truncated_line = line[:1000] + "... [line truncated]"
                    result_lines.append(truncated_line)
                    line_index += 1
                break

            result_lines.append(line)
            current_tokens += line_tokens
            line_index += 1

        # Build response
        response = {"content": "\n".join(result_lines)}

        # Add pagination info
        if line_index < len(lines):
            response["nextCursor"] = CursorManager.create_offset_cursor(line_index)
            response["pagination_info"] = {
                "current_lines": f"{offset + 1}-{line_index}",
                "total_lines": len(lines),
                "has_more": True,
            }
        else:
            response["pagination_info"] = {
                "current_lines": f"{offset + 1}-{len(lines)}",
                "total_lines": len(lines),
                "has_more": False,
            }

        return response

    @staticmethod
    def _handle_list_response(
        items: List[Any], cursor: Optional[str], max_tokens: int
    ) -> Dict[str, Any]:
        """Handle pagination for list responses."""
        # Parse cursor to get offset
        offset = 0
        if cursor:
            cursor_data = CursorManager.parse_cursor(cursor)
            if cursor_data and "offset" in cursor_data:
                offset = cursor_data["offset"]

        if offset >= len(items):
            return {"items": [], "message": "No more items"}

        # Build response item by item, checking tokens
        result_items = []
        current_tokens = 100  # Base overhead
        item_index = offset

        # Add header if continuation
        header_obj = {}
        if offset > 0:
            header_obj["continuation_from"] = offset
            current_tokens += 50

        while item_index < len(items):
            item = items[item_index]

            # Estimate tokens for this item
            item_str = json.dumps(item) if not isinstance(item, str) else item
            item_tokens = estimate_tokens(item_str)

            # Check if adding this item would exceed limit
            if current_tokens + item_tokens > max_tokens:
                if not result_items:
                    # Single item too large, truncate it
                    if isinstance(item, str):
                        truncated = item[:5000] + "... [truncated]"
                        result_items.append(truncated)
                    else:
                        result_items.append(
                            {"error": "Item too large", "index": item_index}
                        )
                    item_index += 1
                break

            result_items.append(item)
            current_tokens += item_tokens
            item_index += 1

        # Build response
        response = {"items": result_items}

        if header_obj:
            response.update(header_obj)

        # Add pagination info
        if item_index < len(items):
            response["nextCursor"] = CursorManager.create_offset_cursor(item_index)
            response["pagination_info"] = {
                "returned_items": len(result_items),
                "total_items": len(items),
                "has_more": True,
                "next_index": item_index,
            }
        else:
            response["pagination_info"] = {
                "returned_items": len(result_items),
                "total_items": len(items),
                "has_more": False,
            }

        return response

    @staticmethod
    def _handle_dict_response(
        content: Dict[str, Any], cursor: Optional[str], max_tokens: int
    ) -> Dict[str, Any]:
        """Handle pagination for dict responses."""
        # For dicts, check if it's too large as-is
        content_str = json.dumps(content, indent=2)
        content_tokens = estimate_tokens(content_str)

        if content_tokens <= max_tokens:
            # Fits within limit
            return content

        # Too large - need to paginate
        # Strategy: Convert to key-value pairs and paginate
        items = list(content.items())
        offset = 0

        if cursor:
            cursor_data = CursorManager.parse_cursor(cursor)
            if cursor_data and "offset" in cursor_data:
                offset = cursor_data["offset"]

        if offset >= len(items):
            return {"content": {}, "message": "No more content"}

        # Build paginated dict
        result = {}
        current_tokens = 100  # Base overhead

        for i in range(offset, len(items)):
            key, value = items[i]

            # Estimate tokens for this entry
            entry_str = json.dumps({key: value})
            entry_tokens = estimate_tokens(entry_str)

            if current_tokens + entry_tokens > max_tokens:
                if not result:
                    # Single entry too large
                    result[key] = "[Value too large - use specific key access]"
                break

            result[key] = value
            current_tokens += entry_tokens

        # Wrap in response
        response = {"content": result}

        # Add pagination info
        processed = offset + len(result)
        if processed < len(items):
            response["nextCursor"] = CursorManager.create_offset_cursor(processed)
            response["pagination_info"] = {
                "keys_returned": len(result),
                "total_keys": len(items),
                "has_more": True,
            }
        else:
            response["pagination_info"] = {
                "keys_returned": len(result),
                "total_keys": len(items),
                "has_more": False,
            }

        return response


def paginate_if_needed(
    response: Any, cursor: Optional[str] = None, force_pagination: bool = False
) -> Union[str, Dict[str, Any]]:
    """Wrap a response with automatic pagination if needed.

    Args:
        response: The response to potentially paginate
        cursor: Optional cursor from request
        force_pagination: Force pagination even for small responses

    Returns:
        Original response if small enough, otherwise paginated dict
    """
    # Quick check - if response is already paginated, return as-is
    if isinstance(response, dict) and (
        "nextCursor" in response or "pagination_info" in response
    ):
        return response

    # For small responses, don't paginate unless forced
    if not force_pagination:
        try:
            response_str = (
                json.dumps(response) if not isinstance(response, str) else response
            )
            if len(response_str) < 10000:  # Quick heuristic
                return response
        except Exception:
            pass

    # Create paginated response
    return AutoPaginatedResponse.create_response(response, cursor)
