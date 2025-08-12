"""Type definitions for Hanzo MCP tools."""

from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class MCPResourceDocument:
    """Resource document returned by MCP tools."""

    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {"data": self.data}
        if self.metadata:
            result["metadata"] = self.metadata
        return result

    def to_json_string(self) -> str:
        """Convert to JSON string."""
        import json

        return json.dumps(self.to_dict(), indent=2)
