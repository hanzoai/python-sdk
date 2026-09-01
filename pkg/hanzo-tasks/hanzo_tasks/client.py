"""The Hanzo Tasks client: `/v1/tasks` over HTTP.

The durable engine (hanzoai/tasks) is embedded in Hanzo Cloud and answers under
`/v1/tasks/namespaces/{namespace}/...` on the same origin as everything else,
authenticated by the caller's IAM bearer. A workflow is started, signalled,
queried, cancelled, terminated and reset here; its body runs in a worker
written with the Go or TypeScript SDK. This module holds no engine protocol of
its own — it is the HTTP contract, one method per route.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

import httpx

DEFAULT_HOST = "https://api.hanzo.ai"


@dataclass(frozen=True)
class TasksConfig:
    """Where the engine is and who is calling.

    `token` is an IAM bearer (a user or service token); the org is read from it
    server-side. `namespace` is the engine namespace the caller's workflows live
    in — the org's own by convention.
    """

    token: str
    namespace: str = "default"
    host: str = DEFAULT_HOST
    timeout: float = 30.0


@dataclass(frozen=True)
class Workflow:
    """One workflow execution as the engine describes it."""

    workflow_id: str
    run_id: str
    status: str = ""
    workflow_type: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def of(cls, d: dict[str, Any]) -> "Workflow":
        wt = d.get("workflowType")
        return cls(
            workflow_id=str(d.get("workflowId", "")),
            run_id=str(d.get("runId", "")),
            status=str(d.get("status", "")),
            workflow_type=str(wt.get("name", "") if isinstance(wt, dict) else wt or ""),
            raw=d,
        )


class TasksError(RuntimeError):
    """The engine refused or failed a call; `status` is the HTTP status."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"tasks: HTTP {status}: {message}")
        self.status = status


class Client:
    """Synchronous client over `/v1/tasks`. Use as a context manager or call `close()`."""

    def __init__(self, config: TasksConfig, transport: httpx.BaseTransport | None = None) -> None:
        self.config = config
        self._http = httpx.Client(
            base_url=config.host.rstrip("/"),
            headers={"Authorization": f"Bearer {config.token}", "Content-Type": "application/json"},
            timeout=config.timeout,
            transport=transport,
        )

    # ── plumbing ─────────────────────────────────────────────────────────────

    def _path(self, *parts: str) -> str:
        return "/v1/tasks/namespaces/" + "/".join([self.config.namespace, *parts])

    def _call(self, method: str, path: str, *, params: dict[str, Any] | None = None, body: Any = None) -> Any:
        r = self._http.request(method, path, params=params or None, json=body)
        if r.status_code >= 400:
            try:
                msg = r.json().get("error") or r.text
            except ValueError:
                msg = r.text
            raise TasksError(r.status_code, str(msg).strip())
        if not r.content:
            return None
        try:
            return r.json()
        except ValueError:
            return r.text

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    # ── workflows ────────────────────────────────────────────────────────────

    def start(
        self,
        workflow_type: str,
        *,
        task_queue: str,
        input: Any = None,
        workflow_id: str | None = None,
        request_id: str | None = None,
    ) -> Workflow:
        """Start a workflow. A caller-chosen `workflow_id` makes the start
        idempotent; `request_id` deduplicates a retried request."""
        body = {
            "workflowId": workflow_id or str(uuid.uuid4()),
            "workflowType": {"name": workflow_type},
            "taskQueue": {"name": task_queue},
            "input": input,
            "requestId": request_id or str(uuid.uuid4()),
        }
        return Workflow.of(self._call("POST", self._path("workflows"), body=body) or body)

    def signal_with_start(
        self,
        workflow_type: str,
        *,
        task_queue: str,
        signal: str,
        payload: Any = None,
        input: Any = None,
        workflow_id: str | None = None,
        request_id: str | None = None,
    ) -> Workflow:
        """Signal a workflow, starting it first if it is not running."""
        body = {
            "workflowId": workflow_id or str(uuid.uuid4()),
            "workflowType": {"name": workflow_type},
            "taskQueue": {"name": task_queue},
            "input": input,
            "signalName": signal,
            "signalPayload": payload,
            "requestId": request_id or str(uuid.uuid4()),
        }
        return Workflow.of(self._call("POST", self._path("workflows", "signal-with-start"), body=body) or body)

    def list(self, query: str = "") -> list[Workflow]:
        out = self._call("GET", self._path("workflows"), params={"query": query} if query else None)
        rows = out.get("workflows", out) if isinstance(out, dict) else out
        return [Workflow.of(w) for w in (rows or [])]

    def describe(self, workflow_id: str, run_id: str = "") -> Workflow:
        out = self._call("GET", self._path("workflows", workflow_id), params={"runId": run_id} if run_id else None)
        return Workflow.of(out or {"workflowId": workflow_id, "runId": run_id})

    def signal(self, workflow_id: str, name: str, payload: Any = None, run_id: str = "") -> None:
        self._call(
            "POST",
            self._path("workflows", workflow_id, "signal"),
            params={"runId": run_id} if run_id else None,
            body={"name": name, "payload": payload},
        )

    def query(self, workflow_id: str, query_type: str, args: Any = None, run_id: str = "") -> Any:
        return self._call(
            "POST",
            self._path("workflows", workflow_id, "query"),
            params={"runId": run_id} if run_id else None,
            body={"queryType": query_type, "args": args},
        )

    def cancel(self, workflow_id: str, reason: str = "", run_id: str = "", identity: str = "") -> Workflow:
        out = self._call(
            "POST",
            self._path("workflows", workflow_id, "cancel"),
            params={"runId": run_id} if run_id else None,
            body={"reason": reason, "identity": identity},
        )
        return Workflow.of(out or {"workflowId": workflow_id, "runId": run_id})

    def terminate(self, workflow_id: str, reason: str = "", run_id: str = "", identity: str = "") -> Workflow:
        out = self._call(
            "POST",
            self._path("workflows", workflow_id, "terminate"),
            params={"runId": run_id} if run_id else None,
            body={"reason": reason, "identity": identity},
        )
        return Workflow.of(out or {"workflowId": workflow_id, "runId": run_id})

    def reset(self, workflow_id: str, event_id: int, run_id: str = "", reason: str = "", identity: str = "") -> Workflow:
        out = self._call(
            "POST",
            self._path("workflows", workflow_id, "reset"),
            body={"runId": run_id, "eventId": event_id, "reason": reason, "identity": identity},
        )
        return Workflow.of(out or {"workflowId": workflow_id, "runId": run_id})

    def history(self, workflow_id: str, run_id: str = "", after: int = 0, page_size: int = 0, reverse: bool = False) -> Any:
        params: dict[str, Any] = {}
        if run_id:
            params["runId"] = run_id
        if after:
            params["afterId"] = after
        if page_size:
            params["pageSize"] = page_size
        if reverse:
            params["reverse"] = "true"
        return self._call("GET", self._path("workflows", workflow_id, "history"), params=params)

    # ── schedules ────────────────────────────────────────────────────────────

    def schedules(self) -> Any:
        return self._call("GET", self._path("schedules"))

    def create_schedule(self, schedule: dict[str, Any]) -> Any:
        """Create a schedule; `schedule` is the engine's schedule document
        (id, spec, action) as the Go and TypeScript SDKs send it."""
        return self._call("POST", self._path("schedules"), body=schedule)

    def schedule(self, schedule_id: str) -> Any:
        return self._call("GET", self._path("schedules", schedule_id))

    def delete_schedule(self, schedule_id: str) -> None:
        self._call("DELETE", self._path("schedules", schedule_id))

    def trigger_schedule(self, schedule_id: str, overlap_policy: str = "", request_id: str | None = None) -> Any:
        return self._call(
            "POST",
            self._path("schedules", schedule_id, "trigger"),
            body={"requestId": request_id or str(uuid.uuid4()), "overlapPolicy": overlap_policy},
        )
