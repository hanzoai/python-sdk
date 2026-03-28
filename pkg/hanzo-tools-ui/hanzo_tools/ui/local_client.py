"""Local filesystem client for reading UI components from ~/work/hanzo/ui.

When the hanzo/ui repo is cloned locally, this client reads component source
directly from disk — no GitHub API calls, no rate limits, always up-to-date
with the developer's working tree.
"""

import json
import os
from pathlib import Path
from typing import Any

import aiofiles

# Default local repo path; overridable via HANZO_UI_PATH env var
DEFAULT_UI_PATH = os.path.expanduser("~/work/hanzo/ui")

# Local package layout — maps to the actual repo structure
LOCAL_PACKAGES: dict[str, dict[str, str]] = {
    "ui": {
        "primitives": "pkg/ui/primitives",
        "src": "pkg/ui/src",
        "blocks": "pkg/ui/primitives",  # blocks live alongside primitives
        "style": "pkg/ui/style",
        "docs": "pkg/ui/docs",
        "util": "pkg/ui/util",
    },
    "react": {
        "components": "pkg/react/src/components",
        "hooks": "pkg/react/src/hooks",
    },
    "commerce": {
        "components": "pkg/commerce/components",
    },
    "brand": {
        "root": "pkg/brand",
    },
    "gui": {
        "root": "pkg/gui",
    },
    "shop": {
        "root": "pkg/shop",
    },
    "checkout": {
        "root": "pkg/checkout",
    },
    "agent-ui": {
        "root": "pkg/agent-ui",
    },
    "tokens": {
        "root": "pkg/tokens",
    },
}

# Extensions to search for components
COMPONENT_EXTENSIONS = (".tsx", ".ts", ".jsx", ".js")


class LocalUIClient:
    """Reads Hanzo UI components from the local filesystem."""

    def __init__(self, ui_path: str | None = None):
        self._ui_path = Path(ui_path or os.environ.get("HANZO_UI_PATH", DEFAULT_UI_PATH))

    @property
    def available(self) -> bool:
        """Check if the local UI repo exists."""
        return (self._ui_path / "pkg" / "ui").is_dir()

    async def list_components(self, framework: str = "hanzo") -> list[dict]:
        """List all components from the local primitives directory."""
        primitives_dir = self._ui_path / "pkg" / "ui" / "primitives"
        if not primitives_dir.is_dir():
            return []

        components = []
        for entry in sorted(primitives_dir.iterdir()):
            if entry.name.startswith(("_", ".")):
                continue
            if entry.name.startswith("index"):
                continue
            if entry.is_dir():
                components.append(
                    {
                        "name": entry.name,
                        "type": "dir",
                        "path": str(entry.relative_to(self._ui_path)),
                    }
                )
            elif entry.is_file() and entry.suffix in COMPONENT_EXTENSIONS:
                components.append(
                    {
                        "name": entry.stem,
                        "type": "file",
                        "path": str(entry.relative_to(self._ui_path)),
                    }
                )
        return components

    async def fetch_component(self, name: str, framework: str = "hanzo") -> str:
        """Fetch component source code from local filesystem."""
        # Search in primitives first, then src modules
        search_dirs = [
            self._ui_path / "pkg" / "ui" / "primitives",
            self._ui_path / "pkg" / "ui" / "src",
            self._ui_path / "pkg" / "react" / "src" / "components",
        ]

        for base_dir in search_dirs:
            if not base_dir.is_dir():
                continue
            # Try direct file match
            for ext in COMPONENT_EXTENSIONS:
                candidate = base_dir / f"{name}{ext}"
                if candidate.is_file():
                    async with aiofiles.open(candidate) as f:
                        return await f.read()

            # Try directory with index file
            comp_dir = base_dir / name
            if comp_dir.is_dir():
                for ext in COMPONENT_EXTENSIONS:
                    index = comp_dir / f"index{ext}"
                    if index.is_file():
                        async with aiofiles.open(index) as f:
                            return await f.read()

        # Search in src barrel exports
        barrel = self._ui_path / "pkg" / "ui" / "src" / f"{name}.ts"
        if barrel.is_file():
            async with aiofiles.open(barrel) as f:
                return await f.read()

        raise FileNotFoundError(f"Component '{name}' not found locally in hanzo/ui")

    async def fetch_component_demo(self, name: str, framework: str = "hanzo") -> str:
        """Fetch component demo from local filesystem."""
        # Check demo/ app directory
        demo_dirs = [
            self._ui_path / "demo",
            self._ui_path / "apps",
        ]
        for demo_dir in demo_dirs:
            if not demo_dir.is_dir():
                continue
            for ext in COMPONENT_EXTENSIONS:
                candidate = demo_dir / f"{name}{ext}"
                if candidate.is_file():
                    async with aiofiles.open(candidate) as f:
                        return await f.read()

        # Check for demo file alongside component
        primitives_dir = self._ui_path / "pkg" / "ui" / "primitives"
        comp_dir = primitives_dir / name
        if comp_dir.is_dir():
            for ext in COMPONENT_EXTENSIONS:
                demo = comp_dir / f"demo{ext}"
                if demo.is_file():
                    async with aiofiles.open(demo) as f:
                        return await f.read()

        raise FileNotFoundError(f"Demo for '{name}' not found locally")

    async def fetch_component_metadata(self, name: str, framework: str = "hanzo") -> dict:
        """Fetch component metadata from local filesystem."""
        primitives_dir = self._ui_path / "pkg" / "ui" / "primitives"

        # Check for metadata.json in component directory
        meta_path = primitives_dir / name / "metadata.json"
        if meta_path.is_file():
            async with aiofiles.open(meta_path) as f:
                content = await f.read()
                return json.loads(content)

        # Build metadata from file info
        for ext in COMPONENT_EXTENSIONS:
            comp_file = primitives_dir / f"{name}{ext}"
            if comp_file.is_file():
                stat = comp_file.stat()
                return {
                    "name": name,
                    "framework": "hanzo",
                    "path": str(comp_file.relative_to(self._ui_path)),
                    "size": stat.st_size,
                    "extension": ext,
                    "source": "local",
                }

        return {"name": name, "framework": "hanzo", "source": "local"}

    async def list_blocks(self, framework: str = "hanzo") -> list[dict]:
        """List blocks from local filesystem."""
        # Check index-blocks.ts for block exports
        blocks_index = self._ui_path / "pkg" / "ui" / "primitives" / "index-blocks.ts"
        if blocks_index.is_file():
            async with aiofiles.open(blocks_index) as f:
                content = await f.read()
            blocks = []
            for line in content.splitlines():
                if line.strip().startswith("export"):
                    # Extract component names from export lines
                    name = line.split("from")[-1].strip().strip("';\"").split("/")[-1]
                    if name:
                        blocks.append({"name": name, "type": "export"})
            return blocks
        return []

    async def fetch_block(self, name: str, framework: str = "hanzo") -> str:
        """Fetch block source code."""
        return await self.fetch_component(name, framework)

    async def get_directory_structure(self, path: str, framework: str = "hanzo") -> dict:
        """Browse directory structure of the local UI repo."""
        if path:
            target = self._ui_path / path
        else:
            target = self._ui_path / "pkg"

        if not target.is_dir():
            raise FileNotFoundError(f"Directory not found: {path}")

        children = []
        for entry in sorted(target.iterdir()):
            if entry.name.startswith(".") or entry.name == "node_modules":
                continue
            item: dict[str, Any] = {
                "name": entry.name,
                "type": "dir" if entry.is_dir() else "file",
                "path": str(entry.relative_to(self._ui_path)),
            }
            if entry.is_file():
                item["size"] = entry.stat().st_size
            children.append(item)

        return {"path": path or "pkg/", "children": children}

    async def list_packages(self) -> list[dict]:
        """List all UI packages available locally."""
        pkg_dir = self._ui_path / "pkg"
        if not pkg_dir.is_dir():
            return []

        packages = []
        for entry in sorted(pkg_dir.iterdir()):
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            pkg_json = entry / "package.json"
            info: dict[str, Any] = {
                "name": entry.name,
                "path": str(entry.relative_to(self._ui_path)),
            }
            if pkg_json.is_file():
                async with aiofiles.open(pkg_json) as f:
                    try:
                        data = json.loads(await f.read())
                        info["version"] = data.get("version", "unknown")
                        info["description"] = data.get("description", "")
                    except json.JSONDecodeError:
                        pass
            packages.append(info)
        return packages

    async def read_file(self, path: str) -> str:
        """Read any file from the UI repo by relative path."""
        target = self._ui_path / path
        if not target.is_file():
            raise FileNotFoundError(f"File not found: {path}")
        async with aiofiles.open(target) as f:
            return await f.read()

    async def search_components(self, query: str) -> list[dict]:
        """Search component files by name and content."""
        query_lower = query.lower()
        results = []

        primitives_dir = self._ui_path / "pkg" / "ui" / "primitives"
        if not primitives_dir.is_dir():
            return results

        for entry in sorted(primitives_dir.iterdir()):
            if entry.name.startswith(("_", ".")) or entry.name.startswith("index"):
                continue

            name = entry.stem if entry.is_file() else entry.name
            if query_lower in name.lower():
                results.append(
                    {
                        "name": name,
                        "type": "dir" if entry.is_dir() else "file",
                        "path": str(entry.relative_to(self._ui_path)),
                        "match": "name",
                    }
                )

        # Also search src modules
        src_dir = self._ui_path / "pkg" / "ui" / "src"
        if src_dir.is_dir():
            for entry in sorted(src_dir.iterdir()):
                if entry.name.startswith(("_", ".")):
                    continue
                name = entry.stem if entry.is_file() else entry.name
                if query_lower in name.lower() and name not in [r["name"] for r in results]:
                    results.append(
                        {
                            "name": name,
                            "type": "dir" if entry.is_dir() else "file",
                            "path": str(entry.relative_to(self._ui_path)),
                            "match": "name",
                        }
                    )

        return results
