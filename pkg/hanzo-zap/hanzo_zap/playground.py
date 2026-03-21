"""
Playground control plane client.

Connects to the playground REST API for agent management,
event streaming, git operations, and human injection.
"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

import httpx


class PlaygroundClient:
    """Client for the Hanzo Playground control plane."""

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        token: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {token}"} if token else {},
            timeout=30.0,
        )

    # --- Agent Discovery ---

    async def discover_agents(self, space_id: str) -> list[dict[str, Any]]:
        """Discover agents in a space via gossip tracker."""
        resp = await self._client.get(
            f"/api/v1/spaces/{space_id}/agents/discover"
        )
        resp.raise_for_status()
        return resp.json().get("agents") or []

    # --- Agent Events (SSE) ---

    async def stream_events(
        self, space_id: str
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream all agent events in a space via SSE."""
        async with self._client.stream(
            "GET", f"/api/v1/spaces/{space_id}/agents/events"
        ) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    try:
                        yield json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue

    async def stream_agent_events(
        self, space_id: str, agent_id: str
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream events for a specific agent via SSE."""
        async with self._client.stream(
            "GET",
            f"/api/v1/spaces/{space_id}/agents/{agent_id}/events",
        ) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    try:
                        yield json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue

    # --- Human Injection ---

    async def inject_message(
        self,
        space_id: str,
        agent_id: str,
        message: str,
        sender_name: str = "human",
    ) -> dict[str, Any]:
        """Send a human message to a specific agent."""
        resp = await self._client.post(
            f"/api/v1/spaces/{space_id}/agents/{agent_id}/inject",
            json={"message": message, "sender_name": sender_name},
        )
        resp.raise_for_status()
        return resp.json()

    async def broadcast_message(
        self,
        space_id: str,
        message: str,
        sender_name: str = "human",
    ) -> dict[str, Any]:
        """Broadcast a human message to all agents in a space."""
        resp = await self._client.post(
            f"/api/v1/spaces/{space_id}/agents/broadcast",
            json={"message": message, "sender_name": sender_name},
        )
        resp.raise_for_status()
        return resp.json()

    # --- Git Operations ---

    async def git_status(self, space_id: str) -> dict[str, Any]:
        """Get git status for a space."""
        resp = await self._client.get(
            f"/api/v1/spaces/{space_id}/git/status"
        )
        resp.raise_for_status()
        return resp.json()

    async def git_clone(
        self, space_id: str, url: str, branch: str = "main"
    ) -> dict[str, Any]:
        """Clone a git repository into a space."""
        resp = await self._client.post(
            f"/api/v1/spaces/{space_id}/git/clone",
            json={"url": url, "branch": branch},
        )
        resp.raise_for_status()
        return resp.json()

    async def git_commit(
        self,
        space_id: str,
        message: str,
        files: list[str] | None = None,
        author_name: str = "",
        author_email: str = "",
    ) -> dict[str, Any]:
        """Create a git commit in a space."""
        body: dict[str, Any] = {"message": message}
        if files:
            body["files"] = files
        if author_name:
            body["author"] = {"name": author_name, "email": author_email}
        resp = await self._client.post(
            f"/api/v1/spaces/{space_id}/git/commit", json=body
        )
        resp.raise_for_status()
        return resp.json()

    async def git_log(
        self, space_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Get git log for a space."""
        resp = await self._client.get(
            f"/api/v1/spaces/{space_id}/git/log", params={"limit": limit}
        )
        resp.raise_for_status()
        return resp.json().get("commits", [])

    async def git_branches(self, space_id: str) -> list[dict[str, Any]]:
        """List git branches in a space."""
        resp = await self._client.get(
            f"/api/v1/spaces/{space_id}/git/branches"
        )
        resp.raise_for_status()
        return resp.json().get("branches", [])

    async def git_files(
        self, space_id: str, path: str = "/"
    ) -> list[dict[str, Any]]:
        """Browse files in a space repository."""
        resp = await self._client.get(
            f"/api/v1/spaces/{space_id}/git/files", params={"path": path}
        )
        resp.raise_for_status()
        return resp.json().get("files", [])

    # --- Lifecycle ---

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> PlaygroundClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
