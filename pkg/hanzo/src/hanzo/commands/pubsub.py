"""Hanzo Pub/Sub - Event streaming and messaging CLI.

Topics, subscriptions, publish, consume.
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

PUBSUB_URL = os.getenv("HANZO_PUBSUB_URL", "https://pubsub.hanzo.ai")


def _request(method: str, path: str, **kwargs) -> httpx.Response:
    return service_request(PUBSUB_URL, method, path, **kwargs)


@click.group(name="pubsub")
def pubsub_group():
    """Hanzo Pub/Sub - Event streaming and messaging.

    \b
    Topics:
      hanzo pubsub topics list       # List topics
      hanzo pubsub topics create     # Create topic
      hanzo pubsub topics delete     # Delete topic

    \b
    Subscriptions:
      hanzo pubsub subs list         # List subscriptions
      hanzo pubsub subs create       # Create subscription
      hanzo pubsub subs delete       # Delete subscription

    \b
    Messages:
      hanzo pubsub publish           # Publish message
      hanzo pubsub pull              # Pull messages
      hanzo pubsub ack               # Acknowledge messages
      hanzo pubsub seek              # Seek to timestamp/snapshot
    """
    pass


# ============================================================================
# Topics
# ============================================================================


@pubsub_group.group()
def topics():
    """Manage pub/sub topics."""
    pass


@topics.command(name="list")
@click.option("--project", "-p", help="Project ID")
def topics_list(project: str):
    """List all topics."""
    params = {}
    if project:
        params["project"] = project

    resp = _request("get", "/v1/topics", params=params)
    data = check_response(resp)
    items = data.get("topics", data.get("items", []))

    table = Table(title="Topics", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Subscriptions", style="white")
    table.add_column("Messages/day", style="green")
    table.add_column("Retention", style="dim")
    table.add_column("Created", style="dim")

    for t in items:
        table.add_row(
            t.get("name", ""),
            str(t.get("subscription_count", 0)),
            str(t.get("messages_per_day", 0)),
            t.get("retention", "-"),
            str(t.get("created_at", ""))[:10],
        )

    console.print(table)
    if not items:
        console.print(
            "[dim]No topics found. Create one with 'hanzo pubsub topics create'[/dim]"
        )


@topics.command(name="create")
@click.argument("name")
@click.option("--retention", "-r", default="7d", help="Message retention period")
@click.option("--schema", "-s", help="Schema for message validation")
def topics_create(name: str, retention: str, schema: str):
    """Create a topic."""
    payload = {"name": name, "retention": retention}
    if schema:
        payload["schema"] = schema

    resp = _request("post", "/v1/topics", json=payload)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Topic '{name}' created")
    console.print(f"  ID: {data.get('id', '-')}")
    console.print(f"  Retention: {retention}")
    if schema:
        console.print(f"  Schema: {schema}")


@topics.command(name="delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def topics_delete(name: str, force: bool):
    """Delete a topic."""
    if not force:
        from rich.prompt import Confirm

        if not Confirm.ask(f"[red]Delete topic '{name}' and all subscriptions?[/red]"):
            return

    resp = _request("delete", f"/v1/topics/{name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Topic '{name}' deleted")


@topics.command(name="describe")
@click.argument("name")
def topics_describe(name: str):
    """Show topic details."""
    resp = _request("get", f"/v1/topics/{name}")
    data = check_response(resp)

    console.print(
        Panel(
            f"[cyan]Topic:[/cyan] {data.get('name', name)}\n"
            f"[cyan]Subscriptions:[/cyan] {data.get('subscription_count', 0)}\n"
            f"[cyan]Messages/day:[/cyan] {data.get('messages_per_day', 0):,}\n"
            f"[cyan]Retention:[/cyan] {data.get('retention', '-')}\n"
            f"[cyan]Schema:[/cyan] {data.get('schema', 'None')}\n"
            f"[cyan]Created:[/cyan] {str(data.get('created_at', ''))[:19]}",
            title="Topic Details",
            border_style="cyan",
        )
    )


# ============================================================================
# Subscriptions
# ============================================================================


@pubsub_group.group()
def subs():
    """Manage subscriptions."""
    pass


@subs.command(name="list")
@click.option("--topic", "-t", help="Filter by topic")
def subs_list(topic: str):
    """List subscriptions."""
    params = {}
    if topic:
        params["topic"] = topic

    resp = _request("get", "/v1/subscriptions", params=params)
    data = check_response(resp)
    items = data.get("subscriptions", data.get("items", []))

    table = Table(title="Subscriptions", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Topic", style="white")
    table.add_column("Type", style="green")
    table.add_column("Pending", style="yellow")
    table.add_column("Ack Deadline", style="dim")

    for s in items:
        sub_type = "push" if s.get("push_endpoint") else "pull"
        table.add_row(
            s.get("name", ""),
            s.get("topic", "-"),
            sub_type,
            str(s.get("pending_count", 0)),
            f"{s.get('ack_deadline', 10)}s",
        )

    console.print(table)
    if not items:
        console.print("[dim]No subscriptions found[/dim]")


@subs.command(name="create")
@click.argument("name")
@click.option("--topic", "-t", required=True, help="Topic to subscribe to")
@click.option("--push-endpoint", help="Push endpoint URL")
@click.option("--ack-deadline", "-a", default=10, help="Ack deadline in seconds")
@click.option("--filter", "-f", help="Message filter expression")
def subs_create(
    name: str, topic: str, push_endpoint: str, ack_deadline: int, filter: str
):
    """Create a subscription."""
    payload = {"name": name, "topic": topic, "ack_deadline": ack_deadline}
    if push_endpoint:
        payload["push_endpoint"] = push_endpoint
    if filter:
        payload["filter"] = filter

    resp = _request("post", "/v1/subscriptions", json=payload)
    data = check_response(resp)

    sub_type = "push" if push_endpoint else "pull"
    console.print(f"[green]✓[/green] Subscription '{name}' created")
    console.print(f"  Topic: {topic}")
    console.print(f"  Type: {sub_type}")
    console.print(f"  Ack deadline: {ack_deadline}s")
    if push_endpoint:
        console.print(f"  Push endpoint: {push_endpoint}")
    if filter:
        console.print(f"  Filter: {filter}")


@subs.command(name="delete")
@click.argument("name")
def subs_delete(name: str):
    """Delete a subscription."""
    resp = _request("delete", f"/v1/subscriptions/{name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Subscription '{name}' deleted")


@subs.command(name="describe")
@click.argument("name")
def subs_describe(name: str):
    """Show subscription details."""
    resp = _request("get", f"/v1/subscriptions/{name}")
    data = check_response(resp)

    sub_type = "Push" if data.get("push_endpoint") else "Pull"
    console.print(
        Panel(
            f"[cyan]Subscription:[/cyan] {data.get('name', name)}\n"
            f"[cyan]Topic:[/cyan] {data.get('topic', '-')}\n"
            f"[cyan]Type:[/cyan] {sub_type}\n"
            f"[cyan]Pending messages:[/cyan] {data.get('pending_count', 0):,}\n"
            f"[cyan]Ack deadline:[/cyan] {data.get('ack_deadline', 10)}s\n"
            f"[cyan]Filter:[/cyan] {data.get('filter', 'None')}",
            title="Subscription Details",
            border_style="cyan",
        )
    )


# ============================================================================
# Publish / Pull / Ack
# ============================================================================


@pubsub_group.command()
@click.argument("topic")
@click.option("--message", "-m", required=True, help="Message data")
@click.option("--attributes", "-a", multiple=True, help="Attributes (key=value)")
def publish(topic: str, message: str, attributes: tuple):
    """Publish a message to a topic."""
    payload = {"data": message}
    if attributes:
        attrs = {}
        for a in attributes:
            k, v = a.split("=", 1)
            attrs[k] = v
        payload["attributes"] = attrs

    resp = _request("post", f"/v1/topics/{topic}/publish", json=payload)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Message published to '{topic}'")
    console.print(f"  Message ID: {data.get('message_id', data.get('id', '-'))}")
    if attributes:
        console.print(f"  Attributes: {', '.join(attributes)}")


@pubsub_group.command()
@click.argument("subscription")
@click.option("--max-messages", "-n", default=10, help="Max messages to pull")
@click.option("--wait", "-w", is_flag=True, help="Wait for messages")
@click.option("--auto-ack", is_flag=True, help="Automatically acknowledge messages")
def pull(subscription: str, max_messages: int, wait: bool, auto_ack: bool):
    """Pull messages from a subscription."""
    params = {"max_messages": max_messages}
    if wait:
        params["wait"] = "true"

    resp = _request("post", f"/v1/subscriptions/{subscription}/pull", json=params)
    data = check_response(resp)
    messages = data.get("messages", [])

    for msg in messages:
        console.print(
            f"[dim]{msg.get('publish_time', '')}[/dim] "
            f"[cyan]{msg.get('message_id', msg.get('id', ''))}[/cyan] "
            f"{msg.get('data', '')}"
        )
        if msg.get("attributes"):
            console.print(f"  [dim]attrs: {json.dumps(msg['attributes'])}[/dim]")

    if auto_ack and messages:
        ack_ids = [m.get("ack_id") for m in messages if m.get("ack_id")]
        if ack_ids:
            _request(
                "post",
                f"/v1/subscriptions/{subscription}/ack",
                json={"ack_ids": ack_ids},
            )
            console.print(f"[dim]Auto-acknowledged {len(ack_ids)} message(s)[/dim]")

    if not messages:
        console.print("[dim]No messages available[/dim]")


@pubsub_group.command()
@click.argument("subscription")
@click.option(
    "--ack-ids", "-a", multiple=True, required=True, help="Ack IDs to acknowledge"
)
def ack(subscription: str, ack_ids: tuple):
    """Acknowledge messages."""
    resp = _request(
        "post", f"/v1/subscriptions/{subscription}/ack", json={"ack_ids": list(ack_ids)}
    )
    check_response(resp)
    console.print(f"[green]✓[/green] Acknowledged {len(ack_ids)} message(s)")


@pubsub_group.command()
@click.argument("subscription")
@click.option("--time", "-t", help="Seek to timestamp (RFC3339)")
@click.option("--snapshot", "-s", help="Seek to snapshot")
def seek(subscription: str, time: str, snapshot: str):
    """Seek subscription to a point in time or snapshot."""
    if not time and not snapshot:
        raise click.ClickException("Specify --time or --snapshot")

    payload = {}
    if time:
        payload["time"] = time
    if snapshot:
        payload["snapshot"] = snapshot

    resp = _request("post", f"/v1/subscriptions/{subscription}/seek", json=payload)
    check_response(resp)

    if time:
        console.print(
            f"[green]✓[/green] Subscription '{subscription}' seeked to {time}"
        )
    else:
        console.print(
            f"[green]✓[/green] Subscription '{subscription}' seeked to snapshot '{snapshot}'"
        )


# ============================================================================
# Snapshots
# ============================================================================


@pubsub_group.group()
def snapshots():
    """Manage subscription snapshots."""
    pass


@snapshots.command(name="list")
def snapshots_list():
    """List snapshots."""
    resp = _request("get", "/v1/snapshots")
    data = check_response(resp)
    items = data.get("snapshots", data.get("items", []))

    table = Table(title="Snapshots", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Subscription", style="white")
    table.add_column("Created", style="dim")
    table.add_column("Expires", style="dim")

    for s in items:
        table.add_row(
            s.get("name", ""),
            s.get("subscription", "-"),
            str(s.get("created_at", ""))[:19],
            str(s.get("expires_at", ""))[:19],
        )

    console.print(table)
    if not items:
        console.print("[dim]No snapshots found[/dim]")


@snapshots.command(name="create")
@click.argument("name")
@click.option("--subscription", "-s", required=True, help="Subscription to snapshot")
def snapshots_create(name: str, subscription: str):
    """Create a snapshot of a subscription."""
    resp = _request(
        "post", "/v1/snapshots", json={"name": name, "subscription": subscription}
    )
    check_response(resp)
    console.print(f"[green]✓[/green] Snapshot '{name}' created from '{subscription}'")


@snapshots.command(name="delete")
@click.argument("name")
def snapshots_delete(name: str):
    """Delete a snapshot."""
    resp = _request("delete", f"/v1/snapshots/{name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Snapshot '{name}' deleted")
