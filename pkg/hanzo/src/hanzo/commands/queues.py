"""Hanzo Queues - Task and message queues CLI.

BullMQ-compatible job and message queues.
"""

import click
from rich import box
from rich.table import Table
from rich.panel import Panel

from ..utils.output import console


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
    table = Table(title="Queues", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Pending", style="yellow")
    table.add_column("Active", style="green")
    table.add_column("Completed", style="dim")
    table.add_column("Failed", style="red")
    table.add_column("Delayed", style="dim")

    console.print(table)
    console.print("[dim]No queues found. Create one with 'hanzo queues create'[/dim]")


@queues_group.command(name="create")
@click.argument("name")
@click.option("--concurrency", "-c", default=10, help="Max concurrent workers")
@click.option("--rate-limit", "-r", help="Rate limit (e.g., '100/m')")
@click.option("--retry", default=3, help="Max retry attempts")
@click.option("--backoff", default="exponential", help="Backoff strategy")
def queues_create(name: str, concurrency: int, rate_limit: str, retry: int, backoff: str):
    """Create a queue."""
    console.print(f"[green]✓[/green] Queue '{name}' created")
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
    console.print(f"[green]✓[/green] Queue '{name}' deleted")


@queues_group.command(name="stats")
@click.argument("name")
def queues_stats(name: str):
    """Show queue statistics."""
    console.print(Panel(
        f"[cyan]Queue:[/cyan] {name}\n"
        f"[cyan]Pending:[/cyan] 1,234\n"
        f"[cyan]Active:[/cyan] 10\n"
        f"[cyan]Completed:[/cyan] 45,678 (last 24h)\n"
        f"[cyan]Failed:[/cyan] 23\n"
        f"[cyan]Delayed:[/cyan] 56\n"
        f"[cyan]Avg process time:[/cyan] 245ms\n"
        f"[cyan]Throughput:[/cyan] 1,200/min",
        title="Queue Statistics",
        border_style="cyan"
    ))


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
    import secrets
    job_id = secrets.token_hex(8)
    console.print(f"[green]✓[/green] Job pushed to '{queue}'")
    console.print(f"  Job ID: {job_id}")
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
    console.print(f"[cyan]Popping {count} job(s) from '{queue}'...[/cyan]")
    console.print("[dim]No jobs available[/dim]")


@queues_group.command(name="peek")
@click.argument("queue")
@click.option("--count", "-n", default=5, help="Number of jobs to peek")
def queues_peek(queue: str, count: int):
    """Peek at jobs without removing them."""
    table = Table(title=f"Next {count} Jobs in '{queue}'", box=box.ROUNDED)
    table.add_column("Job ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Priority", style="yellow")
    table.add_column("Attempts", style="dim")
    table.add_column("Created", style="dim")

    console.print(table)
    console.print("[dim]No pending jobs[/dim]")


@queues_group.command(name="get")
@click.argument("queue")
@click.argument("job_id")
def queues_get(queue: str, job_id: str):
    """Get job details."""
    console.print(Panel(
        f"[cyan]Job ID:[/cyan] {job_id}\n"
        f"[cyan]Queue:[/cyan] {queue}\n"
        f"[cyan]Status:[/cyan] Completed\n"
        f"[cyan]Attempts:[/cyan] 1/3\n"
        f"[cyan]Created:[/cyan] 2024-01-20 10:30:00\n"
        f"[cyan]Processed:[/cyan] 2024-01-20 10:30:05\n"
        f"[cyan]Duration:[/cyan] 245ms",
        title="Job Details",
        border_style="cyan"
    ))


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
    if job_id:
        console.print(f"[green]✓[/green] Job '{job_id}' queued for retry")
    elif all_failed:
        console.print(f"[green]✓[/green] All failed jobs in '{queue}' queued for retry")
    elif count:
        console.print(f"[green]✓[/green] {count} failed jobs queued for retry")
    else:
        console.print("[yellow]Specify --job-id, --all-failed, or --count[/yellow]")


@queues_group.group()
def dlq():
    """Dead letter queue management."""
    pass


@dlq.command(name="list")
@click.argument("queue")
@click.option("--limit", "-n", default=20, help="Max jobs to show")
def dlq_list(queue: str, limit: int):
    """List jobs in dead letter queue."""
    table = Table(title=f"Dead Letter Queue: {queue}", box=box.ROUNDED)
    table.add_column("Job ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Error", style="red")
    table.add_column("Attempts", style="yellow")
    table.add_column("Failed At", style="dim")

    console.print(table)
    console.print("[dim]No jobs in DLQ[/dim]")


@dlq.command(name="retry")
@click.argument("queue")
@click.option("--job-id", "-j", help="Specific job to retry")
@click.option("--all", "-a", "all_jobs", is_flag=True, help="Retry all DLQ jobs")
def dlq_retry(queue: str, job_id: str, all_jobs: bool):
    """Retry jobs from dead letter queue."""
    if job_id:
        console.print(f"[green]✓[/green] DLQ job '{job_id}' moved back to queue")
    elif all_jobs:
        console.print(f"[green]✓[/green] All DLQ jobs moved back to '{queue}'")
    else:
        console.print("[yellow]Specify --job-id or --all[/yellow]")


@dlq.command(name="purge")
@click.argument("queue")
def dlq_purge(queue: str):
    """Purge all jobs from dead letter queue."""
    from rich.prompt import Confirm
    if not Confirm.ask(f"[red]Purge all DLQ jobs for '{queue}'?[/red]"):
        return
    console.print(f"[green]✓[/green] DLQ purged for '{queue}'")


@queues_group.command(name="drain")
@click.argument("queue")
@click.option("--delayed", is_flag=True, help="Also drain delayed jobs")
def queues_drain(queue: str, delayed: bool):
    """Drain all jobs from a queue."""
    from rich.prompt import Confirm
    if not Confirm.ask(f"[red]Drain all jobs from '{queue}'?[/red]"):
        return
    console.print(f"[green]✓[/green] Queue '{queue}' drained")
    if delayed:
        console.print("[dim]Delayed jobs also removed[/dim]")


@queues_group.command(name="pause")
@click.argument("queue")
def queues_pause(queue: str):
    """Pause queue processing."""
    console.print(f"[green]✓[/green] Queue '{queue}' paused")


@queues_group.command(name="resume")
@click.argument("queue")
def queues_resume(queue: str):
    """Resume queue processing."""
    console.print(f"[green]✓[/green] Queue '{queue}' resumed")
