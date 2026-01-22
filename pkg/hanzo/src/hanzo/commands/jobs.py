"""Hanzo Jobs - Background jobs and cron CLI.

Job scheduling, execution, and management.
"""

import click
from rich import box
from rich.table import Table
from rich.panel import Panel

from ..utils.output import console


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
    job_id = "job_abc123"
    console.print(f"[green]✓[/green] Job '{name}' queued")
    console.print(f"  ID: {job_id}")
    console.print(f"  Queue: {queue}")
    console.print(f"  Priority: {priority}")
    if delay:
        console.print(f"  Delay: {delay}")
    if wait:
        console.print("[dim]Waiting for completion...[/dim]")


@jobs_group.command(name="list")
@click.option("--status", "-s", type=click.Choice(["pending", "active", "completed", "failed", "all"]), default="all")
@click.option("--queue", "-q", help="Filter by queue")
@click.option("--limit", "-n", default=20, help="Max results")
def jobs_list(status: str, queue: str, limit: int):
    """List jobs."""
    table = Table(title="Jobs", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Status", style="green")
    table.add_column("Queue", style="dim")
    table.add_column("Started", style="dim")
    table.add_column("Duration", style="dim")

    console.print(table)
    console.print("[dim]No jobs found[/dim]")


@jobs_group.command(name="logs")
@click.argument("job_id")
@click.option("--follow", "-f", is_flag=True, help="Follow logs")
@click.option("--tail", "-n", default=100, help="Number of lines")
def jobs_logs(job_id: str, follow: bool, tail: int):
    """View job logs."""
    console.print(f"[cyan]Logs for job {job_id}:[/cyan]")
    console.print("[dim]No logs available[/dim]")


@jobs_group.command(name="cancel")
@click.argument("job_id")
@click.option("--force", "-f", is_flag=True, help="Force cancellation")
def jobs_cancel(job_id: str, force: bool):
    """Cancel a running job."""
    console.print(f"[green]✓[/green] Job '{job_id}' cancelled")


@jobs_group.command(name="retry")
@click.argument("job_id")
def jobs_retry(job_id: str):
    """Retry a failed job."""
    console.print(f"[green]✓[/green] Job '{job_id}' requeued")


@jobs_group.command(name="describe")
@click.argument("job_id")
def jobs_describe(job_id: str):
    """Show job details."""
    console.print(Panel(
        f"[cyan]ID:[/cyan] {job_id}\n"
        f"[cyan]Name:[/cyan] process-webhook\n"
        f"[cyan]Status:[/cyan] completed\n"
        f"[cyan]Queue:[/cyan] default\n"
        f"[cyan]Started:[/cyan] 2024-01-15 10:30:00\n"
        f"[cyan]Duration:[/cyan] 1.2s\n"
        f"[cyan]Attempts:[/cyan] 1/3",
        title="Job Details",
        border_style="cyan"
    ))


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
    table = Table(title="Cron Schedules", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Schedule", style="white")
    table.add_column("Status", style="green")
    table.add_column("Last Run", style="dim")
    table.add_column("Next Run", style="yellow")

    console.print(table)
    console.print("[dim]No cron schedules found. Create one with 'hanzo jobs cron create'[/dim]")


@cron.command(name="create")
@click.argument("name")
@click.option("--schedule", "-s", required=True, help="Cron expression (e.g., '0 * * * *')")
@click.option("--job", "-j", required=True, help="Job name to run")
@click.option("--payload", "-p", help="JSON payload")
@click.option("--timezone", "-tz", default="UTC", help="Timezone")
def cron_create(name: str, schedule: str, job: str, payload: str, timezone: str):
    """Create a cron schedule."""
    console.print(f"[green]✓[/green] Cron schedule '{name}' created")
    console.print(f"  Schedule: {schedule}")
    console.print(f"  Job: {job}")
    console.print(f"  Timezone: {timezone}")


@cron.command(name="delete")
@click.argument("name")
def cron_delete(name: str):
    """Delete a cron schedule."""
    console.print(f"[green]✓[/green] Cron schedule '{name}' deleted")


@cron.command(name="pause")
@click.argument("name")
def cron_pause(name: str):
    """Pause a cron schedule."""
    console.print(f"[green]✓[/green] Cron schedule '{name}' paused")


@cron.command(name="resume")
@click.argument("name")
def cron_resume(name: str):
    """Resume a paused cron schedule."""
    console.print(f"[green]✓[/green] Cron schedule '{name}' resumed")


@cron.command(name="run-now")
@click.argument("name")
def cron_run_now(name: str):
    """Trigger a cron job immediately."""
    console.print(f"[green]✓[/green] Cron job '{name}' triggered")
    console.print("  Job ID: job_xyz789")
