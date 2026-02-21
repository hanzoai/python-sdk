"""Hanzo Events - Eventing control plane CLI.

Unified eventing layer for schemas, routing, replay, and DLQ.
Abstracts over streaming/pubsub/mq transports.
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

EVENTS_URL = os.getenv("HANZO_EVENTS_URL", "https://events.hanzo.ai")


def _request(method: str, path: str, **kwargs) -> httpx.Response:
    return service_request(EVENTS_URL, method, path, **kwargs)


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
    payload = {"name": name, "backend": backend}
    if region:
        payload["regions"] = list(region)

    resp = _request("post", "/v1/buses", json=payload)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Event bus '{name}' created")
    console.print(f"  ID: {data.get('id', '-')}")
    console.print(f"  Backend: {backend}")
    if region:
        console.print(f"  Regions: {', '.join(region)}")


@bus.command(name="list")
def bus_list():
    """List event buses."""
    resp = _request("get", "/v1/buses")
    data = check_response(resp)
    buses = data.get("buses", data.get("items", []))

    table = Table(title="Event Buses", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Backend", style="white")
    table.add_column("Streams", style="green")
    table.add_column("Routes", style="yellow")
    table.add_column("Status", style="dim")

    for b in buses:
        status = b.get("status", "unknown")
        style = "green" if status == "running" else "yellow"
        table.add_row(
            b.get("name", ""),
            b.get("backend", "-"),
            str(b.get("stream_count", 0)),
            str(b.get("route_count", 0)),
            f"[{style}]● {status}[/{style}]",
        )

    console.print(table)
    if not buses:
        console.print("[dim]No event buses found. Create one with 'hanzo events bus create'[/dim]")


@bus.command(name="describe")
@click.argument("name")
def bus_describe(name: str):
    """Show event bus details."""
    resp = _request("get", f"/v1/buses/{name}")
    data = check_response(resp)

    status = data.get("status", "unknown")
    style = "green" if status == "running" else "yellow"
    regions = data.get("regions", [])

    console.print(
        Panel(
            f"[cyan]Name:[/cyan] {data.get('name', name)}\n"
            f"[cyan]Backend:[/cyan] {data.get('backend', '-')}\n"
            f"[cyan]Status:[/cyan] [{style}]● {status}[/{style}]\n"
            f"[cyan]Streams:[/cyan] {data.get('stream_count', 0)}\n"
            f"[cyan]Routes:[/cyan] {data.get('route_count', 0)}\n"
            f"[cyan]Events/day:[/cyan] {data.get('events_per_day', 0):,}\n"
            f"[cyan]Regions:[/cyan] {', '.join(regions) if regions else '-'}",
            title="Event Bus Details",
            border_style="cyan",
        )
    )


@bus.command(name="delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True)
def bus_delete(name: str, force: bool):
    """Delete an event bus."""
    if not force:
        from rich.prompt import Confirm

        if not Confirm.ask(f"[red]Delete event bus '{name}'?[/red]"):
            return

    resp = _request("delete", f"/v1/buses/{name}")
    check_response(resp)
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
    payload = {"name": name, "format": fmt}
    if version:
        payload["version"] = version
    if file:
        from pathlib import Path

        payload["definition"] = Path(file).read_text()

    resp = _request("post", "/v1/schemas", json=payload)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Schema '{name}' registered")
    console.print(f"  Format: {fmt}")
    console.print(f"  Version: {data.get('version', version or '1')}")


@schema.command(name="get")
@click.argument("name")
@click.option("--version", "-v", help="Specific version")
def schema_get(name: str, version: str):
    """Get schema definition."""
    params = {}
    if version:
        params["version"] = version

    resp = _request("get", f"/v1/schemas/{name}", params=params)
    data = check_response(resp)

    console.print(
        Panel(
            f"[cyan]Name:[/cyan] {data.get('name', name)}\n"
            f"[cyan]Format:[/cyan] {data.get('format', '-')}\n"
            f"[cyan]Version:[/cyan] {data.get('version', '-')}\n"
            f"[cyan]Definition:[/cyan]\n{data.get('definition', '{}')}",
            title="Schema",
            border_style="cyan",
        )
    )


@schema.command(name="list")
def schema_list():
    """List all schemas."""
    resp = _request("get", "/v1/schemas")
    data = check_response(resp)
    schemas = data.get("schemas", data.get("items", []))

    table = Table(title="Event Schemas", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Format", style="white")
    table.add_column("Version", style="green")
    table.add_column("Updated", style="dim")

    for s in schemas:
        table.add_row(
            s.get("name", ""),
            s.get("format", "-"),
            str(s.get("version", "-")),
            str(s.get("updated_at", ""))[:19],
        )

    console.print(table)
    if not schemas:
        console.print("[dim]No schemas found[/dim]")


@schema.command(name="validate")
@click.option("--schema", "-s", required=True, help="Schema name")
@click.option("--file", "-f", type=click.Path(exists=True), help="Event file")
@click.option("--data", "-d", help="Event JSON data")
def schema_validate(schema: str, file: str, data: str):
    """Validate event against schema."""
    if file:
        from pathlib import Path

        event_data = Path(file).read_text()
    elif data:
        event_data = data
    else:
        raise click.ClickException("Provide --file or --data")

    payload = {"schema": schema, "event": json.loads(event_data)}
    resp = _request("post", "/v1/schemas/validate", json=payload)
    result = check_response(resp)

    if result.get("valid", True):
        console.print(f"[green]✓[/green] Event is valid against schema '{schema}'")
    else:
        console.print(f"[red]✗[/red] Validation failed:")
        for err in result.get("errors", []):
            console.print(f"  - {err}")


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
    payload = {"name": name, "partitions": partitions, "retention": retention}
    if schema:
        payload["schema"] = schema

    resp = _request("post", f"/v1/buses/{bus}/streams", json=payload)
    data = check_response(resp)

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
    path = f"/v1/buses/{bus}/streams" if bus else "/v1/streams"
    resp = _request("get", path)
    data = check_response(resp)
    streams = data.get("streams", data.get("items", []))

    table = Table(title="Event Streams", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Bus", style="white")
    table.add_column("Partitions", style="green")
    table.add_column("Retention", style="yellow")
    table.add_column("Events/day", style="dim")

    for s in streams:
        table.add_row(
            s.get("name", ""),
            s.get("bus", "-"),
            str(s.get("partitions", 0)),
            s.get("retention", "-"),
            str(s.get("events_per_day", 0)),
        )

    console.print(table)
    if not streams:
        console.print("[dim]No streams found[/dim]")


@stream.command(name="describe")
@click.argument("name")
def stream_describe(name: str):
    """Show stream details."""
    resp = _request("get", f"/v1/streams/{name}")
    data = check_response(resp)

    console.print(
        Panel(
            f"[cyan]Stream:[/cyan] {data.get('name', name)}\n"
            f"[cyan]Bus:[/cyan] {data.get('bus', '-')}\n"
            f"[cyan]Partitions:[/cyan] {data.get('partitions', 0)}\n"
            f"[cyan]Retention:[/cyan] {data.get('retention', '-')}\n"
            f"[cyan]Schema:[/cyan] {data.get('schema', '-')}\n"
            f"[cyan]Events/day:[/cyan] {data.get('events_per_day', 0):,}\n"
            f"[cyan]Consumers:[/cyan] {data.get('consumer_count', 0)}",
            title="Stream Details",
            border_style="cyan",
        )
    )


@stream.command(name="delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True)
def stream_delete(name: str, force: bool):
    """Delete an event stream."""
    if not force:
        from rich.prompt import Confirm

        if not Confirm.ask(f"[red]Delete stream '{name}'?[/red]"):
            return

    resp = _request("delete", f"/v1/streams/{name}")
    check_response(resp)
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
    payload = {"name": name, "source": from_stream, "target": to}
    if filter:
        payload["filter"] = filter
    if transform:
        payload["transform"] = transform

    resp = _request("post", "/v1/routes", json=payload)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Route '{name}' created")
    console.print(f"  From: {from_stream}")
    console.print(f"  To: {to}")
    if filter:
        console.print(f"  Filter: {filter}")


@route.command(name="list")
@click.option("--stream", "-s", help="Filter by stream")
def route_list(stream: str):
    """List event routes."""
    params = {}
    if stream:
        params["stream"] = stream

    resp = _request("get", "/v1/routes", params=params)
    data = check_response(resp)
    routes = data.get("routes", data.get("items", []))

    table = Table(title="Event Routes", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("From", style="white")
    table.add_column("To", style="yellow")
    table.add_column("Filter", style="dim")
    table.add_column("Status", style="green")

    for r in routes:
        status = r.get("status", "active")
        style = "green" if status == "active" else "yellow"
        table.add_row(
            r.get("name", ""),
            r.get("source", "-"),
            r.get("target", "-"),
            r.get("filter", "-") or "-",
            f"[{style}]{status}[/{style}]",
        )

    console.print(table)
    if not routes:
        console.print("[dim]No routes found[/dim]")


@route.command(name="describe")
@click.argument("name")
def route_describe(name: str):
    """Show route details."""
    resp = _request("get", f"/v1/routes/{name}")
    data = check_response(resp)

    console.print(
        Panel(
            f"[cyan]Name:[/cyan] {data.get('name', name)}\n"
            f"[cyan]Source:[/cyan] {data.get('source', '-')}\n"
            f"[cyan]Target:[/cyan] {data.get('target', '-')}\n"
            f"[cyan]Filter:[/cyan] {data.get('filter', '-')}\n"
            f"[cyan]Transform:[/cyan] {data.get('transform', '-')}\n"
            f"[cyan]Status:[/cyan] {data.get('status', '-')}\n"
            f"[cyan]Events routed:[/cyan] {data.get('events_routed', 0):,}",
            title="Route Details",
            border_style="cyan",
        )
    )


@route.command(name="delete")
@click.argument("name")
def route_delete(name: str):
    """Delete an event route."""
    resp = _request("delete", f"/v1/routes/{name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Route '{name}' deleted")


@route.command(name="pause")
@click.argument("name")
def route_pause(name: str):
    """Pause an event route."""
    resp = _request("post", f"/v1/routes/{name}/pause")
    check_response(resp)
    console.print(f"[green]✓[/green] Route '{name}' paused")


@route.command(name="resume")
@click.argument("name")
def route_resume(name: str):
    """Resume an event route."""
    resp = _request("post", f"/v1/routes/{name}/resume")
    check_response(resp)
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
    if file:
        from pathlib import Path

        event_data = json.loads(Path(file).read_text())
    elif data:
        event_data = json.loads(data)
    else:
        raise click.ClickException("Provide --data or --file")

    payload = {"data": event_data}
    if key:
        payload["key"] = key

    resp = _request("post", f"/v1/streams/{stream}/publish", json=payload)
    result = check_response(resp)

    console.print(f"[green]✓[/green] Event published to '{stream}'")
    console.print(f"  Event ID: {result.get('event_id', result.get('id', '-'))}")
    if key:
        console.print(f"  Key: {key}")


@events_group.command(name="tail")
@click.argument("stream")
@click.option("--from", "from_pos", type=click.Choice(["latest", "earliest"]), default="latest")
@click.option("--filter", "-f", help="Filter expression")
@click.option("--limit", "-n", type=int, help="Max events")
def events_tail(stream: str, from_pos: str, filter: str, limit: int):
    """Tail events from a stream."""
    params = {"position": from_pos}
    if filter:
        params["filter"] = filter
    if limit:
        params["limit"] = limit

    resp = _request("get", f"/v1/streams/{stream}/tail", params=params)
    data = check_response(resp)
    events = data.get("events", [])

    for evt in events:
        console.print(
            f"[dim]{evt.get('timestamp', '')}[/dim] "
            f"[cyan]{evt.get('id', '')}[/cyan] "
            f"{json.dumps(evt.get('data', {}), default=str)}"
        )

    if not events:
        console.print(f"[dim]No events in '{stream}' (position: {from_pos})[/dim]")
    elif not limit:
        console.print("[dim]Press Ctrl+C to stop[/dim]")


@events_group.command(name="replay")
@click.option("--stream", "-s", required=True, help="Stream to replay")
@click.option("--from", "from_pos", required=True, help="Start: earliest, timestamp, offset")
@click.option("--to", "to_pos", help="End: latest, timestamp, offset")
@click.option("--target", "-t", help="Target route or consumer")
@click.option("--dry-run", is_flag=True, help="Show what would be replayed")
def events_replay(stream: str, from_pos: str, to_pos: str, target: str, dry_run: bool):
    """Replay events from a stream."""
    payload = {"stream": stream, "from": from_pos}
    if to_pos:
        payload["to"] = to_pos
    if target:
        payload["target"] = target
    if dry_run:
        payload["dry_run"] = True

    resp = _request("post", "/v1/replay", json=payload)
    data = check_response(resp)

    if dry_run:
        console.print(f"[dim]Dry run: {data.get('event_count', 0)} events would be replayed[/dim]")
    else:
        console.print(f"[green]✓[/green] Replay complete")
        console.print(f"  Events replayed: {data.get('replayed', 0):,}")
        if data.get("duration"):
            console.print(f"  Duration: {data['duration']}")


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
    params = {"limit": limit}
    if stream:
        params["stream"] = stream

    resp = _request("get", "/v1/dlq", params=params)
    data = check_response(resp)
    events = data.get("events", data.get("items", []))

    table = Table(title="Dead Letter Queue", box=box.ROUNDED)
    table.add_column("Event ID", style="cyan")
    table.add_column("Stream", style="white")
    table.add_column("Error", style="red")
    table.add_column("Attempts", style="yellow")
    table.add_column("Failed At", style="dim")

    for e in events:
        table.add_row(
            str(e.get("event_id", e.get("id", "")))[:24],
            e.get("stream", "-"),
            str(e.get("error", "-"))[:40],
            str(e.get("attempts", 0)),
            str(e.get("failed_at", ""))[:19],
        )

    console.print(table)
    if not events:
        console.print("[dim]No dead letter events[/dim]")


@dlq.command(name="retry")
@click.option("--stream", "-s", help="Stream to retry")
@click.option("--event-id", "-e", help="Specific event ID")
@click.option("--all", "retry_all", is_flag=True, help="Retry all DLQ events")
def dlq_retry(stream: str, event_id: str, retry_all: bool):
    """Retry dead letter events."""
    payload = {}
    if retry_all:
        payload["all"] = True
    elif event_id:
        payload["event_id"] = event_id
    elif stream:
        payload["stream"] = stream
    else:
        raise click.ClickException("Provide --event-id, --stream, or --all")

    resp = _request("post", "/v1/dlq/retry", json=payload)
    data = check_response(resp)
    console.print(f"[green]✓[/green] Retried {data.get('retried', 0)} event(s)")


@dlq.command(name="purge")
@click.option("--stream", "-s", help="Stream to purge")
@click.option("--force", "-f", is_flag=True)
def dlq_purge(stream: str, force: bool):
    """Purge dead letter events."""
    if not force:
        from rich.prompt import Confirm

        if not Confirm.ask("[red]Purge DLQ events?[/red]"):
            return

    payload = {}
    if stream:
        payload["stream"] = stream

    resp = _request("post", "/v1/dlq/purge", json=payload)
    data = check_response(resp)
    console.print(f"[green]✓[/green] Purged {data.get('purged', 0)} DLQ event(s)")
