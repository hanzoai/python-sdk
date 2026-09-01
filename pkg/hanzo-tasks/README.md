# hanzo-tasks

The Hanzo Tasks client: durable workflows over `/v1/tasks`.

Hanzo Cloud embeds the hanzoai/tasks engine and serves it at
`https://api.hanzo.ai/v1/tasks/namespaces/{namespace}/…`, authenticated by your
IAM bearer. This package is that HTTP contract, one method per route. A
workflow's body runs in a worker written with the Go (`tasks/pkg/sdk`) or
TypeScript (`@hanzoai/tasks`) SDK.

```bash
pip install hanzo-tasks
```

```python
from hanzo_tasks import Client, TasksConfig

with Client(TasksConfig(token=TOKEN, namespace="acme")) as tasks:
    wf = tasks.start("agent.review", task_queue="agents", input={"repo": "acme/widgets"})
    tasks.signal(wf.workflow_id, "approve", {"by": "z"})
    state = tasks.query(wf.workflow_id, "status")
    tasks.cancel(wf.workflow_id, reason="superseded")
```

Routes covered: start, signal-with-start, list, describe, signal, query,
cancel, terminate, reset, history; schedules create/get/list/delete/trigger.
