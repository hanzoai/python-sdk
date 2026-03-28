"""GitHub API client for fetching UI components from framework repositories."""

import os
import time
from typing import Any

import httpx

GITHUB_API_BASE = "https://api.github.com"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"


class FrameworkConfig:
    """Configuration for a UI framework repository."""

    def __init__(
        self,
        owner: str,
        repo: str,
        branch: str,
        components_path: str,
        extension: str,
        blocks_path: str | None = None,
        examples_path: str | None = None,
    ):
        self.owner = owner
        self.repo = repo
        self.branch = branch
        self.components_path = components_path
        self.blocks_path = blocks_path
        self.examples_path = examples_path
        self.extension = extension


FRAMEWORK_CONFIGS: dict[str, FrameworkConfig] = {
    "hanzo": FrameworkConfig(
        owner="hanzoai",
        repo="ui",
        branch="main",
        components_path="pkg/ui/primitives",
        blocks_path="pkg/ui/primitives",
        extension=".tsx",
    ),
    "hanzo-native": FrameworkConfig(
        owner="hanzoai",
        repo="ui-native",
        branch="main",
        components_path="packages/native/src/components",
        extension=".tsx",
    ),
    "hanzo-vue": FrameworkConfig(
        owner="hanzoai",
        repo="ui-vue",
        branch="main",
        components_path="packages/vue/src/components",
        extension=".vue",
    ),
    "hanzo-svelte": FrameworkConfig(
        owner="hanzoai",
        repo="ui-svelte",
        branch="main",
        components_path="packages/svelte/src/components",
        extension=".svelte",
    ),
    "shadcn": FrameworkConfig(
        owner="shadcn-ui",
        repo="ui",
        branch="main",
        components_path="apps/v4/registry/new-york-v4/ui",
        blocks_path="apps/v4/registry/new-york-v4/blocks",
        examples_path="apps/v4/registry/new-york-v4/examples",
        extension=".tsx",
    ),
    "react": FrameworkConfig(
        owner="shadcn-ui",
        repo="ui",
        branch="main",
        components_path="apps/v4/registry/new-york-v4/ui",
        blocks_path="apps/v4/registry/new-york-v4/blocks",
        examples_path="apps/v4/registry/new-york-v4/examples",
        extension=".tsx",
    ),
    "svelte": FrameworkConfig(
        owner="huntabyte",
        repo="shadcn-svelte",
        branch="main",
        components_path="apps/www/src/lib/registry/new-york/ui",
        blocks_path="apps/www/src/lib/registry/new-york/blocks",
        extension=".svelte",
    ),
    "vue": FrameworkConfig(
        owner="unovue",
        repo="shadcn-vue",
        branch="main",
        components_path="apps/www/src/lib/registry/new-york/ui",
        blocks_path="apps/www/src/lib/registry/new-york/blocks",
        extension=".vue",
    ),
    "react-native": FrameworkConfig(
        owner="founded-labs",
        repo="react-native-reusables",
        branch="main",
        components_path="packages/reusables/src",
        extension=".tsx",
    ),
}

FRAMEWORK_NAMES: dict[str, str] = {
    "hanzo": "Hanzo UI (React)",
    "hanzo-native": "Hanzo UI Native (React Native)",
    "hanzo-vue": "Hanzo UI Vue",
    "hanzo-svelte": "Hanzo UI Svelte",
    "shadcn": "shadcn/ui",
    "react": "shadcn/ui (React)",
    "svelte": "Svelte (shadcn)",
    "vue": "Vue (shadcn)",
    "react-native": "React Native Reusables",
}


class GitHubAPIClient:
    """GitHub API client with caching and rate limit tracking."""

    CACHE_TTL = 15 * 60  # 15 minutes

    def __init__(self):
        self._token = os.environ.get("GITHUB_TOKEN") or os.environ.get(
            "GITHUB_PERSONAL_ACCESS_TOKEN"
        )
        self._cache: dict[str, tuple[Any, float]] = {}
        self._rate_limit_remaining = 60
        self._rate_limit_reset = time.time()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {
                "User-Agent": "Hanzo-MCP-UI-Tool",
                "Accept": "application/vnd.github.v3+json",
            }
            if self._token:
                headers["Authorization"] = f"token {self._token}"
            self._client = httpx.AsyncClient(headers=headers, timeout=30.0)
        return self._client

    def _cache_get(self, key: str) -> Any | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        data, ts = entry
        if time.time() - ts > self.CACHE_TTL:
            del self._cache[key]
            return None
        return data

    def _cache_set(self, key: str, data: Any) -> None:
        self._cache[key] = (data, time.time())

    async def _api_request(self, url: str) -> Any:
        if self._rate_limit_remaining <= 0 and time.time() < self._rate_limit_reset:
            wait = int(self._rate_limit_reset - time.time())
            raise RuntimeError(f"GitHub API rate limit exceeded. Reset in {wait}s.")

        cached = self._cache_get(url)
        if cached is not None:
            return cached

        client = await self._get_client()
        resp = await client.get(url)

        if "x-ratelimit-remaining" in resp.headers:
            self._rate_limit_remaining = int(resp.headers["x-ratelimit-remaining"])
        if "x-ratelimit-reset" in resp.headers:
            self._rate_limit_reset = int(resp.headers["x-ratelimit-reset"])

        if resp.status_code == 200:
            data = resp.json()
            self._cache_set(url, data)
            return data
        elif resp.status_code == 403:
            raise RuntimeError("GitHub API rate limit exceeded or authentication required")
        elif resp.status_code == 404:
            raise FileNotFoundError("Resource not found")
        else:
            raise RuntimeError(f"GitHub API error: {resp.status_code}")

    async def get_raw_content(
        self, owner: str, repo: str, path: str, branch: str
    ) -> str:
        url = f"{GITHUB_RAW_BASE}/{owner}/{repo}/{branch}/{path}"
        cached = self._cache_get(url)
        if cached is not None:
            return cached

        client = await self._get_client()
        resp = await client.get(url)
        if resp.status_code == 200:
            self._cache_set(url, resp.text)
            return resp.text
        elif resp.status_code == 404:
            raise FileNotFoundError(f"File not found: {path}")
        else:
            raise RuntimeError(f"Failed to fetch: {resp.status_code}")

    async def get_directory_contents(
        self, owner: str, repo: str, path: str, branch: str
    ) -> list[dict]:
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}?ref={branch}"
        return await self._api_request(url)

    async def fetch_component(self, name: str, framework: str = "hanzo") -> str:
        config = FRAMEWORK_CONFIGS[framework]
        path = f"{config.components_path}/{name}{config.extension}"
        try:
            return await self.get_raw_content(config.owner, config.repo, path, config.branch)
        except FileNotFoundError:
            index_path = f"{config.components_path}/{name}/index{config.extension}"
            try:
                return await self.get_raw_content(
                    config.owner, config.repo, index_path, config.branch
                )
            except FileNotFoundError:
                raise FileNotFoundError(
                    f"Component '{name}' not found in {framework} repository"
                )

    async def fetch_component_demo(self, name: str, framework: str = "hanzo") -> str:
        config = FRAMEWORK_CONFIGS[framework]
        if not config.examples_path and framework != "hanzo":
            raise RuntimeError(f"Demo/examples not available for {framework}")

        demo_path = (
            f"{config.components_path}/{name}/demo{config.extension}"
            if framework == "hanzo"
            else f"{config.examples_path}/{name}-demo{config.extension}"
        )
        try:
            return await self.get_raw_content(config.owner, config.repo, demo_path, config.branch)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Demo for component '{name}' not found in {framework} repository"
            )

    async def fetch_component_metadata(self, name: str, framework: str = "hanzo") -> dict:
        config = FRAMEWORK_CONFIGS[framework]
        path = f"{config.components_path}/{name}/metadata.json"
        try:
            import json
            content = await self.get_raw_content(config.owner, config.repo, path, config.branch)
            return json.loads(content)
        except (FileNotFoundError, Exception):
            return {
                "name": name,
                "framework": framework,
                "extension": config.extension,
                "path": f"{config.components_path}/{name}",
            }

    async def fetch_block(self, name: str, framework: str = "hanzo") -> str:
        config = FRAMEWORK_CONFIGS[framework]
        if not config.blocks_path:
            raise RuntimeError(f"Blocks not available for {framework}")

        path = f"{config.blocks_path}/{name}{config.extension}"
        try:
            return await self.get_raw_content(config.owner, config.repo, path, config.branch)
        except FileNotFoundError:
            index_path = f"{config.blocks_path}/{name}/index{config.extension}"
            try:
                return await self.get_raw_content(
                    config.owner, config.repo, index_path, config.branch
                )
            except FileNotFoundError:
                raise FileNotFoundError(
                    f"Block '{name}' not found in {framework} repository"
                )

    async def list_components(self, framework: str = "hanzo") -> list[dict]:
        config = FRAMEWORK_CONFIGS[framework]
        contents = await self.get_directory_contents(
            config.owner, config.repo, config.components_path, config.branch
        )
        return [
            {"name": item["name"].replace(config.extension, ""), "type": item["type"]}
            for item in contents
            if item["type"] == "dir"
            or (item["type"] == "file" and item["name"].endswith(config.extension))
        ]

    async def list_blocks(self, framework: str = "hanzo") -> list[dict]:
        config = FRAMEWORK_CONFIGS[framework]
        if not config.blocks_path:
            return []
        try:
            contents = await self.get_directory_contents(
                config.owner, config.repo, config.blocks_path, config.branch
            )
            return [
                {"name": item["name"].replace(config.extension, ""), "type": item["type"]}
                for item in contents
                if item["type"] == "dir"
                or (item["type"] == "file" and item["name"].endswith(config.extension))
            ]
        except Exception:
            return []

    async def get_directory_structure(self, path: str, framework: str = "hanzo") -> dict:
        config = FRAMEWORK_CONFIGS[framework]
        contents = await self.get_directory_contents(
            config.owner, config.repo, path, config.branch
        )
        children = []
        for item in contents:
            entry = {"name": item["name"], "type": item["type"], "path": item["path"]}
            if item["type"] == "file" and "size" in item:
                entry["size"] = item["size"]
            children.append(entry)
        return {"path": path, "children": children}

    def get_rate_limit_info(self) -> dict:
        return {
            "remaining": self._rate_limit_remaining,
            "reset": self._rate_limit_reset,
        }

    def clear_cache(self) -> None:
        self._cache.clear()
