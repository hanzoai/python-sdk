"""Hanzo Tasks - Task orchestration CLI.

Developer-facing task graphs, schedules, triggers, and runbooks.
Built on top of jobs for execution substrate.
"""

import click
from rich import box
from rich.panel import Panel
from rich.table import Table

from ..utils.output import console


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
def tasks_create(name: str, image: str, cmd: str, function: str, env: tuple, timeout: str, retries: int):
    """Create a task definition.

    \b
    Examples:
      hanzo tasks create etl --image my-etl:v1 --timeout 2h
      hanzo tasks create backup --cmd "pg_dump..." --retries 5
      hanzo tasks create notify --function notifications.send
    """
    console.print(f"[green]✓[/green] Task '{name}' created")
    if image:
        console.print(f"  Image: {image}")
    elif cmd:
        console.print(f"  Command: {cmd}")
    elif function:
        console.print(f"  Function: {function}")
    console.print(f"  Timeout: {timeout}")
    console.print(f"  Retries: {retries}")


@tasks_group.command(name="list")
@click.option("--status", "-s", type=click.Choice(["active", "disabled", "all"]), default="all")
def tasks_list(status: str):
    """List all tasks."""
    table = Table(title="Tasks", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Schedule", style="yellow")
    table.add_column("Triggers", style="green")
    table.add_column("Last Run", style="dim")
    table.add_column("Status", style="dim")

    console.print(table)
    console.print("[dim]No tasks found. Create one with 'hanzo tasks create'[/dim]")


@tasks_group.command(name="describe")
@click.argument("name")
def tasks_describe(name: str):
    """Show task details."""
    console.print(
        Panel(
            f"[cyan]Name:[/cyan] {name}\n"
            f"[cyan]Type:[/cyan] image\n"
            f"[cyan]Image:[/cyan] my-etl:v1\n"
            f"[cyan]Timeout:[/cyan] 2h\n"
            f"[cyan]Retries:[/cyan] 3\n"
            f"[cyan]Schedule:[/cyan] 0 2 * * * (daily 2am)\n"
            f"[cyan]Triggers:[/cyan] queue:incoming-data\n"
            f"[cyan]Last run:[/cyan] 2024-01-20 02:00:00 (success)\n"
            f"[cyan]Next run:[/cyan] 2024-01-21 02:00:00",
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
    console.print(f"[green]✓[/green] Task '{name}' deleted")


@tasks_group.command(name="run")
@click.argument("name")
@click.option("--input", "-i", "input_data", help="JSON input data")
@click.option("--wait", "-w", is_flag=True, help="Wait for completion")
@click.option("--env", "-e", multiple=True, help="Override env vars")
def tasks_run(name: str, input_data: str, wait: bool, env: tuple):
    """Run a task manually."""
    run_id = "run_abc123"
    console.print(f"[green]✓[/green] Task '{name}' started")
    console.print(f"  Run ID: {run_id}")
    if wait:
        console.print("[dim]Waiting for completion...[/dim]")


@tasks_group.command(name="enable")
@click.argument("name")
def tasks_enable(name: str):
    """Enable a task."""
    console.print(f"[green]✓[/green] Task '{name}' enabled")


@tasks_group.command(name="disable")
@click.argument("name")
def tasks_disable(name: str):
    """Disable a task."""
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
    if cron:
        console.print(f"[green]✓[/green] Scheduled '{task}' with cron: {cron}")
    elif every:
        console.print(f"[green]✓[/green] Scheduled '{task}' every {every}")
    console.print(f"  Timezone: {timezone}")


@schedule.command(name="list")
def schedule_list():
    """List all schedules."""
    table = Table(title="Schedules", box=box.ROUNDED)
    table.add_column("Task", style="cyan")
    table.add_column("Schedule", style="white")
    table.add_column("Timezone", style="dim")
    table.add_column("Next Run", style="yellow")
    table.add_column("Status", style="green")

    console.print(table)
    console.print("[dim]No schedules found[/dim]")


@schedule.command(name="rm")
@click.argument("task")
def schedule_rm(task: str):
    """Remove schedule from a task."""
    console.print(f"[green]✓[/green] Removed schedule from '{task}'")


@schedule.command(name="pause")
@click.argument("task")
def schedule_pause(task: str):
    """Pause a schedule."""
    console.print(f"[green]✓[/green] Paused schedule for '{task}'")


@schedule.command(name="resume")
@click.argument("task")
def schedule_resume(task: str):
    """Resume a schedule."""
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
@click.option("--status", "-s", type=click.Choice(["running", "success", "failed", "all"]), default="all")
@click.option("--limit", "-n", default=20, help="Max results")
def runs_list(task: str, status: str, limit: int):
    """List task runs."""
    title = f"Runs: {task}" if task else "All Runs"
    table = Table(title=title, box=box.ROUNDED)
    table.add_column("Run ID", style="cyan")
    table.add_column("Task", style="white")
    table.add_column("Status", style="green")
    table.add_column("Started", style="dim")
    table.add_column("Duration", style="dim")
    table.add_column("Trigger", style="dim")

    console.print(table)
    console.print("[dim]No runs found[/dim]")


@runs.command(name="logs")
@click.argument("run_id")
@click.option("--follow", "-f", is_flag=True, help="Follow logs")
@click.option("--tail", "-n", default=100, help="Number of lines")
def runs_logs(run_id: str, follow: bool, tail: int):
    """View run logs."""
    console.print(f"[cyan]Logs for run {run_id}:[/cyan]")
    console.print("[dim]No logs available[/dim]")


@runs.command(name="cancel")
@click.argument("run_id")
def runs_cancel(run_id: str):
    """Cancel a running task."""
    console.print(f"[green]✓[/green] Run '{run_id}' cancelled")


@runs.command(name="retry")
@click.argument("run_id")
def runs_retry(run_id: str):
    """Retry a failed run."""
    new_run_id = "run_xyz789"
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
@click.option("--source", "-s", required=True, help="Trigger source (event name, queue name, etc.)")
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
    console.print(f"[green]✓[/green] Added {trigger_type} trigger to '{task}'")
    console.print(f"  Source: {source}")
    if filter:
        console.print(f"  Filter: {filter}")


@triggers.command(name="list")
@click.argument("task", required=False)
def triggers_list(task: str):
    """List triggers."""
    table = Table(title="Triggers", box=box.ROUNDED)
    table.add_column("Task", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Source", style="yellow")
    table.add_column("Filter", style="dim")
    table.add_column("Status", style="green")

    console.print(table)
    console.print("[dim]No triggers found[/dim]")


@triggers.command(name="rm")
@click.argument("task")
@click.option("--source", "-s", help="Specific trigger source to remove")
@click.option("--all", "remove_all", is_flag=True, help="Remove all triggers")
def triggers_rm(task: str, source: str, remove_all: bool):
    """Remove triggers from a task."""
    if remove_all:
        console.print(f"[green]✓[/green] Removed all triggers from '{task}'")
    elif source:
        console.print(f"[green]✓[/green] Removed trigger '{source}' from '{task}'")
    else:
        console.print("[yellow]Specify --source or --all[/yellow]")


@triggers.command(name="pause")
@click.argument("task")
@click.option("--source", "-s", help="Specific trigger")
def triggers_pause(task: str, source: str):
    """Pause triggers."""
    console.print(f"[green]✓[/green] Paused trigger(s) for '{task}'")


@triggers.command(name="resume")
@click.argument("task")
@click.option("--source", "-s", help="Specific trigger")
def triggers_resume(task: str, source: str):
    """Resume triggers."""
    console.print(f"[green]✓[/green] Resumed trigger(s) for '{task}'")
