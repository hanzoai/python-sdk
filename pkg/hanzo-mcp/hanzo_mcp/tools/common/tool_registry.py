"""Dynamic package manager with hot-reload and self-update capabilities.

Enables:
- Installing tool packages dynamically
- Hot-reloading tools without server restart
- Self-updating the AI's tooling
- Cross-session tool persistence

Note: This is distinct from:
- tools/common/base.py::ToolRegistry - For registering tools with FastMCP
- config/tool_config.py::DynamicToolRegistry - For discovering tools from entry points
"""

import os
import sys
import json
import asyncio
import logging
import importlib
import subprocess
from typing import Any, Type, Callable, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import field, dataclass

logger = logging.getLogger(__name__)


@dataclass
class ToolPackage:
    """Represents an installed tool package."""

    name: str
    version: str
    source: str  # "pypi", "git", "local"
    installed_at: datetime
    tools: list[str] = field(default_factory=list)
    enabled: bool = True


class PackageManager:
    """Centralized registry for dynamic tool management.

    Features:
    - Install tools from PyPI/git/local
    - Hot-reload without restart
    - Track installed packages
    - Enable/disable per tool
    """

    _instance: Optional["PackageManager"] = None
    _lock = asyncio.Lock()

    def __init__(self):
        self._packages: dict[str, ToolPackage] = {}
        self._tools: dict[str, Any] = {}  # name -> tool instance
        self._tool_classes: dict[str, Type] = {}  # name -> tool class
        self._config_path = Path.home() / ".hanzo" / "mcp" / "registry.json"
        self._tools_path = Path.home() / ".hanzo" / "tools"  # Tool packages install here
        self._reload_callbacks: list[Callable] = []
        self._mcp_server = None

        self._tools_path.mkdir(parents=True, exist_ok=True)
        self._load_config()

    @classmethod
    async def get_instance(cls) -> "PackageManager":
        """Get singleton instance."""
        async with cls._lock:
            if cls._instance is None:
                cls._instance = PackageManager()
            return cls._instance

    def set_mcp_server(self, mcp_server) -> None:
        """Set the MCP server for tool registration."""
        self._mcp_server = mcp_server

    def on_reload(self, callback: Callable) -> None:
        """Register callback for reload events."""
        self._reload_callbacks.append(callback)

    def _load_config(self) -> None:
        """Load registry config from disk."""
        if self._config_path.exists():
            try:
                with open(self._config_path) as f:
                    data = json.load(f)
                for name, pkg_data in data.get("packages", {}).items():
                    self._packages[name] = ToolPackage(
                        name=pkg_data["name"],
                        version=pkg_data["version"],
                        source=pkg_data["source"],
                        installed_at=datetime.fromisoformat(pkg_data["installed_at"]),
                        tools=pkg_data.get("tools", []),
                        enabled=pkg_data.get("enabled", True),
                    )
            except Exception as e:
                logger.warning(f"Failed to load registry config: {e}")

    def _save_config(self) -> None:
        """Save registry config to disk."""
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "packages": {
                name: {
                    "name": pkg.name,
                    "version": pkg.version,
                    "source": pkg.source,
                    "installed_at": pkg.installed_at.isoformat(),
                    "tools": pkg.tools,
                    "enabled": pkg.enabled,
                }
                for name, pkg in self._packages.items()
            }
        }
        with open(self._config_path, "w") as f:
            json.dump(data, f, indent=2)

    async def install(
        self,
        package: str,
        source: str = "pypi",
        version: Optional[str] = None,
        upgrade: bool = False,
    ) -> dict[str, Any]:
        """Install a tool package.

        Args:
            package: Package name or git URL
            source: "pypi", "git", or "local"
            version: Specific version (optional)
            upgrade: Upgrade if already installed

        Returns:
            Installation result
        """
        try:
            if source == "pypi":
                # Install from PyPI
                pkg_spec = f"{package}=={version}" if version else package
                cmd = [sys.executable, "-m", "uv", "pip", "install"]
                if upgrade:
                    cmd.append("--upgrade")
                cmd.extend(["--target", str(self._tools_path), pkg_spec])

                result = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await result.communicate()

                if result.returncode != 0:
                    return {
                        "success": False,
                        "error": stderr.decode(),
                        "package": package,
                    }

                # Get installed version
                installed_version = version or "latest"

            elif source == "git":
                # Install from git
                cmd = [
                    sys.executable,
                    "-m",
                    "uv",
                    "pip",
                    "install",
                    "--target",
                    str(self._tools_path),
                    f"git+{package}",
                ]

                result = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await result.communicate()

                if result.returncode != 0:
                    return {
                        "success": False,
                        "error": stderr.decode(),
                        "package": package,
                    }

                installed_version = "git"

            elif source == "local":
                # Install from local path
                cmd = [
                    sys.executable,
                    "-m",
                    "uv",
                    "pip",
                    "install",
                    "--target",
                    str(self._tools_path),
                    "-e",
                    package,
                ]

                result = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await result.communicate()

                if result.returncode != 0:
                    return {
                        "success": False,
                        "error": stderr.decode(),
                        "package": package,
                    }

                installed_version = "local"
            else:
                return {"success": False, "error": f"Unknown source: {source}"}

            # Record package
            pkg_name = package.split("/")[-1] if "/" in package else package
            pkg_name = pkg_name.replace(".git", "")

            self._packages[pkg_name] = ToolPackage(
                name=pkg_name,
                version=installed_version,
                source=source,
                installed_at=datetime.now(),
                enabled=True,
            )
            self._save_config()

            # Hot-reload the package
            await self.reload_package(pkg_name)

            return {
                "success": True,
                "package": pkg_name,
                "version": installed_version,
                "source": source,
                "tools": self._packages[pkg_name].tools,
            }

        except Exception as e:
            logger.exception(f"Failed to install package: {package}")
            return {"success": False, "error": str(e), "package": package}

    async def uninstall(self, package: str) -> dict[str, Any]:
        """Uninstall a tool package."""
        if package not in self._packages:
            return {"success": False, "error": f"Package not found: {package}"}

        try:
            cmd = [
                sys.executable,
                "-m",
                "uv",
                "pip",
                "uninstall",
                "--target",
                str(self._tools_path),
                "-y",
                package,
            ]

            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await result.communicate()

            # Remove from registry
            pkg = self._packages.pop(package, None)

            # Unregister tools
            if pkg:
                for tool_name in pkg.tools:
                    self._tools.pop(tool_name, None)
                    self._tool_classes.pop(tool_name, None)

            self._save_config()

            return {"success": True, "package": package}

        except Exception as e:
            return {"success": False, "error": str(e), "package": package}

    async def upgrade(self, package: Optional[str] = None) -> dict[str, Any]:
        """Upgrade package(s) to latest version.

        Args:
            package: Specific package or None for all
        """
        results = []

        packages_to_upgrade = [package] if package else list(self._packages.keys())

        for pkg_name in packages_to_upgrade:
            if pkg_name not in self._packages:
                results.append({"package": pkg_name, "error": "Not installed"})
                continue

            pkg = self._packages[pkg_name]
            result = await self.install(
                pkg.name,
                source=pkg.source,
                upgrade=True,
            )
            results.append(result)

        return {
            "success": all(r.get("success", False) for r in results),
            "results": results,
        }

    async def reload_package(self, package: str) -> dict[str, Any]:
        """Hot-reload a package without server restart."""
        if package not in self._packages:
            return {"success": False, "error": f"Package not found: {package}"}

        try:
            # Add tools path to sys.path if not there
            tools_path_str = str(self._tools_path)
            if tools_path_str not in sys.path:
                sys.path.insert(0, tools_path_str)

            # Try to import/reload the package
            try:
                # Clear existing module from cache
                modules_to_remove = [
                    mod for mod in sys.modules if mod.startswith(package) or mod.startswith(package.replace("-", "_"))
                ]
                for mod in modules_to_remove:
                    del sys.modules[mod]

                # Import the package
                pkg_module = importlib.import_module(package.replace("-", "_"))

                # Look for tools
                tools_found = []

                # Check for TOOLS export
                if hasattr(pkg_module, "TOOLS"):
                    for tool_class in pkg_module.TOOLS:
                        tool_name = getattr(tool_class, "name", tool_class.__name__)
                        self._tool_classes[tool_name] = tool_class
                        tools_found.append(tool_name)

                        # Register with MCP server if available
                        if self._mcp_server:
                            try:
                                tool_instance = tool_class()
                                if hasattr(tool_instance, "register"):
                                    tool_instance.register(self._mcp_server)
                                self._tools[tool_name] = tool_instance
                            except Exception as e:
                                logger.warning(f"Failed to register tool {tool_name}: {e}")

                # Check for register_* functions
                for attr_name in dir(pkg_module):
                    if attr_name.startswith("register_") and callable(getattr(pkg_module, attr_name)):
                        register_func = getattr(pkg_module, attr_name)
                        if self._mcp_server:
                            try:
                                registered = register_func(self._mcp_server)
                                if registered:
                                    for tool in registered:
                                        tool_name = getattr(tool, "name", str(tool))
                                        tools_found.append(tool_name)
                            except Exception as e:
                                logger.warning(f"Failed to call {attr_name}: {e}")

                # Update package tools list
                self._packages[package].tools = tools_found
                self._save_config()

                # Notify callbacks
                for callback in self._reload_callbacks:
                    try:
                        callback(package, tools_found)
                    except Exception:
                        pass

                return {
                    "success": True,
                    "package": package,
                    "tools": tools_found,
                }

            except ImportError as e:
                return {"success": False, "error": f"Import failed: {e}", "package": package}

        except Exception as e:
            logger.exception(f"Failed to reload package: {package}")
            return {"success": False, "error": str(e), "package": package}

    async def self_update(self) -> dict[str, Any]:
        """Update hanzo-mcp itself (the AI updates its own tooling)."""
        try:
            # Get current version
            from hanzo_mcp import __version__ as current_version

            # Check for updates
            cmd = [sys.executable, "-m", "uv", "pip", "install", "--upgrade", "hanzo-mcp"]

            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": stderr.decode(),
                    "current_version": current_version,
                }

            # Check new version (requires restart to take effect)
            output = stdout.decode()

            return {
                "success": True,
                "current_version": current_version,
                "message": "Updated successfully. Restart required for changes to take effect.",
                "output": output,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_packages(self) -> list[dict[str, Any]]:
        """List all installed tool packages."""
        return [
            {
                "name": pkg.name,
                "version": pkg.version,
                "source": pkg.source,
                "installed_at": pkg.installed_at.isoformat(),
                "tools": pkg.tools,
                "enabled": pkg.enabled,
            }
            for pkg in self._packages.values()
        ]

    def list_tools(self) -> list[str]:
        """List all registered tools."""
        return list(self._tools.keys())

    def get_tool(self, name: str) -> Optional[Any]:
        """Get a tool instance by name."""
        return self._tools.get(name)


# Singleton access
_package_manager: Optional[PackageManager] = None


async def get_package_manager() -> PackageManager:
    """Get the global package manager instance."""
    global _package_manager
    if _package_manager is None:
        _package_manager = await PackageManager.get_instance()
    return _package_manager


# Backwards compatibility alias
async def get_registry() -> PackageManager:
    """Deprecated: Use get_package_manager() instead."""
    return await get_package_manager()
