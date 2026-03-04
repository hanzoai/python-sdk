"""Cloudflare DNS management for Hanzo K8s CLI.

Reads credentials from ~/.hanzo/credentials.json under the 'cloudflare' key.
Provides commands to list zones, list A records, and batch-update IPs.

Usage:
    hanzo k8s dns zones                         # List all zones
    hanzo k8s dns list --zone hanzo.ai          # List A records
    hanzo k8s dns update hanzo.ai 1.2.3.4 5.6.7.8 --dry-run
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click
import httpx
from rich.console import Console
from rich.table import Table

console = Console()

CF_API = "https://api.cloudflare.com/client/v4"
CREDENTIALS_FILE = Path.home() / ".hanzo" / "credentials.json"


def _load_cf_credentials() -> tuple[str, str]:
    """Load Cloudflare email + API key from ~/.hanzo/credentials.json.

    Returns (email, api_key) or exits with an error message.
    """
    if not CREDENTIALS_FILE.exists():
        console.print(
            f"[red]Credentials file not found:[/red] {CREDENTIALS_FILE}\n"
            "Create it with a 'cloudflare' section containing "
            "'email' and 'api_key'."
        )
        sys.exit(1)

    try:
        data = json.loads(CREDENTIALS_FILE.read_text())
    except (json.JSONDecodeError, OSError) as e:
        console.print(f"[red]Failed to read credentials:[/red] {e}")
        sys.exit(1)

    cf = data.get("cloudflare", {})
    email = cf.get("email", "")
    api_key = cf.get("api_key", "")

    if not email or not api_key:
        console.print(
            "[red]Missing Cloudflare credentials.[/red]\n"
            f"Ensure {CREDENTIALS_FILE} has:\n"
            '  {"cloudflare": {"email": "...", "api_key": "..."}}'
        )
        sys.exit(1)

    return email, api_key


def _cf_headers(email: str, api_key: str) -> dict[str, str]:
    """Build Cloudflare API auth headers."""
    return {
        "X-Auth-Email": email,
        "X-Auth-Key": api_key,
        "Content-Type": "application/json",
    }


def _cf_get(
    client: httpx.Client, path: str, params: dict[str, Any] | None = None
) -> Any:
    """GET from Cloudflare API, handling pagination and errors."""
    resp = client.get(f"{CF_API}{path}", params=params)
    data = resp.json()
    if not data.get("success"):
        errors = data.get("errors", [])
        msg = "; ".join(e.get("message", str(e)) for e in errors)
        raise click.ClickException(f"Cloudflare API error: {msg}")
    return data


# ── Click group ───────────────────────────────────────────────────────


@click.group("dns")
def dns() -> None:
    """Cloudflare DNS management.

    List zones, view A records, and batch-update IP addresses.
    Reads credentials from ~/.hanzo/credentials.json.
    """


# ── zones ─────────────────────────────────────────────────────────────


@dns.command("zones")
def dns_zones() -> None:
    """List all Cloudflare zones in the account."""
    email, api_key = _load_cf_credentials()

    with httpx.Client(headers=_cf_headers(email, api_key), timeout=30.0) as client:
        data = _cf_get(client, "/zones", params={"per_page": "50"})

    zones = data.get("result", [])
    if not zones:
        console.print("[yellow]No zones found.[/yellow]")
        return

    table = Table(title="Cloudflare Zones")
    table.add_column("Name", style="cyan")
    table.add_column("ID", style="dim")
    table.add_column("Status", style="green")
    table.add_column("Plan", style="white")

    for z in sorted(zones, key=lambda x: x.get("name", "")):
        table.add_row(
            z.get("name", ""),
            z.get("id", ""),
            z.get("status", ""),
            z.get("plan", {}).get("name", ""),
        )

    console.print(table)


# ── list ──────────────────────────────────────────────────────────────


@dns.command("list")
@click.option(
    "--zone",
    "-z",
    required=True,
    help="Zone name (e.g. hanzo.ai).",
)
@click.option(
    "--type",
    "record_type",
    default="A",
    help="DNS record type (default: A).",
)
def dns_list(zone: str, record_type: str) -> None:
    """List DNS records for a zone."""
    email, api_key = _load_cf_credentials()

    with httpx.Client(headers=_cf_headers(email, api_key), timeout=30.0) as client:
        # Resolve zone name to zone ID
        zone_id = _resolve_zone_id(client, zone)

        # Fetch records
        data = _cf_get(
            client,
            f"/zones/{zone_id}/dns_records",
            params={"type": record_type, "per_page": "100"},
        )

    records = data.get("result", [])
    if not records:
        console.print(f"[yellow]No {record_type} records found for {zone}.[/yellow]")
        return

    table = Table(title=f"DNS Records — {zone} ({record_type})")
    table.add_column("Name", style="cyan", min_width=25)
    table.add_column("Content", style="white")
    table.add_column("TTL", justify="right")
    table.add_column("Proxied", justify="center")
    table.add_column("ID", style="dim")

    for r in sorted(records, key=lambda x: x.get("name", "")):
        ttl = r.get("ttl", 0)
        ttl_str = "Auto" if ttl == 1 else str(ttl)
        proxied = "[green]yes[/green]" if r.get("proxied") else "no"
        table.add_row(
            r.get("name", ""),
            r.get("content", ""),
            ttl_str,
            proxied,
            r.get("id", "")[:12],
        )

    console.print(table)
    console.print(f"\n{len(records)} record(s)")


# ── update ────────────────────────────────────────────────────────────


@dns.command("update")
@click.argument("zone")
@click.argument("old_ip")
@click.argument("new_ip")
@click.option("--dry-run", is_flag=True, help="Show changes without applying.")
def dns_update(zone: str, old_ip: str, new_ip: str, dry_run: bool) -> None:
    """Batch update A records: replace OLD_IP with NEW_IP.

    Finds all A records in ZONE pointing to OLD_IP and updates them
    to NEW_IP. Use --dry-run to preview changes first.
    """
    email, api_key = _load_cf_credentials()

    with httpx.Client(headers=_cf_headers(email, api_key), timeout=30.0) as client:
        zone_id = _resolve_zone_id(client, zone)

        # Fetch A records matching old IP
        data = _cf_get(
            client,
            f"/zones/{zone_id}/dns_records",
            params={"type": "A", "content": old_ip, "per_page": "100"},
        )

        records = data.get("result", [])
        if not records:
            console.print(
                f"[yellow]No A records found in {zone} pointing to {old_ip}.[/yellow]"
            )
            return

        console.print(
            f"Found [cyan]{len(records)}[/cyan] A record(s) "
            f"pointing to [red]{old_ip}[/red]\n"
        )

        table = Table(title="Records to Update")
        table.add_column("Name", style="cyan")
        table.add_column("Current", style="red")
        table.add_column("New", style="green")
        table.add_column("Proxied", justify="center")

        for r in records:
            proxied = "yes" if r.get("proxied") else "no"
            table.add_row(r.get("name", ""), old_ip, new_ip, proxied)

        console.print(table)

        if dry_run:
            console.print("\n[yellow]Dry run — no changes applied.[/yellow]")
            return

        # Apply updates
        updated = 0
        failed = 0
        for r in records:
            record_id = r["id"]
            try:
                resp = client.patch(
                    f"{CF_API}/zones/{zone_id}/dns_records/{record_id}",
                    json={"content": new_ip},
                )
                result = resp.json()
                if result.get("success"):
                    updated += 1
                else:
                    failed += 1
                    errs = result.get("errors", [])
                    msg = "; ".join(e.get("message", "") for e in errs)
                    console.print(
                        f"  [red]Failed:[/red] {r.get('name', '')} — {msg}"
                    )
            except Exception as e:
                failed += 1
                console.print(f"  [red]Error:[/red] {r.get('name', '')} — {e}")

        console.print(
            f"\n[green]{updated} updated[/green]"
            + (f", [red]{failed} failed[/red]" if failed else "")
        )


# ── helpers ───────────────────────────────────────────────────────────


def _resolve_zone_id(client: httpx.Client, zone_name: str) -> str:
    """Resolve a zone name to its Cloudflare zone ID."""
    data = _cf_get(client, "/zones", params={"name": zone_name, "per_page": "1"})
    zones = data.get("result", [])
    if not zones:
        raise click.ClickException(
            f"Zone '{zone_name}' not found in Cloudflare account."
        )
    return zones[0]["id"]
