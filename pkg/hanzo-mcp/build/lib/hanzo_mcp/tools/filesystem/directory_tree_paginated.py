"""Paginated directory tree tool implementation.

This module provides a paginated version of DirectoryTreeTool that supports
MCP cursor-based pagination for large directory structures.
"""

from typing import (
    Any,
    Dict,
    List,
    Unpack,
    Optional,
    Annotated,
    TypedDict,
    final,
    override,
)
from pathlib import Path

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.filesystem.base import FilesystemBaseTool
from hanzo_mcp.tools.common.pagination import (
    CursorManager,
    paginate_list,
)

DirectoryPath = Annotated[
    str,
    Field(
        description="The path to the directory to view",
        title="Path",
    ),
]

Depth = Annotated[
    int,
    Field(
        default=3,
        description="The maximum depth to traverse (0 for unlimited)",
        title="Depth",
    ),
]

IncludeFiltered = Annotated[
    bool,
    Field(
        default=False,
        description="Include directories that are normally filtered",
        title="Include Filtered",
    ),
]

PageSize = Annotated[
    int,
    Field(
        default=100,
        description="Number of entries per page",
        title="Page Size",
    ),
]

Cursor = Annotated[
    Optional[str],
    Field(
        default=None,
        description="Pagination cursor for continuing from previous request",
        title="Cursor",
    ),
]


class DirectoryTreePaginatedParams(TypedDict):
    """Parameters for the paginated DirectoryTreeTool.

    Attributes:
        path: The path to the directory to view
        depth: The maximum depth to traverse (0 for unlimited)
        include_filtered: Include directories that are normally filtered
        page_size: Number of entries per page
        cursor: Pagination cursor
    """

    path: DirectoryPath
    depth: Depth
    include_filtered: IncludeFiltered
    page_size: PageSize
    cursor: Cursor


@final
class DirectoryTreePaginatedTool(FilesystemBaseTool):
    """Tool for viewing directory structure as a tree with pagination support."""

    @property
    @override
    def name(self) -> str:
        """Get the tool name."""
        return "directory_tree_paginated"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Get a paginated recursive tree view of files and directories.

This is a paginated version of directory_tree that supports cursor-based pagination
for large directory structures. Returns a structured view with files and subdirectories.

Directories are marked with trailing slashes. Common development directories like
.git, node_modules, and venv are noted but not traversed unless explicitly requested.

Use the cursor field to continue from where the previous request left off.
Returns nextCursor if more entries are available."""

    @override
    async def call(
        self,
        ctx: MCPContext,
        **params: Unpack[DirectoryTreePaginatedParams],
    ) -> Dict[str, Any]:
        """Execute the tool with the given parameters.

        Args:
            ctx: MCP context
            **params: Tool parameters

        Returns:
            Dictionary with entries and optional nextCursor
        """
        tool_ctx = self.create_tool_context(ctx)

        # Extract parameters
        path: DirectoryPath = params["path"]
        depth = params.get("depth", 3)
        include_filtered = params.get("include_filtered", False)
        page_size = params.get("page_size", 100)
        cursor = params.get("cursor")

        # Validate cursor if provided
        if cursor:
            cursor_data = CursorManager.parse_cursor(cursor)
            if not cursor_data:
                await tool_ctx.error("Invalid cursor provided")
                return {"error": "Invalid cursor"}

        # Validate path parameter
        path_validation = self.validate_path(path)
        if path_validation.is_error:
            await tool_ctx.error(path_validation.error_message)
            return {"error": path_validation.error_message}

        await tool_ctx.info(f"Getting paginated directory tree: {path} (depth: {depth}, page_size: {page_size})")

        # Check if path is allowed
        allowed, error_msg = await self.check_path_allowed(path, tool_ctx)
        if not allowed:
            return {"error": error_msg}

        try:
            dir_path = Path(path)

            # Check if path exists
            exists, error_msg = await self.check_path_exists(path, tool_ctx)
            if not exists:
                return {"error": error_msg}

            # Check if path is a directory
            is_dir, error_msg = await self.check_is_directory(path, tool_ctx)
            if not is_dir:
                return {"error": error_msg}

            # Define filtered directories
            FILTERED_DIRECTORIES = {
                ".git",
                "node_modules",
                ".venv",
                "venv",
                "__pycache__",
                ".pytest_cache",
                ".idea",
                ".vs",
                ".vscode",
                "dist",
                "build",
                "target",
                ".ruff_cache",
                ".llm-context",
            }

            # Check if a directory should be filtered
            def should_filter(current_path: Path) -> bool:
                if str(current_path.absolute()) == str(dir_path.absolute()):
                    return False
                return current_path.name in FILTERED_DIRECTORIES and not include_filtered

            # Collect all entries in a flat list for pagination
            all_entries: List[Dict[str, Any]] = []

            # Build the tree and collect entries
            def collect_entries(current_path: Path, current_depth: int = 0, parent_path: str = "") -> None:
                """Collect entries in a flat list for pagination."""
                if not self.is_path_allowed(str(current_path)):
                    return

                try:
                    # Sort entries: directories first, then files alphabetically
                    entries = sorted(current_path.iterdir(), key=lambda x: (not x.is_dir(), x.name))

                    for entry in entries:
                        if not self.is_path_allowed(str(entry)):
                            continue

                        # Calculate relative path for display
                        relative_path = f"{parent_path}/{entry.name}" if parent_path else entry.name

                        if entry.is_dir():
                            entry_data: Dict[str, Any] = {
                                "path": relative_path,
                                "type": "directory",
                                "depth": current_depth,
                            }

                            # Check if we should filter this directory
                            if should_filter(entry):
                                entry_data["skipped"] = "filtered-directory"
                                all_entries.append(entry_data)
                                continue

                            # Check depth limit
                            if depth > 0 and current_depth >= depth:
                                entry_data["skipped"] = "depth-limit"
                                all_entries.append(entry_data)
                                continue

                            # Add directory entry
                            all_entries.append(entry_data)

                            # Process children recursively
                            collect_entries(entry, current_depth + 1, relative_path)
                        else:
                            # Add file entry
                            if depth <= 0 or current_depth < depth:
                                all_entries.append(
                                    {
                                        "path": relative_path,
                                        "type": "file",
                                        "depth": current_depth,
                                    }
                                )

                except Exception as e:
                    await tool_ctx.warning(f"Error processing {current_path}: {str(e)}")

            # Collect all entries
            await tool_ctx.info("Collecting directory entries...")
            collect_entries(dir_path)

            # Paginate the results
            paginated = paginate_list(all_entries, cursor, page_size)

            # Format the paginated entries for display
            formatted_entries = []
            for entry in paginated.items:
                indent = "  " * entry["depth"]
                if entry["type"] == "directory":
                    if "skipped" in entry:
                        formatted_entries.append(
                            {
                                "entry": f"{indent}{entry['path'].split('/')[-1]}/ [skipped - {entry['skipped']}]",
                                "type": "directory",
                                "skipped": entry.get("skipped"),
                            }
                        )
                    else:
                        formatted_entries.append(
                            {
                                "entry": f"{indent}{entry['path'].split('/')[-1]}/",
                                "type": "directory",
                            }
                        )
                else:
                    formatted_entries.append(
                        {
                            "entry": f"{indent}{entry['path'].split('/')[-1]}",
                            "type": "file",
                        }
                    )

            # Build response
            response = {
                "entries": formatted_entries,
                "total_collected": len(all_entries),
                "page_size": page_size,
                "current_page_count": len(formatted_entries),
            }

            # Add next cursor if available
            if paginated.next_cursor:
                response["nextCursor"] = paginated.next_cursor

            await tool_ctx.info(
                f"Returning page with {len(formatted_entries)} entries"
                f"{' (more available)' if paginated.next_cursor else ' (end of results)'}"
            )

            return response

        except Exception as e:
            await tool_ctx.error(f"Error generating directory tree: {str(e)}")
            return {"error": f"Error generating directory tree: {str(e)}"}

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register this paginated directory tree tool with the MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def directory_tree_paginated(
            path: DirectoryPath,
            depth: Depth = 3,
            include_filtered: IncludeFiltered = False,
            page_size: PageSize = 100,
            cursor: Cursor = None,
            ctx: MCPContext = None,
        ) -> Dict[str, Any]:
            return await tool_self.call(
                ctx,
                path=path,
                depth=depth,
                include_filtered=include_filtered,
                page_size=page_size,
                cursor=cursor,
            )


# Create the tool instance
directory_tree_paginated_tool = DirectoryTreePaginatedTool()
