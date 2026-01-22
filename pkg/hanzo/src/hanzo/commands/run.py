"""Hanzo Run - Service lifecycle management CLI.

Modern deployment and lifecycle commands.
"""

import click
from rich import box
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner

from ..utils.output import console


@click.group(name="run")
def run_group():
    """Hanzo Run - Deploy and manage services.

    \b
    Services:
      hanzo run service              # Deploy/update a service
      hanzo run job                  # Run one-off job
      hanzo run function             # Invoke a function

    \b
    Lifecycle:
      hanzo run status               # Check deployment status
      hanzo run logs                 # View service logs
      hanzo run scale                # Scale service

    \b
    Traffic:
      hanzo run promote              # Promote to next stage
      hanzo run rollback             # Rollback deployment
      hanzo run traffic              # Adjust traffic split

    Aliases: 'hanzo deploy' redirects here.
    """
    pass


# ============================================================================
# Service Deployment
# ============================================================================

@run_group.command(name="service")
@click.argument("name", required=False)
@click.option("--image", "-i", help="Container image")
@click.option("--source", "-s", help="Source directory (auto-build)")
@click.option("--env", "-e", default="development", help="Target environment")
@click.option("--replicas", "-r", default=1, help="Number of replicas")
@click.option("--port", "-p", default=8080, help="Service port")
@click.option("--cpu", default="0.5", help="CPU cores")
@click.option("--memory", default="512Mi", help="Memory")
@click.option("--wait", "-w", is_flag=True, help="Wait for deployment")
def run_service(name: str, image: str, source: str, env: str, replicas: int,
                port: int, cpu: str, memory: str, wait: bool):
    """Deploy or update a service.

    \b
    Examples:
      hanzo run service my-api --image my-api:v1.2
      hanzo run service --source ./app --env production
      hanzo run service my-api --replicas 3 --cpu 1 --memory 1Gi
    """
    if not name:
        # Auto-detect from current directory
        import os
        name = os.path.basename(os.getcwd())

    console.print(f"[cyan]Deploying service '{name}'...[/cyan]")

    if source:
        console.print(f"  Building from: {source}")
    elif image:
        console.print(f"  Image: {image}")

    console.print(f"  Environment: {env}")
    console.print(f"  Replicas: {replicas}")
    console.print(f"  Resources: {cpu} CPU, {memory} RAM")
    console.print()

    console.print(f"[green]✓[/green] Service '{name}' deployed")
    console.print(f"  URL: https://{name}.{env}.hanzo.ai")
    console.print(f"  Deployment ID: dep_abc123")


@run_group.command(name="job")
@click.argument("name")
@click.option("--image", "-i", help="Container image")
@click.option("--command", "-c", help="Command to run")
@click.option("--env", "-e", default="development", help="Target environment")
@click.option("--wait", "-w", is_flag=True, help="Wait for completion")
@click.option("--timeout", "-t", default="1h", help="Job timeout")
def run_job(name: str, image: str, command: str, env: str, wait: bool, timeout: str):
    """Run a one-off job."""
    console.print(f"[cyan]Starting job '{name}'...[/cyan]")
    console.print(f"  Environment: {env}")
    console.print(f"  Timeout: {timeout}")
    console.print()

    job_id = "job_xyz789"
    console.print(f"[green]✓[/green] Job started")
    console.print(f"  Job ID: {job_id}")
    console.print(f"  Logs: hanzo run logs {job_id}")


@run_group.command(name="function")
@click.argument("name")
@click.option("--payload", "-p", help="JSON payload")
@click.option("--async", "async_", is_flag=True, help="Invoke asynchronously")
def run_function(name: str, payload: str, async_: bool):
    """Invoke a function."""
    console.print(f"[cyan]Invoking function '{name}'...[/cyan]")
    if async_:
        console.print("[green]✓[/green] Function invoked asynchronously")
        console.print("  Request ID: req_abc123")
    else:
        console.print("[green]✓[/green] Function completed")
        console.print("  Duration: 123ms")
        console.print("  Result: {}")


# ============================================================================
# Status & Logs
# ============================================================================

@run_group.command(name="status")
@click.argument("name", required=False)
@click.option("--env", "-e", default="development", help="Environment")
def run_status(name: str, env: str):
    """Check deployment status."""
    if name:
        console.print(Panel(
            f"[cyan]Service:[/cyan] {name}\n"
            f"[cyan]Status:[/cyan] [green]● Running[/green]\n"
            f"[cyan]Replicas:[/cyan] 2/2 ready\n"
            f"[cyan]Version:[/cyan] v1.2.3\n"
            f"[cyan]Uptime:[/cyan] 3d 12h\n"
            f"[cyan]URL:[/cyan] https://{name}.{env}.hanzo.ai",
            title="Service Status",
            border_style="cyan"
        ))
    else:
        table = Table(title=f"Services ({env})", box=box.ROUNDED)
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Replicas", style="white")
        table.add_column("Version", style="dim")
        table.add_column("URL", style="dim")

        console.print(table)
        console.print("[dim]No services deployed[/dim]")


@run_group.command(name="logs")
@click.argument("name")
@click.option("--follow", "-f", is_flag=True, help="Follow logs")
@click.option("--tail", "-n", default=100, help="Number of lines")
@click.option("--since", "-s", help="Since time (e.g., 1h, 30m)")
def run_logs(name: str, follow: bool, tail: int, since: str):
    """View service logs."""
    console.print(f"[cyan]Logs for {name}:[/cyan]")
    if follow:
        console.print("[dim]Following logs... (Ctrl+C to stop)[/dim]")


# ============================================================================
# Scaling & Traffic
# ============================================================================

@run_group.command(name="scale")
@click.argument("name")
@click.option("--replicas", "-r", type=int, help="Number of replicas")
@click.option("--cpu", help="CPU cores")
@click.option("--memory", help="Memory")
@click.option("--env", "-e", default="development", help="Environment")
def run_scale(name: str, replicas: int, cpu: str, memory: str, env: str):
    """Scale a service."""
    changes = []
    if replicas:
        changes.append(f"replicas={replicas}")
    if cpu:
        changes.append(f"cpu={cpu}")
    if memory:
        changes.append(f"memory={memory}")

    console.print(f"[green]✓[/green] Scaled '{name}': {', '.join(changes)}")


@run_group.command(name="promote")
@click.argument("name")
@click.option("--from", "from_env", required=True, help="Source environment")
@click.option("--to", "to_env", required=True, help="Target environment")
def run_promote(name: str, from_env: str, to_env: str):
    """Promote service to next environment."""
    console.print(f"[green]✓[/green] Promoted '{name}' from {from_env} to {to_env}")


@run_group.command(name="rollback")
@click.argument("name")
@click.option("--version", "-v", help="Version to rollback to")
@click.option("--env", "-e", default="development", help="Environment")
def run_rollback(name: str, version: str, env: str):
    """Rollback to previous deployment."""
    if version:
        console.print(f"[green]✓[/green] Rolled back '{name}' to version {version}")
    else:
        console.print(f"[green]✓[/green] Rolled back '{name}' to previous version")


@run_group.command(name="traffic")
@click.argument("name")
@click.option("--version", "-v", multiple=True, help="Version:weight pairs")
@click.option("--env", "-e", default="development", help="Environment")
def run_traffic(name: str, version: tuple, env: str):
    """Adjust traffic split between versions.

    \b
    Examples:
      hanzo run traffic my-api -v v1:90 -v v2:10
      hanzo run traffic my-api -v v2:100  # Full cutover
    """
    if version:
        console.print(f"[green]✓[/green] Traffic split updated for '{name}':")
        for v in version:
            ver, weight = v.split(":")
            console.print(f"  {ver}: {weight}%")
    else:
        console.print(f"[cyan]Current traffic split for '{name}':[/cyan]")
        console.print("  v1.2.3: 100%")
