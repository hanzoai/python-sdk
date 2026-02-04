"""Proxy Tool - Enable/disable external MCP servers dynamically.

This tool allows dynamically enabling external MCP servers like:
- platform (Hanzo Platform)
- github (GitHub API)
- cloudflare (Cloudflare API)
- filesystem, postgres, sqlite, docker, kubernetes, etc.

When enabled, tools from these servers become available through hanzo-mcp.
"""

import os
import json
from typing import Any, Dict, List, Optional, Unpack, Annotated, TypedDict, final, override

from pydantic import Field
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, auto_timeout, create_tool_context

from .mcp_proxy import MCPProxyRegistry, MCPServerConfig


# Parameter types
Action = Annotated[
    str,
    Field(
        description="Action: list, enable, disable, add, remove, call, auth",
        default="list",
    ),
]

ServerName = Annotated[
    Optional[str],
    Field(
        description="MCP server name (e.g., platform, github, cloudflare)",
        default=None,
    ),
]

ToolName = Annotated[
    Optional[str],
    Field(
        description="Tool name to call (for 'call' action)",
        default=None,
    ),
]

ToolArgs = Annotated[
    Optional[Dict[str, Any]],
    Field(
        description="Arguments for tool call (JSON object)",
        default=None,
    ),
]

Command = Annotated[
    Optional[str],
    Field(
        description="Command to run the MCP server (for 'add' action)",
        default=None,
    ),
]

AuthToken = Annotated[
    Optional[str],
    Field(
        description="API token for authentication (for 'auth' action)",
        default=None,
    ),
]


class ProxyToolParams(TypedDict, total=False):
    """Parameters for the proxy tool."""

    action: str
    server: Optional[str]
    tool: Optional[str]
    args: Optional[Dict[str, Any]]
    command: Optional[str]
    token: Optional[str]
    env: Optional[Dict[str, str]]
    description: Optional[str]


@final
class ProxyTool(BaseTool):
    """Tool for managing external MCP server proxies."""

    def __init__(self):
        """Initialize the proxy tool."""
        self._registry = MCPProxyRegistry.get_instance()

    @property
    @override
    def name(self) -> str:
        return "proxy"

    @property
    @override
    def description(self) -> str:
        servers = self._registry.list_servers()
        connected = sum(1 for s in servers if s.get("connected"))
        total_tools = sum(s.get("tool_count", 0) for s in servers)

        return f"""Manage external MCP server proxies. Actions: list, enable, disable, add, remove, call, auth.

Connected: {connected}/{len(servers)} servers, {total_tools} tools available.

Built-in servers: platform, github, cloudflare, filesystem, postgres, sqlite, docker, kubernetes

Usage:
  proxy                                      # List all servers
  proxy --action enable --server platform    # Enable Platform MCP
  proxy --action disable --server github     # Disable GitHub MCP
  proxy --action auth --server platform --token <api-key>  # Configure auth
  proxy --action call --server platform --tool application-list  # Call tool"""

    @override
    @auto_timeout("proxy")
    async def call(
        self,
        ctx: MCPContext,
        **params: Unpack[ProxyToolParams],
    ) -> str:
        """Execute proxy action."""
        tool_ctx = None
        try:
            if hasattr(ctx, "client") and ctx.client:
                tool_ctx = create_tool_context(ctx)
                if tool_ctx:
                    await tool_ctx.set_tool_info(self.name)
        except Exception:
            pass

        action = params.get("action", "list")

        if action == "list":
            return self._handle_list()
        elif action == "enable":
            return await self._handle_enable(params.get("server"))
        elif action == "disable":
            return await self._handle_disable(params.get("server"))
        elif action == "add":
            return self._handle_add(params)
        elif action == "remove":
            return self._handle_remove(params.get("server"))
        elif action == "call":
            return await self._handle_call(
                params.get("server"),
                params.get("tool"),
                params.get("args") or {},
            )
        elif action == "auth":
            return self._handle_auth(params.get("server"), params.get("token"))
        else:
            return f"Unknown action: {action}. Valid: list, enable, disable, add, remove, call, auth"

    def _handle_list(self) -> str:
        """List all available MCP servers."""
        servers = self._registry.list_servers()

        if not servers:
            return "No MCP servers available."

        output = ["=== MCP Server Proxies ===", ""]

        # Group by status
        connected = [s for s in servers if s.get("connected")]
        available = [s for s in servers if not s.get("connected") and s.get("auth_configured", True)]
        needs_auth = [s for s in servers if not s.get("connected") and not s.get("auth_configured", True)]

        if connected:
            output.append("🟢 Connected:")
            for s in connected:
                output.append(f"  {s['name']}: {s['description']} ({s['tool_count']} tools)")
            output.append("")

        if available:
            output.append("⚪ Available (ready to enable):")
            for s in available:
                output.append(f"  {s['name']}: {s['description']}")
            output.append("")

        if needs_auth:
            output.append("🔐 Needs authentication:")
            for s in needs_auth:
                auth_info = f"Set {s.get('auth_env_var', 'API key')}"
                if s.get("auth_url"):
                    auth_info += f" or visit {s['auth_url']}"
                output.append(f"  {s['name']}: {s['description']}")
                output.append(f"    → {auth_info}")
            output.append("")

        output.append("Commands:")
        output.append("  proxy --action enable --server <name>")
        output.append("  proxy --action auth --server <name> --token <key>")

        return "\n".join(output)

    async def _handle_enable(self, server: Optional[str]) -> str:
        """Enable an MCP server."""
        if not server:
            return "Error: --server is required"

        result = await self._registry.enable_server(server)

        if result.get("success"):
            tools = result.get("tools", [])
            if tools:
                tool_list = "\n".join([f"  - {t['name']}: {t['description']}" for t in tools[:10]])
                if len(tools) > 10:
                    tool_list += f"\n  ... and {len(tools) - 10} more"
                return f"✅ Enabled '{server}' with {len(tools)} tools:\n{tool_list}"
            return f"✅ {result.get('message', f'Enabled {server}')}"
        else:
            error = result.get("error", "Unknown error")
            if result.get("auth_url"):
                return f"❌ {error}\n\nGet your API key at: {result['auth_url']}\nThen run: proxy --action auth --server {server} --token <key>"
            return f"❌ {error}"

    async def _handle_disable(self, server: Optional[str]) -> str:
        """Disable an MCP server."""
        if not server:
            return "Error: --server is required"

        result = await self._registry.disable_server(server)

        if result.get("success"):
            return f"✅ {result.get('message', f'Disabled {server}')}"
        else:
            return f"❌ {result.get('error', 'Unknown error')}"

    def _handle_add(self, params: Dict[str, Any]) -> str:
        """Add a custom MCP server."""
        server = params.get("server")
        command = params.get("command")

        if not server:
            return "Error: --server (name) is required"
        if not command:
            return "Error: --command is required"

        # Parse command
        import shlex
        cmd_parts = shlex.split(command)

        config = MCPServerConfig(
            name=server,
            command=cmd_parts,
            env=params.get("env", {}),
            description=params.get("description", "Custom MCP server"),
            lazy_load=True,
        )

        result = self._registry.add_server(config)

        if result.get("success"):
            return f"✅ Added server '{server}'. Use 'proxy --action enable --server {server}' to connect."
        else:
            return f"❌ {result.get('error', 'Unknown error')}"

    def _handle_remove(self, server: Optional[str]) -> str:
        """Remove a custom MCP server."""
        if not server:
            return "Error: --server is required"

        result = self._registry.remove_server(server)

        if result.get("success"):
            return f"✅ {result.get('message', f'Removed {server}')}"
        else:
            return f"❌ {result.get('error', 'Unknown error')}"

    async def _handle_call(
        self, server: Optional[str], tool: Optional[str], args: Dict[str, Any]
    ) -> str:
        """Call a tool on a proxied server."""
        if not server:
            return "Error: --server is required"
        if not tool:
            return "Error: --tool is required"

        try:
            result = await self._registry.call_proxied_tool(server, tool, args)
            return json.dumps(result, indent=2) if isinstance(result, (dict, list)) else str(result)
        except Exception as e:
            return f"❌ Error calling {server}/{tool}: {e}"

    def _handle_auth(self, server: Optional[str], token: Optional[str]) -> str:
        """Configure authentication for a server."""
        if not server:
            return "Error: --server is required"

        config = self._registry.get_server_config(server)
        if not config:
            return f"Error: Server '{server}' not found"

        if not config.auth_required:
            return f"Server '{server}' does not require authentication"

        env_var = config.auth_env_var
        if not env_var:
            return f"Server '{server}' has no auth configuration"

        if token:
            # Set the environment variable for this session
            os.environ[env_var] = token

            # Also save to credentials file
            creds_file = self._registry.CONFIG_FILE.parent / "credentials.json"
            creds_file.parent.mkdir(parents=True, exist_ok=True)

            creds = {}
            if creds_file.exists():
                try:
                    with open(creds_file, "r") as f:
                        creds = json.load(f)
                except Exception:
                    pass

            creds[server] = {
                "env_var": env_var,
                "token": token,  # In production, this should be encrypted
            }

            with open(creds_file, "w") as f:
                json.dump(creds, f, indent=2)

            # Set file permissions
            try:
                import stat
                creds_file.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0600
            except Exception:
                pass

            return f"✅ Configured authentication for '{server}'.\nNow run: proxy --action enable --server {server}"
        else:
            # Show auth instructions
            return f"""To authenticate with '{server}':

1. Get your API key:
   {config.auth_url or 'Check the service documentation'}

2. Set it:
   proxy --action auth --server {server} --token YOUR_API_KEY

   Or set environment variable:
   export {env_var}=YOUR_API_KEY"""

    def register(self, mcp_server) -> None:
        """Register this tool with the MCP server."""
        pass
