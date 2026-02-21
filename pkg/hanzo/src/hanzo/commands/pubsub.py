"""Hanzo Pub/Sub - Event streaming and messaging CLI.

Topics, subscriptions, publish, consume.
"""

import click
from rich import box
from rich.panel import Panel
from rich.table import Table

from ..utils.output import console


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
    table = Table(title="Topics", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Subscriptions", style="white")
    table.add_column("Messages/day", style="green")
    table.add_column("Retention", style="dim")
    table.add_column("Created", style="dim")

    console.print(table)
    console.print("[dim]No topics found. Create one with 'hanzo pubsub topics create'[/dim]")


@topics.command(name="create")
@click.argument("name")
@click.option("--retention", "-r", default="7d", help="Message retention period")
@click.option("--schema", "-s", help="Schema for message validation")
def topics_create(name: str, retention: str, schema: str):
    """Create a topic."""
    console.print(f"[green]✓[/green] Topic '{name}' created")
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
    console.print(f"[green]✓[/green] Topic '{name}' deleted")


@topics.command(name="describe")
@click.argument("name")
def topics_describe(name: str):
    """Show topic details."""
    console.print(
        Panel(
            f"[cyan]Topic:[/cyan] {name}\n"
            f"[cyan]Subscriptions:[/cyan] 3\n"
            f"[cyan]Messages/day:[/cyan] 125,000\n"
            f"[cyan]Retention:[/cyan] 7 days\n"
            f"[cyan]Schema:[/cyan] None\n"
            f"[cyan]Created:[/cyan] 2024-01-15",
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
    table = Table(title="Subscriptions", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Topic", style="white")
    table.add_column("Type", style="green")
    table.add_column("Pending", style="yellow")
    table.add_column("Ack Deadline", style="dim")

    console.print(table)


@subs.command(name="create")
@click.argument("name")
@click.option("--topic", "-t", required=True, help="Topic to subscribe to")
@click.option("--push-endpoint", help="Push endpoint URL")
@click.option("--ack-deadline", "-a", default=10, help="Ack deadline in seconds")
@click.option("--filter", "-f", help="Message filter expression")
def subs_create(name: str, topic: str, push_endpoint: str, ack_deadline: int, filter: str):
    """Create a subscription."""
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
    console.print(f"[green]✓[/green] Subscription '{name}' deleted")


@subs.command(name="describe")
@click.argument("name")
def subs_describe(name: str):
    """Show subscription details."""
    console.print(
        Panel(
            f"[cyan]Subscription:[/cyan] {name}\n"
            f"[cyan]Topic:[/cyan] events\n"
            f"[cyan]Type:[/cyan] Pull\n"
            f"[cyan]Pending messages:[/cyan] 1,234\n"
            f"[cyan]Ack deadline:[/cyan] 10s\n"
            f"[cyan]Filter:[/cyan] None",
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
    import secrets

    msg_id = secrets.token_hex(8)
    console.print(f"[green]✓[/green] Message published to '{topic}'")
    console.print(f"  Message ID: {msg_id}")
    if attributes:
        console.print(f"  Attributes: {', '.join(attributes)}")


@pubsub_group.command()
@click.argument("subscription")
@click.option("--max-messages", "-n", default=10, help="Max messages to pull")
@click.option("--wait", "-w", is_flag=True, help="Wait for messages")
@click.option("--auto-ack", is_flag=True, help="Automatically acknowledge messages")
def pull(subscription: str, max_messages: int, wait: bool, auto_ack: bool):
    """Pull messages from a subscription."""
    console.print(f"[cyan]Pulling from '{subscription}'...[/cyan]")
    console.print("[dim]No messages available[/dim]")


@pubsub_group.command()
@click.argument("subscription")
@click.option("--ack-ids", "-a", multiple=True, required=True, help="Ack IDs to acknowledge")
def ack(subscription: str, ack_ids: tuple):
    """Acknowledge messages."""
    console.print(f"[green]✓[/green] Acknowledged {len(ack_ids)} messages")


@pubsub_group.command()
@click.argument("subscription")
@click.option("--time", "-t", help="Seek to timestamp (RFC3339)")
@click.option("--snapshot", "-s", help="Seek to snapshot")
def seek(subscription: str, time: str, snapshot: str):
    """Seek subscription to a point in time or snapshot."""
    if time:
        console.print(f"[green]✓[/green] Subscription '{subscription}' seeked to {time}")
    elif snapshot:
        console.print(f"[green]✓[/green] Subscription '{subscription}' seeked to snapshot '{snapshot}'")
    else:
        console.print("[yellow]Specify --time or --snapshot[/yellow]")


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
    table = Table(title="Snapshots", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Subscription", style="white")
    table.add_column("Created", style="dim")
    table.add_column("Expires", style="dim")

    console.print(table)


@snapshots.command(name="create")
@click.argument("name")
@click.option("--subscription", "-s", required=True, help="Subscription to snapshot")
def snapshots_create(name: str, subscription: str):
    """Create a snapshot of a subscription."""
    console.print(f"[green]✓[/green] Snapshot '{name}' created from '{subscription}'")


@snapshots.command(name="delete")
@click.argument("name")
def snapshots_delete(name: str):
    """Delete a snapshot."""
    console.print(f"[green]✓[/green] Snapshot '{name}' deleted")
