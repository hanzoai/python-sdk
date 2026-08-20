"""The client half: dispatch work, read it back, and settle it.

Every call lands on ``/v1/tasks/namespaces/{namespace}/activities`` under the
one Hanzo endpoint, ``api.hanzo.ai``. The org is never named in a request —
IAM validates the bearer token and the edge mints the org from the validated
claim, so a caller cannot reach another tenant's shard by asking to.
"""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote

import httpx

from .errors import raise_for
from .types import Activity, Event, Page, RetryPolicy

DEFAULT_URL = "https://api.hanzo.ai"
DEFAULT_NAMESPACE = "default"


class Tasks:
    """An async client for the Hanzo Tasks activity plane.

    Usable as an async context manager, which closes the transport it owns::

        async with Tasks(token=...) as tasks:
            await tasks.dispatch("render", input={"scene": 3})
    """

    def __init__(
        self,
        *,
        url: str = DEFAULT_URL,
        namespace: str = DEFAULT_NAMESPACE,
        token: str | None = None,
        identity: str = "",
        timeout: float = 30.0,
        http: httpx.AsyncClient | None = None,
    ) -> None:
        self.url = url.rstrip("/")
        self.namespace = namespace
        self.identity = identity
        self._token = token
        # A caller-supplied transport is borrowed, never closed by us.
        self._owned = http is None
        self._http = http or httpx.AsyncClient(timeout=timeout)

    @classmethod
    def from_env(cls, **kwargs: Any) -> Tasks:
        """Read the endpoint, token and namespace from the environment.

        ``HANZO_API_KEY`` (or ``HANZO_TASKS_TOKEN``), ``HANZO_TASKS_URL``,
        ``HANZO_TASKS_NAMESPACE``. Explicit arguments win.
        """
        kwargs.setdefault("url", os.environ.get("HANZO_TASKS_URL", DEFAULT_URL))
        kwargs.setdefault("namespace", os.environ.get("HANZO_TASKS_NAMESPACE", DEFAULT_NAMESPACE))
        kwargs.setdefault(
            "token",
            os.environ.get("HANZO_API_KEY") or os.environ.get("HANZO_TASKS_TOKEN"),
        )
        return cls(**kwargs)

    async def __aenter__(self) -> Tasks:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owned:
            await self._http.aclose()

    # ── the wire ────────────────────────────────────────────────────────

    def _base(self) -> str:
        return f"{self.url}/v1/tasks/namespaces/{quote(self.namespace, safe='')}/activities"

    def _headers(self) -> dict[str, str]:
        if not self._token:
            return {}
        return {"Authorization": f"Bearer {self._token}"}

    async def _call(
        self,
        method: str,
        path: str = "",
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> tuple[int, Any]:
        response = await self._http.request(
            method,
            self._base() + path,
            json=json,
            params=params,
            headers=self._headers(),
        )
        if response.status_code == 204:
            return 204, None
        body: Any
        try:
            body = response.json()
        except ValueError:
            # Refusals on this surface are sometimes plain text, not JSON.
            body = response.text
        if response.status_code >= 400:
            raise_for(response.status_code, body)
        return response.status_code, body

    # ── dispatch and read ───────────────────────────────────────────────

    async def dispatch(
        self,
        type: str,
        *,
        id: str | None = None,
        input: Any = None,
        task_queue: str = "default",
        retry: RetryPolicy | None = None,
        schedule_to_close_timeout: str = "",
        schedule_to_start_timeout: str = "",
        start_to_close_timeout: str = "",
        heartbeat_timeout: str = "",
        request_id: str = "",
    ) -> Activity:
        """Schedule one activity and return it in SCHEDULED state.

        ``id`` defaults to a fresh uuid4. ``request_id`` makes the call
        idempotent: a retry carrying the same one returns the first activity
        unchanged rather than dispatching a second.

        ``heartbeat_timeout`` doubles as the claim lease — a worker that goes
        quiet for longer has its claim reaped and the activity returned to the
        queue, so set it to the longest gap between heartbeats you expect.
        """
        if id is None:
            from uuid import uuid4

            id = str(uuid4())
        body: dict[str, Any] = {
            "activityId": id,
            "activityType": {"name": type},
            "taskQueue": task_queue,
        }
        if input is not None:
            body["input"] = input
        if retry is not None:
            body["retryPolicy"] = retry.wire()
        for key, value in (
            ("scheduleToCloseTimeout", schedule_to_close_timeout),
            ("scheduleToStartTimeout", schedule_to_start_timeout),
            ("startToCloseTimeout", start_to_close_timeout),
            ("heartbeatTimeout", heartbeat_timeout),
            ("identity", self.identity),
            ("requestId", request_id),
        ):
            if value:
                body[key] = value
        _, out = await self._call("POST", json=body)
        return Activity.from_wire(out)

    async def describe(self, id: str, run_id: str) -> Activity:
        """Read one activity. Raises `NotFound` if this tenant has no such run."""
        _, out = await self._call("GET", f"/{_seg(id)}/{_seg(run_id)}")
        return Activity.from_wire(out)

    async def activities(self, *, cursor: str = "", page_size: int = 0) -> Page:
        """Read one page of this namespace's activities.

        Pass the returned `Page.cursor` back as ``cursor`` for the next page;
        an empty cursor means the listing is exhausted.
        """
        params: dict[str, Any] = {}
        if cursor:
            params["cursor"] = cursor
        if page_size:
            params["pageSize"] = page_size
        _, out = await self._call("GET", params=params or None)
        rows = [Activity.from_wire(row) for row in (out.get("activities") or [])]
        return Page(activities=rows, cursor=out.get("nextCursor") or "")

    async def history(
        self,
        id: str,
        run_id: str,
        *,
        after: int = 0,
        page_size: int = 0,
        reverse: bool = False,
    ) -> tuple[list[Event], int]:
        """Read an activity's durable history and the cursor that continues it."""
        params: dict[str, Any] = {}
        if after:
            params["after"] = after
        if page_size:
            params["pageSize"] = page_size
        if reverse:
            params["reverse"] = "true"
        _, out = await self._call(
            "GET", f"/{_seg(id)}/{_seg(run_id)}/history", params=params or None
        )
        events = [Event.from_wire(row) for row in (out.get("events") or [])]
        return events, out.get("nextCursor") or 0

    # ── claim and settle ────────────────────────────────────────────────

    async def claim(
        self,
        *,
        task_queue: str = "",
        identity: str = "",
        lease_seconds: int = 0,
    ) -> Activity | None:
        """Claim the oldest scheduled activity, or None when the queue is empty.

        An empty queue is the 204 answer and is not an error — it is the
        ordinary result of polling. ``task_queue`` empty claims from any queue.

        The engine reaps expired leases before it claims, so a dead worker's
        in-flight activity returns to the queue and is picked up here without
        any timer on this side.
        """
        body: dict[str, Any] = {"taskQueue": task_queue}
        who = identity or self.identity
        if who:
            body["identity"] = who
        if lease_seconds:
            body["leaseSeconds"] = lease_seconds
        status, out = await self._call("POST", "/claim", json=body)
        if status == 204:
            return None
        return Activity.from_wire(out)

    async def heartbeat(self, id: str, run_id: str, details: Any = None) -> Activity:
        """Report progress, which also extends the claim's lease."""
        return await self._settle(id, run_id, "heartbeat", {"details": details})

    async def complete(self, id: str, run_id: str, result: Any = None) -> Activity:
        """Finish the activity successfully, recording ``result``."""
        return await self._settle(id, run_id, "complete", {"result": result})

    async def fail(self, id: str, run_id: str, cause: str) -> Activity:
        """Finish the activity as failed, recording ``cause``."""
        return await self._settle(id, run_id, "fail", {"cause": cause})

    async def cancel(self, id: str, run_id: str, reason: str = "") -> Activity:
        """Cancel the activity."""
        return await self._settle(id, run_id, "cancel", {"reason": reason})

    async def _settle(self, id: str, run_id: str, verb: str, body: dict[str, Any]) -> Activity:
        if self.identity:
            body.setdefault("identity", self.identity)
        _, out = await self._call("POST", f"/{_seg(id)}/{_seg(run_id)}/{verb}", json=body)
        return Activity.from_wire(out)


def _seg(value: str) -> str:
    """Percent-encode one path segment.

    This keeps a space, ``?`` or ``#`` in an id part of the segment instead of
    becoming a query or fragment. It is NOT protection against every input: the
    engine matches on Go's decoded ``r.URL.Path``, so an id containing a
    literal slash arrives there as two segments and is not addressable at all.
    Keep ids slash-free.
    """
    return quote(value, safe="")
