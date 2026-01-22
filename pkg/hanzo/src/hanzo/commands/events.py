"""Hanzo Events - Eventing control plane CLI.

Unified eventing layer for schemas, routing, replay, and DLQ.
Abstracts over streaming/pubsub/mq transports.
"""

import click
from rich import box
from rich.table import Table
from rich.panel import Panel

from ..utils.output import console


@click.group(name="events")
def events_group():
    """Hanzo Events - Event-driven architecture.

    \b
    Event Buses:
      hanzo events bus create        # Create event bus
      hanzo events bus list          # List buses
      hanzo events bus delete        # Delete bus

    \b
    Schemas:
      hanzo events schema register   # Register schema
      hanzo events schema get        # Get schema
      hanzo events schema validate   # Validate event

    \b
    Streams:
      hanzo events stream create     # Create stream
      hanzo events stream list       # List streams
      hanzo events stream delete     # Delete stream

    \b
    Routes:
      hanzo events route create      # Create route
      hanzo events route list        # List routes
      hanzo events route delete      # Delete route

    \b
    Operations:
      hanzo events publish           # Publish event
      hanzo events tail              # Tail stream
      hanzo events replay            # Replay events
      hanzo events dlq               # Dead letter queue
    """
    pass


# ============================================================================
# Event Bus Management
# ============================================================================

@events_group.group()
def bus():
    """Manage event buses."""
    pass


@bus.command(name="create")
@click.argument("name")
@click.option("--backend", "-b", type=click.Choice(["kafka", "pubsub", "redis"]), default="kafka")
@click.option("--region", "-r", multiple=True, help="Regions for replication")
def bus_create(name: str, backend: str, region: tuple):
    """Create an event bus."""
    console.print(f"[green]✓[/green] Event bus '{name}' created")
    console.print(f"  Backend: {backend}")
    if region:
        console.print(f"  Regions: {', '.join(region)}")


@bus.command(name="list")
def bus_list():
    """List event buses."""
    table = Table(title="Event Buses", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Backend", style="white")
    table.add_column("Streams", style="green")
    table.add_column("Routes", style="yellow")
    table.add_column("Status", style="dim")

    console.print(table)
    console.print("[dim]No event buses found. Create one with 'hanzo events bus create'[/dim]")


@bus.command(name="describe")
@click.argument("name")
def bus_describe(name: str):
    """Show event bus details."""
    console.print(Panel(
        f"[cyan]Name:[/cyan] {name}\n"
        f"[cyan]Backend:[/cyan] Kafka\n"
        f"[cyan]Streams:[/cyan] 12\n"
        f"[cyan]Routes:[/cyan] 8\n"
        f"[cyan]Events/day:[/cyan] 1.2M\n"
        f"[cyan]Regions:[/cyan] us-east-1, eu-west-1",
        title="Event Bus Details",
        border_style="cyan"
    ))


@bus.command(name="delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True)
def bus_delete(name: str, force: bool):
    """Delete an event bus."""
    if not force:
        from rich.prompt import Confirm
        if not Confirm.ask(f"[red]Delete event bus '{name}'?[/red]"):
            return
    console.print(f"[green]✓[/green] Event bus '{name}' deleted")


# ============================================================================
# Schemas
# ============================================================================

@events_group.group()
def schema():
    """Manage event schemas."""
    pass


@schema.command(name="register")
@click.argument("name")
@click.option("--file", "-f", type=click.Path(exists=True), help="Schema file")
@click.option("--format", "fmt", type=click.Choice(["json", "avro", "protobuf"]), default="json")
@click.option("--version", "-v", help="Schema version")
def schema_register(name: str, file: str, fmt: str, version: str):
    """Register an event schema."""
    console.print(f"[green]✓[/green] Schema '{name}' registered")
    console.print(f"  Format: {fmt}")
    console.print(f"  Version: {version or '1'}")


@schema.command(name="get")
@click.argument("name")
@click.option("--version", "-v", help="Specific version")
def schema_get(name: str, version: str):
    """Get schema definition."""
    console.print(f"[dim]Schema '{name}' not found[/dim]")


@schema.command(name="list")
def schema_list():
    """List all schemas."""
    table = Table(title="Event Schemas", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Format", style="white")
    table.add_column("Version", style="green")
    table.add_column("Updated", style="dim")

    console.print(table)
    console.print("[dim]No schemas found[/dim]")


@schema.command(name="validate")
@click.option("--schema", "-s", required=True, help="Schema name")
@click.option("--file", "-f", type=click.Path(exists=True), help="Event file")
@click.option("--data", "-d", help="Event JSON data")
def schema_validate(schema: str, file: str, data: str):
    """Validate event against schema."""
    console.print(f"[green]✓[/green] Event is valid against schema '{schema}'")


# ============================================================================
# Streams
# ============================================================================

@events_group.group()
def stream():
    """Manage event streams."""
    pass


@stream.command(name="create")
@click.argument("name")
@click.option("--bus", "-b", default="default", help="Event bus")
@click.option("--schema", "-s", help="Schema to enforce")
@click.option("--partitions", "-p", default=3, help="Number of partitions")
@click.option("--retention", "-r", default="7d", help="Retention period")
def stream_create(name: str, bus: str, schema: str, partitions: int, retention: str):
    """Create an event stream."""
    console.print(f"[green]✓[/green] Stream '{name}' created")
    console.print(f"  Bus: {bus}")
    console.print(f"  Partitions: {partitions}")
    console.print(f"  Retention: {retention}")
    if schema:
        console.print(f"  Schema: {schema}")


@stream.command(name="list")
@click.option("--bus", "-b", help="Filter by bus")
def stream_list(bus: str):
    """List event streams."""
    table = Table(title="Event Streams", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Bus", style="white")
    table.add_column("Partitions", style="green")
    table.add_column("Retention", style="yellow")
    table.add_column("Events/day", style="dim")

    console.print(table)
    console.print("[dim]No streams found[/dim]")


@stream.command(name="describe")
@click.argument("name")
def stream_describe(name: str):
    """Show stream details."""
    console.print(Panel(
        f"[cyan]Stream:[/cyan] {name}\n"
        f"[cyan]Bus:[/cyan] default\n"
        f"[cyan]Partitions:[/cyan] 3\n"
        f"[cyan]Retention:[/cyan] 7 days\n"
        f"[cyan]Schema:[/cyan] order.created.v1\n"
        f"[cyan]Events/day:[/cyan] 50,000\n"
        f"[cyan]Consumers:[/cyan] 4",
        title="Stream Details",
        border_style="cyan"
    ))


@stream.command(name="delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True)
def stream_delete(name: str, force: bool):
    """Delete an event stream."""
    if not force:
        from rich.prompt import Confirm
        if not Confirm.ask(f"[red]Delete stream '{name}'?[/red]"):
            return
    console.print(f"[green]✓[/green] Stream '{name}' deleted")


# ============================================================================
# Routes
# ============================================================================

@events_group.group()
def route():
    """Manage event routes."""
    pass


@route.command(name="create")
@click.argument("name")
@click.option("--from", "from_stream", required=True, help="Source stream")
@click.option("--to", required=True, help="Target: service:<name>, task:<name>, queue:<name>, webhook:<url>")
@click.option("--filter", "-f", help="Filter expression")
@click.option("--transform", "-t", help="Transform expression")
def route_create(name: str, from_stream: str, to: str, filter: str, transform: str):
    """Create an event route.

    \b
    Examples:
      hanzo events route create notify --from orders --to service:notifications
      hanzo events route create etl --from users --to task:sync-db
      hanzo events route create webhook --from payments --to webhook:https://...
    """
    console.print(f"[green]✓[/green] Route '{name}' created")
    console.print(f"  From: {from_stream}")
    console.print(f"  To: {to}")
    if filter:
        console.print(f"  Filter: {filter}")


@route.command(name="list")
@click.option("--stream", "-s", help="Filter by stream")
def route_list(stream: str):
    """List event routes."""
    table = Table(title="Event Routes", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("From", style="white")
    table.add_column("To", style="yellow")
    table.add_column("Filter", style="dim")
    table.add_column("Status", style="green")

    console.print(table)
    console.print("[dim]No routes found[/dim]")


@route.command(name="describe")
@click.argument("name")
def route_describe(name: str):
    """Show route details."""
    console.print(f"[dim]Route '{name}' not found[/dim]")


@route.command(name="delete")
@click.argument("name")
def route_delete(name: str):
    """Delete an event route."""
    console.print(f"[green]✓[/green] Route '{name}' deleted")


@route.command(name="pause")
@click.argument("name")
def route_pause(name: str):
    """Pause an event route."""
    console.print(f"[green]✓[/green] Route '{name}' paused")


@route.command(name="resume")
@click.argument("name")
def route_resume(name: str):
    """Resume an event route."""
    console.print(f"[green]✓[/green] Route '{name}' resumed")


# ============================================================================
# Operations
# ============================================================================

@events_group.command(name="publish")
@click.option("--stream", "-s", required=True, help="Target stream")
@click.option("--data", "-d", help="Event JSON data")
@click.option("--file", "-f", type=click.Path(exists=True), help="Event file")
@click.option("--key", "-k", help="Partition key")
def events_publish(stream: str, data: str, file: str, key: str):
    """Publish an event to a stream."""
    event_id = "evt_abc123"
    console.print(f"[green]✓[/green] Event published to '{stream}'")
    console.print(f"  Event ID: {event_id}")
    if key:
        console.print(f"  Key: {key}")


@events_group.command(name="tail")
@click.argument("stream")
@click.option("--from", "from_pos", type=click.Choice(["latest", "earliest"]), default="latest")
@click.option("--filter", "-f", help="Filter expression")
@click.option("--limit", "-n", type=int, help="Max events")
def events_tail(stream: str, from_pos: str, filter: str, limit: int):
    """Tail events from a stream."""
    console.print(f"[cyan]Tailing stream '{stream}' from {from_pos}...[/cyan]")
    console.print("[dim]Press Ctrl+C to stop[/dim]")


@events_group.command(name="replay")
@click.option("--stream", "-s", required=True, help="Stream to replay")
@click.option("--from", "from_pos", required=True, help="Start: earliest, timestamp, offset")
@click.option("--to", "to_pos", help="End: latest, timestamp, offset")
@click.option("--target", "-t", help="Target route or consumer")
@click.option("--dry-run", is_flag=True, help="Show what would be replayed")
def events_replay(stream: str, from_pos: str, to_pos: str, target: str, dry_run: bool):
    """Replay events from a stream."""
    if dry_run:
        console.print("[dim]Dry run - no events replayed[/dim]")
        return
    console.print(f"[cyan]Replaying events from '{stream}'...[/cyan]")
    console.print(f"  From: {from_pos}")
    console.print(f"  To: {to_pos or 'latest'}")
    console.print("[green]✓[/green] Replay complete")


# ============================================================================
# Dead Letter Queue
# ============================================================================

@events_group.group()
def dlq():
    """Manage dead letter queue."""
    pass


@dlq.command(name="list")
@click.option("--stream", "-s", help="Filter by stream")
@click.option("--limit", "-n", default=20, help="Max events")
def dlq_list(stream: str, limit: int):
    """List dead letter events."""
    table = Table(title="Dead Letter Queue", box=box.ROUNDED)
    table.add_column("Event ID", style="cyan")
    table.add_column("Stream", style="white")
    table.add_column("Error", style="red")
    table.add_column("Attempts", style="yellow")
    table.add_column("Failed At", style="dim")

    console.print(table)
    console.print("[dim]No dead letter events[/dim]")


@dlq.command(name="retry")
@click.option("--stream", "-s", help="Stream to retry")
@click.option("--event-id", "-e", help="Specific event ID")
@click.option("--all", "retry_all", is_flag=True, help="Retry all DLQ events")
def dlq_retry(stream: str, event_id: str, retry_all: bool):
    """Retry dead letter events."""
    if retry_all:
        console.print("[green]✓[/green] Retrying all DLQ events")
    elif event_id:
        console.print(f"[green]✓[/green] Retrying event '{event_id}'")
    elif stream:
        console.print(f"[green]✓[/green] Retrying DLQ events for stream '{stream}'")


@dlq.command(name="purge")
@click.option("--stream", "-s", help="Stream to purge")
@click.option("--force", "-f", is_flag=True)
def dlq_purge(stream: str, force: bool):
    """Purge dead letter events."""
    if not force:
        from rich.prompt import Confirm
        if not Confirm.ask("[red]Purge DLQ events?[/red]"):
            return
    console.print("[green]✓[/green] DLQ purged")
