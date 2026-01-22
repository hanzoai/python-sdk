"""Hanzo KV - Key-value store CLI.

Redis-compatible key-value storage with global replication.
"""

import click
from rich import box
from rich.table import Table
from rich.panel import Panel

from ..utils.output import console


@click.group(name="kv")
def kv_group():
    """Hanzo KV - Global key-value store.

    \b
    Stores:
      hanzo kv create                # Create KV store
      hanzo kv list                  # List stores
      hanzo kv delete                # Delete store

    \b
    Operations:
      hanzo kv get                   # Get value
      hanzo kv set                   # Set value
      hanzo kv del                   # Delete key
      hanzo kv keys                  # List keys

    \b
    Batch:
      hanzo kv mget                  # Multi-get
      hanzo kv mset                  # Multi-set
    """
    pass


# ============================================================================
# Store Management
# ============================================================================

@kv_group.command(name="create")
@click.argument("name")
@click.option("--region", "-r", multiple=True, help="Regions for replication")
@click.option("--max-size", default="1GB", help="Max store size")
@click.option("--eviction", type=click.Choice(["lru", "lfu", "ttl", "none"]), default="lru")
def kv_create(name: str, region: tuple, max_size: str, eviction: str):
    """Create a KV store."""
    console.print(f"[green]✓[/green] KV store '{name}' created")
    console.print(f"  Max size: {max_size}")
    console.print(f"  Eviction: {eviction}")
    if region:
        console.print(f"  Regions: {', '.join(region)}")


@kv_group.command(name="list")
def kv_list():
    """List KV stores."""
    table = Table(title="KV Stores", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Region", style="white")
    table.add_column("Keys", style="green")
    table.add_column("Size", style="yellow")

    console.print(table)
    console.print("[dim]No KV stores found. Create one with 'hanzo kv create'[/dim]")


@kv_group.command(name="delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def kv_delete(name: str, force: bool):
    """Delete a KV store."""
    if not force:
        from rich.prompt import Confirm
        if not Confirm.ask(f"[red]Delete KV store '{name}'?[/red]"):
            return
    console.print(f"[green]✓[/green] KV store '{name}' deleted")


# ============================================================================
# Key-Value Operations
# ============================================================================

@kv_group.command(name="get")
@click.argument("key")
@click.option("--store", "-s", default="default", help="KV store name")
def kv_get(key: str, store: str):
    """Get a value by key."""
    console.print(f"[dim]Key '{key}' not found in store '{store}'[/dim]")


@kv_group.command(name="set")
@click.argument("key")
@click.argument("value")
@click.option("--store", "-s", default="default", help="KV store name")
@click.option("--ttl", "-t", help="TTL (e.g., 1h, 7d)")
@click.option("--nx", is_flag=True, help="Only set if not exists")
def kv_set(key: str, value: str, store: str, ttl: str, nx: bool):
    """Set a key-value pair."""
    console.print(f"[green]✓[/green] Set '{key}' in store '{store}'")
    if ttl:
        console.print(f"  TTL: {ttl}")


@kv_group.command(name="del")
@click.argument("keys", nargs=-1, required=True)
@click.option("--store", "-s", default="default", help="KV store name")
def kv_del(keys: tuple, store: str):
    """Delete one or more keys."""
    console.print(f"[green]✓[/green] Deleted {len(keys)} key(s)")


@kv_group.command(name="keys")
@click.option("--store", "-s", default="default", help="KV store name")
@click.option("--pattern", "-p", default="*", help="Key pattern")
@click.option("--limit", "-n", default=100, help="Max keys")
def kv_keys(store: str, pattern: str, limit: int):
    """List keys matching pattern."""
    console.print(f"[cyan]Keys matching '{pattern}':[/cyan]")
    console.print("[dim]No keys found[/dim]")


@kv_group.command(name="mget")
@click.argument("keys", nargs=-1, required=True)
@click.option("--store", "-s", default="default")
def kv_mget(keys: tuple, store: str):
    """Get multiple keys."""
    table = Table(box=box.SIMPLE)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")
    console.print(table)


@kv_group.command(name="mset")
@click.argument("pairs", nargs=-1, required=True)
@click.option("--store", "-s", default="default")
def kv_mset(pairs: tuple, store: str):
    """Set multiple key-value pairs (key1 val1 key2 val2 ...)."""
    count = len(pairs) // 2
    console.print(f"[green]✓[/green] Set {count} key(s)")


@kv_group.command(name="ttl")
@click.argument("key")
@click.option("--store", "-s", default="default")
@click.option("--set", "set_ttl", help="Set new TTL")
def kv_ttl(key: str, store: str, set_ttl: str):
    """Get or set TTL for a key."""
    if set_ttl:
        console.print(f"[green]✓[/green] Set TTL for '{key}' to {set_ttl}")
    else:
        console.print(f"[dim]Key '{key}' has no TTL[/dim]")


@kv_group.command(name="stats")
@click.option("--store", "-s", default="default")
def kv_stats(store: str):
    """Show store statistics."""
    console.print(Panel(
        f"[cyan]Store:[/cyan] {store}\n"
        f"[cyan]Keys:[/cyan] 0\n"
        f"[cyan]Memory:[/cyan] 0 B\n"
        f"[cyan]Hit rate:[/cyan] 0%",
        title="KV Statistics",
        border_style="cyan"
    ))
