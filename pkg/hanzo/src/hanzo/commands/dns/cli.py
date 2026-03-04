"""Hanzo DNS CLI — multi-provider DNS management.

Queries all configured DNS providers in parallel, merges results.

Usage:
    hanzo dns zones                              # List zones from all providers
    hanzo dns list -z hanzo.ai                   # List records (all providers)
    hanzo dns list -z hanzo.ai --type CNAME      # Filter by record type
    hanzo dns add -z lux.financial app 1.2.3.4   # Add A record
    hanzo dns add -z lux.financial app tgt --type CNAME --provider cloudflare
    hanzo dns rm -z lux.financial app            # Remove record
    hanzo dns update hanzo.ai 1.2.3.4 5.6.7.8   # Batch update IPs
    hanzo dns providers                          # Show configured providers
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import click

# Import providers to trigger registration
from . import cloudflare as _cf  # noqa: F401
from . import coredns as _cd  # noqa: F401
from .provider import (
    DNSRecord,
    DNSZone,
    get_active_providers,
    list_providers as _list_provider_names,
    load_dns_config,
    require_providers,
    get_provider,
)


def _run_parallel(providers, method: str, *args, **kwargs) -> list[Any]:
    """Run a method on all providers in parallel, collect results."""
    results: list[Any] = []

    if len(providers) == 1:
        try:
            val = getattr(providers[0], method)(*args, **kwargs)
            if isinstance(val, list):
                results.extend(val)
            else:
                results.append((providers[0].name, val))
        except Exception as e:
            results.append((providers[0].name, e))
        return results

    with ThreadPoolExecutor(max_workers=len(providers)) as pool:
        futures = {}
        for p in providers:
            fut = pool.submit(getattr(p, method), *args, **kwargs)
            futures[fut] = p.name

        for fut in as_completed(futures):
            pname = futures[fut]
            try:
                val = fut.result()
                if isinstance(val, list):
                    results.extend(val)
                else:
                    results.append((pname, val))
            except Exception as e:
                results.append((pname, e))

    return results


def _resolve_provider(provider_name: str | None, providers: list):
    """Pick a single provider by name, or first available."""
    if provider_name:
        for p in providers:
            if p.name == provider_name:
                return p
        raise click.ClickException(
            f"Provider '{provider_name}' not configured. "
            f"Active: {', '.join(p.name for p in providers)}"
        )
    return providers[0]


# ── Click group ───────────────────────────────────────────────────────


@click.group("dns")
def dns_group() -> None:
    """Hanzo DNS — multi-provider DNS management.

    \b
    Queries all configured DNS providers in parallel.
    Supports: Cloudflare, CoreDNS, and more.

    \b
    Commands:
      hanzo dns providers                        Show configured providers
      hanzo dns zones                            List all zones
      hanzo dns list -z hanzo.ai                 List records
      hanzo dns add -z lux.financial app 1.2.3.4 Add A record
      hanzo dns rm -z lux.financial app          Remove record
      hanzo dns update hanzo.ai OLD NEW          Batch update IPs

    \b
    Config: ~/.hanzo/credentials.json
      {"dns": {"cloudflare": {"email": "...", "api_key": "..."}}}
      {"dns": {"coredns": {"endpoint": "...", "api_key": "..."}}}
    """


# ── providers ────────────────────────────────────────────────────────


@dns_group.command("providers")
def dns_providers() -> None:
    """Show configured DNS providers and their status."""
    from rich.table import Table
    from ...utils.output import console

    configs = load_dns_config()
    available = _list_provider_names()

    table = Table(title="DNS Providers")
    table.add_column("Provider", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="dim")

    for name in available:
        if name in configs:
            cfg = configs[name]
            detail_parts = []
            if "email" in cfg:
                detail_parts.append(f"email={cfg['email']}")
            if "endpoint" in cfg:
                detail_parts.append(f"endpoint={cfg['endpoint']}")
            detail = ", ".join(detail_parts) if detail_parts else "configured"
            table.add_row(name, "[green]active[/green]", detail)
        else:
            table.add_row(name, "[dim]not configured[/dim]", "")

    console.print(table)

    if not configs:
        console.print(
            f"\n[yellow]No providers configured.[/yellow]\n"
            f"Add credentials to ~/.hanzo/credentials.json"
        )


# ── zones ─────────────────────────────────────────────────────────────


@dns_group.command("zones")
@click.option("--provider", "-p", default=None, help="Filter by provider.")
def dns_zones(provider: str | None) -> None:
    """List all DNS zones across all providers."""
    from rich.table import Table
    from ...utils.output import console

    providers = require_providers()
    if provider:
        providers = [p for p in providers if p.name == provider]
        if not providers:
            raise click.ClickException(f"Provider '{provider}' not configured.")

    results = _run_parallel(providers, "list_zones")

    zones: list[DNSZone] = [r for r in results if isinstance(r, DNSZone)]
    errors = [r for r in results if isinstance(r, tuple) and isinstance(r[1], Exception)]

    if not zones and not errors:
        console.print("[yellow]No zones found.[/yellow]")
        return

    if zones:
        table = Table(title="DNS Zones")
        table.add_column("Name", style="cyan")
        table.add_column("Provider", style="magenta")
        table.add_column("ID", style="dim")
        table.add_column("Status", style="green")
        table.add_column("Plan", style="white")

        for z in sorted(zones, key=lambda x: x.name):
            table.add_row(z.name, z.provider, z.id[:16], z.status, z.plan)

        console.print(table)

    for pname, err in errors:
        console.print(f"  [red]{pname}:[/red] {err}")


# ── list ──────────────────────────────────────────────────────────────


@dns_group.command("list")
@click.option("--zone", "-z", required=True, help="Zone name (e.g. hanzo.ai).")
@click.option("--type", "record_type", default=None, help="Record type filter (A, CNAME, etc.).")
@click.option("--provider", "-p", default=None, help="Filter by provider.")
def dns_list(zone: str, record_type: str | None, provider: str | None) -> None:
    """List DNS records for a zone (queries all providers in parallel)."""
    from rich.table import Table
    from ...utils.output import console

    providers = require_providers()
    if provider:
        providers = [p for p in providers if p.name == provider]
        if not providers:
            raise click.ClickException(f"Provider '{provider}' not configured.")

    results = _run_parallel(providers, "list_records", zone, record_type)

    records: list[DNSRecord] = [r for r in results if isinstance(r, DNSRecord)]
    errors = [r for r in results if isinstance(r, tuple) and isinstance(r[1], Exception)]

    if not records:
        label = f" {record_type}" if record_type else ""
        console.print(f"[yellow]No{label} records found for {zone}.[/yellow]")
        for pname, err in errors:
            console.print(f"  [red]{pname}:[/red] {err}")
        return

    table = Table(title=f"DNS Records — {zone}")
    table.add_column("Type", style="white", min_width=6)
    table.add_column("Name", style="cyan", min_width=25)
    table.add_column("Content", style="white")
    table.add_column("TTL", justify="right")
    table.add_column("Proxied", justify="center")
    table.add_column("Provider", style="magenta")
    table.add_column("ID", style="dim")

    for r in sorted(records, key=lambda x: (x.provider, x.type, x.name)):
        proxied = "[green]yes[/green]" if r.proxied else "no"
        table.add_row(
            r.type, r.name, r.content, r.ttl_display,
            proxied, r.provider, r.id[:12],
        )

    console.print(table)
    console.print(f"\n{len(records)} record(s)")

    for pname, err in errors:
        console.print(f"  [red]{pname}:[/red] {err}")


# ── add ───────────────────────────────────────────────────────────────


@dns_group.command("add")
@click.option("--zone", "-z", required=True, help="Zone name (e.g. lux.financial).")
@click.argument("name")
@click.argument("content")
@click.option("--type", "record_type", default="A", help="Record type (default: A).")
@click.option("--proxied/--no-proxy", default=True, help="Proxy (default: on, CF only).")
@click.option("--ttl", default=1, help="TTL (1 = auto).")
@click.option("--provider", "-p", default=None, help="Target provider (default: first active).")
def dns_add(
    zone: str, name: str, content: str,
    record_type: str, proxied: bool, ttl: int, provider: str | None
) -> None:
    """Add a DNS record.

    \b
    Examples:
      hanzo dns add -z lux.financial app 1.2.3.4           # A record
      hanzo dns add -z lux.financial app tgt --type CNAME   # CNAME
      hanzo dns add -z hanzo.ai api 10.0.0.1 --no-proxy    # Unproxied A
      hanzo dns add -z hanzo.ai app 1.2.3.4 -p cloudflare  # Specific provider
    """
    from ...utils.output import console

    providers = require_providers()
    target = _resolve_provider(provider, providers)

    rec = target.add_record(zone, name, content, record_type, proxied, ttl)
    if rec:
        console.print(f"[green]✓[/green] Created {record_type.upper()} record via [magenta]{target.name}[/magenta]")
        console.print(f"  Name:     {rec.name}")
        console.print(f"  Content:  {content}")
        console.print(f"  Proxied:  {'yes' if rec.proxied else 'no'}")
        console.print(f"  ID:       {rec.id}")


# ── rm ────────────────────────────────────────────────────────────────


@dns_group.command("rm")
@click.option("--zone", "-z", required=True, help="Zone name.")
@click.argument("name")
@click.option("--type", "record_type", default=None, help="Record type filter.")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation.")
@click.option("--provider", "-p", default=None, help="Target provider (default: all).")
def dns_rm(zone: str, name: str, record_type: str | None, force: bool, provider: str | None) -> None:
    """Remove DNS record(s) matching NAME.

    \b
    By default searches all providers. Use --provider to target one.

    \b
    Examples:
      hanzo dns rm -z lux.financial app              # All providers
      hanzo dns rm -z lux.financial app --type A      # Only A records
      hanzo dns rm -z lux.financial app -p cloudflare # CF only
      hanzo dns rm -z lux.financial app -f            # Skip confirmation
    """
    from ...utils.output import console

    providers = require_providers()
    if provider:
        providers = [p for p in providers if p.name == provider]
        if not providers:
            raise click.ClickException(f"Provider '{provider}' not configured.")

    # Preview what will be deleted
    full_name = name if name.endswith(zone) else f"{name}.{zone}"
    results = _run_parallel(providers, "list_records", zone, record_type)
    matching = [r for r in results if isinstance(r, DNSRecord) and r.name == full_name]

    if not matching:
        console.print(f"[yellow]No records found for {full_name}[/yellow]")
        return

    console.print(f"Found [cyan]{len(matching)}[/cyan] record(s) for {full_name}:")
    for r in matching:
        console.print(f"  [{r.provider}] {r.type:6} {r.name} -> {r.content}")

    if not force:
        click.confirm("Delete these records?", abort=True)

    total_deleted = 0
    for p in providers:
        deleted = p.remove_records(zone, name, record_type)
        total_deleted += deleted

    console.print(f"[green]✓[/green] Deleted {total_deleted} record(s)")


# ── update (batch IP swap) ───────────────────────────────────────────


@dns_group.command("update")
@click.argument("zone")
@click.argument("old_ip")
@click.argument("new_ip")
@click.option("--type", "record_type", default="A", help="Record type (default: A).")
@click.option("--dry-run", is_flag=True, help="Show changes without applying.")
@click.option("--provider", "-p", default=None, help="Target provider (default: all).")
def dns_update(
    zone: str, old_ip: str, new_ip: str,
    record_type: str, dry_run: bool, provider: str | None
) -> None:
    """Batch update records: replace OLD_IP with NEW_IP across all providers.

    \b
    Examples:
      hanzo dns update hanzo.ai 1.2.3.4 5.6.7.8 --dry-run
      hanzo dns update lux.network 10.0.0.1 10.0.0.2
      hanzo dns update hanzo.ai 1.2.3.4 5.6.7.8 -p cloudflare
    """
    from rich.table import Table
    from ...utils.output import console

    providers = require_providers()
    if provider:
        providers = [p for p in providers if p.name == provider]
        if not providers:
            raise click.ClickException(f"Provider '{provider}' not configured.")

    # Preview: find matching records across all providers
    results = _run_parallel(providers, "list_records", zone, record_type)
    matching = [
        r for r in results
        if isinstance(r, DNSRecord) and r.content == old_ip
    ]

    if not matching:
        console.print(
            f"[yellow]No {record_type} records found in {zone} "
            f"pointing to {old_ip}.[/yellow]"
        )
        return

    console.print(
        f"Found [cyan]{len(matching)}[/cyan] {record_type} record(s) "
        f"pointing to [red]{old_ip}[/red]\n"
    )

    table = Table(title="Records to Update")
    table.add_column("Provider", style="magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Current", style="red")
    table.add_column("New", style="green")

    for r in matching:
        table.add_row(r.provider, r.name, old_ip, new_ip)

    console.print(table)

    if dry_run:
        console.print("\n[yellow]Dry run — no changes applied.[/yellow]")
        return

    total_updated = 0
    total_failed = 0

    for p in providers:
        updated, failed = p.update_records(zone, old_ip, new_ip, record_type)
        total_updated += updated
        total_failed += failed

    console.print(
        f"\n[green]{total_updated} updated[/green]"
        + (f", [red]{total_failed} failed[/red]" if total_failed else "")
    )
