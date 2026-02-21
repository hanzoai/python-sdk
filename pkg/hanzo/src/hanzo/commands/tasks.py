"""Hanzo Tasks - Task orchestration CLI.

Developer-facing task graphs, schedules, triggers, and runbooks.
Built on top of jobs for execution substrate.
"""

import os
import json

import click
import httpx
from rich import box
from rich.panel import Panel
from rich.table import Table

from .base import check_response, service_request
from ..utils.output import console

TASKS_URL = os.getenv("HANZO_TASKS_URL", "https://tasks.hanzo.ai")


def _request(method: str, path: str, **kwargs) -> httpx.Response:
    return service_request(TASKS_URL, method, path, **kwargs)


@click.group(name="tasks")
def tasks_group():
    """Hanzo Tasks - Workflow orchestration.

    \b
    Tasks:
      hanzo tasks create             # Create a task
      hanzo tasks list               # List tasks
      hanzo tasks describe           # Task details
      hanzo tasks delete             # Delete task
      hanzo tasks run                # Run task manually

    \b
    Schedules:
      hanzo tasks schedule set       # Set cron schedule
      hanzo tasks schedule list      # List schedules
      hanzo tasks schedule rm        # Remove schedule

    \b
    Runs:
      hanzo tasks runs list          # List task runs
      hanzo tasks runs logs          # View run logs
      hanzo tasks runs cancel        # Cancel a run
      hanzo tasks runs retry         # Retry a run

    \b
    Triggers:
      hanzo tasks triggers add       # Add trigger
      hanzo tasks triggers list      # List triggers
      hanzo tasks triggers rm        # Remove trigger
    """
    pass


# ============================================================================
# Task Management
# ============================================================================


@tasks_group.command(name="create")
@click.argument("name")
@click.option("--image", "-i", help="Container image to run")
@click.option("--cmd", "-c", help="Command to execute")
@click.option("--function", "-f", help="Function to invoke")
@click.option("--env", "-e", multiple=True, help="Environment variables")
@click.option("--timeout", "-t", default="1h", help="Task timeout")
@click.option("--retries", "-r", default=3, help="Max retries on failure")
def tasks_create(
    name: str,
    image: str,
    cmd: str,
    function: str,
    env: tuple,
    timeout: str,
    retries: int,
):
    """Create a task definition.

    \b
    Examples:
      hanzo tasks create etl --image my-etl:v1 --timeout 2h
      hanzo tasks create backup --cmd "pg_dump..." --retries 5
      hanzo tasks create notify --function notifications.send
    """
    body = {"name": name, "timeout": timeout, "max_retries": retries}
    if image:
        body["image"] = image
    if cmd:
        body["command"] = cmd
    if function:
        body["function"] = function
    if env:
        env_dict = {}
        for e in env:
            k, v = e.split("=", 1)
            env_dict[k] = v
        body["env"] = env_dict

    resp = _request("post", "/v1/tasks", json=body)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Task '{name}' created")
    console.print(f"  ID: {data.get('id', '-')}")
    if image:
        console.print(f"  Image: {image}")
    elif cmd:
        console.print(f"  Command: {cmd}")
    elif function:
        console.print(f"  Function: {function}")
    console.print(f"  Timeout: {timeout}")
    console.print(f"  Retries: {retries}")


@tasks_group.command(name="list")
@click.option(
    "--status", "-s", type=click.Choice(["active", "disabled", "all"]), default="all"
)
def tasks_list(status: str):
    """List all tasks."""
    params = {}
    if status != "all":
        params["status"] = status

    resp = _request("get", "/v1/tasks", params=params)
    data = check_response(resp)
    items = data.get("tasks", data.get("items", []))

    table = Table(title="Tasks", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Schedule", style="yellow")
    table.add_column("Triggers", style="green")
    table.add_column("Last Run", style="dim")
    table.add_column("Status", style="dim")

    for t in items:
        t_status = t.get("status", "active")
        style = "green" if t_status == "active" else "yellow"
        task_type = (
            "image"
            if t.get("image")
            else "function" if t.get("function") else "command"
        )
        table.add_row(
            t.get("name", ""),
            task_type,
            t.get("schedule", "-"),
            str(t.get("trigger_count", 0)),
            str(t.get("last_run_at", "-"))[:19],
            f"[{style}]{t_status}[/{style}]",
        )

    console.print(table)
    if not items:
        console.print("[dim]No tasks found. Create one with 'hanzo tasks create'[/dim]")


@tasks_group.command(name="describe")
@click.argument("name")
def tasks_describe(name: str):
    """Show task details."""
    resp = _request("get", f"/v1/tasks/{name}")
    data = check_response(resp)

    status = data.get("status", "active")
    status_style = "green" if status == "active" else "yellow"

    console.print(
        Panel(
            f"[cyan]Name:[/cyan] {data.get('name', name)}\n"
            f"[cyan]Type:[/cyan] {'image' if data.get('image') else 'function' if data.get('function') else 'command'}\n"
            f"[cyan]Image:[/cyan] {data.get('image', '-')}\n"
            f"[cyan]Timeout:[/cyan] {data.get('timeout', '-')}\n"
            f"[cyan]Retries:[/cyan] {data.get('max_retries', 3)}\n"
            f"[cyan]Schedule:[/cyan] {data.get('schedule', '-')}\n"
            f"[cyan]Triggers:[/cyan] {data.get('trigger_count', 0)}\n"
            f"[cyan]Status:[/cyan] [{status_style}]{status}[/{status_style}]\n"
            f"[cyan]Last run:[/cyan] {str(data.get('last_run_at', '-'))[:19]}\n"
            f"[cyan]Next run:[/cyan] {str(data.get('next_run_at', '-'))[:19]}",
            title="Task Details",
            border_style="cyan",
        )
    )


@tasks_group.command(name="delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def tasks_delete(name: str, force: bool):
    """Delete a task."""
    if not force:
        from rich.prompt import Confirm

        if not Confirm.ask(f"[red]Delete task '{name}'?[/red]"):
            return

    resp = _request("delete", f"/v1/tasks/{name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Task '{name}' deleted")


@tasks_group.command(name="run")
@click.argument("name")
@click.option("--input", "-i", "input_data", help="JSON input data")
@click.option("--wait", "-w", is_flag=True, help="Wait for completion")
@click.option("--env", "-e", multiple=True, help="Override env vars")
def tasks_run(name: str, input_data: str, wait: bool, env: tuple):
    """Run a task manually."""
    body = {}
    if input_data:
        body["input"] = json.loads(input_data)
    if env:
        env_dict = {}
        for e in env:
            k, v = e.split("=", 1)
            env_dict[k] = v
        body["env"] = env_dict

    resp = _request("post", f"/v1/tasks/{name}/run", json=body)
    data = check_response(resp)

    run_id = data.get("id", data.get("run_id", "-"))
    console.print(f"[green]✓[/green] Task '{name}' started")
    console.print(f"  Run ID: {run_id}")

    if wait:
        console.print("[dim]Waiting for completion...[/dim]")
        resp = _request("get", f"/v1/tasks/{name}/runs/{run_id}/wait", timeout=300)
        result = check_response(resp)
        run_status = result.get("status", "unknown")
        style = "green" if run_status == "success" else "red"
        console.print(f"  Status: [{style}]{run_status}[/{style}]")
        if result.get("duration_ms"):
            console.print(f"  Duration: {result['duration_ms']}ms")


@tasks_group.command(name="enable")
@click.argument("name")
def tasks_enable(name: str):
    """Enable a task."""
    resp = _request("post", f"/v1/tasks/{name}/enable")
    check_response(resp)
    console.print(f"[green]✓[/green] Task '{name}' enabled")


@tasks_group.command(name="disable")
@click.argument("name")
def tasks_disable(name: str):
    """Disable a task."""
    resp = _request("post", f"/v1/tasks/{name}/disable")
    check_response(resp)
    console.print(f"[green]✓[/green] Task '{name}' disabled")


# ============================================================================
# Schedules
# ============================================================================


@tasks_group.group()
def schedule():
    """Manage task schedules."""
    pass


@schedule.command(name="set")
@click.argument("task")
@click.option("--cron", "-c", help="Cron expression (e.g., '0 2 * * *')")
@click.option("--every", "-e", help="Interval (e.g., 5m, 1h, 1d)")
@click.option("--timezone", "-tz", default="UTC", help="Timezone")
def schedule_set(task: str, cron: str, every: str, timezone: str):
    """Set schedule for a task."""
    if not cron and not every:
        raise click.ClickException("Specify --cron or --every")

    body = {"timezone": timezone}
    if cron:
        body["cron"] = cron
    if every:
        body["interval"] = every

    resp = _request("put", f"/v1/tasks/{task}/schedule", json=body)
    check_response(resp)

    if cron:
        console.print(f"[green]✓[/green] Scheduled '{task}' with cron: {cron}")
    elif every:
        console.print(f"[green]✓[/green] Scheduled '{task}' every {every}")
    console.print(f"  Timezone: {timezone}")


@schedule.command(name="list")
def schedule_list():
    """List all schedules."""
    resp = _request("get", "/v1/schedules")
    data = check_response(resp)
    items = data.get("schedules", data.get("items", []))

    table = Table(title="Schedules", box=box.ROUNDED)
    table.add_column("Task", style="cyan")
    table.add_column("Schedule", style="white")
    table.add_column("Timezone", style="dim")
    table.add_column("Next Run", style="yellow")
    table.add_column("Status", style="green")

    for s in items:
        s_status = s.get("status", "active")
        style = "green" if s_status == "active" else "yellow"
        table.add_row(
            s.get("task", ""),
            s.get("cron", s.get("interval", "-")),
            s.get("timezone", "UTC"),
            str(s.get("next_run_at", "-"))[:19],
            f"[{style}]{s_status}[/{style}]",
        )

    console.print(table)
    if not items:
        console.print("[dim]No schedules found[/dim]")


@schedule.command(name="rm")
@click.argument("task")
def schedule_rm(task: str):
    """Remove schedule from a task."""
    resp = _request("delete", f"/v1/tasks/{task}/schedule")
    check_response(resp)
    console.print(f"[green]✓[/green] Removed schedule from '{task}'")


@schedule.command(name="pause")
@click.argument("task")
def schedule_pause(task: str):
    """Pause a schedule."""
    resp = _request("post", f"/v1/tasks/{task}/schedule/pause")
    check_response(resp)
    console.print(f"[green]✓[/green] Paused schedule for '{task}'")


@schedule.command(name="resume")
@click.argument("task")
def schedule_resume(task: str):
    """Resume a schedule."""
    resp = _request("post", f"/v1/tasks/{task}/schedule/resume")
    check_response(resp)
    console.print(f"[green]✓[/green] Resumed schedule for '{task}'")


# ============================================================================
# Runs
# ============================================================================


@tasks_group.group()
def runs():
    """Manage task runs."""
    pass


@runs.command(name="list")
@click.argument("task", required=False)
@click.option(
    "--status",
    "-s",
    type=click.Choice(["running", "success", "failed", "all"]),
    default="all",
)
@click.option("--limit", "-n", default=20, help="Max results")
def runs_list(task: str, status: str, limit: int):
    """List task runs."""
    params = {"limit": limit}
    if status != "all":
        params["status"] = status

    path = f"/v1/tasks/{task}/runs" if task else "/v1/runs"
    resp = _request("get", path, params=params)
    data = check_response(resp)
    items = data.get("runs", data.get("items", []))

    title = f"Runs: {task}" if task else "All Runs"
    table = Table(title=title, box=box.ROUNDED)
    table.add_column("Run ID", style="cyan")
    table.add_column("Task", style="white")
    table.add_column("Status", style="green")
    table.add_column("Started", style="dim")
    table.add_column("Duration", style="dim")
    table.add_column("Trigger", style="dim")

    for r in items:
        r_status = r.get("status", "unknown")
        status_style = {
            "running": "cyan",
            "success": "green",
            "failed": "red",
        }.get(r_status, "white")

        table.add_row(
            str(r.get("id", ""))[:16],
            r.get("task", "-"),
            f"[{status_style}]{r_status}[/{status_style}]",
            str(r.get("started_at", ""))[:19],
            f"{r.get('duration_ms', '-')}ms" if r.get("duration_ms") else "-",
            r.get("trigger", "-"),
        )

    console.print(table)
    if not items:
        console.print("[dim]No runs found[/dim]")


@runs.command(name="logs")
@click.argument("run_id")
@click.option("--follow", "-f", is_flag=True, help="Follow logs")
@click.option("--tail", "-n", default=100, help="Number of lines")
def runs_logs(run_id: str, follow: bool, tail: int):
    """View run logs."""
    params = {"tail": tail}
    if follow:
        params["follow"] = "true"

    resp = _request("get", f"/v1/runs/{run_id}/logs", params=params)
    data = check_response(resp)
    lines = data.get("logs", data.get("lines", []))

    console.print(f"[cyan]Logs for run {run_id}:[/cyan]")
    for line in lines:
        if isinstance(line, dict):
            ts = str(line.get("timestamp", ""))[:19]
            level = line.get("level", "info")
            msg = line.get("message", "")
            style = (
                "red" if level == "error" else "yellow" if level == "warn" else "dim"
            )
            console.print(f"[dim]{ts}[/dim] [{style}]{level}[/{style}] {msg}")
        else:
            console.print(str(line))

    if not lines:
        console.print("[dim]No logs available[/dim]")


@runs.command(name="cancel")
@click.argument("run_id")
def runs_cancel(run_id: str):
    """Cancel a running task."""
    resp = _request("post", f"/v1/runs/{run_id}/cancel")
    check_response(resp)
    console.print(f"[green]✓[/green] Run '{run_id}' cancelled")


@runs.command(name="retry")
@click.argument("run_id")
def runs_retry(run_id: str):
    """Retry a failed run."""
    resp = _request("post", f"/v1/runs/{run_id}/retry")
    data = check_response(resp)
    new_run_id = data.get("id", data.get("run_id", "-"))
    console.print(f"[green]✓[/green] Run '{run_id}' retried")
    console.print(f"  New Run ID: {new_run_id}")


# ============================================================================
# Triggers
# ============================================================================


@tasks_group.group()
def triggers():
    """Manage task triggers."""
    pass


@triggers.command(name="add")
@click.argument("task")
@click.option(
    "--on",
    "trigger_type",
    required=True,
    type=click.Choice(["event", "queue", "topic", "http", "schedule"]),
    help="Trigger type",
)
@click.option(
    "--source",
    "-s",
    required=True,
    help="Trigger source (event name, queue name, etc.)",
)
@click.option("--filter", "-f", help="Event filter expression")
def triggers_add(task: str, trigger_type: str, source: str, filter: str):
    """Add a trigger to a task.

    \b
    Examples:
      hanzo tasks triggers add etl --on queue --source incoming-data
      hanzo tasks triggers add notify --on topic --source orders.created
      hanzo tasks triggers add webhook --on http --source /api/trigger
      hanzo tasks triggers add sync --on event --source user.signup
    """
    body = {"type": trigger_type, "source": source}
    if filter:
        body["filter"] = filter

    resp = _request("post", f"/v1/tasks/{task}/triggers", json=body)
    check_response(resp)

    console.print(f"[green]✓[/green] Added {trigger_type} trigger to '{task}'")
    console.print(f"  Source: {source}")
    if filter:
        console.print(f"  Filter: {filter}")


@triggers.command(name="list")
@click.argument("task", required=False)
def triggers_list(task: str):
    """List triggers."""
    path = f"/v1/tasks/{task}/triggers" if task else "/v1/triggers"
    resp = _request("get", path)
    data = check_response(resp)
    items = data.get("triggers", data.get("items", []))

    table = Table(title="Triggers", box=box.ROUNDED)
    table.add_column("Task", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Source", style="yellow")
    table.add_column("Filter", style="dim")
    table.add_column("Status", style="green")

    for t in items:
        t_status = t.get("status", "active")
        style = "green" if t_status == "active" else "yellow"
        table.add_row(
            t.get("task", "-"),
            t.get("type", "-"),
            t.get("source", "-"),
            t.get("filter", "-"),
            f"[{style}]{t_status}[/{style}]",
        )

    console.print(table)
    if not items:
        console.print("[dim]No triggers found[/dim]")


@triggers.command(name="rm")
@click.argument("task")
@click.option("--source", "-s", help="Specific trigger source to remove")
@click.option("--all", "remove_all", is_flag=True, help="Remove all triggers")
def triggers_rm(task: str, source: str, remove_all: bool):
    """Remove triggers from a task."""
    if not source and not remove_all:
        raise click.ClickException("Specify --source or --all")

    if remove_all:
        resp = _request("delete", f"/v1/tasks/{task}/triggers")
        check_response(resp)
        console.print(f"[green]✓[/green] Removed all triggers from '{task}'")
    elif source:
        resp = _request("delete", f"/v1/tasks/{task}/triggers/{source}")
        check_response(resp)
        console.print(f"[green]✓[/green] Removed trigger '{source}' from '{task}'")


@triggers.command(name="pause")
@click.argument("task")
@click.option("--source", "-s", help="Specific trigger")
def triggers_pause(task: str, source: str):
    """Pause triggers."""
    path = (
        f"/v1/tasks/{task}/triggers/{source}/pause"
        if source
        else f"/v1/tasks/{task}/triggers/pause"
    )
    resp = _request("post", path)
    check_response(resp)
    console.print(f"[green]✓[/green] Paused trigger(s) for '{task}'")


@triggers.command(name="resume")
@click.argument("task")
@click.option("--source", "-s", help="Specific trigger")
def triggers_resume(task: str, source: str):
    """Resume triggers."""
    path = (
        f"/v1/tasks/{task}/triggers/{source}/resume"
        if source
        else f"/v1/tasks/{task}/triggers/resume"
    )
    resp = _request("post", path)
    check_response(resp)
    console.print(f"[green]✓[/green] Resumed trigger(s) for '{task}'")
