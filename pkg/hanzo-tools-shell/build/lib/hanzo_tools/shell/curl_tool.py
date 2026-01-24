"""Curl tool - HTTP client without shell escaping issues.

Provides a clean interface for HTTP requests, avoiding shell quoting problems.
"""

import json
import asyncio
from typing import Literal, Optional, Annotated, final, override

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, auto_timeout, create_tool_context

Method = Annotated[
    Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
    Field(description="HTTP method"),
]


@final
class CurlTool(BaseTool):
    """HTTP client tool - curl without shell escaping nightmares.

    Clean interface for HTTP requests with proper JSON handling.
    """

    name = "curl"

    @property
    @override
    def description(self) -> str:
        return """HTTP client - make requests without shell escaping issues.

Examples:
  curl --url "https://api.example.com/health"
  curl --url "https://api.example.com/data" --method POST --json '{"key": "value"}'
  curl --url "https://api.example.com/auth" --headers '{"Authorization": "Bearer token"}'

Parameters:
  url: Request URL (required)
  method: GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS (default: GET)
  json: JSON body (will be serialized properly)
  data: Raw body data
  headers: Additional headers as JSON object
  timeout: Request timeout in seconds (default: 30)
  follow_redirects: Follow redirects (default: true)
  verbose: Include response headers (default: false)

Returns formatted response with status, headers (if verbose), and body.
"""

    @override
    @auto_timeout("curl")
    async def call(
        self,
        ctx: MCPContext,
        url: str,
        method: str = "GET",
        json_body: Optional[str] = None,
        data: Optional[str] = None,
        headers: Optional[str] = None,
        timeout: int = 30,
        follow_redirects: bool = True,
        verbose: bool = False,
        **kwargs,
    ) -> str:
        """Make HTTP request."""
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        # Build curl command
        cmd = ["curl", "-s", "-S"]  # Silent but show errors

        # Method
        if method != "GET":
            cmd.extend(["-X", method])

        # Follow redirects
        if follow_redirects:
            cmd.append("-L")

        # Timeout
        cmd.extend(["--max-time", str(timeout)])

        # Include headers in output if verbose
        if verbose:
            cmd.append("-i")

        # Headers
        default_headers = {}
        if headers:
            try:
                parsed_headers = json.loads(headers)
                if isinstance(parsed_headers, dict):
                    default_headers.update(parsed_headers)
            except json.JSONDecodeError:
                return f"Error: Invalid headers JSON: {headers}"

        # JSON body
        if json_body:
            default_headers.setdefault("Content-Type", "application/json")
            # Parse and re-serialize to ensure valid JSON
            try:
                parsed_json = json.loads(json_body)
                serialized = json.dumps(parsed_json)
                cmd.extend(["-d", serialized])
            except json.JSONDecodeError:
                return f"Error: Invalid JSON body: {json_body}"
        elif data:
            cmd.extend(["-d", data])

        # Add all headers
        for key, value in default_headers.items():
            cmd.extend(["-H", f"{key}: {value}"])

        # URL (must be last)
        cmd.append(url)

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout + 5,  # Give curl time to timeout first
            )

            output = stdout.decode("utf-8", errors="replace")
            errors = stderr.decode("utf-8", errors="replace")

            if proc.returncode != 0:
                return f"curl failed (exit {proc.returncode}):\n{errors}\n{output}"

            # Try to pretty-print JSON responses
            if not verbose:  # Don't try to parse if headers included
                try:
                    parsed = json.loads(output)
                    return json.dumps(parsed, indent=2)
                except json.JSONDecodeError:
                    pass

            return output

        except asyncio.TimeoutError:
            return f"Request timed out after {timeout}s"
        except FileNotFoundError:
            return "Error: curl not found. Install curl to use this tool."
        except Exception as e:
            return f"Error: {e}"

    def register(self, mcp_server: FastMCP) -> None:
        """Register with MCP server."""
        tool_instance = self

        @mcp_server.tool()
        async def curl(
            url: Annotated[str, Field(description="Request URL")],
            method: Method = "GET",
            json_body: Annotated[
                Optional[str], Field(description="JSON body (will be properly escaped)", alias="json")
            ] = None,
            data: Annotated[Optional[str], Field(description="Raw body data")] = None,
            headers: Annotated[Optional[str], Field(description="Headers as JSON object")] = None,
            timeout: Annotated[int, Field(description="Timeout in seconds")] = 30,
            follow_redirects: Annotated[bool, Field(description="Follow redirects")] = True,
            verbose: Annotated[bool, Field(description="Include response headers")] = False,
            ctx: MCPContext = None,
        ) -> str:
            """HTTP client - curl without shell escaping issues.

            Make HTTP requests with proper JSON handling.
            No more shell quoting nightmares!
            """
            return await tool_instance.call(
                ctx,
                url=url,
                method=method,
                json_body=json_body,
                data=data,
                headers=headers,
                timeout=timeout,
                follow_redirects=follow_redirects,
                verbose=verbose,
            )
