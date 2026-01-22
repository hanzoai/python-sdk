"""Authentication commands for Hanzo CLI."""

import os
import json
from typing import Optional
from pathlib import Path
from datetime import datetime

import click
from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

from ..utils.output import console


class AuthManager:
    """Manage Hanzo authentication."""

    def __init__(self):
        self.config_dir = Path.home() / ".hanzo"
        self.auth_file = self.config_dir / "auth.json"

    def load_auth(self) -> dict:
        """Load authentication data."""
        if self.auth_file.exists():
            try:
                return json.loads(self.auth_file.read_text())
            except Exception:
                pass
        return {}

    def save_auth(self, auth: dict):
        """Save authentication data."""
        self.config_dir.mkdir(exist_ok=True)
        self.auth_file.write_text(json.dumps(auth, indent=2))

    def is_authenticated(self) -> bool:
        """Check if authenticated."""
        if os.getenv("HANZO_API_KEY"):
            return True
        auth = self.load_auth()
        return bool(auth.get("api_key") or auth.get("logged_in"))

    def get_api_key(self) -> Optional[str]:
        """Get API key."""
        if os.getenv("HANZO_API_KEY"):
            return os.getenv("HANZO_API_KEY")
        auth = self.load_auth()
        return auth.get("api_key")


@click.group(name="auth")
def auth_group():
    """Manage Hanzo authentication.

    \b
    Login & Identity:
      hanzo auth login       # Login to Hanzo
      hanzo auth logout      # Logout
      hanzo auth status      # Show auth status
      hanzo auth whoami      # Show current user

    \b
    For managing users, orgs, teams, and API keys:
      hanzo iam users list   # List users
      hanzo iam orgs list    # List organizations
      hanzo iam teams list   # List teams
      hanzo iam keys list    # List API keys
    """
    pass


@auth_group.command()
@click.option("--email", "-e", help="Email address")
@click.option("--password", "-p", help="Password (not recommended, use prompt)")
@click.option("--api-key", "-k", help="API key for direct authentication")
@click.option("--web", "-w", is_flag=True, help="Login via browser (device code flow)")
@click.option("--headless", is_flag=True, help="Headless mode - don't open browser")
@click.pass_context
def login(ctx, email: str, password: str, api_key: str, web: bool, headless: bool):
    """Login to Hanzo AI.

    \b
    Examples:
      hanzo auth login              # Interactive device code flow
      hanzo auth login --web        # Open browser for authentication
      hanzo auth login --headless   # Device code without opening browser
      hanzo auth login -k sk-xxx    # Direct API key authentication
      hanzo auth login -e user@example.com  # Email/password login
    """
    import asyncio

    auth_mgr = AuthManager()

    # Check if already authenticated
    if auth_mgr.is_authenticated():
        console.print("[yellow]Already authenticated[/yellow]")
        auth = auth_mgr.load_auth()
        if auth.get("email"):
            console.print(f"Logged in as: {auth['email']}")
        return

    try:
        if api_key:
            # Direct API key authentication
            console.print("Authenticating with API key...")
            auth = {
                "api_key": api_key,
                "logged_in": True,
                "last_login": datetime.now().isoformat(),
            }
            auth_mgr.save_auth(auth)
            console.print("[green]✓[/green] Successfully authenticated with API key")

        elif web or (not email and not password and not api_key):
            # Device code flow - works on remote/headless systems
            console.print("[cyan]Starting device code authentication...[/cyan]")

            try:
                from hanzoai.auth import HanzoAuth

                async def do_device_auth():
                    hanzo_auth = HanzoAuth()
                    return await hanzo_auth.login_with_device_code(
                        open_browser=not headless
                    )

                result = asyncio.run(do_device_auth())

                auth = {
                    "token": result.get("token"),
                    "email": result.get("email"),
                    "logged_in": True,
                    "last_login": datetime.now().isoformat(),
                }
                auth_mgr.save_auth(auth)

                email = result.get("email", "user")
                console.print(f"[green]✓[/green] Logged in as {email}")

            except ImportError:
                console.print("[yellow]Device auth requires hanzoai package[/yellow]")
                console.print("Install with: pip install hanzoai")
                console.print()
                console.print("[dim]Or use API key: hanzo auth login -k YOUR_KEY[/dim]")

        else:
            # Email/password authentication
            if not email:
                email = Prompt.ask("Email")
            if not password:
                password = Prompt.ask("Password", password=True)

            console.print("Authenticating...")

            try:
                from hanzoai.auth import HanzoAuth

                async def do_email_auth():
                    hanzo_auth = HanzoAuth()
                    return await hanzo_auth.login(email, password)

                result = asyncio.run(do_email_auth())

                auth = {
                    "email": email,
                    "token": result.get("token"),
                    "logged_in": True,
                    "last_login": datetime.now().isoformat(),
                }
                auth_mgr.save_auth(auth)
                console.print(f"[green]✓[/green] Logged in as {email}")

            except ImportError:
                # Fallback to saving credentials locally
                auth = {
                    "email": email,
                    "logged_in": True,
                    "last_login": datetime.now().isoformat(),
                }
                auth_mgr.save_auth(auth)
                console.print(f"[green]✓[/green] Credentials saved for {email}")

    except Exception as e:
        console.print(f"[red]Login failed: {e}[/red]")


@auth_group.command()
@click.pass_context
def logout(ctx):
    """Logout from Hanzo AI."""
    auth_mgr = AuthManager()

    if not auth_mgr.is_authenticated():
        console.print("[yellow]Not logged in[/yellow]")
        return

    try:
        # Try using hanzoai if available
        try:
            from hanzoai.auth import HanzoAuth
            _ = HanzoAuth  # Available for future remote logout
        except ImportError:
            pass  # Local-only auth

        # Clear local auth
        auth_mgr.save_auth({})

        console.print("[green]✓[/green] Logged out successfully")

    except Exception as e:
        console.print(f"[red]Logout failed: {e}[/red]")


@auth_group.command()
@click.pass_context
def status(ctx):
    """Show authentication status."""
    auth_mgr = AuthManager()

    # Create status table
    table = Table(title="Authentication Status", box=box.ROUNDED)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    if auth_mgr.is_authenticated():
        auth = auth_mgr.load_auth()

        table.add_row("Status", "✅ Authenticated")

        # Show auth method
        if os.getenv("HANZO_API_KEY"):
            table.add_row("Method", "Environment Variable")
            api_key = os.getenv("HANZO_API_KEY")
            table.add_row("API Key", f"{api_key[:8]}...{api_key[-4:]}")
        elif auth.get("api_key"):
            table.add_row("Method", "API Key")
            table.add_row("API Key", f"{auth['api_key'][:8]}...")
        elif auth.get("email"):
            table.add_row("Method", "Email/Password")
            table.add_row("Email", auth["email"])

        if auth.get("last_login"):
            table.add_row("Last Login", auth["last_login"])

        # Show current org if set
        if auth.get("current_org"):
            table.add_row("Organization", auth["current_org"])

    else:
        table.add_row("Status", "❌ Not authenticated")
        table.add_row("Action", "Run 'hanzo auth login' to authenticate")

    console.print(table)


@auth_group.command()
def whoami():
    """Show current user information."""
    auth_mgr = AuthManager()

    if not auth_mgr.is_authenticated():
        console.print("[yellow]Not logged in[/yellow]")
        console.print("[dim]Run 'hanzo auth login' to authenticate[/dim]")
        return

    auth = auth_mgr.load_auth()

    # Create user info panel
    lines = []

    if auth.get("email"):
        lines.append(f"[cyan]Email:[/cyan] {auth['email']}")

    if os.getenv("HANZO_API_KEY"):
        lines.append("[cyan]API Key:[/cyan] Set via environment")
    elif auth.get("api_key"):
        lines.append(f"[cyan]API Key:[/cyan] {auth['api_key'][:8]}...")

    if auth.get("current_org"):
        lines.append(f"[cyan]Organization:[/cyan] {auth['current_org']}")

    if auth.get("last_login"):
        lines.append(f"[cyan]Last Login:[/cyan] {auth['last_login']}")

    content = "\n".join(lines) if lines else "[dim]No user information available[/dim]"

    console.print(
        Panel(content, title="[bold cyan]User Information[/bold cyan]", box=box.ROUNDED)
    )


@auth_group.command(name="set-key")
@click.argument("api_key")
def set_key(api_key: str):
    """Set API key for authentication."""
    auth_mgr = AuthManager()

    auth = auth_mgr.load_auth()
    auth["api_key"] = api_key
    auth["logged_in"] = True
    auth["last_login"] = datetime.now().isoformat()

    auth_mgr.save_auth(auth)

    console.print("[green]✓[/green] API key saved successfully")
    console.print("[dim]You can now use Hanzo Cloud services[/dim]")
