"""Type definitions for Hanzo MCP tools."""

from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class MCPResourceDocument:
    """Resource document returned by MCP tools.

    Output format options:
    - to_json_string(): Clean JSON without outer wrapper (default)
    - to_readable_string(): Human-readable formatted text
    - to_dict(): Full dict structure with data/metadata
    """

    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format with data/metadata structure."""
        result = {"data": self.data}
        if self.metadata:
            result["metadata"] = self.metadata
        return result

    def to_json_string(self) -> str:
        """Convert to clean JSON string - just the data, no wrapper."""
        import json

        # Return just the data content directly, no wrapper
        return json.dumps(self.data, indent=2)

    def to_readable_string(self) -> str:
        """Convert to human-readable formatted string for display."""
        import json

        lines = []

        # Format the main data
        if isinstance(self.data, dict):
            # Handle common result structures
            if "results" in self.data:
                results = self.data["results"]
                stats = self.data.get("stats", {})
                pagination = self.data.get("pagination", {})

                # Header with stats
                if stats:
                    query = stats.get("query", "")
                    total = stats.get("total", len(results))
                    time_ms = stats.get("time_ms", {})
                    if time_ms:
                        total_time = sum(time_ms.values()) if isinstance(time_ms, dict) else time_ms
                        lines.append(f"# Search: '{query}' ({total} results, {total_time}ms)")
                    else:
                        lines.append(f"# Found {total} results")
                    lines.append("")

                # Results
                for i, result in enumerate(results[:50], 1):  # Limit display
                    if isinstance(result, dict):
                        file_path = result.get("file", result.get("path", ""))
                        line = result.get("line", "")
                        match = result.get("match", result.get("text", ""))
                        rtype = result.get("type", "")

                        if file_path:
                            loc = f"{file_path}:{line}" if line else file_path
                            lines.append(f"{i}. {loc}")
                            if match:
                                # Truncate long matches
                                match_preview = match[:200] + "..." if len(match) > 200 else match
                                lines.append(f"   {match_preview}")
                            if rtype:
                                lines.append(f"   [{rtype}]")
                        else:
                            lines.append(f"{i}. {json.dumps(result)}")
                    else:
                        lines.append(f"{i}. {result}")

                # Pagination info
                if pagination:
                    page = pagination.get("page", 1)
                    total = pagination.get("total", 0)
                    has_next = pagination.get("has_next", False)
                    if has_next:
                        lines.append(f"\n... showing page {page} of {(total // 50) + 1}")
            else:
                # Generic dict - format as key-value pairs
                for key, value in self.data.items():
                    if isinstance(value, (dict, list)):
                        lines.append(f"{key}:")
                        lines.append(json.dumps(value, indent=2))
                    else:
                        lines.append(f"{key}: {value}")
        else:
            # Non-dict data - just dump as JSON
            lines.append(json.dumps(self.data, indent=2))

        # Add metadata footer if present
        if self.metadata:
            lines.append("")
            lines.append("---")
            for key, value in self.metadata.items():
                lines.append(f"{key}: {value}")

        return "\n".join(lines)
