"""Hanzo CLI — unified command-line interface for the Hanzo platform.

Usage:
    hanzo --version
    hanzo login [--no-browser] [--port N]
    hanzo logout
    hanzo whoami
    hanzo iam <subcommand>
    hanzo kms <subcommand>
    hanzo paas <subcommand>
"""

from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from hanzo_cli import __version__
from hanzo_cli.auth import (
    browser_login,
    get_token_info,
    password_login,
)
from hanzo_cli.auth import (
    logout as do_logout,
)

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="hanzo")
@click.pass_context
def main(ctx: click.Context) -> None:
    """Hanzo CLI — manage IAM, secrets, and deployments."""
    ctx.ensure_object(dict)


# =========================================================================
# Auth commands
# =========================================================================


@main.command()
@click.option("--no-browser", is_flag=True, help="Use password login instead of browser OAuth.")
@click.option("--port", default=8399, help="Local callback port for browser login.")
@click.pass_context
def login(ctx: click.Context, no_browser: bool, port: int) -> None:
    """Authenticate with Hanzo IAM."""
    try:
        if no_browser:
            token_data = password_login()
        else:
            token_data = browser_login(port=port)

        console.print("[green]Logged in successfully.[/green]")
        if token_data.get("access_token"):
            # Decode the token subject for display
            at = token_data["access_token"]
            console.print("Token stored at ~/.hanzo/auth/token.json")
    except Exception as e:
        console.print(f"[red]Login failed:[/red] {e}")
        raise SystemExit(1)


@main.command()
def logout() -> None:
    """Clear stored credentials."""
    do_logout()
    console.print("Logged out. Token removed.")


@main.command()
def whoami() -> None:
    """Show current authentication status."""
    token_data = get_token_info()
    if not token_data:
        console.print("[yellow]Not logged in.[/yellow] Run 'hanzo login'.")
        raise SystemExit(1)

    table = Table(title="Current Session")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Server", token_data.get("server_url", "—"))
    table.add_row("Organization", token_data.get("organization", "—"))
    table.add_row("Application", token_data.get("application", "—"))
    table.add_row("Client ID", token_data.get("client_id", "—"))

    # Try to decode the token for user info
    access_token = token_data.get("access_token", "")
    if access_token:
        try:
            import jwt

            # Decode without verification just to show user info
            claims = jwt.decode(access_token, options={"verify_signature": False})
            table.add_row("User", claims.get("name", claims.get("sub", "—")))
            table.add_row("Email", claims.get("email", "—"))
            table.add_row("Owner", claims.get("owner", "—"))
        except Exception:
            table.add_row("Token", f"{access_token[:20]}...")

    login_time = token_data.get("login_time")
    if login_time:
        from datetime import datetime, timezone

        dt = datetime.fromtimestamp(login_time, tz=timezone.utc)
        table.add_row("Login Time", dt.isoformat())

    console.print(table)


# =========================================================================
# Register subgroups
# =========================================================================

from hanzo_cli.iam.commands import iam  # noqa: E402
from hanzo_cli.kms.commands import kms  # noqa: E402
from hanzo_cli.paas.commands import deploy, paas  # noqa: E402

main.add_command(iam)
main.add_command(kms)
main.add_command(paas)

# Top-level aliases — `hanzo deploy` = `hanzo paas deploy`
main.add_command(deploy)


if __name__ == "__main__":
    main()
