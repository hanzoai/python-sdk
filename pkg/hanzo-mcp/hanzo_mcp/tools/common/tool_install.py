"""Tool installation and self-update tool.

Allows the AI to:
- Install new tool packages dynamically
- Update existing tools
- Self-update hanzo-mcp
- Hot-reload without restart
"""

from typing import Any, Unpack, Literal, Annotated, TypedDict, final, override

from pydantic import Field
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.common.base import BaseTool
from hanzo_mcp.tools.common.context import create_tool_context
from hanzo_mcp.tools.common.auto_timeout import auto_timeout

Action = Annotated[
    Literal[
        "install",  # Install a tool package
        "uninstall",  # Remove a tool package
        "upgrade",  # Upgrade package(s)
        "reload",  # Hot-reload a package
        "list",  # List installed packages
        "self_update",  # Update hanzo-mcp itself
    ],
    Field(description="Action to perform"),
]


class ToolInstallParams(TypedDict, total=False):
    """Parameters for tool install actions."""

    action: str
    package: str
    source: str
    version: str


@final
class ToolInstallTool(BaseTool):
    """Dynamic tool installation and management.

    Allows the AI to expand its own capabilities by installing
    new tool packages, updating existing tools, and even updating itself.
    """

    @property
    @override
    def name(self) -> str:
        return "tool_install"

    @property
    @override
    def description(self) -> str:
        return """Install, update, and manage tool packages dynamically.

Actions:
- install: Install a new tool package
- uninstall: Remove a tool package
- upgrade: Upgrade package(s) to latest
- reload: Hot-reload a package without restart
- list: List all installed packages
- self_update: Update hanzo-mcp itself

Examples:
  tool_install(action="install", package="hanzo-tools-browser")
  tool_install(action="upgrade", package="hanzo-tools-data")
  tool_install(action="self_update")
  tool_install(action="list")
  tool_install(action="reload", package="hanzo-tools-browser")

Sources:
- pypi: Install from PyPI (default)
- git: Install from git URL
- local: Install from local path
"""

    @override
    @auto_timeout("tool_install")
    async def call(
        self,
        ctx: MCPContext,
        **params: Unpack[ToolInstallParams],
    ) -> str:
        """Execute tool management action."""
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        action = params.get("action", "list")
        package = params.get("package")
        source = params.get("source", "pypi")
        version = params.get("version")

        # Import registry lazily
        from hanzo_mcp.tools.common.tool_registry import get_registry

        registry = await get_registry()

        if action == "install":
            if not package:
                return "Error: package name required for install"

            await tool_ctx.info(f"Installing {package} from {source}...")
            result = await registry.install(
                package=package,
                source=source,
                version=version,
            )

            if result["success"]:
                tools = result.get("tools", [])
                return (
                    f"✓ Installed {package} v{result.get('version', 'latest')}\n"
                    f"Tools available: {', '.join(tools) if tools else 'none detected'}"
                )
            else:
                return f"✗ Failed to install {package}: {result.get('error', 'unknown error')}"

        elif action == "uninstall":
            if not package:
                return "Error: package name required for uninstall"

            await tool_ctx.info(f"Uninstalling {package}...")
            result = await registry.uninstall(package)

            if result["success"]:
                return f"✓ Uninstalled {package}"
            else:
                return f"✗ Failed to uninstall {package}: {result.get('error', 'unknown error')}"

        elif action == "upgrade":
            await tool_ctx.info(f"Upgrading {package or 'all packages'}...")
            result = await registry.upgrade(package)

            if result["success"]:
                upgraded = [r["package"] for r in result.get("results", []) if r.get("success")]
                return f"✓ Upgraded: {', '.join(upgraded) if upgraded else 'none'}"
            else:
                errors = [
                    f"{r['package']}: {r.get('error')}" for r in result.get("results", []) if not r.get("success")
                ]
                return f"✗ Some upgrades failed:\n" + "\n".join(errors)

        elif action == "reload":
            if not package:
                return "Error: package name required for reload"

            await tool_ctx.info(f"Reloading {package}...")
            result = await registry.reload_package(package)

            if result["success"]:
                tools = result.get("tools", [])
                return f"✓ Reloaded {package}\nTools: {', '.join(tools) if tools else 'none'}"
            else:
                return f"✗ Failed to reload {package}: {result.get('error', 'unknown error')}"

        elif action == "list":
            packages = registry.list_packages()

            if not packages:
                return "No tool packages installed.\n\nUse tool_install(action='install', package='...') to add tools."

            lines = ["Installed tool packages:", ""]
            for pkg in packages:
                status = "✓" if pkg["enabled"] else "○"
                lines.append(f"{status} {pkg['name']} v{pkg['version']} ({pkg['source']})")
                if pkg["tools"]:
                    lines.append(f"  Tools: {', '.join(pkg['tools'])}")

            return "\n".join(lines)

        elif action == "self_update":
            await tool_ctx.info("Checking for hanzo-mcp updates...")
            result = await registry.self_update()

            if result["success"]:
                return f"✓ Updated hanzo-mcp from v{result.get('current_version')}\n{result.get('message', '')}"
            else:
                return (
                    f"✗ Update failed: {result.get('error', 'unknown error')}\n"
                    f"Current version: v{result.get('current_version', 'unknown')}"
                )

        else:
            return f"Unknown action: {action}"

    def register(self, mcp_server) -> None:
        """Register this tool with the MCP server."""
        tool_instance = self

        @mcp_server.tool()
        async def tool_install(
            action: Action,
            package: Annotated[str | None, Field(description="Package name or URL")] = None,
            source: Annotated[str, Field(description="Source: pypi, git, or local")] = "pypi",
            version: Annotated[str | None, Field(description="Version constraint")] = None,
            ctx: MCPContext = None,
        ) -> str:
            """Install, update, and manage tool packages dynamically.

            The AI can use this to expand its own capabilities by installing
            new tools, updating existing ones, or even updating itself.

            Examples:
                tool_install(action="install", package="hanzo-tools-browser")
                tool_install(action="self_update")
                tool_install(action="list")
            """
            return await tool_instance.call(
                ctx,
                action=action,
                package=package,
                source=source,
                version=version,
            )


def register_tool_install(mcp_server) -> list:
    """Register the tool install tool."""
    tool = ToolInstallTool()
    tool.register(mcp_server)
    return [tool]
