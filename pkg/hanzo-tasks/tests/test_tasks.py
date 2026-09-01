import json

import httpx
import pytest

from hanzo_tasks import Client, TasksConfig, TasksError


def make(handler):
    return Client(TasksConfig(token="tok", namespace="acme", host="https://api.example"), transport=httpx.MockTransport(handler))


def test_start_posts_the_engine_shape():
    seen = {}

    def handler(req: httpx.Request) -> httpx.Response:
        seen["method"], seen["path"], seen["auth"] = req.method, req.url.path, req.headers.get("authorization")
        seen["body"] = json.loads(req.content)
        return httpx.Response(200, json={"workflowId": seen["body"]["workflowId"], "runId": "r-1", "status": "Running"})

    with make(handler) as c:
        wf = c.start("agent.review", task_queue="agents", input={"repo": "acme/widgets"}, workflow_id="wf-1")
    assert seen["method"] == "POST" and seen["path"] == "/v1/tasks/namespaces/acme/workflows"
    assert seen["auth"] == "Bearer tok"
    assert seen["body"]["workflowType"] == {"name": "agent.review"} and seen["body"]["taskQueue"] == {"name": "agents"}
    assert seen["body"]["input"] == {"repo": "acme/widgets"} and seen["body"]["requestId"]
    assert wf.workflow_id == "wf-1" and wf.run_id == "r-1" and wf.status == "Running"


def test_signal_query_cancel_reset_routes():
    calls = []

    def handler(req: httpx.Request) -> httpx.Response:
        calls.append((req.method, req.url.path, req.url.query.decode(), json.loads(req.content) if req.content else None))
        return httpx.Response(200, json={"workflowId": "wf-1", "runId": "r-1", "answer": 42})

    with make(handler) as c:
        c.signal("wf-1", "approve", {"by": "z"}, run_id="r-1")
        out = c.query("wf-1", "status")
        c.cancel("wf-1", reason="done")
        c.terminate("wf-1", reason="hard")
        c.reset("wf-1", event_id=7, run_id="r-1", reason="replay")
        c.signal_with_start("agent.review", task_queue="agents", signal="kick", payload=1, workflow_id="wf-2")
    paths = [(m, p) for m, p, _, _ in calls]
    assert paths == [
        ("POST", "/v1/tasks/namespaces/acme/workflows/wf-1/signal"),
        ("POST", "/v1/tasks/namespaces/acme/workflows/wf-1/query"),
        ("POST", "/v1/tasks/namespaces/acme/workflows/wf-1/cancel"),
        ("POST", "/v1/tasks/namespaces/acme/workflows/wf-1/terminate"),
        ("POST", "/v1/tasks/namespaces/acme/workflows/wf-1/reset"),
        ("POST", "/v1/tasks/namespaces/acme/workflows/signal-with-start"),
    ]
    assert calls[0][2] == "runId=r-1" and calls[0][3] == {"name": "approve", "payload": {"by": "z"}}
    assert calls[1][3] == {"queryType": "status", "args": None} and out["answer"] == 42
    assert calls[4][3] == {"runId": "r-1", "eventId": 7, "reason": "replay", "identity": ""}
    assert calls[5][3]["signalName"] == "kick" and calls[5][3]["signalPayload"] == 1


def test_schedules_and_errors():
    calls = []

    def handler(req: httpx.Request) -> httpx.Response:
        calls.append((req.method, req.url.path))
        if req.url.path.endswith("/schedules/nope"):
            return httpx.Response(404, json={"error": "schedule not found"})
        return httpx.Response(200, json={"ok": True})

    with make(handler) as c:
        c.create_schedule({"id": "nightly", "spec": {"cron": "0 2 * * *"}, "action": {"workflowType": "agent.digest"}})
        c.trigger_schedule("nightly")
        c.delete_schedule("nightly")
        with pytest.raises(TasksError) as e:
            c.schedule("nope")
    assert e.value.status == 404 and "schedule not found" in str(e.value)
    assert calls[:3] == [
        ("POST", "/v1/tasks/namespaces/acme/schedules"),
        ("POST", "/v1/tasks/namespaces/acme/schedules/nightly/trigger"),
        ("DELETE", "/v1/tasks/namespaces/acme/schedules/nightly"),
    ]
