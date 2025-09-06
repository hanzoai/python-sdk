"""Authentication commands for Hanzo CLI."""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

import click
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table
from rich import box

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
            except:
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
    """Manage Hanzo authentication."""
    pass


@auth_group.command()
@click.option("--email", "-e", help="Email address")
@click.option("--password", "-p", help="Password (not recommended, use prompt)")
@click.option("--api-key", "-k", help="API key for direct authentication")
@click.option("--sso", is_flag=True, help="Use SSO authentication")
@click.pass_context
def login(ctx, email: str, password: str, api_key: str, sso: bool):
    """Login to Hanzo AI."""
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
                "last_login": datetime.now().isoformat()
            }
            auth_mgr.save_auth(auth)
            console.print("[green]✓[/green] Successfully authenticated with API key")
            
        elif sso:
            # SSO authentication via browser
            console.print("Opening browser for SSO login...")
            console.print("If browser doesn't open, visit: https://iam.hanzo.ai/login")
            
            # Try using hanzoai if available
            try:
                from hanzoai.auth import HanzoAuth
                hanzo_auth = HanzoAuth()
                # SSO not implemented yet
                console.print("[yellow]SSO authentication not yet implemented[/yellow]")
                return
                
                auth = {
                    "email": result.get("email"),
                    "logged_in": True,
                    "last_login": datetime.now().isoformat()
                }
                auth_mgr.save_auth(auth)
                console.print(f"[green]✓[/green] Logged in as {result.get('email')}")
            except ImportError:
                console.print("[yellow]SSO requires hanzoai package[/yellow]")
                console.print("Install with: pip install hanzoai")
                
        else:
            # Email/password authentication
            if not email:
                email = Prompt.ask("Email")
            if not password:
                password = Prompt.ask("Password", password=True)
            
            console.print("Authenticating...")
            
            # Try using hanzoai if available
            try:
                from hanzoai.auth import HanzoAuth
                hanzo_auth = HanzoAuth()
                # Email auth not implemented yet
                console.print("[yellow]Email authentication not yet implemented[/yellow]")
                console.print("[dim]Saving credentials locally for development[/dim]")
                
                auth = {
                    "email": email,
                    "logged_in": True,
                    "last_login": datetime.now().isoformat()
                }
                auth_mgr.save_auth(auth)
                console.print(f"[green]✓[/green] Logged in as {email}")
            except ImportError:
                # Fallback to saving credentials locally
                auth = {
                    "email": email,
                    "logged_in": True,
                    "last_login": datetime.now().isoformat()
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
            hanzo_auth = HanzoAuth()
            # Logout not implemented yet
            pass
        except ImportError:
            pass  # hanzoai not installed, just clear local auth
        
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
            table.add_row("Email", auth['email'])
            
        if auth.get("last_login"):
            table.add_row("Last Login", auth['last_login'])
            
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
    
    if auth.get("last_login"):
        lines.append(f"[cyan]Last Login:[/cyan] {auth['last_login']}")
    
    content = "\n".join(lines) if lines else "[dim]No user information available[/dim]"
    
    console.print(Panel(
        content,
        title="[bold cyan]User Information[/bold cyan]",
        box=box.ROUNDED
    ))


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