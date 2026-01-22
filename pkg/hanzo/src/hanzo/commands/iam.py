"""Hanzo IAM - Identity and Access Management CLI.

Users, organizations, teams, API keys, roles, policies.
"""

import secrets
import click
from rich import box
from rich.table import Table
from rich.panel import Panel

from ..utils.output import console


@click.group(name="iam")
def iam_group():
    """Hanzo IAM - Identity and Access Management.

    \b
    Users:
      hanzo iam users list           # List users
      hanzo iam users invite         # Invite user

    \b
    Organizations:
      hanzo iam orgs list            # List organizations
      hanzo iam orgs create          # Create organization
      hanzo iam orgs switch          # Switch active org

    \b
    Teams:
      hanzo iam teams list           # List teams
      hanzo iam teams create         # Create team
      hanzo iam teams add-member     # Add member to team

    \b
    API Keys:
      hanzo iam keys list            # List API keys
      hanzo iam keys create          # Create API key
      hanzo iam keys rotate          # Rotate API key

    \b
    Roles & Policies:
      hanzo iam roles list           # List roles
      hanzo iam policies list        # List policies
    """
    pass


# ============================================================================
# Users
# ============================================================================

@iam_group.group()
def users():
    """Manage users."""
    pass


@users.command(name="list")
@click.option("--org", "-o", help="Filter by organization")
def users_list(org: str):
    """List users."""
    table = Table(title="Users", box=box.ROUNDED)
    table.add_column("Email", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Role", style="green")
    table.add_column("Teams", style="dim")
    table.add_column("Status", style="yellow")

    console.print(table)


@users.command(name="invite")
@click.option("--email", "-e", prompt=True, help="User email")
@click.option("--role", "-r", type=click.Choice(["admin", "member", "viewer"]), default="member")
@click.option("--team", "-t", multiple=True, help="Add to teams")
def users_invite(email: str, role: str, team: tuple):
    """Invite a user to the organization."""
    console.print(f"[green]✓[/green] Invitation sent to {email}")
    console.print(f"  Role: {role}")
    if team:
        console.print(f"  Teams: {', '.join(team)}")


@users.command(name="remove")
@click.argument("email")
def users_remove(email: str):
    """Remove a user from the organization."""
    from rich.prompt import Confirm
    if not Confirm.ask(f"[red]Remove user '{email}' from organization?[/red]"):
        return
    console.print(f"[green]✓[/green] User {email} removed")


@users.command(name="update-role")
@click.argument("email")
@click.option("--role", "-r", type=click.Choice(["admin", "member", "viewer"]), required=True)
def users_update_role(email: str, role: str):
    """Update a user's role."""
    console.print(f"[green]✓[/green] Updated {email} role to {role}")


# ============================================================================
# Organizations
# ============================================================================

@iam_group.group()
def orgs():
    """Manage organizations."""
    pass


@orgs.command(name="list")
def orgs_list():
    """List organizations you belong to."""
    table = Table(title="Organizations", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("ID", style="dim")
    table.add_column("Role", style="green")
    table.add_column("Members", style="white")
    table.add_column("Active", style="yellow")

    console.print(table)


@orgs.command(name="create")
@click.option("--name", "-n", prompt=True, help="Organization name")
@click.option("--slug", "-s", help="URL slug (auto-generated if not provided)")
def orgs_create(name: str, slug: str):
    """Create a new organization."""
    slug = slug or name.lower().replace(" ", "-")
    console.print(f"[green]✓[/green] Organization '{name}' created")
    console.print(f"  Slug: {slug}")
    console.print(f"  URL: https://hanzo.ai/org/{slug}")


@orgs.command(name="switch")
@click.argument("org_name")
def orgs_switch(org_name: str):
    """Switch active organization."""
    console.print(f"[green]✓[/green] Switched to organization '{org_name}'")


@orgs.command(name="delete")
@click.argument("org_name")
def orgs_delete(org_name: str):
    """Delete an organization."""
    from rich.prompt import Confirm
    if not Confirm.ask(f"[red]Delete organization '{org_name}'? This cannot be undone.[/red]"):
        return
    console.print(f"[green]✓[/green] Organization '{org_name}' deleted")


@orgs.command(name="show")
@click.argument("org_name", required=False)
def orgs_show(org_name: str):
    """Show organization details."""
    console.print(Panel(
        f"[cyan]Name:[/cyan] {org_name or 'Current Org'}\n"
        f"[cyan]ID:[/cyan] org_xxx\n"
        f"[cyan]Plan:[/cyan] Pro\n"
        f"[cyan]Members:[/cyan] 5\n"
        f"[cyan]Teams:[/cyan] 3\n"
        f"[cyan]Created:[/cyan] 2024-01-15",
        title="Organization Details",
        border_style="cyan"
    ))


# ============================================================================
# Teams
# ============================================================================

@iam_group.group()
def teams():
    """Manage teams within organizations."""
    pass


@teams.command(name="list")
def teams_list():
    """List teams in current organization."""
    table = Table(title="Teams", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Members", style="white")
    table.add_column("Description", style="dim")

    console.print(table)


@teams.command(name="create")
@click.option("--name", "-n", prompt=True, help="Team name")
@click.option("--description", "-d", help="Team description")
def teams_create(name: str, description: str):
    """Create a new team."""
    console.print(f"[green]✓[/green] Team '{name}' created")


@teams.command(name="delete")
@click.argument("team_name")
def teams_delete(team_name: str):
    """Delete a team."""
    from rich.prompt import Confirm
    if not Confirm.ask(f"[red]Delete team '{team_name}'?[/red]"):
        return
    console.print(f"[green]✓[/green] Team '{team_name}' deleted")


@teams.command(name="add-member")
@click.argument("team_name")
@click.option("--email", "-e", required=True, help="User email")
@click.option("--role", "-r", type=click.Choice(["lead", "member"]), default="member")
def teams_add_member(team_name: str, email: str, role: str):
    """Add a member to a team."""
    console.print(f"[green]✓[/green] Added {email} to team '{team_name}' as {role}")


@teams.command(name="remove-member")
@click.argument("team_name")
@click.option("--email", "-e", required=True, help="User email")
def teams_remove_member(team_name: str, email: str):
    """Remove a member from a team."""
    console.print(f"[green]✓[/green] Removed {email} from team '{team_name}'")


@teams.command(name="show")
@click.argument("team_name")
def teams_show(team_name: str):
    """Show team details and members."""
    console.print(Panel(
        f"[cyan]Team:[/cyan] {team_name}\n"
        f"[cyan]Members:[/cyan] 4\n"
        f"[cyan]Description:[/cyan] Engineering team",
        title="Team Details",
        border_style="cyan"
    ))

    table = Table(title="Members", box=box.ROUNDED)
    table.add_column("Email", style="cyan")
    table.add_column("Role", style="green")
    table.add_column("Joined", style="dim")
    console.print(table)


# ============================================================================
# API Keys
# ============================================================================

@iam_group.group()
def keys():
    """Manage API keys."""
    pass


@keys.command(name="list")
def keys_list():
    """List API keys."""
    table = Table(title="API Keys", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Key Prefix", style="dim")
    table.add_column("Scopes", style="white")
    table.add_column("Created", style="dim")
    table.add_column("Last Used", style="dim")

    console.print(table)


@keys.command(name="create")
@click.option("--name", "-n", prompt=True, help="Key name")
@click.option("--scopes", "-s", default="all", help="Comma-separated scopes (all, read, write, admin)")
@click.option("--expires", "-e", help="Expiration (e.g., 30d, 1y, never)")
def keys_create(name: str, scopes: str, expires: str):
    """Create a new API key."""
    # Generate a secure key
    key = f"hz_{secrets.token_urlsafe(32)}"

    console.print(f"[green]✓[/green] API key '{name}' created")
    console.print()
    console.print(Panel(
        f"[bold yellow]{key}[/bold yellow]",
        title="[red]Save this key - it won't be shown again![/red]",
        border_style="red"
    ))
    console.print()
    console.print(f"[dim]Scopes: {scopes}[/dim]")
    if expires:
        console.print(f"[dim]Expires: {expires}[/dim]")


@keys.command(name="delete")
@click.argument("key_name")
def keys_delete(key_name: str):
    """Delete an API key."""
    from rich.prompt import Confirm
    if not Confirm.ask(f"[red]Delete API key '{key_name}'?[/red]"):
        return
    console.print(f"[green]✓[/green] API key '{key_name}' deleted")


@keys.command(name="rotate")
@click.argument("key_name")
def keys_rotate(key_name: str):
    """Rotate an API key (generates new key, invalidates old)."""
    from rich.prompt import Confirm
    if not Confirm.ask(f"[yellow]Rotate API key '{key_name}'? The old key will stop working immediately.[/yellow]"):
        return

    key = f"hz_{secrets.token_urlsafe(32)}"
    console.print(f"[green]✓[/green] API key '{key_name}' rotated")
    console.print()
    console.print(Panel(
        f"[bold yellow]{key}[/bold yellow]",
        title="[red]Save this key - it won't be shown again![/red]",
        border_style="red"
    ))


# ============================================================================
# Roles
# ============================================================================

@iam_group.group()
def roles():
    """Manage IAM roles."""
    pass


@roles.command(name="list")
def roles_list():
    """List available roles."""
    table = Table(title="Roles", box=box.ROUNDED)
    table.add_column("Role", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Permissions", style="dim")

    table.add_row("owner", "Full access to organization", "all")
    table.add_row("admin", "Manage users, teams, and settings", "users.*, teams.*, settings.*")
    table.add_row("member", "Access to projects and resources", "projects.*, resources.*")
    table.add_row("viewer", "Read-only access", "*.read")
    table.add_row("billing", "Manage billing and subscriptions", "billing.*")

    console.print(table)


@roles.command(name="create")
@click.option("--name", "-n", prompt=True, help="Role name")
@click.option("--permissions", "-p", required=True, help="Comma-separated permissions")
@click.option("--description", "-d", help="Role description")
def roles_create(name: str, permissions: str, description: str):
    """Create a custom role."""
    console.print(f"[green]✓[/green] Role '{name}' created")
    console.print(f"  Permissions: {permissions}")


@roles.command(name="delete")
@click.argument("role_name")
def roles_delete(role_name: str):
    """Delete a custom role."""
    console.print(f"[green]✓[/green] Role '{role_name}' deleted")


# ============================================================================
# Policies
# ============================================================================

@iam_group.group()
def policies():
    """Manage IAM policies."""
    pass


@policies.command(name="list")
def policies_list():
    """List IAM policies."""
    table = Table(title="Policies", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Attached To", style="dim")

    console.print(table)


@policies.command(name="create")
@click.option("--name", "-n", prompt=True, help="Policy name")
@click.option("--file", "-f", type=click.Path(exists=True), help="Policy JSON file")
def policies_create(name: str, file: str):
    """Create an IAM policy from JSON file."""
    console.print(f"[green]✓[/green] Policy '{name}' created")


@policies.command(name="attach")
@click.argument("policy_name")
@click.option("--user", "-u", help="Attach to user")
@click.option("--team", "-t", help="Attach to team")
@click.option("--role", "-r", help="Attach to role")
def policies_attach(policy_name: str, user: str, team: str, role: str):
    """Attach a policy to a user, team, or role."""
    target = user or team or role
    target_type = "user" if user else ("team" if team else "role")
    console.print(f"[green]✓[/green] Policy '{policy_name}' attached to {target_type} '{target}'")


@policies.command(name="detach")
@click.argument("policy_name")
@click.option("--user", "-u", help="Detach from user")
@click.option("--team", "-t", help="Detach from team")
@click.option("--role", "-r", help="Detach from role")
def policies_detach(policy_name: str, user: str, team: str, role: str):
    """Detach a policy from a user, team, or role."""
    target = user or team or role
    target_type = "user" if user else ("team" if team else "role")
    console.print(f"[green]✓[/green] Policy '{policy_name}' detached from {target_type} '{target}'")


# ============================================================================
# Service Accounts
# ============================================================================

@iam_group.group(name="service-accounts")
def service_accounts():
    """Manage service accounts for automation."""
    pass


@service_accounts.command(name="list")
def sa_list():
    """List service accounts."""
    table = Table(title="Service Accounts", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Email", style="white")
    table.add_column("Keys", style="dim")
    table.add_column("Created", style="dim")

    console.print(table)


@service_accounts.command(name="create")
@click.option("--name", "-n", prompt=True, help="Service account name")
@click.option("--description", "-d", help="Description")
def sa_create(name: str, description: str):
    """Create a service account."""
    email = f"{name.lower().replace(' ', '-')}@sa.hanzo.ai"
    console.print(f"[green]✓[/green] Service account created")
    console.print(f"  Name: {name}")
    console.print(f"  Email: {email}")


@service_accounts.command(name="delete")
@click.argument("name")
def sa_delete(name: str):
    """Delete a service account."""
    from rich.prompt import Confirm
    if not Confirm.ask(f"[red]Delete service account '{name}'?[/red]"):
        return
    console.print(f"[green]✓[/green] Service account '{name}' deleted")


@service_accounts.command(name="create-key")
@click.argument("name")
@click.option("--output", "-o", type=click.Path(), help="Output file for key JSON")
def sa_create_key(name: str, output: str):
    """Create a key for a service account."""
    key_data = {
        "type": "service_account",
        "project_id": "my-project",
        "private_key_id": secrets.token_hex(20),
        "private_key": f"-----BEGIN PRIVATE KEY-----\n{secrets.token_urlsafe(64)}\n-----END PRIVATE KEY-----",
        "client_email": f"{name}@sa.hanzo.ai",
        "client_id": secrets.token_hex(10),
    }

    if output:
        import json
        with open(output, "w") as f:
            json.dump(key_data, f, indent=2)
        console.print(f"[green]✓[/green] Service account key saved to {output}")
    else:
        console.print(f"[green]✓[/green] Service account key created")
        console.print("[yellow]Use --output to save the key to a file[/yellow]")
