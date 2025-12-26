"""AST-based code structure search using tree-sitter.

This module provides the ASTTool for searching, indexing, and querying code symbols
using tree-sitter AST parsing. It can find function definitions, class declarations,
and other code structures with full context.
"""

import os
from typing import Unpack, Annotated, TypedDict, final, override
from pathlib import Path

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool

# Lazy import for grep_ast
_tree_context_cls = None


def _get_tree_context():
    """Lazy load TreeContext to avoid import-time overhead."""
    global _tree_context_cls
    if _tree_context_cls is None:
        from grep_ast.grep_ast import TreeContext
        _tree_context_cls = TreeContext
    return _tree_context_cls


# Type annotations for parameters
Pattern = Annotated[
    str,
    Field(
        description="The regex pattern to search for in source code files",
        min_length=1,
    ),
]

SearchPath = Annotated[
    str,
    Field(
        description="The path to search in (file or directory)",
        min_length=1,
    ),
]

IgnoreCase = Annotated[
    bool,
    Field(
        description="Whether to ignore case when matching",
        default=False,
    ),
]

LineNumber = Annotated[
    bool,
    Field(
        description="Whether to display line numbers",
        default=False,
    ),
]


class ASTToolParams(TypedDict, total=False):
    """Parameters for the ASTTool.

    Attributes:
        pattern: The regex pattern to search for in source code files
        path: The path to search in (file or directory)
        ignore_case: Whether to ignore case when matching
        line_number: Whether to display line numbers
    """

    pattern: Pattern
    path: SearchPath
    ignore_case: IgnoreCase
    line_number: LineNumber


# Extensions supported by tree-sitter (common programming languages)
SUPPORTED_EXTENSIONS = {
    '.py', '.pyw',  # Python
    '.js', '.jsx', '.mjs', '.cjs',  # JavaScript
    '.ts', '.tsx', '.mts', '.cts',  # TypeScript
    '.go',  # Go
    '.rs',  # Rust
    '.c', '.h',  # C
    '.cpp', '.cc', '.cxx', '.hpp', '.hh', '.hxx',  # C++
    '.java',  # Java
    '.rb',  # Ruby
    '.php',  # PHP
    '.cs',  # C#
    '.swift',  # Swift
    '.kt', '.kts',  # Kotlin
    '.scala',  # Scala
    '.lua',  # Lua
    '.r', '.R',  # R
    '.jl',  # Julia
    '.ex', '.exs',  # Elixir
    '.erl', '.hrl',  # Erlang
    '.ml', '.mli',  # OCaml
    '.hs',  # Haskell
    '.elm',  # Elm
    '.vue',  # Vue
    '.svelte',  # Svelte
}


@final
class ASTTool(BaseTool):
    """Tool for searching and querying code structures using tree-sitter AST parsing."""

    name = "ast"

    @property
    @override
    def description(self) -> str:
        """Get the tool description.

        Returns:
            Tool description
        """
        return """AST-based code structure search using tree-sitter. Find functions, classes, methods with full context.

Usage:
ast "function_name" ./src
ast "class.*Service" ./src
ast "def test_" ./tests

Searches code structure intelligently, understanding syntax and providing semantic context."""

    def _is_supported_file(self, path: str) -> bool:
        """Check if file has a supported extension for tree-sitter parsing."""
        return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS

    @override
    async def call(
        self,
        ctx: MCPContext,
        **params: Unpack[ASTToolParams],
    ) -> str:
        """Execute the tool with the given parameters.

        Args:
            ctx: MCP context
            **params: Tool parameters

        Returns:
            Tool result
        """
        # Extract parameters
        pattern: str = params["pattern"]
        path: str = params["path"]
        ignore_case = params.get("ignore_case", False)
        line_number = params.get("line_number", False)

        # Expand ~ in path
        path = os.path.expanduser(path)

        # Check if path exists
        path_obj = Path(path)
        if not path_obj.exists():
            return f"Error: Path does not exist: {path}"

        # Get the files to process
        files_to_process = []

        if path_obj.is_file():
            if self._is_supported_file(str(path_obj)):
                files_to_process.append(str(path_obj))
            else:
                return f"Error: File type not supported for AST parsing: {path_obj.suffix}"
        elif path_obj.is_dir():
            for root, _, files in os.walk(path_obj):
                # Skip hidden directories and common non-code directories
                root_path = Path(root)
                if any(part.startswith('.') for part in root_path.parts):
                    continue
                if any(part in ('node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build') 
                       for part in root_path.parts):
                    continue
                    
                for file in files:
                    file_path = Path(root) / file
                    if self._is_supported_file(str(file_path)):
                        files_to_process.append(str(file_path))

        if not files_to_process:
            return f"No source code files found in {path}"

        # Get TreeContext class
        TreeContext = _get_tree_context()

        # Process each file
        results = []
        errors = []

        for file_path in files_to_process:
            try:
                # Read the file
                with open(file_path, "r", encoding="utf-8") as f:
                    code = f.read()

                # Process the file with grep-ast
                try:
                    tc = TreeContext(
                        file_path,
                        code,
                        color=False,
                        verbose=False,
                        line_number=line_number,
                    )

                    # Find matches
                    loi = tc.grep(pattern, ignore_case)

                    if loi:
                        tc.add_lines_of_interest(loi)
                        tc.add_context()
                        output = tc.format()

                        # Add the result to our list
                        results.append(f"\n{file_path}:\n{output}\n")
                except Exception as e:
                    # Skip files that can't be parsed by tree-sitter
                    errors.append(f"Could not parse {file_path}: {str(e)}")
            except UnicodeDecodeError:
                errors.append(f"Could not read {file_path} as text")
            except Exception as e:
                errors.append(f"Error processing {file_path}: {str(e)}")

        if not results:
            error_info = ""
            if errors:
                error_info = f"\n\nErrors encountered:\n" + "\n".join(errors[:5])
                if len(errors) > 5:
                    error_info += f"\n... and {len(errors) - 5} more errors"
            return f"No matches found for '{pattern}' in {path}{error_info}"

        summary = f"Found matches in {len(results)} file(s) (searched {len(files_to_process)} files)"
        return summary + "\n" + "".join(results)

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register this tool with the MCP server.

        Creates a wrapper function with explicitly defined parameters that match
        the tool's parameter schema and registers it with the MCP server.

        Args:
            mcp_server: The FastMCP server instance
        """
        tool_self = self  # Create a reference to self for use in the closure

        @mcp_server.tool(name=self.name, description=self.description)
        async def ast(
            ctx: MCPContext,
            pattern: Pattern,
            path: SearchPath,
            ignore_case: IgnoreCase = False,
            line_number: LineNumber = False,
        ) -> str:
            return await tool_self.call(
                ctx,
                pattern=pattern,
                path=path,
                ignore_case=ignore_case,
                line_number=line_number,
            )
