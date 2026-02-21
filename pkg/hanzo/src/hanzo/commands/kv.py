"""Hanzo KV - Key-value store CLI.

Redis-compatible key-value storage with global replication.
"""

import os
import json

import click
import httpx
from rich import box
from rich.panel import Panel
from rich.table import Table

from ..utils.output import console
from .base import service_request, check_response

KV_URL = os.getenv("HANZO_KV_URL", "https://kv.hanzo.ai")


def _request(method: str, path: str, **kwargs) -> httpx.Response:
    return service_request(KV_URL, method, path, **kwargs)


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
    payload = {"name": name, "max_size": max_size, "eviction_policy": eviction}
    if region:
        payload["regions"] = list(region)

    resp = _request("post", "/v1/stores", json=payload)
    data = check_response(resp)

    console.print(f"[green]✓[/green] KV store '{name}' created")
    console.print(f"  ID: {data.get('id', '-')}")
    console.print(f"  Max size: {max_size}")
    console.print(f"  Eviction: {eviction}")
    if region:
        console.print(f"  Regions: {', '.join(region)}")


@kv_group.command(name="list")
def kv_list():
    """List KV stores."""
    resp = _request("get", "/v1/stores")
    data = check_response(resp)
    stores = data.get("stores", data.get("items", []))

    table = Table(title="KV Stores", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Region", style="white")
    table.add_column("Keys", style="green")
    table.add_column("Size", style="yellow")

    for s in stores:
        regions = s.get("regions", [])
        table.add_row(
            s.get("name", ""),
            ", ".join(regions) if regions else s.get("region", "-"),
            str(s.get("key_count", 0)),
            s.get("size", "0 B"),
        )

    console.print(table)
    if not stores:
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

    resp = _request("delete", f"/v1/stores/{name}")
    check_response(resp)
    console.print(f"[green]✓[/green] KV store '{name}' deleted")


# ============================================================================
# Key-Value Operations
# ============================================================================


@kv_group.command(name="get")
@click.argument("key")
@click.option("--store", "-s", default="default", help="KV store name")
def kv_get(key: str, store: str):
    """Get a value by key."""
    resp = _request("get", f"/v1/stores/{store}/keys/{key}")
    if resp.status_code == 404:
        console.print(f"[dim]Key '{key}' not found in store '{store}'[/dim]")
        return
    data = check_response(resp)
    value = data.get("value", "")
    console.print(f"[cyan]{key}[/cyan] = {value}")


@kv_group.command(name="set")
@click.argument("key")
@click.argument("value")
@click.option("--store", "-s", default="default", help="KV store name")
@click.option("--ttl", "-t", help="TTL (e.g., 1h, 7d)")
@click.option("--nx", is_flag=True, help="Only set if not exists")
def kv_set(key: str, value: str, store: str, ttl: str, nx: bool):
    """Set a key-value pair."""
    payload = {"key": key, "value": value}
    if ttl:
        payload["ttl"] = ttl
    if nx:
        payload["nx"] = True

    resp = _request("put", f"/v1/stores/{store}/keys/{key}", json=payload)
    data = check_response(resp)

    if nx and not data.get("set", True):
        console.print(f"[yellow]Key '{key}' already exists (NX mode)[/yellow]")
    else:
        console.print(f"[green]✓[/green] Set '{key}' in store '{store}'")
        if ttl:
            console.print(f"  TTL: {ttl}")


@kv_group.command(name="del")
@click.argument("keys", nargs=-1, required=True)
@click.option("--store", "-s", default="default", help="KV store name")
def kv_del(keys: tuple, store: str):
    """Delete one or more keys."""
    resp = _request("post", f"/v1/stores/{store}/delete", json={"keys": list(keys)})
    data = check_response(resp)
    console.print(f"[green]✓[/green] Deleted {data.get('deleted', len(keys))} key(s)")


@kv_group.command(name="keys")
@click.option("--store", "-s", default="default", help="KV store name")
@click.option("--pattern", "-p", default="*", help="Key pattern")
@click.option("--limit", "-n", default=100, help="Max keys")
def kv_keys(store: str, pattern: str, limit: int):
    """List keys matching pattern."""
    resp = _request("get", f"/v1/stores/{store}/keys", params={"pattern": pattern, "limit": limit})
    data = check_response(resp)
    keys = data.get("keys", [])

    console.print(f"[cyan]Keys matching '{pattern}':[/cyan]")
    for k in keys:
        if isinstance(k, dict):
            console.print(f"  {k.get('key', k.get('name', ''))}")
        else:
            console.print(f"  {k}")

    if not keys:
        console.print("[dim]No keys found[/dim]")
    else:
        console.print(f"\n[dim]{len(keys)} key(s)[/dim]")


@kv_group.command(name="mget")
@click.argument("keys", nargs=-1, required=True)
@click.option("--store", "-s", default="default")
def kv_mget(keys: tuple, store: str):
    """Get multiple keys."""
    resp = _request("post", f"/v1/stores/{store}/mget", json={"keys": list(keys)})
    data = check_response(resp)
    results = data.get("results", data.get("values", []))

    table = Table(box=box.SIMPLE)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")

    for r in results:
        if isinstance(r, dict):
            table.add_row(r.get("key", ""), str(r.get("value", "(nil)")))
        else:
            table.add_row("-", str(r))

    console.print(table)


@kv_group.command(name="mset")
@click.argument("pairs", nargs=-1, required=True)
@click.option("--store", "-s", default="default")
def kv_mset(pairs: tuple, store: str):
    """Set multiple key-value pairs (key1 val1 key2 val2 ...)."""
    if len(pairs) % 2 != 0:
        raise click.ClickException("Pairs must be even: key1 val1 key2 val2 ...")

    items = []
    for i in range(0, len(pairs), 2):
        items.append({"key": pairs[i], "value": pairs[i + 1]})

    resp = _request("post", f"/v1/stores/{store}/mset", json={"items": items})
    data = check_response(resp)
    console.print(f"[green]✓[/green] Set {data.get('set', len(items))} key(s)")


@kv_group.command(name="ttl")
@click.argument("key")
@click.option("--store", "-s", default="default")
@click.option("--set", "set_ttl", help="Set new TTL")
def kv_ttl(key: str, store: str, set_ttl: str):
    """Get or set TTL for a key."""
    if set_ttl:
        resp = _request("put", f"/v1/stores/{store}/keys/{key}/ttl", json={"ttl": set_ttl})
        check_response(resp)
        console.print(f"[green]✓[/green] Set TTL for '{key}' to {set_ttl}")
    else:
        resp = _request("get", f"/v1/stores/{store}/keys/{key}/ttl")
        data = check_response(resp)
        ttl_val = data.get("ttl", -1)
        if ttl_val == -1:
            console.print(f"[dim]Key '{key}' has no TTL (persistent)[/dim]")
        elif ttl_val == -2:
            console.print(f"[dim]Key '{key}' does not exist[/dim]")
        else:
            console.print(f"[cyan]TTL for '{key}':[/cyan] {ttl_val}s")


@kv_group.command(name="stats")
@click.option("--store", "-s", default="default")
def kv_stats(store: str):
    """Show store statistics."""
    resp = _request("get", f"/v1/stores/{store}/stats")
    data = check_response(resp)

    console.print(
        Panel(
            f"[cyan]Store:[/cyan] {data.get('name', store)}\n"
            f"[cyan]Keys:[/cyan] {data.get('key_count', 0):,}\n"
            f"[cyan]Memory:[/cyan] {data.get('memory', '0 B')}\n"
            f"[cyan]Hit rate:[/cyan] {data.get('hit_rate', 0):.1f}%\n"
            f"[cyan]Ops/sec:[/cyan] {data.get('ops_per_sec', 0):,}\n"
            f"[cyan]Eviction policy:[/cyan] {data.get('eviction_policy', '-')}",
            title="KV Statistics",
            border_style="cyan",
        )
    )
