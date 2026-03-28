"""Registry cache — eagerly fetches all component data from GitHub.

On startup, walks the hanzoai/ui repo and fetches every component's
source, metadata, and demo. Stores everything in memory. Refreshes
on a background timer. All lookups are O(1) dict reads.
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

from ..github_api import FRAMEWORK_CONFIGS, GitHubAPIClient

logger = logging.getLogger(__name__)

DEFAULT_REFRESH_INTERVAL = int(os.environ.get("REFRESH_INTERVAL", "900"))  # 15 min
MAX_CONCURRENCY = 10


@dataclass
class ComponentEntry:
    name: str
    type: str  # "file" or "dir"
    path: str = ""
    source: str | None = None
    metadata: dict | None = None
    demo: str | None = None
    category: str = ""
    description: str = ""


@dataclass
class FrameworkData:
    """All cached data for a single framework."""

    components: dict[str, ComponentEntry] = field(default_factory=dict)
    blocks: dict[str, ComponentEntry] = field(default_factory=dict)
    directory_cache: dict[str, dict] = field(default_factory=dict)


class RegistryCache:
    """In-memory cache of all UI component data from GitHub."""

    def __init__(
        self,
        frameworks: list[str] | None = None,
        refresh_interval: int = DEFAULT_REFRESH_INTERVAL,
    ):
        self._github = GitHubAPIClient()
        self._frameworks = frameworks or ["hanzo"]
        self._refresh_interval = refresh_interval
        self._data: dict[str, FrameworkData] = {}
        self._last_refresh: float = 0
        self._refresh_duration: float = 0
        self._refreshing = False
        self._ready = False
        self._task: asyncio.Task | None = None

    @property
    def ready(self) -> bool:
        return self._ready

    @property
    def health(self) -> dict:
        total_components = sum(len(d.components) for d in self._data.values())
        total_blocks = sum(len(d.blocks) for d in self._data.values())
        age = time.time() - self._last_refresh if self._last_refresh else None
        return {
            "status": "healthy" if self._ready else "warming",
            "ready": self._ready,
            "last_refresh": self._last_refresh,
            "cache_age_seconds": round(age, 1) if age else None,
            "refresh_duration_seconds": round(self._refresh_duration, 1),
            "refreshing": self._refreshing,
            "frameworks": self._frameworks,
            "components_cached": total_components,
            "blocks_cached": total_blocks,
        }

    async def refresh(self) -> None:
        """Full refresh: fetch all components for all frameworks."""
        if self._refreshing:
            logger.info("Refresh already in progress, skipping")
            return

        self._refreshing = True
        start = time.time()
        logger.info("Starting cache refresh for frameworks: %s", self._frameworks)

        try:
            for framework in self._frameworks:
                await self._refresh_framework(framework)
        except Exception:
            logger.exception("Cache refresh failed")
        finally:
            self._refreshing = False
            self._last_refresh = time.time()
            self._refresh_duration = time.time() - start
            self._ready = True
            total = sum(len(d.components) for d in self._data.values())
            logger.info(
                "Cache refresh complete: %d components in %.1fs",
                total,
                self._refresh_duration,
            )

    async def _refresh_framework(self, framework: str) -> None:
        """Refresh all data for a single framework."""
        if framework not in FRAMEWORK_CONFIGS:
            logger.warning("Unknown framework: %s", framework)
            return

        fw_data = FrameworkData()
        sem = asyncio.Semaphore(MAX_CONCURRENCY)

        # Fetch component list
        try:
            comp_list = await self._github.list_components(framework)
        except Exception:
            logger.exception("Failed to list components for %s", framework)
            return

        # Fetch source + metadata + demo for each component concurrently
        async def fetch_one(comp: dict) -> ComponentEntry:
            name = comp["name"]
            entry = ComponentEntry(
                name=name,
                type=comp.get("type", "file"),
                path=comp.get("path", ""),
            )
            async with sem:
                # Source
                try:
                    entry.source = await self._github.fetch_component(name, framework)
                except Exception:
                    logger.debug("No source for %s/%s", framework, name)

                # Metadata
                try:
                    entry.metadata = await self._github.fetch_component_metadata(
                        name, framework
                    )
                except Exception:
                    pass

                # Demo
                try:
                    entry.demo = await self._github.fetch_component_demo(
                        name, framework
                    )
                except Exception:
                    pass

            return entry

        entries = await asyncio.gather(
            *[fetch_one(c) for c in comp_list],
            return_exceptions=True,
        )

        for entry in entries:
            if isinstance(entry, ComponentEntry):
                fw_data.components[entry.name] = entry
            elif isinstance(entry, Exception):
                logger.debug("Component fetch error: %s", entry)

        # Fetch blocks
        try:
            block_list = await self._github.list_blocks(framework)
            for block in block_list:
                name = block["name"]
                b_entry = ComponentEntry(name=name, type=block.get("type", "file"))
                try:
                    async with sem:
                        b_entry.source = await self._github.fetch_block(
                            name, framework
                        )
                except Exception:
                    pass
                fw_data.blocks[name] = b_entry
        except Exception:
            logger.debug("No blocks for %s", framework)

        # Cache directory structure
        config = FRAMEWORK_CONFIGS[framework]
        try:
            structure = await self._github.get_directory_structure(
                config.components_path, framework
            )
            fw_data.directory_cache[config.components_path] = structure
        except Exception:
            pass

        # Atomic swap
        self._data[framework] = fw_data
        logger.info(
            "Cached %d components, %d blocks for %s",
            len(fw_data.components),
            len(fw_data.blocks),
            framework,
        )

    async def start_background_refresh(self) -> None:
        """Run refresh loop in the background."""
        while True:
            await asyncio.sleep(self._refresh_interval)
            try:
                await self.refresh()
            except Exception:
                logger.exception("Background refresh failed")

    def start(self) -> None:
        """Start the background refresh task."""
        if self._task is None:
            self._task = asyncio.create_task(self.start_background_refresh())

    def stop(self) -> None:
        """Stop the background refresh task."""
        if self._task is not None:
            self._task.cancel()
            self._task = None

    # --- Lookup methods (all O(1)) ---

    def _fw(self, framework: str) -> FrameworkData:
        return self._data.get(framework, FrameworkData())

    def get_components(self, framework: str = "hanzo") -> list[dict]:
        return [
            {
                "name": e.name,
                "type": e.type,
                "path": e.path,
                "has_source": e.source is not None,
                "has_demo": e.demo is not None,
            }
            for e in self._fw(framework).components.values()
        ]

    def get_component(self, name: str, framework: str = "hanzo") -> dict | None:
        entry = self._fw(framework).components.get(name)
        if entry is None:
            return None
        return {
            "name": entry.name,
            "type": entry.type,
            "source": entry.source,
            "metadata": entry.metadata,
            "demo": entry.demo,
        }

    def get_component_source(self, name: str, framework: str = "hanzo") -> str | None:
        entry = self._fw(framework).components.get(name)
        return entry.source if entry else None

    def get_component_demo(self, name: str, framework: str = "hanzo") -> str | None:
        entry = self._fw(framework).components.get(name)
        return entry.demo if entry else None

    def get_component_metadata(
        self, name: str, framework: str = "hanzo"
    ) -> dict | None:
        entry = self._fw(framework).components.get(name)
        return entry.metadata if entry else None

    def get_blocks(self, framework: str = "hanzo") -> list[dict]:
        return [
            {"name": e.name, "type": e.type, "has_source": e.source is not None}
            for e in self._fw(framework).blocks.values()
        ]

    def get_block(self, name: str, framework: str = "hanzo") -> dict | None:
        entry = self._fw(framework).blocks.get(name)
        if entry is None:
            return None
        return {"name": entry.name, "source": entry.source}

    def search(self, query: str, framework: str = "hanzo") -> list[dict]:
        q = query.lower()
        results = []
        for entry in self._fw(framework).components.values():
            if (
                q in entry.name.lower()
                or q in entry.description.lower()
                or q in entry.category.lower()
            ):
                results.append(
                    {"name": entry.name, "type": entry.type, "match": "name"}
                )
        return results

    def get_structure(
        self, path: str, framework: str = "hanzo"
    ) -> dict[str, Any] | None:
        return self._fw(framework).directory_cache.get(path)

    def build_index(self, framework: str = "hanzo") -> dict:
        """Build the full registry index (single-payload for client hydration)."""
        components = {}
        for name, entry in self._fw(framework).components.items():
            components[name] = {
                "name": entry.name,
                "type": entry.type,
                "source": entry.source,
                "metadata": entry.metadata,
                "demo": entry.demo,
            }

        blocks = {}
        for name, entry in self._fw(framework).blocks.items():
            blocks[name] = {"name": entry.name, "source": entry.source}

        return {
            "framework": framework,
            "generated_at": self._last_refresh,
            "components": components,
            "blocks": blocks,
            "total_components": len(components),
            "total_blocks": len(blocks),
        }
