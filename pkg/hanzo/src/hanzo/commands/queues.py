"""Hanzo Queues - Task and message queues CLI.

BullMQ-compatible job and message queues.
"""

import os
import json

import click
import httpx
from rich import box
from rich.panel import Panel
from rich.table import Table

from ..utils.output import console
from .base import service_request, check_response

QUEUES_URL = os.getenv("HANZO_QUEUES_URL", "https://queues.hanzo.ai")


def _request(method: str, path: str, **kwargs) -> httpx.Response:
    return service_request(QUEUES_URL, method, path, **kwargs)


@click.group(name="queues")
def queues_group():
    """Hanzo Queues - Task and message queues.

    \b
    Queues:
      hanzo queues list              # List queues
      hanzo queues create            # Create queue
      hanzo queues stats             # Queue statistics

    \b
    Jobs:
      hanzo queues push              # Push job to queue
      hanzo queues pop               # Pop job from queue
      hanzo queues peek              # Peek at next job

    \b
    Management:
      hanzo queues retry             # Retry failed jobs
      hanzo queues dlq               # Dead letter queue management
      hanzo queues drain             # Drain a queue
    """
    pass


# ============================================================================
# Queue Management
# ============================================================================


@queues_group.command(name="list")
@click.option("--project", "-p", help="Project ID")
def queues_list(project: str):
    """List all queues."""
    params = {}
    if project:
        params["project"] = project

    resp = _request("get", "/v1/queues", params=params)
    data = check_response(resp)
    items = data.get("queues", data.get("items", []))

    table = Table(title="Queues", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Pending", style="yellow")
    table.add_column("Active", style="green")
    table.add_column("Completed", style="dim")
    table.add_column("Failed", style="red")
    table.add_column("Delayed", style="dim")

    for q in items:
        table.add_row(
            q.get("name", ""),
            str(q.get("pending", 0)),
            str(q.get("active", 0)),
            str(q.get("completed", 0)),
            str(q.get("failed", 0)),
            str(q.get("delayed", 0)),
        )

    console.print(table)
    if not items:
        console.print("[dim]No queues found. Create one with 'hanzo queues create'[/dim]")


@queues_group.command(name="create")
@click.argument("name")
@click.option("--concurrency", "-c", default=10, help="Max concurrent workers")
@click.option("--rate-limit", "-r", help="Rate limit (e.g., '100/m')")
@click.option("--retry", default=3, help="Max retry attempts")
@click.option("--backoff", default="exponential", help="Backoff strategy")
def queues_create(name: str, concurrency: int, rate_limit: str, retry: int, backoff: str):
    """Create a queue."""
    payload = {
        "name": name,
        "concurrency": concurrency,
        "max_retries": retry,
        "backoff": backoff,
    }
    if rate_limit:
        payload["rate_limit"] = rate_limit

    resp = _request("post", "/v1/queues", json=payload)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Queue '{name}' created")
    console.print(f"  ID: {data.get('id', '-')}")
    console.print(f"  Concurrency: {concurrency}")
    console.print(f"  Max retries: {retry}")
    console.print(f"  Backoff: {backoff}")
    if rate_limit:
        console.print(f"  Rate limit: {rate_limit}")


@queues_group.command(name="delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Force delete with pending jobs")
def queues_delete(name: str, force: bool):
    """Delete a queue."""
    if not force:
        from rich.prompt import Confirm

        if not Confirm.ask(f"[red]Delete queue '{name}'?[/red]"):
            return

    resp = _request("delete", f"/v1/queues/{name}", params={"force": str(force).lower()})
    check_response(resp)
    console.print(f"[green]✓[/green] Queue '{name}' deleted")


@queues_group.command(name="stats")
@click.argument("name")
def queues_stats(name: str):
    """Show queue statistics."""
    resp = _request("get", f"/v1/queues/{name}/stats")
    data = check_response(resp)

    console.print(
        Panel(
            f"[cyan]Queue:[/cyan] {data.get('name', name)}\n"
            f"[cyan]Pending:[/cyan] {data.get('pending', 0):,}\n"
            f"[cyan]Active:[/cyan] {data.get('active', 0)}\n"
            f"[cyan]Completed:[/cyan] {data.get('completed', 0):,} (last 24h)\n"
            f"[cyan]Failed:[/cyan] {data.get('failed', 0)}\n"
            f"[cyan]Delayed:[/cyan] {data.get('delayed', 0)}\n"
            f"[cyan]Avg process time:[/cyan] {data.get('avg_process_time_ms', 0)}ms\n"
            f"[cyan]Throughput:[/cyan] {data.get('throughput_per_min', 0):,}/min",
            title="Queue Statistics",
            border_style="cyan",
        )
    )


# ============================================================================
# Job Operations
# ============================================================================


@queues_group.command(name="push")
@click.argument("queue")
@click.option("--data", "-d", required=True, help="Job data (JSON)")
@click.option("--name", "-n", help="Job name")
@click.option("--priority", "-p", type=int, default=0, help="Job priority (higher = more urgent)")
@click.option("--delay", help="Delay before processing (e.g., '5m', '1h')")
@click.option("--attempts", "-a", default=3, help="Max attempts")
def queues_push(queue: str, data: str, name: str, priority: int, delay: str, attempts: int):
    """Push a job to a queue."""
    payload = {"data": json.loads(data), "priority": priority, "max_attempts": attempts}
    if name:
        payload["name"] = name
    if delay:
        payload["delay"] = delay

    resp = _request("post", f"/v1/queues/{queue}/jobs", json=payload)
    result = check_response(resp)

    console.print(f"[green]✓[/green] Job pushed to '{queue}'")
    console.print(f"  Job ID: {result.get('id', result.get('job_id', '-'))}")
    if name:
        console.print(f"  Name: {name}")
    if delay:
        console.print(f"  Delay: {delay}")
    console.print(f"  Priority: {priority}")


@queues_group.command(name="pop")
@click.argument("queue")
@click.option("--count", "-n", default=1, help="Number of jobs to pop")
@click.option("--wait", "-w", is_flag=True, help="Wait for jobs if none available")
def queues_pop(queue: str, count: int, wait: bool):
    """Pop jobs from a queue (for workers)."""
    params = {"count": count}
    if wait:
        params["wait"] = "true"

    resp = _request("post", f"/v1/queues/{queue}/pop", json=params)
    data = check_response(resp)
    jobs = data.get("jobs", [])

    for job in jobs:
        console.print(
            Panel(
                f"[cyan]ID:[/cyan] {job.get('id', '-')}\n"
                f"[cyan]Name:[/cyan] {job.get('name', '-')}\n"
                f"[cyan]Data:[/cyan] {json.dumps(job.get('data', {}), default=str)}",
                border_style="cyan",
            )
        )

    if not jobs:
        console.print("[dim]No jobs available[/dim]")


@queues_group.command(name="peek")
@click.argument("queue")
@click.option("--count", "-n", default=5, help="Number of jobs to peek")
def queues_peek(queue: str, count: int):
    """Peek at jobs without removing them."""
    resp = _request("get", f"/v1/queues/{queue}/jobs", params={"limit": count, "status": "pending"})
    data = check_response(resp)
    jobs = data.get("jobs", data.get("items", []))

    table = Table(title=f"Next {count} Jobs in '{queue}'", box=box.ROUNDED)
    table.add_column("Job ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Priority", style="yellow")
    table.add_column("Attempts", style="dim")
    table.add_column("Created", style="dim")

    for j in jobs:
        table.add_row(
            str(j.get("id", ""))[:16],
            j.get("name", "-"),
            str(j.get("priority", 0)),
            f"{j.get('attempts', 0)}/{j.get('max_attempts', 3)}",
            str(j.get("created_at", ""))[:19],
        )

    console.print(table)
    if not jobs:
        console.print("[dim]No pending jobs[/dim]")


@queues_group.command(name="get")
@click.argument("queue")
@click.argument("job_id")
def queues_get(queue: str, job_id: str):
    """Get job details."""
    resp = _request("get", f"/v1/queues/{queue}/jobs/{job_id}")
    data = check_response(resp)

    status = data.get("status", "unknown")
    status_style = {
        "pending": "yellow",
        "active": "cyan",
        "completed": "green",
        "failed": "red",
        "delayed": "dim",
    }.get(status, "white")

    console.print(
        Panel(
            f"[cyan]Job ID:[/cyan] {data.get('id', job_id)}\n"
            f"[cyan]Queue:[/cyan] {queue}\n"
            f"[cyan]Name:[/cyan] {data.get('name', '-')}\n"
            f"[cyan]Status:[/cyan] [{status_style}]{status}[/{status_style}]\n"
            f"[cyan]Attempts:[/cyan] {data.get('attempts', 0)}/{data.get('max_attempts', 3)}\n"
            f"[cyan]Created:[/cyan] {str(data.get('created_at', ''))[:19]}\n"
            f"[cyan]Processed:[/cyan] {str(data.get('processed_at', '-'))[:19]}\n"
            f"[cyan]Duration:[/cyan] {data.get('duration_ms', '-')}ms\n"
            f"[cyan]Data:[/cyan] {json.dumps(data.get('data', {}), indent=2, default=str)}",
            title="Job Details",
            border_style="cyan",
        )
    )


# ============================================================================
# Retry / DLQ / Drain
# ============================================================================


@queues_group.command(name="retry")
@click.argument("queue")
@click.option("--job-id", "-j", help="Specific job ID to retry")
@click.option("--all-failed", is_flag=True, help="Retry all failed jobs")
@click.option("--count", "-n", type=int, help="Retry N failed jobs")
def queues_retry(queue: str, job_id: str, all_failed: bool, count: int):
    """Retry failed jobs."""
    if not job_id and not all_failed and not count:
        raise click.ClickException("Specify --job-id, --all-failed, or --count")

    payload = {}
    if job_id:
        payload["job_id"] = job_id
    if all_failed:
        payload["all_failed"] = True
    if count:
        payload["count"] = count

    resp = _request("post", f"/v1/queues/{queue}/retry", json=payload)
    data = check_response(resp)
    console.print(f"[green]✓[/green] {data.get('retried', 0)} job(s) queued for retry")


@queues_group.group()
def dlq():
    """Dead letter queue management."""
    pass


@dlq.command(name="list")
@click.argument("queue")
@click.option("--limit", "-n", default=20, help="Max jobs to show")
def dlq_list(queue: str, limit: int):
    """List jobs in dead letter queue."""
    resp = _request("get", f"/v1/queues/{queue}/dlq", params={"limit": limit})
    data = check_response(resp)
    jobs = data.get("jobs", data.get("items", []))

    table = Table(title=f"Dead Letter Queue: {queue}", box=box.ROUNDED)
    table.add_column("Job ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Error", style="red")
    table.add_column("Attempts", style="yellow")
    table.add_column("Failed At", style="dim")

    for j in jobs:
        table.add_row(
            str(j.get("id", ""))[:16],
            j.get("name", "-"),
            str(j.get("error", "-"))[:40],
            str(j.get("attempts", 0)),
            str(j.get("failed_at", ""))[:19],
        )

    console.print(table)
    if not jobs:
        console.print("[dim]No jobs in DLQ[/dim]")


@dlq.command(name="retry")
@click.argument("queue")
@click.option("--job-id", "-j", help="Specific job to retry")
@click.option("--all", "-a", "all_jobs", is_flag=True, help="Retry all DLQ jobs")
def dlq_retry(queue: str, job_id: str, all_jobs: bool):
    """Retry jobs from dead letter queue."""
    if not job_id and not all_jobs:
        raise click.ClickException("Specify --job-id or --all")

    payload = {}
    if job_id:
        payload["job_id"] = job_id
    if all_jobs:
        payload["all"] = True

    resp = _request("post", f"/v1/queues/{queue}/dlq/retry", json=payload)
    data = check_response(resp)
    console.print(f"[green]✓[/green] {data.get('retried', 0)} DLQ job(s) moved back to queue")


@dlq.command(name="purge")
@click.argument("queue")
def dlq_purge(queue: str):
    """Purge all jobs from dead letter queue."""
    from rich.prompt import Confirm

    if not Confirm.ask(f"[red]Purge all DLQ jobs for '{queue}'?[/red]"):
        return

    resp = _request("post", f"/v1/queues/{queue}/dlq/purge")
    data = check_response(resp)
    console.print(f"[green]✓[/green] Purged {data.get('purged', 0)} DLQ job(s) for '{queue}'")


@queues_group.command(name="drain")
@click.argument("queue")
@click.option("--delayed", is_flag=True, help="Also drain delayed jobs")
def queues_drain(queue: str, delayed: bool):
    """Drain all jobs from a queue."""
    from rich.prompt import Confirm

    if not Confirm.ask(f"[red]Drain all jobs from '{queue}'?[/red]"):
        return

    payload = {"delayed": delayed}
    resp = _request("post", f"/v1/queues/{queue}/drain", json=payload)
    data = check_response(resp)
    console.print(f"[green]✓[/green] Drained {data.get('drained', 0)} job(s) from '{queue}'")
    if delayed:
        console.print("[dim]Delayed jobs also removed[/dim]")


@queues_group.command(name="pause")
@click.argument("queue")
def queues_pause(queue: str):
    """Pause queue processing."""
    resp = _request("post", f"/v1/queues/{queue}/pause")
    check_response(resp)
    console.print(f"[green]✓[/green] Queue '{queue}' paused")


@queues_group.command(name="resume")
@click.argument("queue")
def queues_resume(queue: str):
    """Resume queue processing."""
    resp = _request("post", f"/v1/queues/{queue}/resume")
    check_response(resp)
    console.print(f"[green]✓[/green] Queue '{queue}' resumed")
