"""repo — your repositories on Hanzo git and the GitHub links that feed them (HIP-0300).

    list  GET  /v1/sync           every link: source, target, direction, where it stands
    sync  POST /v1/sync/{id}/run  sync one now; the reconcile is queued and runs in the background

A link is a GitHub repository (or a whole account) declared once and kept in step
with its copy on git.hanzo.ai. The calls go to api.hanzo.ai through the one
HanzoCloud client and the caller's Hanzo credential.
"""

from typing import Any, ClassVar
from urllib.parse import quote

from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, HanzoCloud, InvalidParamsError, ToolError
from hanzo_tools.core.cloud import NO_KEY, CloudError


def row(v: Any) -> dict[str, Any]:
    """One link as an agent reads it: where it comes from, where it goes, how it stands."""
    v = v if isinstance(v, dict) else {}
    native = v.get("native") if isinstance(v.get("native"), dict) else {}
    return {
        "id": v.get("id"),
        "scope": v.get("scope"),
        "source": (v.get("source") or {}).get("locator"),
        "target": (v.get("target") or {}).get("locator"),
        "direction": v.get("direction"),
        "trigger": v.get("trigger"),
        "status": native.get("status"),
        "branch": native.get("branch"),
        "url": native.get("url"),
        # bumped by every reconcile, so it reads as the last sync
        "synced_at": v.get("updatedAt"),
    }


LIST_SCHEMA = {
    "type": "object",
    "properties": {
        "search": {
            "type": "string",
            "description": "list: words that must all appear in the source or target",
        },
        "status": {
            "type": "string",
            "enum": ["synced", "conflict", "pending", "paused"],
            "description": "list: only links that stand so",
        },
    },
    "required": [],
}
SYNC_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "description": "sync: the link's id from list (sync_...)"}
    },
    "required": [],
}


class RepoTool(BaseTool):
    """Repositories on Hanzo git linked to GitHub: list them, sync one now."""

    name: ClassVar[str] = "repo"
    VERSION: ClassVar[str] = "0.1.0"
    DEFAULT_ACTION: ClassVar[str] = "list"

    def __init__(self):
        super().__init__()
        self._cloud: HanzoCloud | None = None

        @self.action("list", "Every repository link and where it stands", schema=LIST_SCHEMA)
        async def list_(
            ctx: MCPContext, search: str | None = None, status: str | None = None
        ) -> dict:
            body = await self._send("GET", "/v1/sync")
            rows = body.get("data") if isinstance(body, dict) else None
            words = (search or "").lower().split()
            links = []
            for v in rows if isinstance(rows, list) else []:
                r = row(v)
                if status and r["status"] != status:
                    continue
                hay = f"{r['source'] or ''} {r['target'] or ''}".lower()
                if all(w in hay for w in words):
                    links.append(r)
            return {"count": len(links), "repos": links}

        @self.action("sync", "Sync one repository link now", schema=SYNC_SCHEMA)
        async def sync(ctx: MCPContext, id: str | None = None) -> dict:
            if not isinstance(id, str) or not id.strip():
                raise InvalidParamsError(
                    "id required: a link's id from repo list (sync_...)", param="id"
                )
            return await self._send("POST", f"/v1/sync/{quote(id.strip(), safe='')}/run")

    @property
    def description(self) -> str:
        return (
            "Your repositories on Hanzo git and the GitHub links that keep them in step (/v1/sync). "
            "list (default): every link with its id, scope (repo or account), source, target, direction "
            "(both, pull, push, off), trigger, status (synced, conflict, pending, paused), branch, url and "
            "synced_at; search (words in source or target) and status narrow it. "
            "sync: sync one link now by its id; answers {queued, id} and the reconcile runs in the background."
        )

    async def _send(self, method: str, path: str) -> Any:
        if self._cloud is None:
            self._cloud = HanzoCloud()
        if not self._cloud.configured():
            raise ToolError(code="INVALID_PARAMS", message=NO_KEY)
        try:
            return await self._cloud.call(method, path)
        except CloudError as e:
            if e.status == 404:
                raise ToolError(code="NOT_FOUND", message=str(e))
            raise ToolError(code="UPSTREAM", message=str(e))
