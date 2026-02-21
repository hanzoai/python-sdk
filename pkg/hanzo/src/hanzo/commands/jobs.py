"""Hanzo Jobs - Background jobs and cron CLI.

Job scheduling, execution, and management.
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

JOBS_URL = os.getenv("HANZO_JOBS_URL", "https://jobs.hanzo.ai")


def _request(method: str, path: str, **kwargs) -> httpx.Response:
    return service_request(JOBS_URL, method, path, **kwargs)


@click.group(name="jobs")
def jobs_group():
    """Hanzo Jobs - Background jobs and scheduling.

    \b
    Jobs:
      hanzo jobs run                 # Run a job
      hanzo jobs list                # List jobs
      hanzo jobs logs                # View job logs
      hanzo jobs cancel              # Cancel a job
      hanzo jobs retry               # Retry failed job

    \b
    Cron:
      hanzo jobs cron list           # List scheduled jobs
      hanzo jobs cron create         # Create cron schedule
      hanzo jobs cron pause          # Pause schedule
      hanzo jobs cron resume         # Resume schedule
      hanzo jobs cron run-now        # Trigger immediately
    """
    pass


# ============================================================================
# Job Operations
# ============================================================================


@jobs_group.command(name="run")
@click.argument("name")
@click.option("--payload", "-p", help="JSON payload")
@click.option("--queue", "-q", default="default", help="Queue name")
@click.option("--priority", type=int, default=5, help="Priority (1-10)")
@click.option("--delay", "-d", help="Delay before execution (e.g., 5m, 1h)")
@click.option("--wait", "-w", is_flag=True, help="Wait for completion")
def jobs_run(name: str, payload: str, queue: str, priority: int, delay: str, wait: bool):
    """Run a background job."""
    body = {"name": name, "queue": queue, "priority": priority}
    if payload:
        body["payload"] = json.loads(payload)
    if delay:
        body["delay"] = delay

    resp = _request("post", "/v1/jobs", json=body)
    data = check_response(resp)

    job_id = data.get("id", data.get("job_id", "-"))
    console.print(f"[green]✓[/green] Job '{name}' queued")
    console.print(f"  ID: {job_id}")
    console.print(f"  Queue: {queue}")
    console.print(f"  Priority: {priority}")
    if delay:
        console.print(f"  Delay: {delay}")

    if wait:
        console.print("[dim]Waiting for completion...[/dim]")
        resp = _request("get", f"/v1/jobs/{job_id}/wait", timeout=300)
        result = check_response(resp)
        status = result.get("status", "unknown")
        style = "green" if status == "completed" else "red"
        console.print(f"  Status: [{style}]{status}[/{style}]")
        if result.get("duration_ms"):
            console.print(f"  Duration: {result['duration_ms']}ms")


@jobs_group.command(name="list")
@click.option("--status", "-s", type=click.Choice(["pending", "active", "completed", "failed", "all"]), default="all")
@click.option("--queue", "-q", help="Filter by queue")
@click.option("--limit", "-n", default=20, help="Max results")
def jobs_list(status: str, queue: str, limit: int):
    """List jobs."""
    params = {"limit": limit}
    if status != "all":
        params["status"] = status
    if queue:
        params["queue"] = queue

    resp = _request("get", "/v1/jobs", params=params)
    data = check_response(resp)
    jobs = data.get("jobs", data.get("items", []))

    table = Table(title="Jobs", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Status", style="green")
    table.add_column("Queue", style="dim")
    table.add_column("Started", style="dim")
    table.add_column("Duration", style="dim")

    for j in jobs:
        j_status = j.get("status", "unknown")
        status_style = {
            "pending": "yellow",
            "active": "cyan",
            "completed": "green",
            "failed": "red",
        }.get(j_status, "white")

        table.add_row(
            str(j.get("id", ""))[:16],
            j.get("name", "-"),
            f"[{status_style}]{j_status}[/{status_style}]",
            j.get("queue", "-"),
            str(j.get("started_at", ""))[:19],
            f"{j.get('duration_ms', '-')}ms" if j.get("duration_ms") else "-",
        )

    console.print(table)
    if not jobs:
        console.print("[dim]No jobs found[/dim]")


@jobs_group.command(name="logs")
@click.argument("job_id")
@click.option("--follow", "-f", is_flag=True, help="Follow logs")
@click.option("--tail", "-n", default=100, help="Number of lines")
def jobs_logs(job_id: str, follow: bool, tail: int):
    """View job logs."""
    params = {"tail": tail}
    if follow:
        params["follow"] = "true"

    resp = _request("get", f"/v1/jobs/{job_id}/logs", params=params)
    data = check_response(resp)
    lines = data.get("logs", data.get("lines", []))

    console.print(f"[cyan]Logs for job {job_id}:[/cyan]")
    for line in lines:
        if isinstance(line, dict):
            ts = str(line.get("timestamp", ""))[:19]
            level = line.get("level", "info")
            msg = line.get("message", "")
            style = "red" if level == "error" else "yellow" if level == "warn" else "dim"
            console.print(f"[dim]{ts}[/dim] [{style}]{level}[/{style}] {msg}")
        else:
            console.print(str(line))

    if not lines:
        console.print("[dim]No logs available[/dim]")


@jobs_group.command(name="cancel")
@click.argument("job_id")
@click.option("--force", "-f", is_flag=True, help="Force cancellation")
def jobs_cancel(job_id: str, force: bool):
    """Cancel a running job."""
    payload = {}
    if force:
        payload["force"] = True

    resp = _request("post", f"/v1/jobs/{job_id}/cancel", json=payload)
    check_response(resp)
    console.print(f"[green]✓[/green] Job '{job_id}' cancelled")


@jobs_group.command(name="retry")
@click.argument("job_id")
def jobs_retry(job_id: str):
    """Retry a failed job."""
    resp = _request("post", f"/v1/jobs/{job_id}/retry")
    data = check_response(resp)
    new_id = data.get("id", data.get("job_id", "-"))
    console.print(f"[green]✓[/green] Job '{job_id}' requeued")
    console.print(f"  New ID: {new_id}")


@jobs_group.command(name="describe")
@click.argument("job_id")
def jobs_describe(job_id: str):
    """Show job details."""
    resp = _request("get", f"/v1/jobs/{job_id}")
    data = check_response(resp)

    status = data.get("status", "unknown")
    status_style = {
        "pending": "yellow",
        "active": "cyan",
        "completed": "green",
        "failed": "red",
    }.get(status, "white")

    console.print(
        Panel(
            f"[cyan]ID:[/cyan] {data.get('id', job_id)}\n"
            f"[cyan]Name:[/cyan] {data.get('name', '-')}\n"
            f"[cyan]Status:[/cyan] [{status_style}]{status}[/{status_style}]\n"
            f"[cyan]Queue:[/cyan] {data.get('queue', '-')}\n"
            f"[cyan]Priority:[/cyan] {data.get('priority', '-')}\n"
            f"[cyan]Attempts:[/cyan] {data.get('attempts', 0)}/{data.get('max_attempts', 3)}\n"
            f"[cyan]Started:[/cyan] {str(data.get('started_at', '-'))[:19]}\n"
            f"[cyan]Duration:[/cyan] {data.get('duration_ms', '-')}ms\n"
            f"[cyan]Payload:[/cyan] {json.dumps(data.get('payload', {}), indent=2, default=str)}",
            title="Job Details",
            border_style="cyan",
        )
    )
    if data.get("error"):
        console.print(f"\n[red]Error:[/red] {data['error']}")


# ============================================================================
# Cron Operations
# ============================================================================


@jobs_group.group()
def cron():
    """Manage scheduled jobs (cron)."""
    pass


@cron.command(name="list")
@click.option("--status", "-s", type=click.Choice(["active", "paused", "all"]), default="all")
def cron_list(status: str):
    """List cron schedules."""
    params = {}
    if status != "all":
        params["status"] = status

    resp = _request("get", "/v1/cron", params=params)
    data = check_response(resp)
    items = data.get("schedules", data.get("items", []))

    table = Table(title="Cron Schedules", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Schedule", style="white")
    table.add_column("Status", style="green")
    table.add_column("Last Run", style="dim")
    table.add_column("Next Run", style="yellow")

    for c in items:
        c_status = c.get("status", "active")
        style = "green" if c_status == "active" else "yellow"
        table.add_row(
            c.get("name", ""),
            c.get("schedule", "-"),
            f"[{style}]{c_status}[/{style}]",
            str(c.get("last_run_at", "-"))[:19],
            str(c.get("next_run_at", "-"))[:19],
        )

    console.print(table)
    if not items:
        console.print("[dim]No cron schedules found. Create one with 'hanzo jobs cron create'[/dim]")


@cron.command(name="create")
@click.argument("name")
@click.option("--schedule", "-s", required=True, help="Cron expression (e.g., '0 * * * *')")
@click.option("--job", "-j", required=True, help="Job name to run")
@click.option("--payload", "-p", help="JSON payload")
@click.option("--timezone", "-tz", default="UTC", help="Timezone")
def cron_create(name: str, schedule: str, job: str, payload: str, timezone: str):
    """Create a cron schedule."""
    body = {"name": name, "schedule": schedule, "job": job, "timezone": timezone}
    if payload:
        body["payload"] = json.loads(payload)

    resp = _request("post", "/v1/cron", json=body)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Cron schedule '{name}' created")
    console.print(f"  Schedule: {schedule}")
    console.print(f"  Job: {job}")
    console.print(f"  Timezone: {timezone}")
    if data.get("next_run_at"):
        console.print(f"  Next run: {data['next_run_at']}")


@cron.command(name="delete")
@click.argument("name")
def cron_delete(name: str):
    """Delete a cron schedule."""
    resp = _request("delete", f"/v1/cron/{name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Cron schedule '{name}' deleted")


@cron.command(name="pause")
@click.argument("name")
def cron_pause(name: str):
    """Pause a cron schedule."""
    resp = _request("post", f"/v1/cron/{name}/pause")
    check_response(resp)
    console.print(f"[green]✓[/green] Cron schedule '{name}' paused")


@cron.command(name="resume")
@click.argument("name")
def cron_resume(name: str):
    """Resume a paused cron schedule."""
    resp = _request("post", f"/v1/cron/{name}/resume")
    check_response(resp)
    console.print(f"[green]✓[/green] Cron schedule '{name}' resumed")


@cron.command(name="run-now")
@click.argument("name")
def cron_run_now(name: str):
    """Trigger a cron job immediately."""
    resp = _request("post", f"/v1/cron/{name}/trigger")
    data = check_response(resp)
    console.print(f"[green]✓[/green] Cron job '{name}' triggered")
    console.print(f"  Job ID: {data.get('job_id', data.get('id', '-'))}")
