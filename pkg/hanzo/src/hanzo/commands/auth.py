"""Authentication commands for Hanzo CLI."""

import os
import json
import secrets
import threading
import webbrowser
from typing import Optional
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse, urlencode

import click
from rich import box
from rich.panel import Panel
from rich.table import Table

from ..utils.output import console

# OAuth constants
HANZO_IAM_URL = "https://hanzo.id"
HANZO_CLIENT_ID = "app-hanzo"
CALLBACK_PORT = 1456
CALLBACK_PATH = "/callback"
CALLBACK_URI = f"http://localhost:{CALLBACK_PORT}{CALLBACK_PATH}"


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
        return bool(
            auth.get("api_key")
            or auth.get("logged_in")
            or auth.get("token")
            or auth.get("tokens", {}).get("access_token")
        )

    def get_api_key(self) -> Optional[str]:
        """Get API key or access token."""
        if os.getenv("HANZO_API_KEY"):
            return os.getenv("HANZO_API_KEY")
        auth = self.load_auth()
        return (
            auth.get("api_key")
            or auth.get("token")
            or auth.get("tokens", {}).get("access_token")
        )


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
@click.option("--api-key", "-k", help="API key for direct authentication")
@click.option("--device-code", is_flag=True, help="Device code flow (for SSH/headless)")
@click.option("--headless", is_flag=True, help="Don't open browser automatically")
@click.pass_context
def login(ctx, api_key: str, device_code: bool, headless: bool):
    """Login to Hanzo AI.

    Opens your browser to hanzo.id where you can sign in with
    email/password, GitHub, Google, or any configured provider.

    \b
    Examples:
      hanzo auth login                # Browser login (default)
      hanzo auth login --device-code  # Device code for SSH/headless
      hanzo auth login -k sk-xxx      # Direct API key
    """
    auth_mgr = AuthManager()

    try:
        if api_key:
            auth = auth_mgr.load_auth()
            auth.update(
                {
                    "api_key": api_key,
                    "logged_in": True,
                    "last_login": datetime.now().isoformat(),
                }
            )
            auth_mgr.save_auth(auth)
            console.print(f"You are now logged in with API key {api_key[:8]}***.")

        elif device_code:
            _login_device_code(auth_mgr, headless)

        else:
            _login_browser_oauth(auth_mgr)

    except Exception as e:
        console.print(f"[red]Login failed: {e}[/red]")


def _get_iam_url(auth_mgr: AuthManager) -> str:
    """Get the IAM URL from env or stored config."""
    existing = auth_mgr.load_auth()
    return os.getenv(
        "IAM_URL", os.getenv("HANZO_IAM_URL", existing.get("iam_url", HANZO_IAM_URL))
    )


def _decode_jwt_claims(token: str) -> dict:
    """Decode JWT payload without verification (for extracting email/name)."""
    import base64

    try:
        parts = token.split(".")
        if len(parts) < 2:
            return {}
        payload = parts[1]
        # Add padding
        payload += "=" * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception:
        return {}


def _login_browser_oauth(auth_mgr: AuthManager):
    """Browser-based OAuth login using only stdlib (like gcloud auth login)."""
    import urllib.request

    iam_url = _get_iam_url(auth_mgr)
    state = secrets.token_urlsafe(32)

    # Result container for the callback handler
    auth_result = {"code": None, "error": None}
    server_ready = threading.Event()

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path != CALLBACK_PATH:
                self.send_response(404)
                self.end_headers()
                return

            params = parse_qs(parsed.query)

            # Verify state
            if params.get("state", [None])[0] != state:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid state parameter.")
                auth_result["error"] = "Invalid state"
                return

            if "error" in params:
                self.send_response(400)
                self.end_headers()
                msg = params.get("error_description", params["error"])[0]
                self.wfile.write(msg.encode())
                auth_result["error"] = msg
                return

            auth_result["code"] = params.get("code", [None])[0]

            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h2>Authentication successful!</h2>"
                b"<p>You can close this window and return to the terminal.</p>"
                b"</body></html>"
            )

        def log_message(self, format, *args):
            pass  # Suppress server logs

    # Start local callback server
    server = HTTPServer(("localhost", CALLBACK_PORT), CallbackHandler)
    server.timeout = 120  # 2 minute timeout

    def serve():
        server_ready.set()
        server.handle_request()  # Handle exactly one request

    server_thread = threading.Thread(target=serve, daemon=True)
    server_thread.start()
    server_ready.wait()

    # Build OAuth authorize URL
    params = {
        "client_id": HANZO_CLIENT_ID,
        "redirect_uri": CALLBACK_URI,
        "response_type": "code",
        "scope": "openid profile email",
        "state": state,
    }
    authorize_url = f"{iam_url}/login/oauth/authorize?{urlencode(params)}"

    console.print("Your browser has been opened to visit:\n")
    console.print(f"    {authorize_url}\n")

    webbrowser.open(authorize_url)

    # Wait for callback
    server_thread.join(timeout=120)
    server.server_close()

    if auth_result["error"]:
        console.print(f"[red]Login failed: {auth_result['error']}[/red]")
        return

    if not auth_result["code"]:
        console.print("[red]Login timed out. Please try again.[/red]")
        return

    # Exchange authorization code for tokens
    token_url = f"{iam_url}/api/login/oauth/access_token"
    token_data = urlencode(
        {
            "client_id": HANZO_CLIENT_ID,
            "code": auth_result["code"],
            "grant_type": "authorization_code",
            "redirect_uri": CALLBACK_URI,
        }
    ).encode()

    req = urllib.request.Request(  # noqa: S310
        token_url,
        data=token_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            data = json.loads(resp.read().decode())
    except Exception as e:
        console.print(f"[red]Token exchange failed: {e}[/red]")
        return

    access_token = data.get("access_token", "")
    id_token = data.get("id_token", "")

    # Decode JWT to get user info
    claims = _decode_jwt_claims(id_token or access_token)
    user_email = claims.get("email", claims.get("name", ""))

    # Save auth
    auth = auth_mgr.load_auth()
    auth.update(
        {
            "token": access_token,
            "id_token": id_token,
            "email": user_email,
            "logged_in": True,
            "last_login": datetime.now().isoformat(),
        }
    )
    auth_mgr.save_auth(auth)

    if user_email:
        console.print(f"You are now logged in as [{user_email}].")
    else:
        console.print("You are now logged in.")
    console.print("Your credentials have been saved to: ~/.hanzo/auth.json")


def _login_device_code(auth_mgr: AuthManager, headless: bool):
    """Device code login flow (for SSH/headless)."""
    import time
    import urllib.request

    iam_url = _get_iam_url(auth_mgr)

    # Step 1: Request device code
    device_req_data = json.dumps(
        {
            "client_id": HANZO_CLIENT_ID,
            "scope": "openid profile email",
        }
    ).encode()

    req = urllib.request.Request(  # noqa: S310
        f"{iam_url}/api/device/code",
        data=device_req_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            data = json.loads(resp.read().decode())
    except Exception as e:
        console.print(f"[red]Failed to request device code: {e}[/red]")
        return

    device_code = data["device_code"]
    user_code = data["user_code"]
    verification_url = data.get("verification_uri", f"{iam_url}/device")
    verification_url_complete = data.get(
        "verification_uri_complete", f"{verification_url}?user_code={user_code}"
    )
    expires_in = data.get("expires_in", 300)
    interval = data.get("interval", 5)

    # Step 2: Show instructions
    console.print(f"\nTo sign in, visit: [cyan]{verification_url}[/cyan]")
    console.print(f"Enter code: [bold yellow]{user_code}[/bold yellow]\n")

    if not headless:
        try:
            webbrowser.open(verification_url_complete)
            console.print("[dim](Browser opened automatically)[/dim]\n")
        except Exception:
            pass

    # Step 3: Poll for completion
    start_time = time.time()
    while time.time() - start_time < expires_in:
        time.sleep(interval)

        poll_data = json.dumps(
            {
                "client_id": HANZO_CLIENT_ID,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            }
        ).encode()

        poll_req = urllib.request.Request(  # noqa: S310
            f"{iam_url}/api/login/oauth/access_token",
            data=poll_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(poll_req, timeout=30) as resp:  # noqa: S310
                token_data = json.loads(resp.read().decode())

            access_token = token_data.get("access_token", "")
            id_token = token_data.get("id_token", "")

            claims = _decode_jwt_claims(id_token or access_token)
            user_email = claims.get("email", claims.get("name", ""))

            auth = auth_mgr.load_auth()
            auth.update(
                {
                    "token": access_token,
                    "id_token": id_token,
                    "email": user_email,
                    "logged_in": True,
                    "last_login": datetime.now().isoformat(),
                }
            )
            auth_mgr.save_auth(auth)

            if user_email:
                console.print(f"You are now logged in as [{user_email}].")
            else:
                console.print("You are now logged in.")
            return

        except urllib.error.HTTPError as e:
            if e.code == 400:
                try:
                    error_data = json.loads(e.read().decode())
                    error = error_data.get("error", "")
                    if error == "authorization_pending":
                        continue
                    elif error == "slow_down":
                        interval += 5
                        continue
                    elif error == "expired_token":
                        console.print(
                            "[red]Device code expired. Please try again.[/red]"
                        )
                        return
                    elif error == "access_denied":
                        console.print("[red]Authentication denied.[/red]")
                        return
                except Exception:
                    continue
            else:
                continue
        except Exception:
            continue

    console.print("[red]Authentication timed out. Please try again.[/red]")


@auth_group.command()
@click.pass_context
def logout(ctx):
    """Logout from Hanzo AI."""
    auth_mgr = AuthManager()

    if not auth_mgr.is_authenticated():
        console.print("[yellow]Not logged in[/yellow]")
        return

    try:
        # Clear login state but preserve IAM config
        auth = auth_mgr.load_auth()
        preserved = {}
        for key in (
            "iam_url",
            "iam_client_id",
            "iam_client_secret",
            "iam_org",
            "iam_app",
        ):
            if key in auth:
                preserved[key] = auth[key]
        auth_mgr.save_auth(preserved)

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
        elif auth.get("token") or auth.get("tokens", {}).get("access_token"):
            table.add_row("Method", "IAM OAuth")
            token = auth.get("token") or auth.get("tokens", {}).get("access_token", "")
            if token:
                claims = _decode_jwt_claims(token)
                email = claims.get("email", "")
                if email:
                    table.add_row("User", email)
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
    lines = []

    # Try to get email from stored data or JWT claims
    email = auth.get("email", "")
    if not email:
        token = auth.get("token") or auth.get("tokens", {}).get("access_token", "")
        if token:
            claims = _decode_jwt_claims(token)
            email = claims.get("email", "")
            name = claims.get("displayName") or claims.get("name", "")
            if name:
                lines.append(f"[cyan]Name:[/cyan] {name}")

    if email:
        lines.append(f"[cyan]Email:[/cyan] {email}")

    if os.getenv("HANZO_API_KEY"):
        lines.append("[cyan]Auth:[/cyan] API key (env)")
    elif auth.get("api_key"):
        lines.append(f"[cyan]Auth:[/cyan] API key ({auth['api_key'][:8]}...)")
    elif auth.get("token") or auth.get("tokens", {}).get("access_token"):
        lines.append("[cyan]Auth:[/cyan] IAM OAuth")

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


# ============================================================================
# Context management  (org / project / env selection)
# ============================================================================


@auth_group.group(name="context", invoke_without_command=True)
@click.pass_context
def context_group(ctx):
    """Manage active org/project/env context.

    \b
    Examples:
      hanzo auth context                    # Show current context
      hanzo auth context set --org hanzo    # Set active org/project/env
      hanzo auth context list               # List available orgs & projects
    """
    if ctx.invoked_subcommand is None:
        _print_context()


@context_group.command(name="show")
def context_show():
    """Show current context."""
    _print_context()


def _print_context():
    from ..utils.api_client import load_context

    ctx = load_context()
    if not ctx:
        console.print("[yellow]No context set.[/yellow]")
        console.print(
            "[dim]Run 'hanzo auth context set --org ORG --project PROJECT --env ENV'[/dim]"
        )
        return

    table = Table(title="Active Context", box=box.ROUNDED)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    for key in (
        "org_id",
        "org_name",
        "project_id",
        "project_name",
        "env_id",
        "env_name",
    ):
        if ctx.get(key):
            label = key.replace("_", " ").title()
            table.add_row(label, ctx[key])

    console.print(table)


@context_group.command(name="set")
@click.option("--org", "-o", required=True, help="Organization ID or name")
@click.option("--project", "-p", help="Project ID or name")
@click.option("--env", "-e", help="Environment ID or name")
def context_set(org: str, project: str, env: str):
    """Set active org/project/env context.

    \b
    Examples:
      hanzo auth context set --org hanzo
      hanzo auth context set --org hanzo --project myapp --env development
    """
    from ..utils.api_client import (
        PaaSClient,
        env_url,
        org_url,
        project_url,
        save_context,
    )

    try:
        client = PaaSClient()
    except SystemExit:
        return

    ctx = {}

    # Resolve org
    with console.status("Resolving organization..."):
        data = client.get(org_url())
        if data is None:
            return

    orgs = data if isinstance(data, list) else data.get("orgs", data.get("data", []))
    matched_org = None
    for o in orgs:
        oid = o.get("_id") or o.get("iid") or o.get("id", "")
        oname = o.get("name", "")
        if org in (oid, oname):
            matched_org = o
            break

    if not matched_org:
        console.print(f"[red]Organization '{org}' not found.[/red]")
        return

    ctx["org_id"] = (
        matched_org.get("_id") or matched_org.get("iid") or matched_org.get("id")
    )
    ctx["org_name"] = matched_org.get("name", org)
    console.print(f"[green]✓[/green] Organization: {ctx['org_name']}")

    # Resolve project (if given)
    if project:
        with console.status("Resolving project..."):
            data = client.get(project_url(ctx["org_id"]))
            if data is None:
                save_context(ctx)
                return

        projects = (
            data
            if isinstance(data, list)
            else data.get("projects", data.get("data", []))
        )
        matched_proj = None
        for p in projects:
            pid = p.get("_id") or p.get("iid") or p.get("id", "")
            pname = p.get("name", "")
            if project in (pid, pname):
                matched_proj = p
                break

        if not matched_proj:
            console.print(
                f"[yellow]Project '{project}' not found. Saving org-only context.[/yellow]"
            )
            save_context(ctx)
            return

        ctx["project_id"] = (
            matched_proj.get("_id") or matched_proj.get("iid") or matched_proj.get("id")
        )
        ctx["project_name"] = matched_proj.get("name", project)
        console.print(f"[green]✓[/green] Project: {ctx['project_name']}")

    # Resolve env (if given and project was resolved)
    if env and ctx.get("project_id"):
        with console.status("Resolving environment..."):
            data = client.get(env_url(ctx["org_id"], ctx["project_id"]))
            if data is None:
                save_context(ctx)
                return

        envs = (
            data
            if isinstance(data, list)
            else data.get("environments", data.get("data", []))
        )
        matched_env = None
        for e in envs:
            eid = e.get("_id") or e.get("iid") or e.get("id", "")
            ename = e.get("name", "")
            if env in (eid, ename):
                matched_env = e
                break

        if not matched_env:
            console.print(
                f"[yellow]Environment '{env}' not found. Saving org+project context.[/yellow]"
            )
            save_context(ctx)
            return

        ctx["env_id"] = (
            matched_env.get("_id") or matched_env.get("iid") or matched_env.get("id")
        )
        ctx["env_name"] = matched_env.get("name", env)
        console.print(f"[green]✓[/green] Environment: {ctx['env_name']}")

    save_context(ctx)
    console.print("[green]✓[/green] Context saved to ~/.hanzo/context.json")


@context_group.command(name="list")
def context_list():
    """List available orgs, projects, and environments."""
    from ..utils.api_client import (
        PaaSClient,
        env_url,
        org_url,
        project_url,
        load_context,
    )

    try:
        client = PaaSClient()
    except SystemExit:
        return

    current = load_context()

    # List orgs
    with console.status("Fetching organizations..."):
        data = client.get(org_url())
        if data is None:
            return

    orgs = data if isinstance(data, list) else data.get("orgs", data.get("data", []))

    table = Table(title="Organizations", box=box.ROUNDED)
    table.add_column("", style="green", width=2)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")

    for o in orgs:
        oid = o.get("_id") or o.get("iid") or o.get("id", "")
        oname = o.get("name", "")
        active = "●" if oid == current.get("org_id") else ""
        table.add_row(active, oid, oname)

    console.print(table)

    # List projects for active org
    if current.get("org_id"):
        with console.status("Fetching projects..."):
            data = client.get(project_url(current["org_id"]))

        if data:
            projects = (
                data
                if isinstance(data, list)
                else data.get("projects", data.get("data", []))
            )
            if projects:
                ptable = Table(
                    title=f"Projects in {current.get('org_name', current['org_id'])}",
                    box=box.ROUNDED,
                )
                ptable.add_column("", style="green", width=2)
                ptable.add_column("ID", style="cyan")
                ptable.add_column("Name", style="white")

                for p in projects:
                    pid = p.get("_id") or p.get("iid") or p.get("id", "")
                    pname = p.get("name", "")
                    active = "●" if pid == current.get("project_id") else ""
                    ptable.add_row(active, pid, pname)

                console.print(ptable)

    # List envs for active project
    if current.get("org_id") and current.get("project_id"):
        with console.status("Fetching environments..."):
            data = client.get(env_url(current["org_id"], current["project_id"]))

        if data:
            envs = (
                data
                if isinstance(data, list)
                else data.get("environments", data.get("data", []))
            )
            if envs:
                etable = Table(
                    title=f"Environments in {current.get('project_name', current['project_id'])}",
                    box=box.ROUNDED,
                )
                etable.add_column("", style="green", width=2)
                etable.add_column("ID", style="cyan")
                etable.add_column("Name", style="white")

                for e in envs:
                    eid = e.get("_id") or e.get("iid") or e.get("id", "")
                    ename = e.get("name", "")
                    active = "●" if eid == current.get("env_id") else ""
                    etable.add_row(active, eid, ename)

                console.print(etable)
