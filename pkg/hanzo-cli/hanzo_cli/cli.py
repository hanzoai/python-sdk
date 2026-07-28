"""Hanzo CLI — unified command-line interface for the Hanzo platform.

Usage:
    hanzo --version
    hanzo login [--no-browser] [--port N]
    hanzo logout
    hanzo whoami
    hanzo iam <subcommand>
    hanzo kms <subcommand>
    hanzo paas <subcommand>
    hanzo s3 <subcommand>
    hanzo k8s <subcommand | kubectl args>
"""

from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from hanzo_cli import __version__
from hanzo_cli.auth import (
    browser_login,
    get_token_info,
    verify_token,
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
@click.option(
    "--no-browser",
    is_flag=True,
    help="Print the sign-in URL instead of opening a browser.",
)
@click.option(
    "--port",
    default=None,
    type=int,
    help=(
        "Loopback callback port. Must be one registered on the IAM application"
        " — iam matches redirect_uri by exact string."
    ),
)
@click.pass_context
def login(ctx: click.Context, no_browser: bool, port: int | None) -> None:
    """Authenticate with Hanzo IAM (OAuth2 authorization code + PKCE).

    Password login is deliberately absent: iam's password grant requires client
    authentication (it answers 401 invalid_client without a secret), and a CLI
    cannot hold a secret. The device-code grant would be the right answer for a
    headless box, but no PUBLIC client is registered, so it 401s for every
    client_id today. --no-browser prints the URL for you to open elsewhere.
    """
    try:
        token_data = browser_login(port=port, open_browser=not no_browser)
    except Exception as e:
        console.print(f"[red]Login failed:[/red] {e}")
        raise SystemExit(1) from e

    result = verify_token()
    claims = result.claims
    console.print("[green]Logged in.[/green]")
    console.print(f"  user:  {claims.get('email') or claims.get('sub')}")
    console.print(f"  org:   {claims.get('owner') or token_data.get('organization')}")
    console.print(f"  token: verified, stored in {token_data.get('stored_in')}")


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

    # Identity comes from a VERIFIED token. The previous version decoded with
    # verify_signature=False and printed whatever the token claimed, so a
    # forged file made `whoami` report an attacker-chosen identity as fact.
    result = verify_token()
    table.add_row("Token", "[green]verified[/green]" if result.valid
                  else f"[red]INVALID[/red] ({result.reason}: {result.detail})")
    if result.valid:
        claims = result.claims
        table.add_row("User", claims.get("name") or claims.get("sub", "—"))
        table.add_row("Email", claims.get("email", "—"))
        table.add_row("Owner", claims.get("owner", "—"))

    login_time = token_data.get("login_time")
    if login_time:
        from datetime import datetime, timezone

        dt = datetime.fromtimestamp(login_time, tz=timezone.utc)
        table.add_row("Login Time", dt.isoformat())

    console.print(table)


# =========================================================================
# Register subgroups
# =========================================================================

from hanzo_cli.bot.commands import bot  # noqa: E402
from hanzo_cli.iam.commands import iam  # noqa: E402
from hanzo_cli.k8s.commands import k8s  # noqa: E402
from hanzo_cli.kms.commands import kms  # noqa: E402
from hanzo_cli.paas.commands import deploy, paas  # noqa: E402
from hanzo_cli.s3.commands import s3  # noqa: E402

main.add_command(bot)
main.add_command(iam)
main.add_command(k8s)
main.add_command(kms)
main.add_command(paas)
main.add_command(s3)

# Top-level aliases — `hanzo deploy` = `hanzo paas deploy`
main.add_command(deploy)


if __name__ == "__main__":
    main()
