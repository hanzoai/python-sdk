"""Registry client — fetches component data from the Hanzo UI registry server.

Mirrors the GitHubAPIClient / LocalUIClient interface so it can be used
as a drop-in backend in UiTool. Has its own short TTL cache to avoid
hitting the server on every tool call during a session.
"""

import os
import time
from typing import Any

import httpx

DEFAULT_REGISTRY_URL = "https://ui.hanzo.ai"
CLIENT_CACHE_TTL = 60  # 1 minute local cache


class RegistryClient:
    """Client for the Hanzo UI registry server."""

    def __init__(self, base_url: str | None = None):
        self._base_url = (
            base_url
            or os.environ.get("HANZO_UI_REGISTRY_URL")
            or DEFAULT_REGISTRY_URL
        ).rstrip("/")
        self._client: httpx.AsyncClient | None = None
        self._cache: dict[str, tuple[Any, float]] = {}
        self._available: bool | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=15.0,
                headers={"User-Agent": "Hanzo-MCP-UI-Tool"},
            )
        return self._client

    def _cache_get(self, key: str) -> Any | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        data, ts = entry
        if time.time() - ts > CLIENT_CACHE_TTL:
            del self._cache[key]
            return None
        return data

    def _cache_set(self, key: str, data: Any) -> None:
        self._cache[key] = (data, time.time())

    async def _get(self, path: str, params: dict | None = None) -> Any:
        cache_key = f"{path}:{params}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        client = await self._get_client()
        resp = await client.get(path, params=params)
        resp.raise_for_status()
        data = resp.json()
        self._cache_set(cache_key, data)
        return data

    async def check_available(self) -> bool:
        """Check if the registry server is reachable."""
        if self._available is not None:
            return self._available
        try:
            client = await self._get_client()
            resp = await client.get("/api/health", timeout=5.0)
            self._available = resp.status_code == 200
        except Exception:
            self._available = False
        return self._available

    @property
    def available(self) -> bool | None:
        """Cached availability check result. None if not yet checked."""
        return self._available

    # --- Mirror of GitHubAPIClient / LocalUIClient interface ---

    async def list_components(self, framework: str = "hanzo") -> list[dict]:
        data = await self._get("/api/components", {"framework": framework})
        return data.get("components", [])

    async def fetch_component(self, name: str, framework: str = "hanzo") -> str:
        data = await self._get(f"/api/components/{name}", {"framework": framework})
        source = data.get("source")
        if source is None:
            raise FileNotFoundError(f"Component '{name}' source not available")
        return source

    async def fetch_component_demo(self, name: str, framework: str = "hanzo") -> str:
        data = await self._get(
            f"/api/components/{name}/demo", {"framework": framework}
        )
        demo = data.get("demo")
        if demo is None:
            raise FileNotFoundError(f"Demo for '{name}' not available")
        return demo

    async def fetch_component_metadata(
        self, name: str, framework: str = "hanzo"
    ) -> dict:
        data = await self._get(
            f"/api/components/{name}/metadata", {"framework": framework}
        )
        return data.get("metadata", data)

    async def list_blocks(self, framework: str = "hanzo") -> list[dict]:
        data = await self._get("/api/blocks", {"framework": framework})
        return data.get("blocks", [])

    async def fetch_block(self, name: str, framework: str = "hanzo") -> str:
        data = await self._get(f"/api/blocks/{name}", {"framework": framework})
        source = data.get("source")
        if source is None:
            raise FileNotFoundError(f"Block '{name}' source not available")
        return source

    async def search_components(self, query: str, framework: str = "hanzo") -> list[dict]:
        data = await self._get("/api/search", {"q": query, "framework": framework})
        return data.get("results", [])

    async def get_directory_structure(
        self, path: str, framework: str = "hanzo"
    ) -> dict:
        return await self._get("/api/structure", {"path": path, "framework": framework})

    async def fetch_full_index(self, framework: str = "hanzo") -> dict:
        """Fetch the full registry index — all components in one payload.

        Use this to hydrate a local cache with a single HTTP call.
        """
        return await self._get("/registry/index.json", {"framework": framework})

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
