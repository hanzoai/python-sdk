"""JQ tool - JSON processing without shell escaping issues.

Provides a clean interface for jq queries, avoiding shell quoting problems.
"""

import json
import asyncio
from typing import Optional, Annotated, final, override

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, auto_timeout, create_tool_context


@final
class JqTool(BaseTool):
    """JQ tool - JSON processing without shell escaping nightmares.

    Clean interface for jq queries with proper handling.
    """

    name = "jq"

    @property
    @override
    def description(self) -> str:
        return """JSON processor - jq without shell escaping issues.

Examples:
  jq --filter ".result.data" --input '{"result": {"data": [1,2,3]}}'
  jq --filter ".[] | select(.active)" --file data.json
  jq --filter "keys" --input '{"a": 1, "b": 2}'
  jq --filter '.checks | to_entries[] | select(.value.error != null)' --file health.json

Parameters:
  filter: jq filter expression (required)
  input: JSON input as string
  file: Path to JSON file (alternative to input)
  raw: Output raw strings without quotes (default: false)
  compact: Compact output (default: false)
  slurp: Read entire input as single array (default: false)
  sort_keys: Sort object keys (default: false)

The filter is passed directly to jq without shell interpretation,
so you don't need to escape special characters like ! or |
"""

    @override
    @auto_timeout("jq")
    async def call(
        self,
        ctx: MCPContext,
        filter: str,
        input: Optional[str] = None,
        file: Optional[str] = None,
        raw: bool = False,
        compact: bool = False,
        slurp: bool = False,
        sort_keys: bool = False,
        **kwargs,
    ) -> str:
        """Process JSON with jq."""
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        if not input and not file:
            return "Error: Either 'input' or 'file' is required"

        # Build jq command
        cmd = ["jq"]

        # Options
        if raw:
            cmd.append("-r")
        if compact:
            cmd.append("-c")
        if slurp:
            cmd.append("-s")
        if sort_keys:
            cmd.append("-S")

        # Filter (passed as argument, not through shell)
        cmd.append(filter)

        # File input
        if file:
            cmd.append(file)

        try:
            if input:
                # Validate input is valid JSON first
                try:
                    json.loads(input)
                except json.JSONDecodeError as e:
                    return f"Error: Invalid JSON input: {e}"

                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input=input.encode("utf-8")),
                    timeout=30,
                )
            else:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=30,
                )

            output = stdout.decode("utf-8", errors="replace")
            errors = stderr.decode("utf-8", errors="replace")

            if proc.returncode != 0:
                # Provide helpful error message
                if "syntax error" in errors.lower():
                    return f"jq syntax error in filter:\n  {filter}\n\nError: {errors}"
                return f"jq failed (exit {proc.returncode}):\n{errors}"

            return output.rstrip()

        except asyncio.TimeoutError:
            return "jq timed out after 30s"
        except FileNotFoundError:
            return "Error: jq not found. Install jq: brew install jq"
        except Exception as e:
            return f"Error: {e}"

    def register(self, mcp_server: FastMCP) -> None:
        """Register with MCP server."""
        tool_instance = self

        @mcp_server.tool()
        async def jq(
            filter: Annotated[str, Field(description="jq filter expression")],
            input: Annotated[Optional[str], Field(description="JSON input string")] = None,
            file: Annotated[Optional[str], Field(description="Path to JSON file")] = None,
            raw: Annotated[bool, Field(description="Output raw strings")] = False,
            compact: Annotated[bool, Field(description="Compact output")] = False,
            slurp: Annotated[bool, Field(description="Read as single array")] = False,
            sort_keys: Annotated[bool, Field(description="Sort object keys")] = False,
            ctx: MCPContext = None,
        ) -> str:
            """JSON processor - jq without shell escaping issues.

            Process JSON with jq filters. No shell quoting nightmares!
            Supports all standard jq operations.
            """
            return await tool_instance.call(
                ctx,
                filter=filter,
                input=input,
                file=file,
                raw=raw,
                compact=compact,
                slurp=slurp,
                sort_keys=sort_keys,
            )
