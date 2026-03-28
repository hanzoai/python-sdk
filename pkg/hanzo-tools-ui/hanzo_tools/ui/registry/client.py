"""Registry client — fetches component data from the Hanzo UI site.

Works with both:
- Static hosting (CF Pages, GitHub Pages): fetches pre-built JSON from /api/registry/
- Server mode (Hanzo PaaS, dev): hits Next.js API routes at /api/registry/

Mirrors the GitHubAPIClient / LocalUIClient interface so it can be used
as a drop-in backend in UiTool. Has its own short TTL cache to avoid
hitting the server on every tool call during a session.
"""

import os
import time
from typing import Any

import httpx

# Registry URLs by framework
REGISTRY_URLS: dict[str, str] = {
    "hanzo": "https://ui.hanzo.ai",
    "lux": "https://ui.lux.finance",
}
DEFAULT_REGISTRY_URL = "https://ui.hanzo.ai"
CLIENT_CACHE_TTL = 300  # 5 min local cache (server data is pre-built)


class RegistryClient:
    """Client for the Hanzo UI registry (static or dynamic)."""

    def __init__(self, base_url: str | None = None):
        self._base_url = (
            base_url
            or os.environ.get("HANZO_UI_REGISTRY_URL")
            or DEFAULT_REGISTRY_URL
        ).rstrip("/")
        self._client: httpx.AsyncClient | None = None
        self._cache: dict[str, tuple[Any, float]] = {}
        self._available: bool | None = None
        # Full index cache — hydrated on first use
        self._index: dict | None = None
        self._index_ts: float = 0

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=15.0,
                follow_redirects=True,
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
        """Check if the registry is reachable (tries static files first)."""
        if self._available is not None:
            return self._available
        try:
            client = await self._get_client()
            # Try the static components.json (works on CF Pages / static hosting)
            resp = await client.get("/api/registry/components.json", timeout=5.0)
            if resp.status_code == 200:
                self._available = True
                return True
            # Try server-mode health endpoint
            resp = await client.get("/api/health", timeout=5.0)
            self._available = resp.status_code == 200
        except Exception:
            self._available = False
        return self._available

    @property
    def available(self) -> bool | None:
        return self._available

    async def _ensure_index(self) -> dict:
        """Fetch and cache the full index (single HTTP call, all components)."""
        if self._index and time.time() - self._index_ts < CLIENT_CACHE_TTL:
            return self._index

        try:
            # Try static file first (CF Pages)
            data = await self._get("/api/registry/index.json")
        except Exception:
            # Fallback to server-mode API route
            data = await self._get("/api/registry/index")

        self._index = data
        self._index_ts = time.time()
        return data

    def _extract_source(self, component: dict) -> str | None:
        """Extract source code from a registry component entry."""
        files = component.get("files", [])
        if not files:
            return None
        first = files[0]
        if isinstance(first, dict):
            return first.get("content")
        return None

    # --- Mirror of GitHubAPIClient / LocalUIClient interface ---

    async def list_components(self, framework: str = "hanzo") -> list[dict]:
        try:
            data = await self._get("/api/registry/components.json")
        except Exception:
            data = await self._get("/api/registry", {"type": f"components:ui"})
        return data.get("components", [])

    async def fetch_component(self, name: str, framework: str = "hanzo") -> str:
        try:
            # Try static file (CF Pages)
            data = await self._get(f"/api/registry/components/{name}.json")
        except Exception:
            # Fallback to API route
            data = await self._get(f"/api/registry/components/{name}")

        source = self._extract_source(data)
        if source is None:
            raise FileNotFoundError(f"Component '{name}' source not available")
        return source

    async def fetch_component_demo(self, name: str, framework: str = "hanzo") -> str:
        try:
            data = await self._get(f"/api/registry/components/{name}-demo.json")
        except Exception:
            try:
                data = await self._get(f"/api/registry/components/{name}-demo")
            except Exception:
                raise FileNotFoundError(f"Demo for '{name}' not available")

        source = self._extract_source(data)
        if source is None:
            raise FileNotFoundError(f"Demo for '{name}' not available")
        return source

    async def fetch_component_metadata(
        self, name: str, framework: str = "hanzo"
    ) -> dict:
        try:
            data = await self._get(f"/api/registry/components/{name}.json")
        except Exception:
            data = await self._get(f"/api/registry/components/{name}")

        return {
            "name": data.get("name", name),
            "type": data.get("type"),
            "dependencies": data.get("dependencies", []),
            "registryDependencies": data.get("registryDependencies", []),
            "source": "registry",
        }

    async def list_blocks(self, framework: str = "hanzo") -> list[dict]:
        comps = await self.list_components(framework)
        return [c for c in comps if "block" in c.get("type", "").lower()]

    async def fetch_block(self, name: str, framework: str = "hanzo") -> str:
        return await self.fetch_component(name, framework)

    async def search_components(
        self, query: str, framework: str = "hanzo"
    ) -> list[dict]:
        try:
            # Try server-mode search
            data = await self._get("/api/registry/search", {"q": query})
            return data.get("results", [])
        except Exception:
            pass

        # Fallback: search client-side using the static index
        try:
            data = await self._get("/api/registry/search-index.json")
        except Exception:
            data = await self.list_components(framework)
            q = query.lower()
            return [c for c in data if q in c.get("name", "").lower()]

        q = query.lower()
        return [
            {"name": item["n"], "type": item.get("t", "")}
            for item in data
            if q in item.get("n", "").lower()
        ]

    async def get_directory_structure(
        self, path: str, framework: str = "hanzo"
    ) -> dict:
        # Not available as static — return component list as structure
        comps = await self.list_components(framework)
        return {
            "path": path or "/",
            "children": [
                {"name": c["name"], "type": "file"} for c in comps
            ],
        }

    async def fetch_full_index(self, framework: str = "hanzo") -> dict:
        """Fetch the full registry index — all components in one payload."""
        return await self._ensure_index()

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
