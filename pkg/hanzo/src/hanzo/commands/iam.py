"""Hanzo IAM - Identity and Access Management CLI.

Real API calls to Casdoor-based IAM at hanzo.id.
Manages users, organizations, providers, roles, and applications.
"""

import os
import json

import click
import httpx
from rich import box
from rich.panel import Panel
from rich.table import Table

from ..utils.output import console

# ============================================================================
# IAM Client Helper
# ============================================================================


def _get_iam_url() -> str:
    return os.getenv("IAM_URL", os.getenv("HANZO_IAM_URL", "https://hanzo.id"))


def _get_iam_credentials() -> tuple[str, str]:
    """Get client_id and client_secret from env or defaults."""
    client_id = os.getenv("IAM_CLIENT_ID", os.getenv("HANZO_IAM_CLIENT_ID", ""))
    client_secret = os.getenv(
        "IAM_CLIENT_SECRET", os.getenv("HANZO_IAM_CLIENT_SECRET", "")
    )
    if not client_id or not client_secret:
        # Try loading from auth file
        from pathlib import Path

        auth_file = Path.home() / ".hanzo" / "auth.json"
        if auth_file.exists():
            try:
                auth = json.loads(auth_file.read_text())
                client_id = client_id or auth.get("iam_client_id", "")
                client_secret = client_secret or auth.get("iam_client_secret", "")
            except Exception:
                pass
    return client_id, client_secret


def _iam_request(
    method: str,
    path: str,
    params: dict | None = None,
    json_body: dict | None = None,
    auth_params: bool = True,
) -> dict:
    """Make authenticated request to IAM API."""
    url = _get_iam_url().rstrip("/") + path
    client_id, client_secret = _get_iam_credentials()

    if not client_id or not client_secret:
        console.print("[red]Error:[/red] IAM credentials not configured")
        console.print("Set IAM_CLIENT_ID and IAM_CLIENT_SECRET environment variables")
        console.print("Or run: hanzo iam configure")
        raise SystemExit(1)

    if params is None:
        params = {}

    if auth_params:
        params["clientId"] = client_id
        params["clientSecret"] = client_secret

    try:
        with httpx.Client(timeout=30.0) as http:
            if method == "GET":
                resp = http.get(url, params=params)
            else:
                resp = http.post(url, params=params, json=json_body)
            resp.raise_for_status()
            return resp.json()
    except httpx.ConnectError:
        console.print(f"[red]Error:[/red] Cannot connect to IAM at {_get_iam_url()}")
        raise SystemExit(1)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]Error:[/red] IAM returned {e.response.status_code}")
        try:
            detail = e.response.json()
            console.print(f"  {detail.get('msg', detail)}")
        except Exception:
            console.print(f"  {e.response.text[:200]}")
        raise SystemExit(1)


def _check_response(data: dict, action: str) -> None:
    """Check API response and print error if failed."""
    if data.get("status") == "error":
        console.print(f"[red]Error:[/red] {data.get('msg', f'Failed to {action}')}")
        raise SystemExit(1)


# ============================================================================
# Main IAM Group
# ============================================================================


@click.group(name="iam")
def iam_group():
    """Hanzo IAM - Identity and Access Management.

    \b
    Configure:
      hanzo iam configure          # Set IAM credentials
      hanzo iam status             # Check IAM connection

    \b
    Users:
      hanzo iam users list         # List users
      hanzo iam users get NAME     # Get user details
      hanzo iam users create       # Create user
      hanzo iam users delete NAME  # Delete user

    \b
    Organizations:
      hanzo iam orgs list          # List organizations
      hanzo iam orgs get NAME      # Get organization details

    \b
    Providers:
      hanzo iam providers list     # List auth providers
      hanzo iam providers get NAME # Get provider details

    \b
    Applications:
      hanzo iam apps list          # List applications
      hanzo iam apps get NAME      # Get application details

    \b
    Roles:
      hanzo iam roles list         # List roles

    \b
    Admin:
      hanzo iam login              # Login as user (masquerade)
    """
    pass


# ============================================================================
# Configure
# ============================================================================


@iam_group.command()
@click.option("--url", "-u", help="IAM server URL (default: https://hanzo.id)")
@click.option("--client-id", "-i", help="OAuth2 client ID")
@click.option("--client-secret", "-s", help="OAuth2 client secret")
@click.option("--org", "-o", default="hanzo", help="Default organization")
def configure(url: str, client_id: str, client_secret: str, org: str):
    """Configure IAM credentials for CLI access.

    \b
    Examples:
      hanzo iam configure -i MY_CLIENT_ID -s MY_SECRET
      hanzo iam configure --url https://iam.hanzo.ai
    """
    from pathlib import Path

    from rich.prompt import Prompt

    auth_file = Path.home() / ".hanzo" / "auth.json"
    auth = {}
    if auth_file.exists():
        try:
            auth = json.loads(auth_file.read_text())
        except Exception:
            pass

    if not url:
        url = Prompt.ask("IAM URL", default=auth.get("iam_url", "https://hanzo.id"))
    if not client_id:
        client_id = Prompt.ask("Client ID", default=auth.get("iam_client_id", ""))
    if not client_secret:
        client_secret = Prompt.ask(
            "Client Secret", password=True, default=auth.get("iam_client_secret", "")
        )

    auth["iam_url"] = url
    auth["iam_client_id"] = client_id
    auth["iam_client_secret"] = client_secret
    auth["iam_org"] = org

    Path.home().joinpath(".hanzo").mkdir(exist_ok=True)
    auth_file.write_text(json.dumps(auth, indent=2))

    console.print("[green]✓[/green] IAM credentials saved to ~/.hanzo/auth.json")

    # Test connection
    try:
        os.environ["IAM_CLIENT_ID"] = client_id
        os.environ["IAM_CLIENT_SECRET"] = client_secret
        os.environ["IAM_URL"] = url
        data = _iam_request("GET", "/api/get-account", auth_params=True)
        if data.get("status") != "error":
            console.print("[green]✓[/green] Connected to IAM successfully")
        else:
            console.print(
                "[yellow]⚠[/yellow] Connected but got error: "
                + data.get("msg", "unknown")
            )
    except SystemExit:
        console.print(
            "[yellow]⚠[/yellow] Could not verify connection (credentials saved anyway)"
        )


@iam_group.command(name="status")
def iam_status():
    """Check IAM connection and credentials."""
    url = _get_iam_url()
    client_id, client_secret = _get_iam_credentials()

    table = Table(title="IAM Status", box=box.ROUNDED)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("IAM URL", url)
    table.add_row(
        "Client ID", client_id[:12] + "..." if client_id else "[red]Not set[/red]"
    )
    table.add_row(
        "Client Secret",
        "****" + client_secret[-4:] if client_secret else "[red]Not set[/red]",
    )

    if client_id and client_secret:
        try:
            data = _iam_request("GET", "/.well-known/openid-configuration")
            table.add_row("Connection", "[green]OK[/green]")
            table.add_row("Issuer", str(data.get("issuer", "unknown")))
        except SystemExit:
            table.add_row("Connection", "[red]Failed[/red]")
    else:
        table.add_row("Connection", "[yellow]No credentials[/yellow]")

    console.print(table)


# ============================================================================
# Users
# ============================================================================


@iam_group.group()
def users():
    """Manage IAM users."""
    pass


@users.command(name="list")
@click.option("--org", "-o", default="hanzo", help="Organization name")
def users_list(org: str):
    """List users in organization."""
    data = _iam_request("GET", "/api/get-users", params={"owner": org})
    _check_response(data, "list users")

    users_data = data.get("data") if isinstance(data, dict) else data
    if not users_data:
        console.print("[dim]No users found[/dim]")
        return

    table = Table(title=f"Users ({org})", box=box.ROUNDED)
    table.add_column("Username", style="cyan")
    table.add_column("Display Name", style="white")
    table.add_column("Email", style="green")
    table.add_column("Phone", style="dim")
    table.add_column("Admin", style="yellow")
    table.add_column("Status", style="white")

    for u in users_data:
        status = "🟢" if not u.get("isForbidden") and not u.get("isDeleted") else "🔴"
        admin = "✓" if u.get("isAdmin") else ""
        table.add_row(
            u.get("name", ""),
            u.get("displayName", ""),
            u.get("email", ""),
            u.get("phone", ""),
            admin,
            status,
        )

    console.print(table)
    console.print(f"[dim]Total: {len(users_data)} users[/dim]")


@users.command(name="get")
@click.argument("username")
@click.option("--org", "-o", default="hanzo", help="Organization name")
def users_get(username: str, org: str):
    """Get user details."""
    data = _iam_request("GET", "/api/get-user", params={"id": f"{org}/{username}"})
    _check_response(data, "get user")

    user = data.get("data") if isinstance(data, dict) else data
    if not user:
        console.print(f"[red]User '{username}' not found[/red]")
        return

    lines = [
        f"[cyan]Username:[/cyan] {user.get('name', '')}",
        f"[cyan]Display Name:[/cyan] {user.get('displayName', '')}",
        f"[cyan]Email:[/cyan] {user.get('email', '')}",
        f"[cyan]Phone:[/cyan] {user.get('phone', '')}",
        f"[cyan]Organization:[/cyan] {user.get('owner', '')}",
        f"[cyan]Admin:[/cyan] {'Yes' if user.get('isAdmin') else 'No'}",
        f"[cyan]Forbidden:[/cyan] {'Yes' if user.get('isForbidden') else 'No'}",
        f"[cyan]Email Verified:[/cyan] {'Yes' if user.get('emailVerified') else 'No'}",
        f"[cyan]Signup App:[/cyan] {user.get('signupApplication', '')}",
        f"[cyan]Created:[/cyan] {user.get('createdTime', '')}",
        f"[cyan]Updated:[/cyan] {user.get('updatedTime', '')}",
    ]

    # Show roles/groups if present
    if user.get("roles"):
        lines.append(f"[cyan]Roles:[/cyan] {', '.join(str(r) for r in user['roles'])}")
    if user.get("groups"):
        lines.append(
            f"[cyan]Groups:[/cyan] {', '.join(str(g) for g in user['groups'])}"
        )

    console.print(
        Panel("\n".join(lines), title=f"User: {username}", border_style="cyan")
    )


@users.command(name="create")
@click.option("--username", "-u", required=True, help="Username")
@click.option("--email", "-e", help="Email address")
@click.option("--password", "-p", help="Password")
@click.option("--name", "-n", help="Display name")
@click.option("--phone", help="Phone number")
@click.option("--org", "-o", default="hanzo", help="Organization")
@click.option("--admin", is_flag=True, help="Make admin")
def users_create(
    username: str,
    email: str,
    password: str,
    name: str,
    phone: str,
    org: str,
    admin: bool,
):
    """Create a new user."""
    user_obj = {
        "owner": org,
        "name": username,
        "displayName": name or username,
        "email": email or "",
        "phone": phone or "",
        "password": "",
        "isAdmin": admin,
        "type": "normal-user",
    }

    data = _iam_request("POST", "/api/add-user", json_body=user_obj)
    _check_response(data, "create user")

    console.print(f"[green]✓[/green] User '{username}' created in org '{org}'")
    if email:
        console.print(f"  Email: {email}")

    # Set password via set-password API (proper hashing)
    if password:
        client_id, client_secret = _get_iam_credentials()
        try:
            with httpx.Client(timeout=30.0) as http:
                resp = http.post(
                    f"{_get_iam_url().rstrip('/')}/api/set-password",
                    params={"clientId": client_id, "clientSecret": client_secret},
                    data={
                        "userOwner": org,
                        "userName": username,
                        "oldPassword": "",
                        "newPassword": password,
                    },
                )
                if resp.status_code == 200 and resp.json().get("status") == "ok":
                    console.print("[green]✓[/green] Password set")
                else:
                    console.print(
                        f"[yellow]⚠[/yellow] Password may not have been set: {resp.json().get('msg', '')}"
                    )
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Could not set password: {e}")


@users.command(name="update")
@click.argument("username")
@click.option("--email", "-e", help="New email")
@click.option("--name", "-n", help="New display name")
@click.option("--phone", help="New phone")
@click.option("--password", "-p", help="New password")
@click.option("--admin/--no-admin", default=None, help="Set admin status")
@click.option("--forbidden/--no-forbidden", default=None, help="Ban/unban user")
@click.option("--org", "-o", default="hanzo", help="Organization")
def users_update(
    username: str,
    email: str,
    name: str,
    phone: str,
    password: str,
    admin: bool,
    forbidden: bool,
    org: str,
):
    """Update user fields."""
    # First get existing user
    get_data = _iam_request("GET", "/api/get-user", params={"id": f"{org}/{username}"})
    _check_response(get_data, "get user")
    user_obj = get_data.get("data", get_data)
    if not user_obj:
        console.print(f"[red]User '{username}' not found[/red]")
        return

    # Apply updates (except password which uses set-password API)
    new_password = password
    if email is not None:
        user_obj["email"] = email
    if name is not None:
        user_obj["displayName"] = name
    if phone is not None:
        user_obj["phone"] = phone
    if admin is not None:
        user_obj["isAdmin"] = admin
    if forbidden is not None:
        user_obj["isForbidden"] = forbidden

    data = _iam_request(
        "POST",
        "/api/update-user",
        params={"id": f"{org}/{username}"},
        json_body=user_obj,
    )
    _check_response(data, "update user")

    console.print(f"[green]✓[/green] User '{username}' updated")

    # Set password via proper set-password API
    if new_password is not None:
        client_id, client_secret = _get_iam_credentials()
        try:
            with httpx.Client(timeout=30.0) as http:
                resp = http.post(
                    f"{_get_iam_url().rstrip('/')}/api/set-password",
                    params={"clientId": client_id, "clientSecret": client_secret},
                    data={
                        "userOwner": org,
                        "userName": username,
                        "oldPassword": "",
                        "newPassword": new_password,
                    },
                )
                if resp.status_code == 200 and resp.json().get("status") == "ok":
                    console.print("[green]✓[/green] Password updated")
                else:
                    console.print(
                        f"[yellow]⚠[/yellow] Password update issue: {resp.json().get('msg', '')}"
                    )
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Could not update password: {e}")


@users.command(name="delete")
@click.argument("username")
@click.option("--org", "-o", default="hanzo", help="Organization")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def users_delete(username: str, org: str, yes: bool):
    """Delete a user."""
    if not yes:
        from rich.prompt import Confirm

        if not Confirm.ask(f"[red]Delete user '{username}' from '{org}'?[/red]"):
            return

    user_obj = {"owner": org, "name": username}
    data = _iam_request("POST", "/api/delete-user", json_body=user_obj)
    _check_response(data, "delete user")

    console.print(f"[green]✓[/green] User '{username}' deleted")


@users.command(name="count")
@click.option("--org", "-o", default="hanzo", help="Organization name")
def users_count(org: str):
    """Get user count in organization."""
    data = _iam_request("GET", "/api/get-user-count", params={"owner": org})
    _check_response(data, "count users")

    count = data.get("data", data) if isinstance(data, dict) else data
    console.print(f"Users in '{org}': [bold]{count}[/bold]")


# ============================================================================
# Organizations
# ============================================================================


@iam_group.group()
def orgs():
    """Manage IAM organizations."""
    pass


@orgs.command(name="list")
def orgs_list():
    """List all organizations."""
    data = _iam_request("GET", "/api/get-organizations", params={"owner": "admin"})
    _check_response(data, "list organizations")

    orgs_data = data.get("data") if isinstance(data, dict) else data
    if not orgs_data:
        console.print("[dim]No organizations found[/dim]")
        return

    table = Table(title="Organizations", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Display Name", style="white")
    table.add_column("Website", style="dim")
    table.add_column("Password Type", style="dim")
    table.add_column("Created", style="dim")

    for o in orgs_data:
        table.add_row(
            o.get("name", ""),
            o.get("displayName", ""),
            o.get("websiteUrl", ""),
            o.get("passwordType", ""),
            o.get("createdTime", "")[:10] if o.get("createdTime") else "",
        )

    console.print(table)


@orgs.command(name="get")
@click.argument("name")
def orgs_get(name: str):
    """Get organization details."""
    data = _iam_request("GET", "/api/get-organization", params={"id": f"admin/{name}"})
    _check_response(data, "get organization")

    org = data.get("data") if isinstance(data, dict) else data
    if not org:
        console.print(f"[red]Organization '{name}' not found[/red]")
        return

    lines = [
        f"[cyan]Name:[/cyan] {org.get('name', '')}",
        f"[cyan]Display Name:[/cyan] {org.get('displayName', '')}",
        f"[cyan]Website:[/cyan] {org.get('websiteUrl', '')}",
        f"[cyan]Favicon:[/cyan] {org.get('favicon', '')}",
        f"[cyan]Password Type:[/cyan] {org.get('passwordType', '')}",
        f"[cyan]Phone Prefix:[/cyan] {org.get('phonePrefix', '')}",
        f"[cyan]Default Avatar:[/cyan] {org.get('defaultAvatar', '')}",
        f"[cyan]Master Password:[/cyan] {'Set' if org.get('masterPassword') else 'Not set'}",
        f"[cyan]Init Score:[/cyan] {org.get('initScore', 0)}",
        f"[cyan]MFA Enabled:[/cyan] {', '.join(org.get('mfaItems', [])) if org.get('mfaItems') else 'None'}",
        f"[cyan]Created:[/cyan] {org.get('createdTime', '')}",
    ]

    console.print(
        Panel("\n".join(lines), title=f"Organization: {name}", border_style="cyan")
    )


@orgs.command(name="create")
@click.option("--name", "-n", required=True, help="Organization name (slug)")
@click.option("--display-name", "-d", help="Display name")
@click.option("--website", "-w", help="Website URL")
def orgs_create(name: str, display_name: str, website: str):
    """Create a new organization."""
    org_obj = {
        "owner": "admin",
        "name": name,
        "displayName": display_name or name,
        "websiteUrl": website or "",
        "passwordType": "bcrypt",
    }

    data = _iam_request("POST", "/api/add-organization", json_body=org_obj)
    _check_response(data, "create organization")

    console.print(f"[green]✓[/green] Organization '{name}' created")


@orgs.command(name="delete")
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def orgs_delete(name: str, yes: bool):
    """Delete an organization."""
    if not yes:
        from rich.prompt import Confirm

        if not Confirm.ask(
            f"[red]Delete organization '{name}'? This cannot be undone.[/red]"
        ):
            return

    org_obj = {"owner": "admin", "name": name}
    data = _iam_request("POST", "/api/delete-organization", json_body=org_obj)
    _check_response(data, "delete organization")

    console.print(f"[green]✓[/green] Organization '{name}' deleted")


# ============================================================================
# Providers
# ============================================================================


@iam_group.group()
def providers():
    """Manage authentication providers (OAuth, SAML, etc.)."""
    pass


@providers.command(name="list")
@click.option("--owner", default="admin", help="Provider owner")
def providers_list(owner: str):
    """List authentication providers."""
    data = _iam_request("GET", "/api/get-providers", params={"owner": owner})
    _check_response(data, "list providers")

    provs = data.get("data") if isinstance(data, dict) else data
    if not provs:
        console.print("[dim]No providers found[/dim]")
        return

    table = Table(title="Providers", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Display Name", style="white")
    table.add_column("Type", style="green")
    table.add_column("Category", style="yellow")
    table.add_column("Client ID", style="dim")

    for p in provs:
        table.add_row(
            p.get("name", ""),
            p.get("displayName", ""),
            p.get("type", ""),
            p.get("category", ""),
            (p.get("clientId", "")[:16] + "...") if p.get("clientId") else "",
        )

    console.print(table)


@providers.command(name="get")
@click.argument("name")
@click.option("--owner", default="admin", help="Provider owner")
def providers_get(name: str, owner: str):
    """Get provider details."""
    data = _iam_request("GET", "/api/get-provider", params={"id": f"{owner}/{name}"})
    _check_response(data, "get provider")

    prov = data.get("data") if isinstance(data, dict) else data
    if not prov:
        console.print(f"[red]Provider '{name}' not found[/red]")
        return

    lines = [
        f"[cyan]Name:[/cyan] {prov.get('name', '')}",
        f"[cyan]Display Name:[/cyan] {prov.get('displayName', '')}",
        f"[cyan]Type:[/cyan] {prov.get('type', '')}",
        f"[cyan]Category:[/cyan] {prov.get('category', '')}",
        f"[cyan]Client ID:[/cyan] {prov.get('clientId', '')}",
        f"[cyan]Client Secret:[/cyan] {'****' + prov.get('clientSecret', '')[-4:] if prov.get('clientSecret') else 'Not set'}",
        f"[cyan]Provider URL:[/cyan] {prov.get('providerUrl', '')}",
        f"[cyan]Scopes:[/cyan] {prov.get('scopes', '')}",
        f"[cyan]Created:[/cyan] {prov.get('createdTime', '')}",
    ]

    console.print(
        Panel("\n".join(lines), title=f"Provider: {name}", border_style="cyan")
    )


@providers.command(name="create")
@click.option("--name", "-n", required=True, help="Provider name")
@click.option(
    "--type",
    "-t",
    "ptype",
    required=True,
    type=click.Choice(
        [
            "Google",
            "GitHub",
            "Facebook",
            "Twitter",
            "Apple",
            "Microsoft",
            "Discord",
            "Slack",
            "WeChat",
            "SAML",
            "OIDC",
            "CAS",
            "LDAP",
        ]
    ),
    help="Provider type",
)
@click.option("--display-name", "-d", help="Display name")
@click.option("--client-id", "-i", required=True, help="OAuth client ID")
@click.option("--client-secret", "-s", required=True, help="OAuth client secret")
@click.option("--scopes", help="OAuth scopes")
@click.option("--owner", default="admin", help="Provider owner")
def providers_create(
    name: str,
    ptype: str,
    display_name: str,
    client_id: str,
    client_secret: str,
    scopes: str,
    owner: str,
):
    """Create an authentication provider."""
    prov_obj = {
        "owner": owner,
        "name": name,
        "displayName": display_name or f"{ptype} Login",
        "type": ptype,
        "category": "OAuth",
        "clientId": client_id,
        "clientSecret": client_secret,
        "scopes": scopes or "",
    }

    data = _iam_request("POST", "/api/add-provider", json_body=prov_obj)
    _check_response(data, "create provider")

    console.print(f"[green]✓[/green] Provider '{name}' ({ptype}) created")


@providers.command(name="delete")
@click.argument("name")
@click.option("--owner", default="admin", help="Provider owner")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def providers_delete(name: str, owner: str, yes: bool):
    """Delete an authentication provider."""
    if not yes:
        from rich.prompt import Confirm

        if not Confirm.ask(f"[red]Delete provider '{name}'?[/red]"):
            return

    prov_obj = {"owner": owner, "name": name}
    data = _iam_request("POST", "/api/delete-provider", json_body=prov_obj)
    _check_response(data, "delete provider")

    console.print(f"[green]✓[/green] Provider '{name}' deleted")


# ============================================================================
# Applications
# ============================================================================


@iam_group.group()
def apps():
    """Manage IAM applications."""
    pass


@apps.command(name="list")
@click.option("--org", "-o", default="admin", help="Organization/owner")
def apps_list(org: str):
    """List applications."""
    data = _iam_request("GET", "/api/get-applications", params={"owner": org})
    _check_response(data, "list applications")

    apps_data = data.get("data") if isinstance(data, dict) else data
    if not apps_data:
        console.print("[dim]No applications found[/dim]")
        return

    table = Table(title="Applications", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Display Name", style="white")
    table.add_column("Organization", style="green")
    table.add_column("Client ID", style="dim")
    table.add_column("Providers", style="yellow")

    for a in apps_data:
        providers_count = len(a.get("providers", []))
        table.add_row(
            a.get("name", ""),
            a.get("displayName", ""),
            a.get("organization", ""),
            (
                a.get("clientId", "")[:20] + "..."
                if len(a.get("clientId", "")) > 20
                else a.get("clientId", "")
            ),
            str(providers_count),
        )

    console.print(table)


@apps.command(name="get")
@click.argument("name")
@click.option("--org", "-o", default="admin", help="Organization/owner")
def apps_get(name: str, org: str):
    """Get application details."""
    data = _iam_request("GET", "/api/get-application", params={"id": f"{org}/{name}"})
    _check_response(data, "get application")

    app = data.get("data") if isinstance(data, dict) else data
    if not app:
        console.print(f"[red]Application '{name}' not found[/red]")
        return

    lines = [
        f"[cyan]Name:[/cyan] {app.get('name', '')}",
        f"[cyan]Display Name:[/cyan] {app.get('displayName', '')}",
        f"[cyan]Organization:[/cyan] {app.get('organization', '')}",
        f"[cyan]Client ID:[/cyan] {app.get('clientId', '')}",
        f"[cyan]Client Secret:[/cyan] {'****' + app.get('clientSecret', '')[-4:] if app.get('clientSecret') else 'N/A'}",
        f"[cyan]Homepage:[/cyan] {app.get('homepageUrl', '')}",
        f"[cyan]Redirect URIs:[/cyan] {', '.join(app.get('redirectUris') or [])}",
        f"[cyan]Grant Types:[/cyan] {', '.join(app.get('grantTypes') or [])}",
        f"[cyan]Token Expiry:[/cyan] {app.get('expireInHours', '?')} hours",
        f"[cyan]Enable Password:[/cyan] {app.get('enablePassword', '?')}",
        f"[cyan]Enable Signup:[/cyan] {app.get('enableSignUp', '?')}",
    ]

    # Show providers
    providers_list = app.get("providers", [])
    if providers_list:
        lines.append(f"[cyan]Providers:[/cyan]")
        for p in providers_list:
            pname = p.get("name", "") if isinstance(p, dict) else str(p)
            lines.append(f"  - {pname}")

    # Show signup items
    signup_items = app.get("signupItems", [])
    if signup_items:
        lines.append(f"[cyan]Signup Items:[/cyan]")
        for s in signup_items:
            sname = s.get("name", "") if isinstance(s, dict) else str(s)
            required = s.get("required", False) if isinstance(s, dict) else False
            lines.append(f"  - {sname} {'(required)' if required else '(optional)'}")

    console.print(
        Panel("\n".join(lines), title=f"Application: {name}", border_style="cyan")
    )


# ============================================================================
# Roles
# ============================================================================


@iam_group.group()
def roles():
    """Manage IAM roles."""
    pass


@roles.command(name="list")
@click.option("--org", "-o", default="hanzo", help="Organization")
def roles_list(org: str):
    """List roles in organization."""
    data = _iam_request("GET", "/api/get-roles", params={"owner": org})
    _check_response(data, "list roles")

    roles_data = data.get("data") if isinstance(data, dict) else data
    if not roles_data:
        console.print("[dim]No roles found[/dim]")
        return

    table = Table(title=f"Roles ({org})", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Display Name", style="white")
    table.add_column("Users", style="green")
    table.add_column("Domains", style="dim")
    table.add_column("Created", style="dim")

    for r in roles_data:
        users_count = len(r.get("users", []))
        domains = ", ".join(r.get("domains", []))
        table.add_row(
            r.get("name", ""),
            r.get("displayName", ""),
            str(users_count),
            domains,
            r.get("createdTime", "")[:10] if r.get("createdTime") else "",
        )

    console.print(table)


@roles.command(name="get")
@click.argument("name")
@click.option("--org", "-o", default="hanzo", help="Organization")
def roles_get(name: str, org: str):
    """Get role details."""
    data = _iam_request("GET", "/api/get-role", params={"id": f"{org}/{name}"})
    _check_response(data, "get role")

    role = data.get("data") if isinstance(data, dict) else data
    if not role:
        console.print(f"[red]Role '{name}' not found[/red]")
        return

    lines = [
        f"[cyan]Name:[/cyan] {role.get('name', '')}",
        f"[cyan]Display Name:[/cyan] {role.get('displayName', '')}",
        f"[cyan]Description:[/cyan] {role.get('description', '')}",
    ]

    users_list = role.get("users", [])
    if users_list:
        lines.append(f"[cyan]Users ({len(users_list)}):[/cyan]")
        for u in users_list:
            lines.append(f"  - {u}")

    roles_sub = role.get("roles", [])
    if roles_sub:
        lines.append(f"[cyan]Sub-Roles:[/cyan]")
        for sr in roles_sub:
            lines.append(f"  - {sr}")

    console.print(Panel("\n".join(lines), title=f"Role: {name}", border_style="cyan"))


# ============================================================================
# Admin: Login / Masquerade
# ============================================================================


@iam_group.command(name="login")
@click.option("--username", "-u", help="Username or email")
@click.option("--password", "-p", help="Password")
@click.option("--org", "-o", default="hanzo", help="Organization")
@click.option("--app", "-a", default="app-hanzo", help="Application name")
def iam_login(username: str, password: str, org: str, app: str):
    """Login as a user via IAM (email/password).

    \b
    Uses the Casdoor /api/login endpoint directly.
    Stores the resulting token in ~/.hanzo/auth.json.

    \b
    Examples:
      hanzo iam login -u admin@hanzo.ai
      hanzo iam login -u z -p mypassword --org hanzo
    """
    from pathlib import Path
    from datetime import datetime

    from rich.prompt import Prompt

    if not username:
        username = Prompt.ask("Username or email")
    if not password:
        password = Prompt.ask("Password", password=True)

    url = _get_iam_url().rstrip("/")

    try:
        with httpx.Client(timeout=30.0) as http:
            resp = http.post(
                f"{url}/api/login",
                json={
                    "type": "token",
                    "username": username,
                    "password": password,
                    "organization": org,
                    "application": app,
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.ConnectError:
        console.print(f"[red]Error:[/red] Cannot connect to IAM at {url}")
        return
    except httpx.HTTPStatusError as e:
        console.print(f"[red]Error:[/red] Login failed ({e.response.status_code})")
        return

    if data.get("status") != "ok":
        console.print(f"[red]Login failed:[/red] {data.get('msg', 'Unknown error')}")
        return

    token = data.get("data", "")
    console.print(f"[green]✓[/green] Logged in as {username}")

    # Save to auth.json
    auth_file = Path.home() / ".hanzo" / "auth.json"
    auth = {}
    if auth_file.exists():
        try:
            auth = json.loads(auth_file.read_text())
        except Exception:
            pass

    auth["logged_in"] = True
    auth["email"] = username
    auth["token"] = token
    auth["iam_org"] = org
    auth["iam_app"] = app
    auth["last_login"] = datetime.now().isoformat()

    Path.home().joinpath(".hanzo").mkdir(exist_ok=True)
    auth_file.write_text(json.dumps(auth, indent=2))

    console.print("[green]✓[/green] Access token saved to ~/.hanzo/auth.json")

    # Also try password grant for refresh token
    client_id, client_secret = _get_iam_credentials()
    if client_id and client_secret:
        try:
            with httpx.Client(timeout=30.0) as http:
                token_resp = http.post(
                    f"{url}/api/login/oauth/access_token",
                    data={
                        "grant_type": "password",
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "username": username,
                        "password": password,
                        "scope": "openid profile email",
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                if token_resp.status_code == 200:
                    token_data = token_resp.json()
                    if token_data.get("refresh_token"):
                        auth["refresh_token"] = token_data["refresh_token"]
                        auth_file.write_text(json.dumps(auth, indent=2))
                        console.print("[green]✓[/green] Refresh token obtained")
        except Exception:
            pass  # Refresh token is optional


# ============================================================================
# Admin: Raw API Call
# ============================================================================


@iam_group.command(name="api")
@click.argument("endpoint")
@click.option("--method", "-m", default="GET", type=click.Choice(["GET", "POST"]))
@click.option("--data", "-d", "body", help="JSON body for POST requests")
@click.option("--param", "-p", multiple=True, help="Extra params (key=value)")
def iam_api(endpoint: str, method: str, body: str, param: tuple):
    """Make raw API call to IAM server.

    \b
    Examples:
      hanzo iam api /api/get-users --param owner=hanzo
      hanzo iam api /api/get-application --param id=hanzo/app-hanzo
      hanzo iam api /api/get-providers --param owner=admin
    """
    extra_params = {}
    for p in param:
        if "=" in p:
            k, v = p.split("=", 1)
            extra_params[k] = v

    json_body = None
    if body:
        try:
            json_body = json.loads(body)
        except json.JSONDecodeError:
            console.print("[red]Error:[/red] Invalid JSON body")
            return

    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint

    data = _iam_request(method, endpoint, params=extra_params, json_body=json_body)

    # Pretty print the response
    console.print_json(json.dumps(data, indent=2, default=str))


# ============================================================================
# Tokens
# ============================================================================


@iam_group.group()
def tokens():
    """Manage and inspect tokens."""
    pass


@tokens.command(name="inspect")
@click.argument("token", required=False)
def tokens_inspect(token: str):
    """Inspect a JWT token (decode without verification)."""
    import base64

    if not token:
        # Try to get from auth.json
        from pathlib import Path

        auth_file = Path.home() / ".hanzo" / "auth.json"
        if auth_file.exists():
            auth = json.loads(auth_file.read_text())
            token = auth.get("token", "")

    if not token:
        console.print(
            "[red]No token provided and none found in ~/.hanzo/auth.json[/red]"
        )
        return

    parts = token.split(".")
    if len(parts) != 3:
        console.print("[red]Invalid JWT format (expected 3 parts)[/red]")
        return

    # Decode header and payload (without verification)
    for label, part in [("Header", parts[0]), ("Payload", parts[1])]:
        # Add padding
        padded = part + "=" * (4 - len(part) % 4)
        try:
            decoded = base64.urlsafe_b64decode(padded)
            data = json.loads(decoded)
            console.print(f"\n[bold cyan]{label}:[/bold cyan]")
            console.print_json(json.dumps(data, indent=2, default=str))
        except Exception as e:
            console.print(f"[red]Error decoding {label}: {e}[/red]")

    # Show expiry info
    try:
        padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        if "exp" in payload:
            from datetime import datetime

            exp = datetime.fromtimestamp(payload["exp"])
            now = datetime.now()
            if now > exp:
                console.print(f"\n[red]Token EXPIRED at {exp}[/red]")
            else:
                delta = exp - now
                console.print(
                    f"\n[green]Token valid until {exp} ({delta} remaining)[/green]"
                )
    except Exception:
        pass


@tokens.command(name="exchange")
@click.argument("code")
@click.option(
    "--redirect-uri", "-r", default="", help="Redirect URI used in authorization"
)
def tokens_exchange(code: str, redirect_uri: str):
    """Exchange authorization code for access token."""
    client_id, client_secret = _get_iam_credentials()
    if not client_id:
        console.print("[red]Error:[/red] No client credentials configured")
        return

    url = _get_iam_url().rstrip("/")
    try:
        with httpx.Client(timeout=30.0) as http:
            resp = http.post(
                f"{url}/api/login/oauth/access_token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        return

    if data.get("access_token"):
        console.print("[green]✓[/green] Token exchange successful")
        console.print(f"  Access Token: {data['access_token'][:30]}...")
        if data.get("refresh_token"):
            console.print(f"  Refresh Token: {data['refresh_token'][:30]}...")
        console.print(f"  Expires In: {data.get('expires_in', '?')}s")

        # Save to auth.json
        from pathlib import Path

        auth_file = Path.home() / ".hanzo" / "auth.json"
        auth = {}
        if auth_file.exists():
            try:
                auth = json.loads(auth_file.read_text())
            except Exception:
                pass
        auth["token"] = data["access_token"]
        if data.get("refresh_token"):
            auth["refresh_token"] = data["refresh_token"]
        auth_file.write_text(json.dumps(auth, indent=2))
        console.print("[green]✓[/green] Token saved to ~/.hanzo/auth.json")
    else:
        console.print("[red]Token exchange failed[/red]")
        console.print_json(json.dumps(data, indent=2, default=str))
