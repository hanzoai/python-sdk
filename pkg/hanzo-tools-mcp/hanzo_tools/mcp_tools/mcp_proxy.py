"""Dynamic MCP Proxy for lazy-loading external MCP servers.

This module provides functionality to:
1. Connect to external MCP servers on-demand
2. Discover their tools dynamically
3. Proxy tool calls through hanzo-mcp
4. Support lazy loading - only start when needed

Example servers that can be proxied:
- platform-mcp (Hanzo Platform)
- @modelcontextprotocol/server-github (GitHub)
- @modelcontextprotocol/server-cloudflare (Cloudflare)
"""

import os
import json
import shutil
import asyncio
import logging
import subprocess
from typing import Any, Dict, List, Callable, Optional, Awaitable
from pathlib import Path
from dataclasses import field, dataclass

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for an external MCP server."""

    name: str
    command: List[str]
    env: Dict[str, str] = field(default_factory=dict)
    working_dir: Optional[str] = None
    description: str = ""
    auto_start: bool = False
    lazy_load: bool = True
    auth_required: bool = False
    auth_env_var: Optional[str] = None
    auth_url: Optional[str] = None


@dataclass
class ProxiedTool:
    """A tool proxied from an external MCP server."""

    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str


class MCPServerConnection:
    """Connection to an external MCP server."""

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.tools: List[ProxiedTool] = []
        self.resources: List[Dict[str, Any]] = []
        self.prompts: List[Dict[str, Any]] = []
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._request_id = 0
        self._pending_requests: Dict[int, asyncio.Future] = {}
        self._read_task: Optional[asyncio.Task] = None

    async def connect(self) -> bool:
        """Connect to the MCP server."""
        if self.process is not None:
            return True

        # Check auth if required
        if self.config.auth_required and self.config.auth_env_var:
            if not os.environ.get(self.config.auth_env_var):
                logger.warning(
                    f"MCP server '{self.config.name}' requires {self.config.auth_env_var} to be set"
                )
                return False

        # Prepare environment
        env = os.environ.copy()
        env.update(self.config.env)

        # Process environment variable references
        for key, value in list(env.items()):
            if (
                isinstance(value, str)
                and value.startswith("${")
                and value.endswith("}")
            ):
                var_name = value[2:-1]
                env[key] = os.environ.get(var_name, "")

        try:
            # Start the MCP server process
            self.process = await asyncio.create_subprocess_exec(
                *self.config.command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=self.config.working_dir,
            )

            self._reader = self.process.stdout
            self._writer = self.process.stdin

            # Start reading responses
            self._read_task = asyncio.create_task(self._read_loop())

            # Initialize the connection
            await self._initialize()

            # Discover tools
            await self._discover_tools()

            logger.info(
                f"Connected to MCP server '{self.config.name}' with {len(self.tools)} tools"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to connect to MCP server '{self.config.name}': {e}")
            await self.disconnect()
            return False

    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
            self._read_task = None

        if self.process:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()
            self.process = None

        self._reader = None
        self._writer = None
        self.tools = []

    async def _read_loop(self):
        """Read responses from the MCP server."""
        try:
            while True:
                if not self._reader:
                    break

                # Read content-length header
                header = await self._reader.readline()
                if not header:
                    break

                # Handle JSON-RPC over stdio (newline-delimited)
                line = header.decode("utf-8").strip()
                if not line:
                    continue

                try:
                    response = json.loads(line)

                    # Handle response
                    if "id" in response and response["id"] in self._pending_requests:
                        future = self._pending_requests.pop(response["id"])
                        if "error" in response:
                            future.set_exception(Exception(response["error"]))
                        else:
                            future.set_result(response.get("result"))

                except json.JSONDecodeError:
                    continue

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error reading from MCP server: {e}")

    async def _send_request(self, method: str, params: Optional[Dict] = None) -> Any:
        """Send a JSON-RPC request to the MCP server."""
        if not self._writer:
            raise ConnectionError("Not connected to MCP server")

        self._request_id += 1
        request_id = self._request_id

        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params:
            request["params"] = params

        # Create future for response
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending_requests[request_id] = future

        # Send request
        request_json = json.dumps(request) + "\n"
        self._writer.write(request_json.encode("utf-8"))
        await self._writer.drain()

        # Wait for response with timeout
        try:
            result = await asyncio.wait_for(future, timeout=30.0)
            return result
        except asyncio.TimeoutError:
            self._pending_requests.pop(request_id, None)
            raise TimeoutError(f"Request to MCP server timed out: {method}")

    async def _initialize(self):
        """Initialize the MCP connection."""
        result = await self._send_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {"listChanged": True},
                },
                "clientInfo": {
                    "name": "hanzo-mcp-proxy",
                    "version": "1.0.0",
                },
            },
        )

        # Send initialized notification
        if self._writer:
            notification = {"jsonrpc": "2.0", "method": "notifications/initialized"}
            self._writer.write((json.dumps(notification) + "\n").encode("utf-8"))
            await self._writer.drain()

        return result

    async def _discover_tools(self):
        """Discover tools from the MCP server."""
        try:
            result = await self._send_request("tools/list")

            self.tools = []
            for tool in result.get("tools", []):
                self.tools.append(
                    ProxiedTool(
                        name=tool["name"],
                        description=tool.get("description", ""),
                        input_schema=tool.get("inputSchema", {}),
                        server_name=self.config.name,
                    )
                )

        except Exception as e:
            logger.warning(f"Failed to discover tools from '{self.config.name}': {e}")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server."""
        result = await self._send_request(
            "tools/call",
            {
                "name": tool_name,
                "arguments": arguments,
            },
        )
        return result


class MCPProxyRegistry:
    """Registry for managing external MCP server proxies."""

    _instance: Optional["MCPProxyRegistry"] = None

    CONFIG_FILE = Path.home() / ".hanzo" / "mcp" / "proxy.json"

    # Pre-configured servers
    BUILTIN_SERVERS: Dict[str, MCPServerConfig] = {
        "platform": MCPServerConfig(
            name="platform",
            command=["npx", "--yes", "@hanzo/platform-mcp"],
            env={"PLATFORM_API_KEY": "${PLATFORM_API_KEY}"},
            description="Hanzo Platform - deploy and manage applications",
            auth_required=True,
            auth_env_var="PLATFORM_API_KEY",
            auth_url="https://platform.hanzo.ai/settings/api-keys",
            lazy_load=True,
        ),
        "github": MCPServerConfig(
            name="github",
            command=["npx", "--yes", "@modelcontextprotocol/server-github"],
            env={"GITHUB_TOKEN": "${GITHUB_TOKEN}"},
            description="GitHub API - repositories, issues, PRs",
            auth_required=True,
            auth_env_var="GITHUB_TOKEN",
            lazy_load=True,
        ),
        "cloudflare": MCPServerConfig(
            name="cloudflare",
            command=["npx", "--yes", "mcp-server-cloudflare"],
            env={"CLOUDFLARE_API_TOKEN": "${CLOUDFLARE_API_TOKEN}"},
            description="Cloudflare API - DNS, Workers, R2, KV",
            auth_required=True,
            auth_env_var="CLOUDFLARE_API_TOKEN",
            lazy_load=True,
        ),
        "filesystem": MCPServerConfig(
            name="filesystem",
            command=["npx", "--yes", "@modelcontextprotocol/server-filesystem", "/tmp"],
            description="File system access",
            lazy_load=True,
        ),
        "postgres": MCPServerConfig(
            name="postgres",
            command=["npx", "--yes", "@modelcontextprotocol/server-postgres"],
            env={"DATABASE_URL": "${DATABASE_URL}"},
            description="PostgreSQL database access",
            auth_required=True,
            auth_env_var="DATABASE_URL",
            lazy_load=True,
        ),
        "sqlite": MCPServerConfig(
            name="sqlite",
            command=["uvx", "mcp-server-sqlite"],
            description="SQLite database access",
            lazy_load=True,
        ),
        "docker": MCPServerConfig(
            name="docker",
            command=["uvx", "mcp-server-docker"],
            description="Docker container management",
            lazy_load=True,
        ),
        "kubernetes": MCPServerConfig(
            name="kubernetes",
            command=["uvx", "mcp-server-kubernetes"],
            description="Kubernetes cluster management",
            lazy_load=True,
        ),
    }

    def __init__(self):
        self._connections: Dict[str, MCPServerConnection] = {}
        self._custom_servers: Dict[str, MCPServerConfig] = {}
        self._load_config()

    @classmethod
    def get_instance(cls) -> "MCPProxyRegistry":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = MCPProxyRegistry()
        return cls._instance

    def _load_config(self):
        """Load custom server configurations."""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    for name, config in data.get("servers", {}).items():
                        self._custom_servers[name] = MCPServerConfig(
                            name=name,
                            command=config.get("command", []),
                            env=config.get("env", {}),
                            working_dir=config.get("working_dir"),
                            description=config.get("description", ""),
                            auto_start=config.get("auto_start", False),
                            lazy_load=config.get("lazy_load", True),
                            auth_required=config.get("auth_required", False),
                            auth_env_var=config.get("auth_env_var"),
                            auth_url=config.get("auth_url"),
                        )
            except Exception as e:
                logger.warning(f"Failed to load proxy config: {e}")

    def _save_config(self):
        """Save custom server configurations."""
        self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

        servers = {}
        for name, config in self._custom_servers.items():
            servers[name] = {
                "command": config.command,
                "env": config.env,
                "working_dir": config.working_dir,
                "description": config.description,
                "auto_start": config.auto_start,
                "lazy_load": config.lazy_load,
                "auth_required": config.auth_required,
                "auth_env_var": config.auth_env_var,
                "auth_url": config.auth_url,
            }

        with open(self.CONFIG_FILE, "w") as f:
            json.dump({"servers": servers}, f, indent=2)

    def get_server_config(self, name: str) -> Optional[MCPServerConfig]:
        """Get server configuration by name."""
        if name in self._custom_servers:
            return self._custom_servers[name]
        if name in self.BUILTIN_SERVERS:
            return self.BUILTIN_SERVERS[name]
        return None

    def list_servers(self) -> List[Dict[str, Any]]:
        """List all available servers."""
        servers = []

        # Add builtin servers
        for name, config in self.BUILTIN_SERVERS.items():
            is_connected = name in self._connections
            auth_configured = True
            if config.auth_required and config.auth_env_var:
                auth_configured = bool(os.environ.get(config.auth_env_var))

            servers.append(
                {
                    "name": name,
                    "description": config.description,
                    "builtin": True,
                    "connected": is_connected,
                    "auth_required": config.auth_required,
                    "auth_configured": auth_configured,
                    "auth_env_var": config.auth_env_var,
                    "auth_url": config.auth_url,
                    "tool_count": (
                        len(self._connections[name].tools) if is_connected else 0
                    ),
                }
            )

        # Add custom servers
        for name, config in self._custom_servers.items():
            if name in self.BUILTIN_SERVERS:
                continue

            is_connected = name in self._connections
            auth_configured = True
            if config.auth_required and config.auth_env_var:
                auth_configured = bool(os.environ.get(config.auth_env_var))

            servers.append(
                {
                    "name": name,
                    "description": config.description,
                    "builtin": False,
                    "connected": is_connected,
                    "auth_required": config.auth_required,
                    "auth_configured": auth_configured,
                    "auth_env_var": config.auth_env_var,
                    "auth_url": config.auth_url,
                    "tool_count": (
                        len(self._connections[name].tools) if is_connected else 0
                    ),
                }
            )

        return servers

    async def enable_server(self, name: str) -> Dict[str, Any]:
        """Enable and connect to an MCP server.

        This starts the server if not running and discovers its tools.
        """
        config = self.get_server_config(name)
        if not config:
            return {"success": False, "error": f"Server '{name}' not found"}

        # Check auth
        if config.auth_required and config.auth_env_var:
            if not os.environ.get(config.auth_env_var):
                return {
                    "success": False,
                    "error": f"Authentication required. Set {config.auth_env_var}",
                    "auth_url": config.auth_url,
                }

        # Check if already connected
        if name in self._connections:
            conn = self._connections[name]
            return {
                "success": True,
                "message": f"Already connected to '{name}'",
                "tools": [
                    {"name": t.name, "description": t.description} for t in conn.tools
                ],
            }

        # Create and connect
        conn = MCPServerConnection(config)
        if await conn.connect():
            self._connections[name] = conn
            return {
                "success": True,
                "message": f"Connected to '{name}'",
                "tools": [
                    {"name": t.name, "description": t.description} for t in conn.tools
                ],
            }
        else:
            return {"success": False, "error": f"Failed to connect to '{name}'"}

    async def disable_server(self, name: str) -> Dict[str, Any]:
        """Disable and disconnect from an MCP server."""
        if name not in self._connections:
            return {"success": False, "error": f"Server '{name}' is not connected"}

        conn = self._connections.pop(name)
        await conn.disconnect()

        return {"success": True, "message": f"Disconnected from '{name}'"}

    def add_server(self, config: MCPServerConfig) -> Dict[str, Any]:
        """Add a custom MCP server configuration."""
        self._custom_servers[config.name] = config
        self._save_config()
        return {"success": True, "message": f"Added server '{config.name}'"}

    def remove_server(self, name: str) -> Dict[str, Any]:
        """Remove a custom MCP server configuration."""
        if name not in self._custom_servers:
            if name in self.BUILTIN_SERVERS:
                return {
                    "success": False,
                    "error": f"Cannot remove builtin server '{name}'",
                }
            return {"success": False, "error": f"Server '{name}' not found"}

        # Disconnect if connected
        if name in self._connections:
            asyncio.create_task(self.disable_server(name))

        del self._custom_servers[name]
        self._save_config()
        return {"success": True, "message": f"Removed server '{name}'"}

    def get_all_proxied_tools(self) -> List[ProxiedTool]:
        """Get all tools from connected servers."""
        tools = []
        for conn in self._connections.values():
            tools.extend(conn.tools)
        return tools

    async def call_proxied_tool(
        self, server_name: str, tool_name: str, arguments: Dict[str, Any]
    ) -> Any:
        """Call a tool on a proxied server.

        If lazy_load is enabled, the server will be connected on first use.
        """
        # Lazy load if not connected
        if server_name not in self._connections:
            config = self.get_server_config(server_name)
            if config and config.lazy_load:
                result = await self.enable_server(server_name)
                if not result.get("success"):
                    raise ConnectionError(result.get("error", "Failed to connect"))
            else:
                raise ConnectionError(f"Server '{server_name}' is not connected")

        conn = self._connections.get(server_name)
        if not conn:
            raise ConnectionError(f"Server '{server_name}' is not connected")

        return await conn.call_tool(tool_name, arguments)


# Convenience function for lazy loading
async def enable_mcp_server(name: str) -> Dict[str, Any]:
    """Enable an MCP server by name.

    This is a convenience function for lazy-loading MCP servers.

    Example:
        result = await enable_mcp_server("platform")
        if result["success"]:
            print(f"Enabled with {len(result['tools'])} tools")
    """
    registry = MCPProxyRegistry.get_instance()
    return await registry.enable_server(name)


async def call_mcp_tool(server: str, tool: str, **kwargs) -> Any:
    """Call a tool on an MCP server.

    This is a convenience function that handles lazy loading.

    Example:
        result = await call_mcp_tool("platform", "application-list")
    """
    registry = MCPProxyRegistry.get_instance()
    return await registry.call_proxied_tool(server, tool, kwargs)


# Export builtin servers for convenience
BUILTIN_SERVERS = MCPProxyRegistry.BUILTIN_SERVERS
