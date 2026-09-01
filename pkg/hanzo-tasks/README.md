# hanzo-tasks

Durable activities on the native Hanzo Tasks engine.

The engine is Hanzo's own (`hanzoai/tasks`), reached over JSON at
`api.hanzo.ai/v1/tasks`. It speaks no protobuf and no gRPC, and this package
depends on no workflow runtime — dispatching work and running a worker are both
plain HTTP over `httpx`.

```bash
pip install hanzo-tasks
```

## Dispatch

```python
from hanzo_tasks import Tasks

async with Tasks.from_env() as tasks:
    activity = await tasks.dispatch(
        "render",
        input={"scene": 3},
        task_queue="gpu",
        heartbeat_timeout="60s",
    )
    print(activity.id, activity.run_id, activity.status)
```

`from_env()` reads `HANZO_API_KEY`, `HANZO_TASKS_URL` and
`HANZO_TASKS_NAMESPACE`. The org is never named in a request: IAM validates the
bearer token and the edge mints the org from the validated claim, so a caller
cannot reach another tenant's shard by asking to.

## Run a worker

The worker **polls**. It never accepts a push, so it needs no inbound address
and runs behind NAT.

```python
from hanzo_tasks import Tasks, Worker

tasks = Tasks.from_env()
worker = Worker(tasks, task_queue="gpu")


@worker.handler("render")
async def render(activity):
    return {"frames": 120}


await worker.run()
```

Return a value to complete the activity; raise to fail it with that cause.
Handlers may be async or plain functions.

## What the engine does, so you don't

These are properties of the engine, not of this client. There is deliberately
no second copy of them here, because a second copy can disagree.

- **A dead worker's work comes back.** The engine reaps expired leases before
  every claim, so an activity whose claimant stopped heartbeating returns to
  `SCHEDULED` and the next poll picks it up. No client-side timer.
- **Two workers never claim the same activity.** Claims are serialized per
  namespace.
- **The lease is the activity's own heartbeat timeout**, else the worker's
  `lease_seconds`, else the engine default. `Worker` heartbeats at a third of
  the window the server actually granted, so a beat can be missed without
  losing the claim.
- **An empty queue is not an error.** It is `204`, and `claim()` returns
  `None`.
- **Retries are the engine's.** Pass a `RetryPolicy` to `dispatch()`; the
  engine counts attempts and fails the activity when they are exhausted.

## Reading state

```python
page = await tasks.activities(page_size=50)
for activity in page:
    print(activity.id, activity.status, activity.attempt)

activity = await tasks.describe(id, run_id)
events, cursor = await tasks.history(id, run_id)
```

## Errors

The engine reports `{"error": ..., "code": <int>}` — `code` is a number here,
not the `status` string the rest of the Hanzo API uses.

| Exception | Meaning |
|---|---|
| `Denied` | 401/403 — no validated principal, or one carrying no org |
| `NotFound` | 404 — no such activity in this namespace |
| `Terminal` | 409 — already completed, failed or canceled |
| `TasksError` | anything else, carrying `.code` |

## License

MIT
