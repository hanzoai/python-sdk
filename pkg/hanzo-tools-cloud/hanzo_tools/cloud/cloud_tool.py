"""The Hanzo Cloud surface, offered as the fleet publishes it.

One tool per subsystem, carrying that subsystem's operation names, plus
``describe`` — which answers one operation's prose and schema. That is the shape
the fleet serves at ``POST /v1/mcp``, and it is why this file is short: a flat
projection is 1,416 tools and roughly a megabyte to enumerate, which a model pays
for on every turn and a client with a tool cap truncates.

The names come from ``catalog.json``, generated out of cloud's own typed
operations (``plugin/gen-mcp-catalog``). It is the same file the TypeScript and
Rust runtimes embed, so the three cannot come to disagree about what the API
offers — which is what "the runtimes mirror one another" has to mean to be worth
saying.

It is a catalog rather than a fetch because a tool list is answered before any
request has been made, and a client that needs the network to say what it can do
has nothing to say when the network is what failed.

Every call goes to ``api.hanzo.ai`` — the one endpoint. The ten hand-written
packages this replaces dialled four hosts, named resources the fleet had renamed,
and asked for plurals where it publishes singulars.
"""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_CATALOG = Path(__file__).with_name("catalog.json")


@lru_cache(maxsize=1)
def _fleet() -> dict[str, dict[str, list[str]]]:
    return json.loads(_CATALOG.read_text())


def services() -> list[str]:
    """Every subsystem the fleet offers, in a stable order."""
    return sorted(_fleet())


def operations(service: str) -> list[str]:
    """One subsystem's operations, empty for a name the fleet does not serve."""
    return list(_fleet().get(service, {}).get("ops", []))


def reach() -> int:
    """What this client can address, for anything reporting coverage."""
    return sum(len(e["ops"]) for e in _fleet().values())


def _endpoint() -> str:
    return os.getenv("HANZO_API_URL", "https://api.hanzo.ai").rstrip("/")


def _token() -> str:
    for name in ("HANZO_API_KEY", "API_KEY", "API_TOKEN", "HANZO_TOKEN"):
        value = os.getenv(name)
        if value:
            return value
    return ""


def call(service: str, op: str, params: dict[str, Any] | None = None) -> Any:
    """Hand one operation to the fleet and return what it answered.

    A refusal is returned as a refusal. Folding it into a success whose body
    happens to say it failed is a refusal the caller cannot see, which is worse
    than no answer because it is acted on.
    """
    # The name is checked first because it is a fact held here, needing no
    # credential. Demanding a key for a subsystem that does not exist sends the
    # caller to fix a credential when the request is what was wrong.
    if service not in _fleet():
        raise ValueError(f"the fleet does not serve {service!r}; it serves {', '.join(services())}")
    key = _token()
    if not key:
        raise RuntimeError("HANZO_API_KEY required")

    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": service, "arguments": {"op": op, "input": params or {}}},
    }
    with httpx.Client(timeout=30.0) as client:
        answer = client.post(
            f"{_endpoint()}/v1/mcp",
            json=body,
            headers={"Authorization": f"Bearer {key}"},
        )
    answer.raise_for_status()
    payload = answer.json()

    if "error" in payload:
        raise RuntimeError(payload["error"].get("message", "refused"))

    result = payload.get("result", payload)
    if isinstance(result, dict) and result.get("isError"):
        content = result.get("content") or [{}]
        raise RuntimeError(content[0].get("text", "refused"))
    return result


class CloudTool:
    """The fleet behind one tool, routed by subsystem and operation.

    One tool rather than 114, for the reason the fleet groups its own: a flat
    projection is roughly a megabyte to enumerate, which a model pays for on
    every turn and a client with a tool cap truncates. The subsystem names and
    their operations are read from the generated catalog, so a subsystem the
    fleet gains is reachable here the day the catalog is regenerated — there is
    no list in this file to fall behind.
    """

    @property
    def name(self) -> str:
        return "cloud"

    @property
    def description(self) -> str:
        return (
            f"The Hanzo Cloud API: {len(services())} subsystems, {reach()} operations. "
            "Name a subsystem in `service` and one of its operations in `op`, and pass "
            "that operation's own arguments in `input`. Omit `op` to list a subsystem's "
            "operations; omit `service` to list the subsystems."
        )

    async def call(self, ctx: Any = None, **params: Any) -> Any:
        service = (params.get("service") or "").strip()
        if not service:
            return {"services": services()}
        if service not in _fleet():
            return {"error": f"the fleet does not serve {service!r}", "services": services()}
        op = (params.get("op") or "").strip()
        if not op:
            return {"service": service, "operations": operations(service)}
        try:
            return call(service, op, params.get("input") or {})
        except Exception as exc:  # a refusal is reported as one, never as an empty result
            logger.debug("cloud %s.%s refused", service, op, exc_info=True)
            return {"error": str(exc)}

    def register(self, mcp_server: Any) -> None:
        @mcp_server.tool(name=self.name, description=self.description)
        async def cloud(  # type: ignore[no-untyped-def]
            service: str = "", op: str = "", input: dict[str, Any] | None = None
        ):
            return await self.call(service=service, op=op, input=input)
