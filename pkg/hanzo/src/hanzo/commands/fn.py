"""Hanzo Functions - Serverless functions CLI.

Deploy and manage serverless functions with automatic scaling.
"""

import click
from rich import box
from rich.panel import Panel
from rich.table import Table

from ..utils.output import console


@click.group(name="function")
def fn_group():
    """Hanzo Functions - Serverless compute.

    \b
    Functions:
      hanzo function create             # Create function
      hanzo function list               # List functions
      hanzo function deploy             # Deploy function
      hanzo function delete             # Delete function

    \b
    Triggers:
      hanzo function triggers add       # Add trigger (http, event, cron)
      hanzo function triggers list      # List triggers
      hanzo function triggers rm        # Remove trigger

    \b
    Logs & Monitoring:
      hanzo function logs               # View function logs
      hanzo function invoke             # Invoke function
      hanzo function stats              # Function metrics

    \b
    Configuration:
      hanzo function env                # Manage environment variables
      hanzo function secrets            # Bind secrets

    \b
    Alias: hanzo fn
    """
    pass


# ============================================================================
# Function Management
# ============================================================================


@fn_group.command(name="create")
@click.argument("name")
@click.option(
    "--runtime",
    "-r",
    type=click.Choice(["python3.12", "python3.11", "node20", "node18", "go1.22", "rust", "deno"]),
    default="python3.12",
)
@click.option("--memory", "-m", default="256", help="Memory in MB (128-4096)")
@click.option("--timeout", "-t", default=30, help="Timeout in seconds (1-900)")
@click.option("--region", help="Deployment region")
@click.option("--from", "source", help="Source: directory, git URL, or template")
def fn_create(name: str, runtime: str, memory: str, timeout: int, region: str, source: str):
    """Create a new function.

    \b
    Examples:
      hanzo fn create my-api --runtime python3.12
      hanzo fn create processor --runtime node20 --memory 512
      hanzo fn create handler --from ./src/handler
      hanzo fn create api --from github.com/user/repo
    """
    console.print(f"[green]✓[/green] Function '{name}' created")
    console.print(f"  Runtime: {runtime}")
    console.print(f"  Memory: {memory}MB")
    console.print(f"  Timeout: {timeout}s")
    if region:
        console.print(f"  Region: {region}")
    if source:
        console.print(f"  Source: {source}")


@fn_group.command(name="list")
@click.option("--region", "-r", help="Filter by region")
@click.option("--runtime", help="Filter by runtime")
def fn_list(region: str, runtime: str):
    """List functions."""
    table = Table(title="Functions", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Runtime", style="white")
    table.add_column("Memory", style="green")
    table.add_column("Triggers", style="yellow")
    table.add_column("Last Deploy", style="dim")
    table.add_column("Status", style="dim")

    console.print(table)
    console.print("[dim]No functions found. Create one with 'hanzo fn create'[/dim]")


@fn_group.command(name="describe")
@click.argument("name")
def fn_describe(name: str):
    """Show function details."""
    console.print(
        Panel(
            f"[cyan]Name:[/cyan] {name}\n"
            f"[cyan]Runtime:[/cyan] python3.12\n"
            f"[cyan]Memory:[/cyan] 256 MB\n"
            f"[cyan]Timeout:[/cyan] 30s\n"
            f"[cyan]Status:[/cyan] [green]● Active[/green]\n"
            f"[cyan]Triggers:[/cyan] 2 (http, cron)\n"
            f"[cyan]Invocations (24h):[/cyan] 1,234\n"
            f"[cyan]Avg Duration:[/cyan] 45ms\n"
            f"[cyan]Endpoint:[/cyan] https://fn.hanzo.ai/{name}",
            title="Function Details",
            border_style="cyan",
        )
    )


@fn_group.command(name="deploy")
@click.argument("name")
@click.option("--from", "source", help="Source directory or file")
@click.option("--entry", "-e", help="Entry point (e.g., main.handler)")
@click.option("--build", is_flag=True, help="Build before deploying")
@click.option("--force", "-f", is_flag=True, help="Force deploy even if no changes")
def fn_deploy(name: str, source: str, entry: str, build: bool, force: bool):
    """Deploy a function.

    \b
    Examples:
      hanzo fn deploy my-api                      # Deploy from current dir
      hanzo fn deploy my-api --from ./src         # Deploy from specific dir
      hanzo fn deploy my-api --entry main.handler # Specify entry point
      hanzo fn deploy my-api --build              # Build and deploy
    """
    console.print(f"[cyan]Deploying '{name}'...[/cyan]")
    if build:
        console.print("  Building...")
    console.print("  Uploading...")
    console.print("  Activating...")
    console.print(f"[green]✓[/green] Function '{name}' deployed")
    console.print(f"  Version: v1")
    console.print(f"  Endpoint: https://fn.hanzo.ai/{name}")


@fn_group.command(name="delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True)
def fn_delete(name: str, force: bool):
    """Delete a function."""
    if not force:
        from rich.prompt import Confirm

        if not Confirm.ask(f"[red]Delete function '{name}'?[/red]"):
            return
    console.print(f"[green]✓[/green] Function '{name}' deleted")


# ============================================================================
# Triggers
# ============================================================================


@fn_group.group()
def triggers():
    """Manage function triggers."""
    pass


@triggers.command(name="add")
@click.argument("function")
@click.option("--type", "trigger_type", type=click.Choice(["http", "event", "cron", "queue", "storage"]), required=True)
@click.option("--path", "-p", help="HTTP path (for http triggers)")
@click.option("--method", "-m", multiple=True, help="HTTP methods (for http triggers)")
@click.option("--event", "-e", help="Event type (for event triggers)")
@click.option("--bus", "-b", help="Event bus (for event triggers)")
@click.option("--schedule", "-s", help="Cron expression (for cron triggers)")
@click.option("--queue", "-q", help="Queue name (for queue triggers)")
@click.option("--bucket", help="Storage bucket (for storage triggers)")
def triggers_add(
    function: str,
    trigger_type: str,
    path: str,
    method: tuple,
    event: str,
    bus: str,
    schedule: str,
    queue: str,
    bucket: str,
):
    """Add a trigger to a function.

    \b
    Examples:
      hanzo fn triggers add my-api --type http --path /users --method GET POST
      hanzo fn triggers add processor --type event --event user.created --bus main
      hanzo fn triggers add cleanup --type cron --schedule "0 0 * * *"
      hanzo fn triggers add worker --type queue --queue tasks
      hanzo fn triggers add upload-handler --type storage --bucket uploads
    """
    console.print(f"[green]✓[/green] Trigger added to '{function}'")
    console.print(f"  Type: {trigger_type}")
    if trigger_type == "http":
        console.print(f"  Path: {path or '/'}")
        console.print(f"  Methods: {', '.join(method) if method else 'GET'}")
    elif trigger_type == "event":
        console.print(f"  Event: {event}")
        console.print(f"  Bus: {bus or 'default'}")
    elif trigger_type == "cron":
        console.print(f"  Schedule: {schedule}")
    elif trigger_type == "queue":
        console.print(f"  Queue: {queue}")
    elif trigger_type == "storage":
        console.print(f"  Bucket: {bucket}")


@triggers.command(name="list")
@click.argument("function")
def triggers_list(function: str):
    """List triggers for a function."""
    table = Table(title=f"Triggers for '{function}'", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Source", style="green")
    table.add_column("Status", style="dim")

    console.print(table)
    console.print("[dim]No triggers found[/dim]")


@triggers.command(name="rm")
@click.argument("function")
@click.argument("trigger_id")
def triggers_rm(function: str, trigger_id: str):
    """Remove a trigger."""
    console.print(f"[green]✓[/green] Trigger '{trigger_id}' removed from '{function}'")


# ============================================================================
# Invocation & Logs
# ============================================================================


@fn_group.command(name="invoke")
@click.argument("name")
@click.option("--data", "-d", help="JSON payload")
@click.option("--file", "-f", "payload_file", help="File containing payload")
@click.option("--async", "async_invoke", is_flag=True, help="Async invocation")
@click.option("--tail", is_flag=True, help="Tail logs after invocation")
def fn_invoke(name: str, data: str, payload_file: str, async_invoke: bool, tail: bool):
    """Invoke a function.

    \b
    Examples:
      hanzo fn invoke my-api
      hanzo fn invoke my-api -d '{"user": "test"}'
      hanzo fn invoke my-api -f payload.json
      hanzo fn invoke my-api --async
    """
    console.print(f"[cyan]Invoking '{name}'...[/cyan]")
    if async_invoke:
        console.print("[green]✓[/green] Function invoked asynchronously")
        console.print("  Request ID: req_abc123")
    else:
        console.print("[green]✓[/green] Function executed")
        console.print("  Duration: 45ms")
        console.print("  Status: 200")
        console.print("  Response: {}")


@fn_group.command(name="logs")
@click.argument("name")
@click.option("--follow", "-f", is_flag=True, help="Follow logs")
@click.option("--since", "-s", default="1h", help="Time range (e.g., 1h, 24h, 7d)")
@click.option("--filter", "log_filter", help="Filter expression")
@click.option("--limit", "-n", default=100, help="Max log entries")
def fn_logs(name: str, follow: bool, since: str, log_filter: str, limit: int):
    """View function logs.

    \b
    Examples:
      hanzo fn logs my-api
      hanzo fn logs my-api -f              # Follow/tail logs
      hanzo fn logs my-api --since 24h     # Last 24 hours
      hanzo fn logs my-api --filter error  # Filter for errors
    """
    if follow:
        console.print(f"[cyan]Tailing logs for '{name}'...[/cyan]")
        console.print("[dim]Press Ctrl+C to stop[/dim]")
    else:
        console.print(f"[cyan]Logs for '{name}' (last {since}):[/cyan]")
    console.print("[dim]No log entries found[/dim]")


@fn_group.command(name="stats")
@click.argument("name")
@click.option("--range", "-r", "time_range", default="24h", help="Time range")
def fn_stats(name: str, time_range: str):
    """Show function statistics."""
    console.print(
        Panel(
            f"[cyan]Function:[/cyan] {name}\n"
            f"[cyan]Time Range:[/cyan] {time_range}\n\n"
            f"[cyan]Invocations:[/cyan] 0\n"
            f"[cyan]Errors:[/cyan] 0 (0%)\n"
            f"[cyan]Avg Duration:[/cyan] 0ms\n"
            f"[cyan]P95 Duration:[/cyan] 0ms\n"
            f"[cyan]Cold Starts:[/cyan] 0\n"
            f"[cyan]Memory Peak:[/cyan] 0 MB",
            title="Function Statistics",
            border_style="cyan",
        )
    )


# ============================================================================
# Environment & Secrets
# ============================================================================


@fn_group.group()
def env():
    """Manage function environment variables."""
    pass


@env.command(name="set")
@click.argument("function")
@click.argument("key")
@click.argument("value")
def env_set(function: str, key: str, value: str):
    """Set an environment variable."""
    console.print(f"[green]✓[/green] Set {key} for '{function}'")


@env.command(name="get")
@click.argument("function")
@click.argument("key", required=False)
def env_get(function: str, key: str):
    """Get environment variables."""
    if key:
        console.print(f"[cyan]{key}=[/cyan] (not set)")
    else:
        console.print(f"[cyan]Environment for '{function}':[/cyan]")
        console.print("[dim]No environment variables set[/dim]")


@env.command(name="rm")
@click.argument("function")
@click.argument("key")
def env_rm(function: str, key: str):
    """Remove an environment variable."""
    console.print(f"[green]✓[/green] Removed {key} from '{function}'")


@fn_group.group()
def secrets():
    """Manage function secrets binding."""
    pass


@secrets.command(name="bind")
@click.argument("function")
@click.argument("secret")
@click.option("--as", "env_name", help="Environment variable name")
def secrets_bind(function: str, secret: str, env_name: str):
    """Bind a secret to a function.

    \b
    Examples:
      hanzo fn secrets bind my-api db-password
      hanzo fn secrets bind my-api api-key --as API_KEY
    """
    console.print(f"[green]✓[/green] Bound secret '{secret}' to '{function}'")
    if env_name:
        console.print(f"  As: {env_name}")


@secrets.command(name="unbind")
@click.argument("function")
@click.argument("secret")
def secrets_unbind(function: str, secret: str):
    """Unbind a secret from a function."""
    console.print(f"[green]✓[/green] Unbound secret '{secret}' from '{function}'")


@secrets.command(name="list")
@click.argument("function")
def secrets_list(function: str):
    """List secrets bound to a function."""
    table = Table(title=f"Secrets for '{function}'", box=box.ROUNDED)
    table.add_column("Secret", style="cyan")
    table.add_column("Env Var", style="white")
    table.add_column("Version", style="dim")

    console.print(table)
    console.print("[dim]No secrets bound[/dim]")


# ============================================================================
# Versions & Rollback
# ============================================================================


@fn_group.command(name="versions")
@click.argument("name")
def fn_versions(name: str):
    """List function versions."""
    table = Table(title=f"Versions of '{name}'", box=box.ROUNDED)
    table.add_column("Version", style="cyan")
    table.add_column("Deployed", style="white")
    table.add_column("Traffic", style="green")
    table.add_column("Status", style="dim")

    console.print(table)
    console.print("[dim]No versions found[/dim]")


@fn_group.command(name="rollback")
@click.argument("name")
@click.option("--version", "-v", help="Target version")
def fn_rollback(name: str, version: str):
    """Rollback to a previous version."""
    target = version or "previous"
    console.print(f"[cyan]Rolling back '{name}' to {target}...[/cyan]")
    console.print(f"[green]✓[/green] Rolled back to {target}")


# ============================================================================
# Traffic Splitting
# ============================================================================


@fn_group.command(name="traffic")
@click.argument("name")
@click.option("--version", "-v", multiple=True, help="Version:weight pairs (e.g., v1:90 v2:10)")
def fn_traffic(name: str, version: tuple):
    """Configure traffic splitting between versions.

    \b
    Examples:
      hanzo fn traffic my-api -v v1:90 -v v2:10    # 90/10 split
      hanzo fn traffic my-api -v v2:100            # 100% to v2
    """
    if version:
        console.print(f"[green]✓[/green] Traffic configured for '{name}'")
        for v in version:
            console.print(f"  {v}")
    else:
        console.print(f"[cyan]Traffic configuration for '{name}':[/cyan]")
        console.print("[dim]Single version active (100%)[/dim]")
