"""Wget tool - reliable file and site downloads.

Provides a clean interface for wget with proper handling of recursive downloads.
"""

import os
import asyncio
from typing import Optional, Annotated, final, override

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, auto_timeout, create_tool_context


@final
class WgetTool(BaseTool):
    """Wget tool - reliable downloads without shell escaping issues.

    Supports single file downloads and full site mirroring.
    """

    name = "wget"

    @property
    @override
    def description(self) -> str:
        return """Download files and mirror websites reliably.

Examples:
  wget --url "https://example.com/file.zip"
  wget --url "https://example.com/file.zip" --output "/tmp/myfile.zip"
  wget --url "https://docs.example.com" --mirror true
  wget --url "https://docs.example.com" --recursive true --depth 2
  wget --url "https://example.com" --recursive true --accept "*.pdf,*.doc"

Parameters:
  url: URL to download (required)
  output: Output file or directory
  mirror: Mirror site for offline viewing (sets recursive + timestamps)
  recursive: Download recursively
  depth: Maximum recursion depth (default: 5 for recursive)
  accept: Accept only files matching pattern (e.g., "*.pdf,*.html")
  reject: Reject files matching pattern
  domains: Limit to specific domains
  no_parent: Don't ascend to parent directory
  continue_download: Continue partial downloads
  timeout: Timeout in seconds (default: 300 for mirrors, 60 for files)
  quiet: Suppress output

Returns status and download summary.
"""

    @override
    @auto_timeout("wget")
    async def call(
        self,
        ctx: MCPContext,
        url: str,
        output: Optional[str] = None,
        mirror: bool = False,
        recursive: bool = False,
        depth: Optional[int] = None,
        accept: Optional[str] = None,
        reject: Optional[str] = None,
        domains: Optional[str] = None,
        no_parent: bool = True,
        continue_download: bool = False,
        timeout: Optional[int] = None,
        quiet: bool = False,
        **kwargs,
    ) -> str:
        """Download files or mirror websites."""
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        # Build wget command
        cmd = ["wget"]

        # Mirror mode (most common for site downloads)
        if mirror:
            cmd.extend([
                "--mirror",           # Turn on mirroring
                "--convert-links",    # Convert links for offline viewing
                "--adjust-extension", # Add .html extension
                "--page-requisites",  # Get all assets (css, js, images)
                "--no-host-directories",  # Don't create host directory
            ])
            recursive = True  # Mirror implies recursive

        # Recursive download
        if recursive:
            cmd.append("-r")
            if depth is not None:
                cmd.extend(["-l", str(depth)])
            elif not mirror:
                cmd.extend(["-l", "5"])  # Default depth limit

        # No parent directory traversal (safety)
        if no_parent:
            cmd.append("--no-parent")

        # Continue partial downloads
        if continue_download:
            cmd.append("-c")

        # Accept/reject patterns
        if accept:
            cmd.extend(["-A", accept])
        if reject:
            cmd.extend(["-R", reject])

        # Domain restrictions
        if domains:
            cmd.extend(["-D", domains])

        # Output location
        if output:
            if recursive or mirror:
                cmd.extend(["-P", output])  # Directory for recursive
            else:
                cmd.extend(["-O", output])  # File for single download

        # Timeout
        actual_timeout = timeout or (300 if (mirror or recursive) else 60)
        cmd.extend(["--timeout", str(min(actual_timeout, 30))])  # Per-request timeout
        cmd.extend(["--tries", "3"])  # Retry count
        cmd.extend(["--waitretry", "1"])  # Wait between retries

        # Progress
        if quiet:
            cmd.append("-q")
        else:
            cmd.append("--progress=dot:mega")  # Show progress for large files

        # User agent (avoid blocks)
        cmd.extend([
            "--user-agent",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        ])

        # URL (last)
        cmd.append(url)

        try:
            # Check if output is a directory (non-blocking)
            cwd = None
            if output:
                loop = asyncio.get_event_loop()
                is_dir = await loop.run_in_executor(None, os.path.isdir, output)
                if is_dir:
                    cwd = output

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=actual_timeout + 30,
            )

            output_text = stdout.decode("utf-8", errors="replace")
            errors = stderr.decode("utf-8", errors="replace")

            # Combine stdout and stderr (wget uses stderr for progress)
            combined = f"{errors}\n{output_text}".strip()

            if proc.returncode != 0:
                return f"wget failed (exit {proc.returncode}):\n{combined}"

            # Summarize success
            lines = combined.split("\n")
            summary_lines = [l for l in lines if any(x in l.lower() for x in [
                "saved", "downloaded", "finished", "total", "retrieved"
            ])]

            if summary_lines:
                return "Download complete:\n" + "\n".join(summary_lines[-5:])
            return f"Download complete:\n{combined[-500:]}"

        except asyncio.TimeoutError:
            return f"Download timed out after {actual_timeout}s"
        except FileNotFoundError:
            return "Error: wget not found. Install wget: brew install wget"
        except Exception as e:
            return f"Error: {e}"

    def register(self, mcp_server: FastMCP) -> None:
        """Register with MCP server."""
        tool_instance = self

        @mcp_server.tool()
        async def wget(
            url: Annotated[str, Field(description="URL to download")],
            output: Annotated[Optional[str], Field(description="Output file or directory")] = None,
            mirror: Annotated[bool, Field(description="Mirror site for offline viewing")] = False,
            recursive: Annotated[bool, Field(description="Download recursively")] = False,
            depth: Annotated[Optional[int], Field(description="Max recursion depth")] = None,
            accept: Annotated[Optional[str], Field(description="Accept pattern (e.g. '*.pdf')")] = None,
            reject: Annotated[Optional[str], Field(description="Reject pattern")] = None,
            domains: Annotated[Optional[str], Field(description="Limit to domains")] = None,
            no_parent: Annotated[bool, Field(description="Don't go to parent directories")] = True,
            continue_download: Annotated[bool, Field(description="Continue partial downloads")] = False,
            timeout: Annotated[Optional[int], Field(description="Timeout in seconds")] = None,
            quiet: Annotated[bool, Field(description="Suppress output")] = False,
            ctx: MCPContext = None,
        ) -> str:
            """Download files and mirror websites reliably.

            Supports single file downloads and full site mirroring.
            Handles retries, timeouts, and link conversion automatically.
            """
            return await tool_instance.call(
                ctx,
                url=url,
                output=output,
                mirror=mirror,
                recursive=recursive,
                depth=depth,
                accept=accept,
                reject=reject,
                domains=domains,
                no_parent=no_parent,
                continue_download=continue_download,
                timeout=timeout,
                quiet=quiet,
            )
