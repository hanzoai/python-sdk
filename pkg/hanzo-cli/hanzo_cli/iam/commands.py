"""Hanzo CLI — IAM subcommands.

Usage:
    hanzo iam users                         — List users
    hanzo iam user <name>                   — Get user details
    hanzo iam set-password <user> [pw]      — Set password (prompt if no pw)
    hanzo iam orgs                          — List organizations
    hanzo iam apps                          — List applications
    hanzo iam sync-app <name> [--init-data] — Sync redirect URIs
"""

from __future__ import annotations

import json

import click
from rich.console import Console
from rich.table import Table

from hanzo_cli.auth import get_client

console = Console()


@click.group()
def iam() -> None:
    """Manage Hanzo IAM — users, orgs, apps, passwords."""


# =========================================================================
# Users
# =========================================================================


@iam.command("users")
def list_users() -> None:
    """List all users in the organization."""
    client = get_client()
    try:
        users = client.get_users()
    finally:
        client.close()

    if not users:
        console.print("[yellow]No users found.[/yellow]")
        return

    table = Table(title=f"Users ({len(users)})")
    table.add_column("Name", style="cyan")
    table.add_column("Display Name", style="white")
    table.add_column("Email", style="white")
    table.add_column("Admin", style="yellow")
    table.add_column("Online", style="green")

    for u in users:
        table.add_row(
            u.name,
            u.display_name or "—",
            u.email or "—",
            "yes" if u.is_admin else "",
            "yes" if u.is_online else "",
        )

    console.print(table)


@iam.command("user")
@click.argument("name")
def get_user(name: str) -> None:
    """Get details for a specific user."""
    client = get_client()
    try:
        user = client.get_user(name)
    finally:
        client.close()

    table = Table(title=f"User: {user.owner}/{user.name}")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("ID", user.id or "—")
    table.add_row("Owner", user.owner)
    table.add_row("Name", user.name)
    table.add_row("Display Name", user.display_name or "—")
    table.add_row("Email", user.email or "—")
    table.add_row("Phone", user.phone or "—")
    table.add_row("Type", user.type or "—")
    table.add_row("Admin", "yes" if user.is_admin else "no")
    table.add_row("Deleted", "yes" if user.is_deleted else "no")
    table.add_row("Forbidden", "yes" if user.is_forbidden else "no")
    table.add_row("Online", "yes" if user.is_online else "no")
    table.add_row("Email Verified", "yes" if user.email_verified else "no")
    table.add_row("Balance", str(user.balance))
    table.add_row("Created", user.created_time or "—")
    table.add_row("Updated", user.updated_time or "—")

    if user.roles:
        table.add_row("Roles", ", ".join(user.roles))
    if user.groups:
        table.add_row("Groups", ", ".join(user.groups))

    console.print(table)


# =========================================================================
# Password Management
# =========================================================================


@iam.command("set-password")
@click.argument("user")
@click.argument("password", required=False)
def set_password(user: str, password: str | None) -> None:
    """Set a user's password. Prompts if password not given."""
    if not password:
        password = click.prompt("New password", hide_input=True, confirmation_prompt=True)

    client = get_client()
    org = client.config.organization

    try:
        result = client.set_password(
            user_owner=org,
            user_name=user,
            new_password=password,
        )
    finally:
        client.close()

    status = result.get("status", "unknown")
    if status == "ok":
        console.print(f"[green]Password set for {org}/{user}.[/green]")
    else:
        msg = result.get("msg", "Unknown error")
        console.print(f"[red]Failed:[/red] {msg}")
        raise SystemExit(1)


# =========================================================================
# Organizations
# =========================================================================


@iam.command("orgs")
def list_orgs() -> None:
    """List all organizations."""
    client = get_client()
    try:
        orgs = client.get_organizations()
    finally:
        client.close()

    if not orgs:
        console.print("[yellow]No organizations found.[/yellow]")
        return

    table = Table(title=f"Organizations ({len(orgs)})")
    table.add_column("Name", style="cyan")
    table.add_column("Display Name", style="white")
    table.add_column("Website", style="white")

    for o in orgs:
        table.add_row(
            o.get("name", "—"),
            o.get("displayName", "—"),
            o.get("websiteUrl", "—"),
        )

    console.print(table)


# =========================================================================
# Applications
# =========================================================================


@iam.command("apps")
def list_apps() -> None:
    """List all applications."""
    client = get_client()
    try:
        apps = client.get_applications()
    finally:
        client.close()

    if not apps:
        console.print("[yellow]No applications found.[/yellow]")
        return

    table = Table(title=f"Applications ({len(apps)})")
    table.add_column("Owner", style="white")
    table.add_column("Name", style="cyan")
    table.add_column("Display Name", style="white")
    table.add_column("Client ID", style="dim")
    table.add_column("Redirect URIs", style="white")

    for app in apps:
        uris = ", ".join(app.redirect_uris) if app.redirect_uris else "—"
        table.add_row(
            app.owner,
            app.name,
            app.display_name or "—",
            app.client_id[:16] + "..." if len(app.client_id) > 16 else app.client_id,
            uris,
        )

    console.print(table)


@iam.command("sync-app")
@click.argument("name")
@click.option("--init-data", is_flag=True, help="Initialize default redirect URIs.")
def sync_app(name: str, init_data: bool) -> None:
    """Sync an application's redirect URIs.

    Reads the application, optionally initializes default URIs,
    and updates it back.
    """
    client = get_client()
    try:
        # Get all apps and find the one we want
        apps = client.get_applications()
        target = None
        for app in apps:
            if app.name == name:
                target = app
                break

        if target is None:
            console.print(f"[red]Application '{name}' not found.[/red]")
            raise SystemExit(1)

        if init_data:
            # Add standard development redirect URIs if not present
            default_uris = [
                "http://localhost:3000/callback",
                "http://localhost:3000/api/auth/callback/hanzo",
                "http://localhost:8399/callback",
            ]
            existing = set(target.redirect_uris)
            added = []
            for uri in default_uris:
                if uri not in existing:
                    target.redirect_uris.append(uri)
                    added.append(uri)

            if added:
                result = client.update_application(target)
                console.print(f"[green]Added {len(added)} redirect URIs to {name}:[/green]")
                for uri in added:
                    console.print(f"  + {uri}")
            else:
                console.print(f"All default URIs already present in {name}.")
        else:
            console.print(f"Application: {target.owner}/{target.name}")
            console.print(f"Client ID: {target.client_id}")
            console.print(f"Redirect URIs:")
            for uri in target.redirect_uris:
                console.print(f"  - {uri}")
    finally:
        client.close()
