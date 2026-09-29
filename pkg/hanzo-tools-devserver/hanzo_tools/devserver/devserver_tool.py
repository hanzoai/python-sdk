"""The `devserver` tool: find running dev servers, call their MCP tools,
and read their current build and runtime errors."""

import re
import json
from typing import Any, ClassVar
from dataclasses import asdict

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, ToolError, NotFoundError, InvalidParamsError
from hanzo_tools.mcp_tools.mcp_proxy import MCPServerConfig, MCPServerConnection

from .discovery import DevServer, discover

# Reads Vite's error overlay, which every Vite-based framework shows for a
# failed transform. With the overlay on, Vite writes the error nowhere else the
# page can see — not the console — so the overlay is the source. It appears
# once the HMR socket delivers the error, so poll for up to two seconds.
OVERLAY = """(async () => {
  for (let i = 0; i < 20; i++) {
    const root = document.querySelector('vite-error-overlay')?.shadowRoot;
    if (root) {
      const text = s => root.querySelector(s)?.textContent.trim() || undefined;
      return {plugin: text('.plugin'), message: text('.message'), file: text('.file'), frame: text('.frame')};
    }
    await new Promise(r => setTimeout(r, 100));
  }
  return null;
})()"""

# Terminal colour codes dev servers leave in the errors they report, raw or
# JSON-escaped; removing a whole escaped code leaves the JSON valid.
ANSI = re.compile(r"(?:\x1b|\\u001[bB])\[[0-9;]*m")

PORT = {"type": "integer", "description": "Dev server port; required when more than one runs"}
CWD = {"type": "string", "description": "Project directory; narrows to dev servers of projects around it"}

HELP = {
    "actions": {
        "index": "Dev servers on this machine: framework, version, url, pid, MCP endpoint and its tools. port= / cwd= narrow it.",
        "call": "Run a server's MCP tool: tool=<name from index> args={...}; port= only when two servers list it.",
        "errors": "Current build/runtime errors. Opens the app (path=, default /) in the browser tool, then asks the "
        "server's MCP get_errors, or reads Vite's error overlay, console errors and page errors.",
    },
    "workflow": "index -> call tool=<listed> -> edit code -> errors",
    "mcp": {
        "next": "16+ serves /_next/mcp by default",
        "vite, nuxt, remix, react-router, astro, sveltekit": "add vite-plugin-mcp (nuxt-mcp-dev for Nuxt) to serve /__mcp/sse",
    },
}


def payload(result: dict) -> Any:
    """What an MCP tool result says: structured content, else its text blocks,
    uncoloured and decoded when they are JSON. Other blocks pass through."""
    if "structuredContent" in result:
        return result["structuredContent"]
    out = []
    for block in result.get("content", []):
        if block.get("type") != "text":
            out.append(block)
            continue
        text = ANSI.sub("", block["text"])
        try:
            out.append(json.loads(text))
        except ValueError:
            out.append(text)
    return out[0] if len(out) == 1 else out


def since(result: dict, key: str, before: int) -> list:
    """Entries the browser counted after `before`: it keeps console messages and
    page errors across page loads, so older ones are not current."""
    items = result.get(key) or []
    fresh = result.get("count", len(items)) - before
    return items[-fresh:] if fresh > 0 else []


def port_of(value: Any) -> int | None:
    """A port from a caller, who may send it as a number or a string."""
    if value in (None, "", 0):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise InvalidParamsError(f"port must be a number, not {value!r}", param="port") from None


def structured(out: Any) -> dict:
    """A FastMCP tool's return as a dict: the structured half when the tool
    declares an output schema, else its JSON text, unwrapped from the
    unified {ok, data, error} envelope when it arrives in one."""
    if isinstance(out, tuple):
        data = out[1]
    else:
        text = next((b.text for b in out if getattr(b, "text", None) is not None), "{}")
        try:
            data = json.loads(text)
        except ValueError:
            return {"text": text}
    if isinstance(data, dict) and {"ok", "data", "error"} <= data.keys():
        return data["data"] if data["ok"] else {"error": data["error"]}
    return data


class DevserverTool(BaseTool):
    """Running dev servers as MCP nodes."""

    name: ClassVar[str] = "devserver"
    VERSION: ClassVar[str] = "0.1.0"

    def __init__(self):
        super().__init__()
        # The MCP server this tool is registered on: `errors` reaches the
        # `browser` tool through its registry, never around it.
        self._server: FastMCP | None = None
        self._register_actions()

    @property
    def description(self) -> str:
        return (
            "Running dev servers (Next, Vite, Nuxt, Remix, React Router, Astro, SvelteKit): find them, "
            "call their built-in MCP tools, read current build/runtime errors.\nStart with action=help."
        )

    def register(self, mcp_server: FastMCP) -> None:
        self._server = mcp_server
        super().register(mcp_server)

    async def _browser(self, action: str, **args: Any) -> dict:
        if self._server is None:
            raise ToolError("INTERNAL_ERROR", "devserver is not registered on an MCP server; no browser tool to call")
        return structured(await self._server.call_tool("browser", {"action": action, **args}))

    async def _pick(self, port: Any, cwd: str | None, tool: str | None = None) -> DevServer:
        """The one dev server the caller means: narrowed by port, cwd and, for
        a call, by which servers list the tool."""
        servers = await discover(port=port_of(port), cwd=cwd)
        if tool:
            servers = [s for s in servers if any(t["name"] == tool for t in s.tools)]
        if len(servers) == 1:
            return servers[0]
        if not servers:
            listing = f" lists MCP tool {tool!r}" if tool else " matches"
            raise NotFoundError(f"no running dev server{listing}; index shows what runs")
        ports = ", ".join(f"{s.port} ({s.framework})" for s in servers)
        raise InvalidParamsError(f"{len(servers)} dev servers match: {ports}; pass port=", param="port")

    async def _call(self, server: DevServer, tool: str, args: dict) -> dict:
        connection = MCPServerConnection(MCPServerConfig(name=f"{server.framework}:{server.port}", url=server.mcp))
        result = await connection.call_tool(tool, args)
        return {"is_error": result.get("isError", False), "result": payload(result)}

    def _register_actions(self) -> None:
        @self.action("help", "What devserver does and the index -> call workflow")
        async def help_action(ctx: MCPContext) -> dict:
            return HELP

        @self.action(
            "index",
            "List dev servers, their MCP endpoints and tools",
            schema={"type": "object", "properties": {"port": PORT, "cwd": CWD}},
        )
        async def index(ctx: MCPContext, port: Any = None, cwd: str | None = None) -> dict:
            servers = await discover(port=port_of(port), cwd=cwd)
            return {"count": len(servers), "servers": [asdict(s) for s in servers]}

        @self.action(
            "call",
            "Invoke a dev server's MCP tool",
            schema={
                "type": "object",
                "properties": {
                    "tool": {"type": "string", "description": "MCP tool name, as index lists it"},
                    "args": {"type": "object", "description": "The tool's arguments"},
                    "port": PORT,
                    "cwd": CWD,
                },
                "required": ["tool"],
            },
        )
        async def call(
            ctx: MCPContext, tool: str, args: dict | None = None, port: Any = None, cwd: str | None = None
        ) -> dict:
            server = await self._pick(port, cwd, tool)
            return {"server": server.mcp, "tool": tool, **await self._call(server, tool, args or {})}

        @self.action(
            "errors",
            "Current build/runtime errors of a dev server",
            schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Route to open, default /"},
                    "port": PORT,
                    "cwd": CWD,
                },
            },
        )
        async def errors(ctx: MCPContext, path: str = "/", port: Any = None, cwd: str | None = None) -> dict:
            server = await self._pick(port, cwd)
            url = server.url + "/" + path.lstrip("/")
            if any(t["name"] == "get_errors" for t in server.tools):
                # Next reports the errors its browser sessions report, so open one
                # and let it settle: at `load` the session is connected but has
                # not yet reported a build error. The server's answer stands
                # without a browser.
                try:
                    opened = await self._browser("navigate", url=url, args={"state": "networkidle"})
                except Exception as e:
                    opened = {"error": str(e)}
                report = {"server": server.url, "source": "mcp", **await self._call(server, "get_errors", {})}
                if opened.get("error"):
                    report["browser"] = opened["error"]
                return report
            before = (
                (await self._browser("console", args={"level": "error"})).get("count", 0),
                (await self._browser("errors")).get("count", 0),
            )
            opened = await self._browser("navigate", url=url, args={"state": "networkidle"})
            if opened.get("error"):
                raise ToolError("INTERNAL_ERROR", f"browser could not open {url}: {opened['error']}")
            overlay = (await self._browser("evaluate", code=OVERLAY)).get("result")
            console = await self._browser("console", args={"level": "error"})
            thrown = await self._browser("errors")
            return {
                "server": server.url,
                "source": "browser",
                "overlay": overlay,
                "console": since(console, "messages", before[0]),
                "errors": since(thrown, "errors", before[1]),
            }
