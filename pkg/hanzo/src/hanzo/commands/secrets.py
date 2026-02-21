"""Hanzo Secrets - Secret management CLI.

Secure secret storage with versioning and rotation via Hanzo KMS.
"""

import os
import sys
import json

import click
import httpx
from rich import box
from rich.panel import Panel
from rich.table import Table

from .base import check_response, service_request
from ..utils.output import console

KMS_URL = os.getenv("HANZO_KMS_URL", "https://kms.hanzo.ai")


def _request(method: str, path: str, **kwargs) -> httpx.Response:
    return service_request(KMS_URL, method, path, **kwargs)


@click.group(name="secrets")
def secrets_group():
    """Hanzo Secrets - Secure secret management.

    \b
    Operations:
      hanzo secrets set <name>       # Set a secret
      hanzo secrets get <name>       # Get secret value
      hanzo secrets list             # List secrets (names only)
      hanzo secrets unset <name>     # Delete a secret
      hanzo secrets rotate <name>    # Rotate a secret

    \b
    Versions:
      hanzo secrets versions <name>  # List secret versions
      hanzo secrets rollback <name>  # Rollback to previous version

    \b
    Access:
      hanzo secrets grant            # Grant access to secret
      hanzo secrets revoke           # Revoke access
      hanzo secrets audit            # View access logs
    """
    pass


# ============================================================================
# Secret Operations
# ============================================================================


@secrets_group.command(name="set")
@click.argument("name")
@click.option("--value", "-v", help="Secret value (or use stdin)")
@click.option("--file", "-f", type=click.Path(exists=True), help="Read value from file")
@click.option("--env", "-e", help="Environment (dev/staging/prod)")
@click.option("--description", "-d", help="Secret description")
def secrets_set(name: str, value: str, file: str, env: str, description: str):
    """Set a secret value.

    \b
    Examples:
      hanzo secrets set API_KEY --value sk-abc123
      echo "secret" | hanzo secrets set DB_PASSWORD
      hanzo secrets set CERT --file ./cert.pem
    """
    if file:
        from pathlib import Path

        value = Path(file).read_text().strip()
    elif not value:
        if not sys.stdin.isatty():
            value = sys.stdin.read().strip()
        else:
            value = click.prompt("Secret value", hide_input=True)

    payload = {"key": name, "value": value}
    if env:
        payload["environment"] = env
    if description:
        payload["description"] = description

    resp = _request("post", "/v1/secrets", json=payload)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Secret '{name}' set")
    console.print(f"  Version: {data.get('version', 1)}")
    if env:
        console.print(f"  Environment: {env}")


@secrets_group.command(name="get")
@click.argument("name")
@click.option("--env", "-e", help="Environment (dev/staging/prod)")
@click.option("--version", "-v", help="Specific version")
@click.option("--plain", is_flag=True, help="Output value only (no formatting)")
def secrets_get(name: str, env: str, version: str, plain: bool):
    """Get a secret value."""
    params = {}
    if env:
        params["environment"] = env
    if version:
        params["version"] = version

    resp = _request("get", f"/v1/secrets/{name}", params=params)
    data = check_response(resp)

    if plain:
        click.echo(data.get("value", ""))
    else:
        console.print(
            Panel(
                f"[cyan]Name:[/cyan] {name}\n"
                f"[cyan]Value:[/cyan] {data.get('value', '')}\n"
                f"[cyan]Version:[/cyan] {data.get('version', '-')}\n"
                f"[cyan]Environment:[/cyan] {data.get('environment', 'default')}\n"
                f"[cyan]Updated:[/cyan] {data.get('updated_at', '-')}",
                title="Secret",
                border_style="cyan",
            )
        )


@secrets_group.command(name="list")
@click.option("--env", "-e", help="Filter by environment")
@click.option("--prefix", "-p", help="Filter by prefix")
def secrets_list(env: str, prefix: str):
    """List all secrets (names only, not values)."""
    params = {}
    if env:
        params["environment"] = env
    if prefix:
        params["prefix"] = prefix

    resp = _request("get", "/v1/secrets", params=params)
    data = check_response(resp)
    items = data.get("secrets", data.get("items", []))

    table = Table(title="Secrets", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Environment", style="white")
    table.add_column("Version", style="green")
    table.add_column("Updated", style="dim")

    for s in items:
        table.add_row(
            s.get("key", s.get("name", "")),
            s.get("environment", "default"),
            str(s.get("version", "-")),
            str(s.get("updated_at", "-"))[:19],
        )

    console.print(table)
    if not items:
        console.print(
            "[dim]No secrets found. Create one with 'hanzo secrets set'[/dim]"
        )


@secrets_group.command(name="unset")
@click.argument("name")
@click.option("--env", "-e", help="Environment (dev/staging/prod)")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def secrets_unset(name: str, env: str, force: bool):
    """Delete a secret."""
    if not force:
        from rich.prompt import Confirm

        if not Confirm.ask(f"[red]Delete secret '{name}'?[/red]"):
            return

    params = {}
    if env:
        params["environment"] = env

    resp = _request("delete", f"/v1/secrets/{name}", params=params)
    check_response(resp)
    console.print(f"[green]✓[/green] Secret '{name}' deleted")


@secrets_group.command(name="rotate")
@click.argument("name")
@click.option("--env", "-e", help="Environment")
def secrets_rotate(name: str, env: str):
    """Rotate a secret (generate new value)."""
    payload = {}
    if env:
        payload["environment"] = env

    resp = _request("post", f"/v1/secrets/{name}/rotate", json=payload)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Secret '{name}' rotated")
    console.print(f"  New version: {data.get('version', '-')}")
    console.print(f"  Previous version expires: {data.get('previous_expires', '24h')}")


# ============================================================================
# Version Management
# ============================================================================


@secrets_group.command(name="versions")
@click.argument("name")
@click.option("--env", "-e", help="Environment")
def secrets_versions(name: str, env: str):
    """List secret versions."""
    params = {}
    if env:
        params["environment"] = env

    resp = _request("get", f"/v1/secrets/{name}/versions", params=params)
    data = check_response(resp)
    versions = data.get("versions", [])

    table = Table(title=f"Versions: {name}", box=box.ROUNDED)
    table.add_column("Version", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Created", style="dim")
    table.add_column("Created By", style="dim")

    for v in versions:
        status = "● Active" if v.get("active") else "○ Inactive"
        style = "green" if v.get("active") else "dim"
        table.add_row(
            str(v.get("version", "")),
            f"[{style}]{status}[/{style}]",
            str(v.get("created_at", ""))[:19],
            v.get("created_by", "-"),
        )

    console.print(table)
    if not versions:
        console.print(f"[dim]No versions found for '{name}'[/dim]")


@secrets_group.command(name="rollback")
@click.argument("name")
@click.option("--version", "-v", required=True, help="Version to rollback to")
@click.option("--env", "-e", help="Environment")
def secrets_rollback(name: str, version: str, env: str):
    """Rollback to a previous secret version."""
    payload = {"version": int(version)}
    if env:
        payload["environment"] = env

    resp = _request("post", f"/v1/secrets/{name}/rollback", json=payload)
    check_response(resp)
    console.print(f"[green]✓[/green] Rolled back '{name}' to version {version}")


# ============================================================================
# Access Control
# ============================================================================


@secrets_group.command(name="grant")
@click.argument("name")
@click.option("--to", "-t", required=True, help="Service or user to grant access")
@click.option(
    "--role", "-r", default="read", type=click.Choice(["read", "write", "admin"])
)
def secrets_grant(name: str, to: str, role: str):
    """Grant access to a secret."""
    resp = _request(
        "post", f"/v1/secrets/{name}/access", json={"principal": to, "role": role}
    )
    check_response(resp)
    console.print(f"[green]✓[/green] Granted {role} access to '{name}' for {to}")


@secrets_group.command(name="revoke")
@click.argument("name")
@click.option("--from", "from_", required=True, help="Service or user to revoke")
def secrets_revoke(name: str, from_: str):
    """Revoke access to a secret."""
    resp = _request("delete", f"/v1/secrets/{name}/access/{from_}")
    check_response(resp)
    console.print(f"[green]✓[/green] Revoked access to '{name}' from {from_}")


@secrets_group.command(name="audit")
@click.argument("name", required=False)
@click.option("--limit", "-n", default=50, help="Number of entries")
def secrets_audit(name: str, limit: int):
    """View secret access logs."""
    path = f"/v1/secrets/{name}/audit" if name else "/v1/secrets/audit"
    resp = _request("get", path, params={"limit": limit})
    data = check_response(resp)
    entries = data.get("entries", data.get("logs", []))

    table = Table(title="Secret Access Log", box=box.ROUNDED)
    table.add_column("Time", style="dim")
    table.add_column("Secret", style="cyan")
    table.add_column("Action", style="white")
    table.add_column("Actor", style="green")
    table.add_column("IP", style="dim")

    for e in entries:
        table.add_row(
            str(e.get("timestamp", ""))[:19],
            e.get("secret", e.get("key", "-")),
            e.get("action", "-"),
            e.get("actor", e.get("principal", "-")),
            e.get("ip", e.get("source_ip", "-")),
        )

    console.print(table)
    if not entries:
        console.print("[dim]No access logs found[/dim]")
