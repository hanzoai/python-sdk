"""Type definitions for Hanzo tool packages."""

import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class MCPResourceDocument:
    """Resource document returned by MCP tools.

    Output format options:
    - to_json_string(): Clean JSON format (default for structured data)
    - to_readable_string(): Human-readable formatted text for display
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
        """Convert to clean JSON string."""
        # Return wrapped in "result" for consistency
        return json.dumps({"result": self.data}, indent=2)

    def to_readable_string(self) -> str:
        """Convert to human-readable formatted string for display.

        Optimized for readability in Claude Code output panels.
        """
        lines: List[str] = []

        if isinstance(self.data, dict):
            # Handle search/find results with "results" array
            if "results" in self.data:
                results = self.data["results"]
                stats = self.data.get("stats", {})
                pagination = self.data.get("pagination", {})

                # Header with stats
                if stats:
                    query = stats.get("query", stats.get("pattern", ""))
                    total = stats.get("total", len(results))
                    time_ms = stats.get("time_ms", {})
                    if time_ms:
                        if isinstance(time_ms, dict):
                            total_time = sum(time_ms.values())
                        else:
                            total_time = time_ms
                        lines.append(f"# Search: '{query}' ({total} results, {total_time}ms)")
                    else:
                        lines.append(f"# Found {total} results for '{query}'")
                else:
                    lines.append(f"# Found {len(results)} results")
                lines.append("")

                # Format each result
                for i, result in enumerate(results[:50], 1):
                    if isinstance(result, dict):
                        # Common patterns for search results
                        file_path = result.get("file", result.get("path", ""))
                        line_num = result.get("line", result.get("line_number", ""))
                        match_text = result.get("match", result.get("text", result.get("content", "")))
                        result_type = result.get("type", "")

                        if file_path:
                            loc = f"{file_path}:{line_num}" if line_num else file_path
                            lines.append(f"{i}. {loc}")
                            if match_text:
                                # Truncate long matches for readability
                                preview = match_text[:200] + "..." if len(match_text) > 200 else match_text
                                lines.append(f"   {preview}")
                            if result_type:
                                lines.append(f"   [{result_type}]")
                        else:
                            lines.append(f"{i}. {json.dumps(result, default=str)}")
                    else:
                        lines.append(f"{i}. {result}")

                # Show pagination info
                if pagination:
                    page = pagination.get("page", 1)
                    total = pagination.get("total", 0)
                    has_next = pagination.get("has_next", False)
                    if has_next and total > 0:
                        total_pages = (total // 50) + 1
                        lines.append(f"\n... page {page} of {total_pages} ({total} total)")

            # Handle command execution results
            elif "output" in self.data or "stdout" in self.data or "stderr" in self.data:
                # Shell command output
                exit_code = self.data.get("exit_code", self.data.get("returncode", 0))
                stdout = self.data.get("output", self.data.get("stdout", ""))
                stderr = self.data.get("stderr", "")
                elapsed = self.data.get("elapsed", self.data.get("time_ms", ""))

                if exit_code == 0:
                    lines.append(f"✓ Command succeeded")
                else:
                    lines.append(f"✗ Command failed (exit {exit_code})")

                if elapsed:
                    lines.append(f"Time: {elapsed}ms" if isinstance(elapsed, (int, float)) else f"Time: {elapsed}")
                lines.append("")

                if stdout:
                    lines.append(stdout.rstrip())
                if stderr:
                    lines.append("\n--- stderr ---")
                    lines.append(stderr.rstrip())

            # Handle error results
            elif "error" in self.data:
                lines.append(f"Error: {self.data['error']}")
                if "details" in self.data:
                    lines.append(f"Details: {self.data['details']}")

            # Generic dict - format as key-value pairs
            else:
                for key, value in self.data.items():
                    if isinstance(value, (dict, list)):
                        lines.append(f"{key}:")
                        lines.append(json.dumps(value, indent=2, default=str))
                    else:
                        lines.append(f"{key}: {value}")

        elif isinstance(self.data, list):
            # List data - format as numbered items
            for i, item in enumerate(self.data[:50], 1):
                if isinstance(item, dict):
                    lines.append(f"{i}. {json.dumps(item, default=str)}")
                else:
                    lines.append(f"{i}. {item}")
            if len(self.data) > 50:
                lines.append(f"\n... {len(self.data) - 50} more items")

        else:
            # Scalar or other - just convert to string
            lines.append(str(self.data))

        # Add metadata footer if present
        if self.metadata:
            lines.append("")
            lines.append("---")
            for key, value in self.metadata.items():
                lines.append(f"{key}: {value}")

        return "\n".join(lines)
