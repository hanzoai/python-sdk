"""UI component search via Hanzo Cloud search infrastructure.

Uses the Hanzo Cloud RAG pipeline:
- POST /api/search-docs — hybrid fulltext + vector search
- POST /api/chat-docs  — RAG chat with component context
- POST /api/index-docs — index components into the search backend

Authentication: publishable key (pk-*) for read, API key (hk-*) for write.
"""

import json
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Hanzo Cloud search endpoints
CLOUD_API = os.environ.get("HANZO_CLOUD_API", "https://cloud-api.hanzo.ai")
SEARCH_ENDPOINT = f"{CLOUD_API}/api/search-docs"
CHAT_ENDPOINT = f"{CLOUD_API}/api/chat-docs"
INDEX_ENDPOINT = f"{CLOUD_API}/api/index-docs"
STATS_ENDPOINT = f"{CLOUD_API}/api/search-docs/stats"

# Search index for UI components
SEARCH_INDEX = os.environ.get("HANZO_UI_SEARCH_INDEX", "app-ui-hanzo-ai")

# Keys
PUBLISHABLE_KEY = os.environ.get("HANZO_UI_SEARCH_KEY", "pk-hanzo-ui-search-2026")
ADMIN_KEY = os.environ.get("HANZO_SEARCH_ADMIN_KEY", "")


def _auth_headers(write: bool = False) -> dict[str, str]:
    """Get auth headers — publishable key for reads, admin key for writes."""
    key = ADMIN_KEY if write else PUBLISHABLE_KEY
    if not key:
        key = os.environ.get("HANZO_API_KEY", "")
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


async def search_components(
    query: str,
    limit: int = 10,
    tags: list[str] | None = None,
) -> list[dict]:
    """Search UI components using Hanzo Cloud hybrid search.

    Uses both fulltext (Meilisearch) and vector (Qdrant) search.
    """
    payload: dict[str, Any] = {
        "query": query,
        "index": SEARCH_INDEX,
        "limit": limit,
    }
    if tags:
        payload["tags"] = tags

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            SEARCH_ENDPOINT,
            headers=_auth_headers(),
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()


async def chat_about_components(
    question: str,
    history: list[dict] | None = None,
    stream: bool = False,
) -> dict | Any:
    """RAG chat — ask questions about UI components.

    Uses Hanzo Cloud's /api/chat-docs which:
    1. Searches the component index for relevant context
    2. Passes context + question to the LLM
    3. Returns a grounded answer
    """
    messages = history or []
    messages.append({"role": "user", "content": question})

    payload = {
        "messages": messages,
        "index": SEARCH_INDEX,
        "stream": stream,
        "systemPrompt": (
            "You are a UI component expert for the Hanzo UI library. "
            "Answer questions about components, their props, usage patterns, "
            "and how to compose them. Be specific — reference component names, "
            "props, and show code examples when helpful. "
            "The components are React/TypeScript using Radix UI primitives "
            "and Tailwind CSS."
        ),
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            CHAT_ENDPOINT,
            headers=_auth_headers(),
            json=payload,
        )
        resp.raise_for_status()

        if stream:
            return resp.text  # SSE stream
        return resp.json()


async def index_components(
    components: list[dict],
    replace: bool = False,
) -> dict:
    """Index UI components into Hanzo Cloud search.

    Each component becomes a document with:
    - id: component name
    - title: component name (human-readable)
    - content: source code + metadata
    - url: link to component page
    - tag: component type (ui, block, example, etc.)
    - section: package/category
    """
    documents = []
    for comp in components:
        name = comp["name"]
        source = comp.get("source", "")
        comp_type = comp.get("type", "components:ui")
        deps = comp.get("dependencies", [])
        reg_deps = comp.get("registryDependencies", [])

        # Build rich content for embedding
        content_parts = [
            f"Component: {name}",
            f"Type: {comp_type}",
        ]
        if deps:
            content_parts.append(f"Dependencies: {', '.join(deps)}")
        if reg_deps:
            content_parts.append(f"Registry dependencies: {', '.join(reg_deps)}")
        if source:
            content_parts.append(f"\nSource code:\n{source}")

        documents.append({
            "id": f"component-{name}",
            "page_id": name,
            "title": name.replace("-", " ").title(),
            "url": f"https://ui.hanzo.ai/components/{name}",
            "content": "\n".join(content_parts),
            "section": comp_type.split(":")[-1] if ":" in comp_type else "ui",
            "tag": comp_type,
        })

    admin_key = ADMIN_KEY or os.environ.get("HANZO_API_KEY", "")
    if not admin_key:
        return {"error": "HANZO_SEARCH_ADMIN_KEY or HANZO_API_KEY required for indexing"}

    payload: dict[str, Any] = {
        "index": SEARCH_INDEX,
        "documents": documents,
    }
    if replace:
        payload["replace"] = True

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            INDEX_ENDPOINT,
            headers=_auth_headers(write=True),
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()


async def get_index_stats() -> dict:
    """Get search index statistics."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            STATS_ENDPOINT,
            headers=_auth_headers(),
            params={"index": SEARCH_INDEX},
        )
        resp.raise_for_status()
        return resp.json()


async def index_from_local(ui_path: str | None = None) -> dict:
    """Index all components from the local hanzo/ui repo into Hanzo Cloud."""
    from .local_client import LocalUIClient

    local = LocalUIClient(ui_path)
    if not local.available:
        return {"error": "Local hanzo/ui repo not found"}

    comp_list = await local.list_components()
    components = []

    for comp in comp_list:
        name = comp["name"]
        try:
            source = await local.fetch_component(name)
            components.append({
                "name": name,
                "type": comp.get("type", "file"),
                "source": source,
            })
        except Exception as e:
            logger.debug("Skipping %s: %s", name, e)

    if not components:
        return {"error": "No components found"}

    result = await index_components(components, replace=True)
    return {
        "indexed": len(components),
        "source": "local",
        **result,
    }


async def index_from_registry(registry_url: str | None = None) -> dict:
    """Index all components from the registry into Hanzo Cloud."""
    from .registry.client import RegistryClient

    client = RegistryClient(registry_url)
    try:
        index_data = await client.fetch_full_index()
    except Exception as e:
        return {"error": f"Failed to fetch registry: {e}"}

    raw_components = index_data.get("components", {})
    components = []

    for name, data in raw_components.items():
        files = data.get("files", [])
        source = ""
        if files:
            first = files[0]
            if isinstance(first, dict):
                source = first.get("content", "")

        components.append({
            "name": name,
            "type": data.get("type", ""),
            "source": source,
            "dependencies": data.get("dependencies", []),
            "registryDependencies": data.get("registryDependencies", []),
        })

    await client.close()

    if not components:
        return {"error": "No components in registry"}

    result = await index_components(components, replace=True)
    return {
        "indexed": len(components),
        "source": "registry",
        **result,
    }
