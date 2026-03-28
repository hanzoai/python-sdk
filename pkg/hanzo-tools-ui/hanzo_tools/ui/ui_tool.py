"""Unified UI component registry tool (HIP-0300).

Single 'ui' tool for browsing, searching, installing, and managing
UI components from Hanzo and other registries.

Local-first: when ~/work/hanzo/ui exists, reads directly from disk
for the hanzo framework. Falls back to GitHub API otherwise.

Actions:
- list_components: List available components for a framework
- get_component: Get component source code
- get_demo: Get component demo/example
- get_metadata: Get component metadata
- list_blocks: List UI blocks
- get_block: Get block implementation
- search: Search components by name/description
- get_structure: Browse repository directory structure
- install: Install component via CLI
- set_framework: Switch active framework
- get_framework: Show current and available frameworks
- create_composition: Scaffold a composition from components
- list_packages: List all local UI packages (local only)
- read_file: Read any file from the UI repo (local only)
"""

import asyncio
import logging
from typing import ClassVar

from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool

from .github_api import (
    FRAMEWORK_CONFIGS,
    FRAMEWORK_NAMES,
    GitHubAPIClient,
)
from .local_client import LocalUIClient

logger = logging.getLogger(__name__)

# Module-level current framework state
_current_framework = "hanzo"


class UiTool(BaseTool):
    """UI component registry tool (HIP-0300).

    Browse, search, install, and manage UI components from
    Hanzo and other registries (shadcn/ui, Vue, Svelte, React Native).

    Local-first: prefers ~/work/hanzo/ui when available for hanzo framework.
    """

    name: ClassVar[str] = "ui"
    VERSION: ClassVar[str] = "0.2.0"

    def __init__(self):
        super().__init__()
        self._github = GitHubAPIClient()
        self._local = LocalUIClient()
        if self._local.available:
            logger.info("UI tool: local hanzo/ui repo detected, using local-first mode")
        self._register_ui_actions()

    def _use_local(self, framework: str) -> bool:
        """Use local client for hanzo frameworks when repo is available."""
        return framework.startswith("hanzo") and self._local.available

    @property
    def description(self) -> str:
        local_status = " (local repo detected)" if self._local.available else ""
        return f"""UI component registry tool (HIP-0300){local_status}.

Actions:
- list_components: List available components (framework, category)
- get_component: Get component source code (name, framework)
- get_demo: Get component demo/example (name, framework)
- get_metadata: Get component metadata (name, framework)
- list_blocks: List UI blocks (framework, category)
- get_block: Get block implementation (name, framework)
- search: Search components (query, framework)
- get_structure: Browse repo directory structure (path, framework)
- install: Install component via CLI (name, framework)
- set_framework: Switch active framework (framework)
- get_framework: Show current and available frameworks
- create_composition: Scaffold from components (name, components)
- list_packages: List all UI packages (hanzo local only)
- read_file: Read any file from the UI repo by path (hanzo local only)

Frameworks: hanzo (default), hanzo-native, hanzo-vue, hanzo-svelte,
            shadcn, react, svelte, vue, react-native
"""

    def _fw_name(self, framework: str) -> str:
        return FRAMEWORK_NAMES.get(framework, framework)

    def _register_ui_actions(self):
        global _current_framework

        @self.action("list_components", "List available components")
        async def list_components(
            ctx: MCPContext,
            framework: str | None = None,
            category: str | None = None,
        ) -> dict:
            fw = framework or _current_framework
            if fw not in FRAMEWORK_CONFIGS:
                return {"error": f"Unknown framework: {fw}. Available: {', '.join(FRAMEWORK_CONFIGS)}"}

            if self._use_local(fw):
                components = await self._local.list_components(fw)
                source = "local"
            else:
                components = await self._github.list_components(fw)
                source = "github"

            if category:
                components = [c for c in components if c.get("category") == category]

            return {
                "framework": self._fw_name(fw),
                "source": source,
                "total": len(components),
                "components": components,
            }

        @self.action("get_component", "Get component source code")
        async def get_component(
            ctx: MCPContext,
            name: str | None = None,
            component: str | None = None,
            framework: str | None = None,
        ) -> dict:
            comp_name = name or component
            if not comp_name:
                return {"error": "Component name is required"}

            fw = framework or _current_framework

            if self._use_local(fw):
                try:
                    source = await self._local.fetch_component(comp_name, fw)
                    return {
                        "framework": self._fw_name(fw),
                        "component": comp_name,
                        "source": source,
                        "backend": "local",
                    }
                except FileNotFoundError:
                    pass  # Fall through to GitHub

            source = await self._github.fetch_component(comp_name, fw)
            return {
                "framework": self._fw_name(fw),
                "component": comp_name,
                "source": source,
                "backend": "github",
            }

        @self.action("get_demo", "Get component demo/example")
        async def get_demo(
            ctx: MCPContext,
            name: str | None = None,
            component: str | None = None,
            framework: str | None = None,
        ) -> dict:
            comp_name = name or component
            if not comp_name:
                return {"error": "Component name is required"}

            fw = framework or _current_framework

            if self._use_local(fw):
                try:
                    demo = await self._local.fetch_component_demo(comp_name, fw)
                    return {
                        "framework": self._fw_name(fw),
                        "component": comp_name,
                        "demo": demo,
                        "backend": "local",
                    }
                except FileNotFoundError:
                    pass

            demo = await self._github.fetch_component_demo(comp_name, fw)
            return {
                "framework": self._fw_name(fw),
                "component": comp_name,
                "demo": demo,
                "backend": "github",
            }

        @self.action("get_metadata", "Get component metadata")
        async def get_metadata(
            ctx: MCPContext,
            name: str | None = None,
            component: str | None = None,
            framework: str | None = None,
        ) -> dict:
            comp_name = name or component
            if not comp_name:
                return {"error": "Component name is required"}

            fw = framework or _current_framework

            if self._use_local(fw):
                metadata = await self._local.fetch_component_metadata(comp_name, fw)
                return {
                    "framework": self._fw_name(fw),
                    "component": comp_name,
                    "metadata": metadata,
                }

            metadata = await self._github.fetch_component_metadata(comp_name, fw)
            return {
                "framework": self._fw_name(fw),
                "component": comp_name,
                "metadata": metadata,
            }

        @self.action("list_blocks", "List UI blocks")
        async def list_blocks(
            ctx: MCPContext,
            framework: str | None = None,
            category: str | None = None,
        ) -> dict:
            fw = framework or _current_framework

            if self._use_local(fw):
                blocks = await self._local.list_blocks(fw)
                source = "local"
            else:
                blocks = await self._github.list_blocks(fw)
                source = "github"

            if category:
                blocks = [b for b in blocks if b.get("category") == category]

            return {
                "framework": self._fw_name(fw),
                "source": source,
                "total": len(blocks),
                "blocks": blocks,
            }

        @self.action("get_block", "Get block implementation")
        async def get_block(
            ctx: MCPContext,
            name: str | None = None,
            block: str | None = None,
            framework: str | None = None,
        ) -> dict:
            block_name = name or block
            if not block_name:
                return {"error": "Block name is required"}

            fw = framework or _current_framework

            if self._use_local(fw):
                try:
                    content = await self._local.fetch_block(block_name, fw)
                    return {
                        "framework": self._fw_name(fw),
                        "block": block_name,
                        "implementation": content,
                        "backend": "local",
                    }
                except FileNotFoundError:
                    pass

            content = await self._github.fetch_block(block_name, fw)
            return {
                "framework": self._fw_name(fw),
                "block": block_name,
                "implementation": content,
                "backend": "github",
            }

        @self.action("search", "Search components")
        async def search(
            ctx: MCPContext,
            query: str | None = None,
            search: str | None = None,
            framework: str | None = None,
        ) -> dict:
            q = query or search
            if not q:
                return {"error": "Search query is required"}

            fw = framework or _current_framework

            if self._use_local(fw):
                matches = await self._local.search_components(q)
                return {
                    "framework": self._fw_name(fw),
                    "query": q,
                    "source": "local",
                    "results": matches,
                }

            components = await self._github.list_components(fw)
            q_lower = q.lower()

            matches = [
                c
                for c in components
                if q_lower in c.get("name", "").lower()
                or q_lower in c.get("description", "").lower()
                or q_lower in c.get("category", "").lower()
            ]

            return {
                "framework": self._fw_name(fw),
                "query": q,
                "source": "github",
                "results": matches,
            }

        @self.action("get_structure", "Browse repository directory structure")
        async def get_structure(
            ctx: MCPContext,
            path: str = "",
            framework: str | None = None,
            depth: int = 3,
        ) -> dict:
            fw = framework or _current_framework

            if self._use_local(fw):
                structure = await self._local.get_directory_structure(path, fw)
                return {
                    "framework": self._fw_name(fw),
                    "path": path or "pkg/",
                    "source": "local",
                    "structure": structure,
                }

            structure = await self._github.get_directory_structure(path, fw)
            return {
                "framework": self._fw_name(fw),
                "path": path or "/",
                "source": "github",
                "structure": structure,
            }

        @self.action("install", "Install component via CLI")
        async def install(
            ctx: MCPContext,
            name: str | None = None,
            component: str | None = None,
            framework: str | None = None,
            overwrite: bool = False,
        ) -> dict:
            comp_name = name or component
            if not comp_name:
                return {"error": "Component name is required"}

            fw = framework or _current_framework

            if fw.startswith("hanzo"):
                cmd = f"npx @hanzo/ui add {comp_name}"
            elif fw in ("shadcn", "react"):
                cmd = f"npx shadcn@latest add {comp_name}"
            else:
                return {"error": f"Installation not supported for framework: {fw}"}

            if overwrite:
                cmd += " --overwrite"

            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)

            return {
                "framework": self._fw_name(fw),
                "component": comp_name,
                "command": cmd,
                "output": stdout.decode() if stdout else "",
                "warnings": stderr.decode() if stderr else "",
            }

        @self.action("set_framework", "Switch active framework")
        async def set_framework(ctx: MCPContext, framework: str | None = None) -> dict:
            global _current_framework
            if not framework:
                return {"error": "Framework is required"}
            if framework not in FRAMEWORK_CONFIGS:
                return {
                    "error": f"Unknown framework: {framework}. Available: {', '.join(FRAMEWORK_CONFIGS)}"
                }
            _current_framework = framework
            return {
                "success": True,
                "framework": self._fw_name(framework),
                "message": f"Switched to {self._fw_name(framework)}",
            }

        @self.action("get_framework", "Show current and available frameworks")
        async def get_framework(ctx: MCPContext) -> dict:
            return {
                "current": self._fw_name(_current_framework),
                "framework": _current_framework,
                "local_available": self._local.available,
                "available": [
                    {
                        "key": key,
                        "name": FRAMEWORK_NAMES.get(key, key),
                        "has_registry": key.startswith("hanzo"),
                    }
                    for key in FRAMEWORK_CONFIGS
                ],
            }

        @self.action("create_composition", "Scaffold a composition from components")
        async def create_composition(
            ctx: MCPContext,
            name: str | None = None,
            components: list[str] | None = None,
            description: str | None = None,
            framework: str | None = None,
        ) -> dict:
            if not name:
                return {"error": "Composition name is required"}

            fw = framework or _current_framework
            comps = components or []

            lines = ["/**", f" * {name}"]
            if description:
                lines.append(f" * {description}")
            lines.append(f" * Framework: {self._fw_name(fw)}")
            lines.append(f" * Components: {', '.join(comps)}")
            lines.append(" */")
            lines.append("")

            def pascal(s: str) -> str:
                return "".join(p.capitalize() for p in s.split("-"))

            if fw.startswith("hanzo"):
                for comp in comps:
                    lines.append(f'import {{ {pascal(comp)} }} from "@hanzo/ui/{comp}"')
            elif fw in ("shadcn", "react"):
                for comp in comps:
                    lines.append(f'import {{ {pascal(comp)} }} from "@/components/ui/{comp}"')

            lines.append("")
            lines.append(f"export function {name}() {{")
            lines.append("  return (")
            lines.append('    <div className="container mx-auto p-6">')
            for comp in comps:
                lines.append(f"      <{pascal(comp)} />")
            lines.append("    </div>")
            lines.append("  )")
            lines.append("}")

            code = "\n".join(lines) + "\n"

            return {
                "framework": self._fw_name(fw),
                "name": name,
                "code": code,
                "components": comps,
            }

        @self.action("list_packages", "List all UI packages (local only)")
        async def list_packages(ctx: MCPContext) -> dict:
            if not self._local.available:
                return {"error": "Local hanzo/ui repo not found. Set HANZO_UI_PATH or clone to ~/work/hanzo/ui"}

            packages = await self._local.list_packages()
            return {
                "source": "local",
                "total": len(packages),
                "packages": packages,
            }

        @self.action("read_file", "Read any file from the UI repo by relative path")
        async def read_file(
            ctx: MCPContext,
            path: str | None = None,
            file: str | None = None,
        ) -> dict:
            file_path = path or file
            if not file_path:
                return {"error": "File path is required (relative to hanzo/ui root)"}

            if not self._local.available:
                return {"error": "Local hanzo/ui repo not found. Set HANZO_UI_PATH or clone to ~/work/hanzo/ui"}

            content = await self._local.read_file(file_path)
            return {
                "path": file_path,
                "source": "local",
                "content": content,
            }

    # Inherits call() and register() from BaseTool — action routing is automatic


# Singleton reference
ui_tool = UiTool
