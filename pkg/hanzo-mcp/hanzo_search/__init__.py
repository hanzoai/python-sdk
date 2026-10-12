"""`search`: ranked code spans for a natural-language or error-text query, from a local index."""

from __future__ import annotations

from typing import Any

DESCRIPTION = (
    "Find code: the spans of a source tree most relevant to a question or to error text "
    "(a traceback or failing test output works as is), ranked, each as path:start-end and its lines. "
    "Indexes root (default: working directory) once and follows edits. Use before grep/read."
)

SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "root": {"type": "string"},
        "k": {"type": "integer", "default": 5},
    },
    "required": ["query"],
}


def register(mcp: Any) -> None:
    """Add `search` to a FastMCP server; the index loads on the first call."""

    @mcp.tool(name="search", description=DESCRIPTION)
    async def search(query: str, root: str = "", k: int = 5) -> str:
        import asyncio

        from hanzo_search.index import search as run

        return await asyncio.to_thread(run, query, root, k)
