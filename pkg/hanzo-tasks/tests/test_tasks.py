"""Tests against a fake that mirrors the engine's verified wire.

The fake is deliberately faithful to the shapes read out of
`hanzoai/tasks` `pkg/tasks/embed.go` (handleActivities) and `activities.go`:
an empty claim is 204 with no body, a second terminal call is 409, errors are
`{"error", "code"}` with a NUMERIC code, and an activity is keyed by the
`execution.workflowId` / `execution.runId` pair.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC

import httpx
import pytest

from hanzo_tasks import (
    Activity,
    Denied,
    NotFound,
    RetryPolicy,
    Tasks,
    Terminal,
    Worker,
)

NS = "default"
BASE = f"/v1/tasks/namespaces/{NS}/activities"

SCHEDULED = "ACTIVITY_TASK_STATE_SCHEDULED"
STARTED = "ACTIVITY_TASK_STATE_STARTED"
COMPLETED = "ACTIVITY_TASK_STATE_COMPLETED"
FAILED = "ACTIVITY_TASK_STATE_FAILED"


class Engine:
    """A tiny stand-in for the standalone-activity surface."""

    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], dict] = {}
        self.queue: list[tuple[str, str]] = []
        self.calls: list[tuple[str, str]] = []
        self.raw: list[tuple[str, str]] = []
        self.beats: list[tuple[str, str]] = []
        self.headers: list[httpx.Headers] = []

    # ── construction ────────────────────────────────────────────────────

    def row(self, activity_id: str, run_id: str, **over) -> dict:
        row = {
            "execution": {"workflowId": activity_id, "runId": run_id},
            "type": {"name": over.pop("type", "echo")},
            "taskQueue": over.pop("task_queue", "default"),
            "status": SCHEDULED,
            "attempt": 1,
        }
        row.update(over)
        return row

    def schedule(self, activity_id: str, run_id: str = "run-1", **over) -> dict:
        row = self.row(activity_id, run_id, **over)
        self.rows[(activity_id, run_id)] = row
        self.queue.append((activity_id, run_id))
        return row

    # ── transport ───────────────────────────────────────────────────────

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.headers.append(request.headers)
        path = request.url.path
        method = request.method
        # Both forms: the engine splits the DECODED path (embed.go:612), while
        # the raw one is what actually went on the wire.
        self.calls.append((method, path))
        self.raw.append((method, request.url.raw_path.decode()))

        if not path.startswith(BASE):
            return self.err(404, "not found")
        rest = path[len(BASE) :].strip("/")
        parts = rest.split("/") if rest else []
        body = json.loads(request.content) if request.content else {}

        if not parts and method == "POST":
            return self.start(body)
        if not parts and method == "GET":
            return self.list(request)
        if parts == ["claim"] and method == "POST":
            return self.claim(body)
        if len(parts) == 2 and method == "GET":
            return self.describe(parts[0], parts[1])
        if len(parts) == 3 and parts[2] == "history" and method == "GET":
            return self.history(parts[0], parts[1])
        if len(parts) == 3 and method == "POST":
            return self.settle(parts[0], parts[1], parts[2], body)
        return self.err(404, "not found")

    # ── operations ──────────────────────────────────────────────────────

    def start(self, body: dict) -> httpx.Response:
        activity_id = body.get("activityId") or ""
        if not activity_id:
            return self.err(400, "activityId required")
        row = self.schedule(
            activity_id,
            "run-1",
            type=(body.get("activityType") or {}).get("name", ""),
            task_queue=body.get("taskQueue", "default"),
            input=body.get("input"),
            heartbeatTimeout=body.get("heartbeatTimeout", ""),
            retryPolicy=body.get("retryPolicy"),
        )
        return httpx.Response(200, json=row)

    def list(self, request: httpx.Request) -> httpx.Response:
        rows = list(self.rows.values())
        return httpx.Response(200, json={"activities": rows, "nextCursor": ""})

    def claim(self, body: dict) -> httpx.Response:
        want = body.get("taskQueue") or ""
        for key in list(self.queue):
            row = self.rows[key]
            if want and row["taskQueue"] != want:
                continue
            self.queue.remove(key)
            row["status"] = STARTED
            row["identity"] = body.get("identity", "")
            # The engine stamps the lease it granted; the worker beats off it.
            row["leaseExpiry"] = "2099-01-01T00:00:00+00:00"
            return httpx.Response(200, json=row)
        return httpx.Response(204)

    def describe(self, activity_id: str, run_id: str) -> httpx.Response:
        row = self.rows.get((activity_id, run_id))
        if row is None:
            return self.err(404, "activity not found")
        return httpx.Response(200, json=row)

    def history(self, activity_id: str, run_id: str) -> httpx.Response:
        if (activity_id, run_id) not in self.rows:
            return self.err(404, "activity not found")
        events = [
            {
                "eventId": 1,
                "eventTime": "2026-01-01T00:00:00Z",
                "eventType": "ACTIVITY_TASK_SCHEDULED",
                "attributes": {"taskQueue": "gpu"},
            }
        ]
        return httpx.Response(200, json={"events": events, "nextCursor": 0})

    def settle(self, activity_id: str, run_id: str, verb: str, body: dict) -> httpx.Response:
        row = self.rows.get((activity_id, run_id))
        if row is None:
            return self.err(404, "activity not found")
        if row["status"] in (COMPLETED, FAILED):
            return self.err(409, f"activity terminal: status={row['status']}")
        if verb == "heartbeat":
            self.beats.append((activity_id, run_id))
        elif verb == "complete":
            row["status"] = COMPLETED
            row["result"] = body.get("result")
        elif verb == "fail":
            row["status"] = FAILED
            row["failureCause"] = body.get("cause", "")
        elif verb == "cancel":
            row["status"] = "ACTIVITY_TASK_STATE_CANCELED"
        else:
            return self.err(404, "not found")
        return httpx.Response(200, json=row)

    @staticmethod
    def err(code: int, message: str) -> httpx.Response:
        # code is a NUMBER on this surface, unlike the rest of the API.
        return httpx.Response(code, json={"error": message, "code": code})


@pytest.fixture
def engine() -> Engine:
    return Engine()


@pytest.fixture
def tasks(engine: Engine) -> Tasks:
    transport = httpx.MockTransport(engine.handler)
    return Tasks(
        url="https://api.hanzo.ai",
        namespace=NS,
        token="hk-test",
        http=httpx.AsyncClient(transport=transport),
    )


# ── the package no longer carries the trap ──────────────────────────────


def test_no_temporal_anywhere() -> None:
    """0.1.0 shipped a Temporal gRPC client aimed at a port we do not serve."""
    import pathlib

    import hanzo_tasks

    root = pathlib.Path(hanzo_tasks.__file__).parent
    for path in root.rglob("*.py"):
        source = path.read_text()
        assert "temporalio" not in source, path
        assert "7233" not in source, path


def test_version_is_the_superseding_one() -> None:
    import hanzo_tasks

    assert hanzo_tasks.__version__ == "0.2.0"


# ── client ──────────────────────────────────────────────────────────────


async def test_dispatch_sends_the_engines_shape(tasks: Tasks, engine: Engine) -> None:
    activity = await tasks.dispatch(
        "render",
        id="job-1",
        input={"scene": 3},
        task_queue="gpu",
        heartbeat_timeout="60s",
        retry=RetryPolicy(maximum_attempts=5, backoff_coefficient=2.0),
    )
    assert ("POST", BASE) in engine.calls
    assert activity.id == "job-1"
    assert activity.type == "render"
    assert activity.task_queue == "gpu"
    assert activity.status == SCHEDULED
    assert not activity.terminal

    stored = engine.rows[("job-1", "run-1")]
    assert stored["input"] == {"scene": 3}
    assert stored["heartbeatTimeout"] == "60s"
    assert stored["retryPolicy"] == {"maximumAttempts": 5, "backoffCoefficient": 2.0}


async def test_dispatch_mints_an_id_when_none_is_given(tasks: Tasks) -> None:
    activity = await tasks.dispatch("render")
    assert activity.id


async def test_bearer_token_is_sent(tasks: Tasks, engine: Engine) -> None:
    await tasks.dispatch("render", id="job-1")
    assert engine.headers[-1]["authorization"] == "Bearer hk-test"


async def test_empty_queue_is_none_not_an_error(tasks: Tasks) -> None:
    """204 is the ordinary result of polling, not a failure."""
    assert await tasks.claim(task_queue="gpu") is None


async def test_claim_returns_the_started_activity(tasks: Tasks, engine: Engine) -> None:
    engine.schedule("job-1", task_queue="gpu")
    claimed = await tasks.claim(task_queue="gpu", identity="spark")
    assert claimed is not None
    assert claimed.id == "job-1"
    assert claimed.status == STARTED
    assert claimed.identity == "spark"


async def test_claim_filters_by_queue(tasks: Tasks, engine: Engine) -> None:
    engine.schedule("cpu-job", task_queue="cpu")
    assert await tasks.claim(task_queue="gpu") is None
    assert (await tasks.claim(task_queue="cpu")) is not None


async def test_describe_and_list(tasks: Tasks, engine: Engine) -> None:
    engine.schedule("job-1")
    activity = await tasks.describe("job-1", "run-1")
    assert activity.id == "job-1"

    page = await tasks.activities(page_size=10)
    assert len(page) == 1
    assert [a.id for a in page] == ["job-1"]


async def test_history(tasks: Tasks, engine: Engine) -> None:
    engine.schedule("job-1")
    events, cursor = await tasks.history("job-1", "run-1")
    assert [e.type for e in events] == ["ACTIVITY_TASK_SCHEDULED"]
    assert events[0].id == 1
    assert cursor == 0


async def test_missing_activity_is_not_found(tasks: Tasks) -> None:
    with pytest.raises(NotFound) as caught:
        await tasks.describe("nope", "run-1")
    assert caught.value.code == 404


async def test_second_settle_is_terminal(tasks: Tasks, engine: Engine) -> None:
    engine.schedule("job-1")
    await tasks.complete("job-1", "run-1", {"ok": True})
    with pytest.raises(Terminal) as caught:
        await tasks.complete("job-1", "run-1", {"ok": True})
    assert caught.value.code == 409


async def test_refusal_is_denied(engine: Engine) -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": "identity required", "code": 403})

    tasks = Tasks(http=httpx.AsyncClient(transport=httpx.MockTransport(refuse)))
    with pytest.raises(Denied):
        await tasks.dispatch("render")


async def test_path_segments_are_percent_encoded(tasks: Tasks, engine: Engine) -> None:
    """Ids go on the wire encoded, so they cannot corrupt the URL.

    This is hygiene, not protection against every input: the engine splits
    Go's DECODED r.URL.Path (embed.go:612), so an id containing a literal
    slash arrives as two segments and is simply not addressable there. What
    encoding does buy is that a space, '?' or '#' in an id stays part of the
    segment instead of becoming a query or fragment.
    """
    engine.rows[("job 1?x", "run-1")] = engine.row("job 1?x", "run-1")
    activity = await tasks.describe("job 1?x", "run-1")
    assert activity.id == "job 1?x"
    # Encoded on the wire, decoded back to one segment by the reader.
    assert ("GET", f"{BASE}/job%201%3Fx/run-1") in engine.raw


# ── worker ──────────────────────────────────────────────────────────────


async def test_worker_runs_the_handler_and_completes(tasks: Tasks, engine: Engine) -> None:
    engine.schedule("job-1", type="render", task_queue="gpu")
    worker = Worker(tasks, task_queue="gpu")

    seen: list[Activity] = []

    @worker.handler("render")
    async def render(activity: Activity) -> dict:
        seen.append(activity)
        return {"frames": 120}

    assert await worker.step() is True
    assert [a.id for a in seen] == ["job-1"]
    assert engine.rows[("job-1", "run-1")]["status"] == COMPLETED
    assert engine.rows[("job-1", "run-1")]["result"] == {"frames": 120}


async def test_worker_reports_idle(tasks: Tasks) -> None:
    worker = Worker(tasks, task_queue="gpu")
    assert await worker.step() is False


async def test_sync_handlers_work(tasks: Tasks, engine: Engine) -> None:
    engine.schedule("job-1", type="render", task_queue="gpu")
    worker = Worker(tasks, task_queue="gpu")

    @worker.handler("render")
    def render(activity: Activity) -> str:
        return "done"

    await worker.step()
    assert engine.rows[("job-1", "run-1")]["result"] == "done"


async def test_handler_exception_fails_the_activity(tasks: Tasks, engine: Engine) -> None:
    engine.schedule("job-1", type="render", task_queue="gpu")
    worker = Worker(tasks, task_queue="gpu")

    @worker.handler("render")
    async def render(activity: Activity) -> None:
        raise RuntimeError("gpu fell over")

    await worker.step()
    row = engine.rows[("job-1", "run-1")]
    assert row["status"] == FAILED
    assert "gpu fell over" in row["failureCause"]


async def test_unknown_type_is_failed_not_dropped(tasks: Tasks, engine: Engine) -> None:
    """Left claimed it would just wait out its lease and come back here."""
    engine.schedule("job-1", type="unregistered", task_queue="gpu")
    worker = Worker(tasks, task_queue="gpu")
    await worker.step()
    row = engine.rows[("job-1", "run-1")]
    assert row["status"] == FAILED
    assert "no handler registered" in row["failureCause"]


async def test_worker_holds_the_lease_while_the_handler_runs(
    tasks: Tasks, engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The heartbeat is what keeps the engine from reaping live work."""
    engine.schedule("job-1", type="slow", task_queue="gpu")
    worker = Worker(tasks, task_queue="gpu")
    monkeypatch.setattr(worker, "_interval", lambda activity: 0.02)

    @worker.handler("slow")
    async def slow(activity: Activity) -> str:
        await asyncio.sleep(0.25)
        return "done"

    await worker.step()
    assert len(engine.beats) >= 2, engine.beats
    assert engine.rows[("job-1", "run-1")]["status"] == COMPLETED


async def test_heartbeat_stops_once_the_handler_returns(
    tasks: Tasks, engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine.schedule("job-1", type="quick", task_queue="gpu")
    worker = Worker(tasks, task_queue="gpu")
    monkeypatch.setattr(worker, "_interval", lambda activity: 0.01)

    @worker.handler("quick")
    async def quick(activity: Activity) -> str:
        return "done"

    await worker.step()
    settled = len(engine.beats)
    await asyncio.sleep(0.1)
    assert len(engine.beats) == settled


def test_interval_is_a_third_of_the_granted_lease(tasks: Tasks) -> None:
    """Policy is read off the lease the SERVER granted, not recomputed."""
    from datetime import datetime, timedelta

    worker = Worker(tasks, lease_seconds=60)
    expiry = datetime.now(UTC) + timedelta(seconds=30)
    activity = Activity.from_wire(
        {
            "execution": {"workflowId": "a", "runId": "r"},
            "type": {"name": "t"},
            "status": STARTED,
            "leaseExpiry": expiry.isoformat(),
        }
    )
    assert 8.0 < worker._interval(activity) < 11.0

    # No lease stamped: fall back to what this worker asked for.
    bare = Activity.from_wire(
        {"execution": {"workflowId": "a", "runId": "r"}, "type": {"name": "t"}, "status": STARTED}
    )
    assert worker._interval(bare) == 20.0


async def test_run_loop_stops_when_asked(tasks: Tasks, engine: Engine) -> None:
    engine.schedule("job-1", type="render", task_queue="gpu")
    worker = Worker(tasks, task_queue="gpu", poll_interval=0.01)

    @worker.handler("render")
    async def render(activity: Activity) -> str:
        return "done"

    stop = asyncio.Event()
    task = asyncio.create_task(worker.run(stop=stop))
    await asyncio.sleep(0.1)
    stop.set()
    await asyncio.wait_for(task, timeout=2)
    assert engine.rows[("job-1", "run-1")]["status"] == COMPLETED


async def test_poll_failure_does_not_end_the_loop(engine: Engine) -> None:
    calls = {"n": 0}

    def flaky(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ConnectError("network blip")
        return httpx.Response(204)

    tasks = Tasks(http=httpx.AsyncClient(transport=httpx.MockTransport(flaky)))
    seen: list[BaseException] = []
    worker = Worker(tasks, poll_interval=0.01, on_error=lambda exc, activity: seen.append(exc))

    stop = asyncio.Event()
    task = asyncio.create_task(worker.run(stop=stop))
    await asyncio.sleep(0.1)
    stop.set()
    await asyncio.wait_for(task, timeout=2)

    assert len(seen) == 1
    assert calls["n"] > 1, "the loop kept polling after the blip"
