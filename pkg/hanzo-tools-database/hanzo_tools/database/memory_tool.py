"""Unified memory tool with hybrid storage backend.

Combines plaintext markdown files, SQLite FTS, and vector search.
"""

import os
from typing import (
    Any,
    Dict,
    Unpack,
    Optional,
    Annotated,
    TypedDict,
    final,
    override,
)

from pydantic import Field
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, PermissionManager, auto_timeout

from .memory_manager import MemoryManager

# Parameter types
Action = Annotated[
    str,
    Field(
        description="Memory action: read, write, append, search, create, list, stats",
        default="search",
    ),
]

Content = Annotated[
    Optional[str],
    Field(
        description="Content to store or search query",
        default=None,
    ),
]

FilePath = Annotated[
    Optional[str],
    Field(
        description="Markdown file path (e.g., 'rules.md', 'sessions/today.md')",
        default=None,
    ),
]

Category = Annotated[
    Optional[str],
    Field(
        description="Memory category for organization",
        default=None,
    ),
]

Scope = Annotated[
    str,
    Field(
        description="Memory scope: global, project, or both",
        default="project",
    ),
]

SearchType = Annotated[
    str,
    Field(
        description="Search type: fulltext, vector, or hybrid",
        default="fulltext",
    ),
]

Importance = Annotated[
    int,
    Field(
        description="Memory importance (1-10)",
        default=5,
    ),
]

Limit = Annotated[
    int,
    Field(
        description="Maximum results to return",
        default=10,
    ),
]


class MemoryParams(TypedDict, total=False):
    """Parameters for memory tool."""

    action: str
    content: Optional[str]
    file_path: Optional[str]
    category: Optional[str]
    scope: str
    search_type: str
    importance: int
    limit: int


@final
class MemoryTool(BaseTool):
    """Unified memory tool with hybrid storage."""

    def __init__(self, permission_manager: PermissionManager):
        """Initialize the memory tool."""
        super().__init__(permission_manager)
        self.memory_manager = MemoryManager(permission_manager)

    @property
    @override
    def name(self) -> str:
        """Get the tool name."""
        return "memory"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Hybrid memory management. Actions: read, write, append, search, create, list, stats.

Storage types:
- Markdown files: Human-readable rule/context files
- SQLite FTS: Full-text search across all content
- Vector search: Semantic similarity (when available)

Usage:
memory --action read --file-path rules.md --scope global
memory --action write --file-path architecture.md --content "..." 
memory --action append --file-path sessions/today.md --content "New insight"
memory --action search --content "database design" --scope both
memory --action create --content "Important fact" --category general
memory --action list --scope project
memory --action stats
"""

    @override
    @auto_timeout("memory")
    async def call(
        self,
        ctx: MCPContext,
        **params: Unpack[MemoryParams],
    ) -> str:
        """Execute memory operation."""
        tool_ctx = self.create_tool_context(ctx)

        # Extract action
        action = params.get("action", "search")
        
        # Get current working directory for project context
        project_path = os.getcwd()

        # Route to appropriate handler
        try:
            if action == "read":
                return await self._handle_read(params, project_path, tool_ctx)
            elif action == "write":
                return await self._handle_write(params, project_path, tool_ctx)
            elif action == "append":
                return await self._handle_append(params, project_path, tool_ctx)
            elif action == "search":
                return await self._handle_search(params, project_path, tool_ctx)
            elif action == "create":
                return await self._handle_create(params, project_path, tool_ctx)
            elif action == "list":
                return await self._handle_list(params, project_path, tool_ctx)
            elif action == "stats":
                return await self._handle_stats(params, project_path, tool_ctx)
            else:
                return f"Error: Unknown action '{action}'. Valid actions: read, write, append, search, create, list, stats"
                
        except Exception as e:
            await tool_ctx.error(f"Memory operation failed: {str(e)}")
            return f"Error: {str(e)}"

    async def _handle_read(self, params: Dict[str, Any], project_path: str, tool_ctx) -> str:
        """Read markdown memory file."""
        file_path = params.get("file_path")
        if not file_path:
            return "Error: file_path required for read action"

        scope = params.get("scope", "project")
        
        content = self.memory_manager.read_markdown_file(file_path, scope, project_path)
        
        if content is None:
            return f"Error: File '{file_path}' not found in {scope} scope"
            
        await tool_ctx.info(f"Read {scope} memory file: {file_path}")
        
        return f"=== {file_path} ({scope}) ===\n\n{content}"

    async def _handle_write(self, params: Dict[str, Any], project_path: str, tool_ctx) -> str:
        """Write markdown memory file."""
        file_path = params.get("file_path")
        content = params.get("content")
        
        if not file_path:
            return "Error: file_path required for write action"
        if not content:
            return "Error: content required for write action"

        scope = params.get("scope", "project")
        category = params.get("category")
        
        success = self.memory_manager.write_markdown_file(
            file_path, content, scope, project_path, category
        )
        
        if success:
            await tool_ctx.info(f"Wrote {scope} memory file: {file_path}")
            return f"Successfully wrote {scope} memory file: {file_path}"
        else:
            return f"Error: Failed to write memory file: {file_path}"

    async def _handle_append(self, params: Dict[str, Any], project_path: str, tool_ctx) -> str:
        """Append to markdown memory file."""
        file_path = params.get("file_path")
        content = params.get("content")
        
        if not file_path:
            return "Error: file_path required for append action"
        if not content:
            return "Error: content required for append action"

        scope = params.get("scope", "project")
        category = params.get("category")
        
        success = self.memory_manager.append_markdown_file(
            file_path, content, scope, project_path, category
        )
        
        if success:
            await tool_ctx.info(f"Appended to {scope} memory file: {file_path}")
            return f"Successfully appended to {scope} memory file: {file_path}"
        else:
            return f"Error: Failed to append to memory file: {file_path}"

    async def _handle_search(self, params: Dict[str, Any], project_path: str, tool_ctx) -> str:
        """Search across all memory types."""
        query = params.get("content")
        if not query:
            return "Error: content (search query) required for search action"

        scope = params.get("scope", "both")
        search_type = params.get("search_type", "fulltext")
        limit = params.get("limit", 10)
        
        results = self.memory_manager.search_memories(
            query, scope, project_path, search_type, limit
        )
        
        if not results:
            return f"No memories found for query: '{query}'"
            
        # Format results
        output = [f"=== Memory Search Results for '{query}' ==="]
        output.append(f"Found {len(results)} results (scope: {scope})\n")
        
        for i, result in enumerate(results, 1):
            source = result["source"]
            scope_name = result["scope"]
            
            if source == "markdown":
                output.append(f"{i}. [{scope_name}] {result['path']} (markdown)")
                if "snippet" in result:
                    output.append(f"   {result['snippet']}")
                output.append(f"   Category: {result.get('category', 'none')}")
                output.append(f"   Modified: {result['modified_at']}")
                
            elif source == "memory":
                output.append(f"{i}. [{scope_name}] Memory #{result['id']} (structured)")
                if "snippet" in result:
                    output.append(f"   {result['snippet']}")
                output.append(f"   Category: {result.get('category', 'none')}")
                output.append(f"   Importance: {result['importance']}")
                output.append(f"   Created: {result['created_at']}")
                
            output.append("")
            
        await tool_ctx.info(f"Found {len(results)} memories for: {query}")
        
        return "\n".join(output)

    async def _handle_create(self, params: Dict[str, Any], project_path: str, tool_ctx) -> str:
        """Create structured memory record."""
        content = params.get("content")
        if not content:
            return "Error: content required for create action"

        scope = params.get("scope", "project")
        category = params.get("category")
        importance = params.get("importance", 5)
        
        memory_id = self.memory_manager.create_memory(
            content, category, importance, None, scope, project_path
        )
        
        await tool_ctx.info(f"Created {scope} memory: #{memory_id}")
        
        return f"Successfully created {scope} memory #{memory_id}\nContent: {content[:100]}..."

    async def _handle_list(self, params: Dict[str, Any], project_path: str, tool_ctx) -> str:
        """List memory files and records."""
        scope = params.get("scope", "both")
        
        # List markdown files
        markdown_files = self.memory_manager.list_markdown_files(scope, project_path)
        
        output = [f"=== Memory Files ({scope} scope) ==="]
        
        if markdown_files:
            output.append("\nMarkdown Files:")
            for file_info in markdown_files:
                size_kb = file_info["size"] / 1024
                output.append(
                    f"  [{file_info['scope']}] {file_info['path']} "
                    f"({size_kb:.1f}KB, {file_info['modified']})"
                )
        else:
            output.append("\nNo markdown files found")
            
        # Get stats for structured memories
        stats = self.memory_manager.get_memory_stats(scope, project_path)
        
        output.append(f"\nStructured Memories:")
        if scope in ("global", "both"):
            output.append(f"  Global: {stats['structured_memories']['global']} records")
        if scope in ("project", "both"):
            output.append(f"  Project: {stats['structured_memories']['project']} records")
            
        total_size_mb = stats["total_size_bytes"] / 1024 / 1024
        output.append(f"\nTotal size: {total_size_mb:.2f}MB")
        
        return "\n".join(output)

    async def _handle_stats(self, params: Dict[str, Any], project_path: str, tool_ctx) -> str:
        """Get detailed memory statistics."""
        scope = params.get("scope", "both")
        
        stats = self.memory_manager.get_memory_stats(scope, project_path)
        
        output = [f"=== Memory System Statistics ({scope} scope) ==="]
        output.append(f"Project: {project_path}\n")
        
        # Markdown files
        output.append("Markdown Files:")
        output.append(f"  Global: {stats['markdown_files']['global']} files")
        output.append(f"  Project: {stats['markdown_files']['project']} files")
        
        # Structured memories
        output.append("\nStructured Memories:")
        output.append(f"  Global: {stats['structured_memories']['global']} records")
        output.append(f"  Project: {stats['structured_memories']['project']} records")
        
        # Vector embeddings
        output.append("\nVector Embeddings:")
        output.append(f"  Global: {stats['vector_embeddings']['global']} embeddings")
        output.append(f"  Project: {stats['vector_embeddings']['project']} embeddings")
        
        # Storage size
        total_size_mb = stats["total_size_bytes"] / 1024 / 1024
        output.append(f"\nTotal Storage: {total_size_mb:.2f}MB")
        
        # Features status
        output.append("\nFeature Status:")
        output.append("  ✓ Markdown files")
        output.append("  ✓ SQLite FTS5 full-text search")
        
        # Check sqlite-vec availability
        try:
            import sqlite3
            conn = sqlite3.connect(":memory:")
            conn.enable_load_extension(True)
            conn.load_extension("vec0")
            output.append("  ✓ sqlite-vec vector search")
            conn.close()
        except Exception:
            output.append("  ✗ sqlite-vec vector search (not available)")
        
        return "\n".join(output)

    def register(self, mcp_server) -> None:
        """Register this tool with the MCP server."""
        pass