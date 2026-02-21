"""Git provider integration for Hanzo CLI.

Connect git providers (GitHub, GitLab, Bitbucket) and link repos to containers.
"""

import click
from rich import box
from rich.table import Table

from ..utils.output import console


@click.group(name="git")
def git_group():
    """Manage git provider connections and repo links.

    \b
    Providers:
      hanzo git connect github     # Connect GitHub account
      hanzo git providers          # List connected providers
      hanzo git disconnect ID      # Remove a provider

    \b
    Repos:
      hanzo git repos              # List repos from connected provider
      hanzo git branches REPO      # List branches
      hanzo git link REPO          # Link repo to container
    """
    pass


def _get_client():
    from ..utils.api_client import PaaSClient

    try:
        return PaaSClient(timeout=30)
    except SystemExit:
        return None


# ============================================================================
# Provider management
# ============================================================================


@git_group.command(name="connect")
@click.argument("provider", type=click.Choice(["github", "gitlab", "bitbucket"]))
@click.option("--token", "-t", help="Personal access token (alternative to OAuth)")
def git_connect(provider, token):
    """Connect a git provider.

    \b
    Examples:
      hanzo git connect github              # OAuth flow
      hanzo git connect github --token ghp_xxx  # PAT
      hanzo git connect gitlab --token glpat_xxx
    """
    from ..utils.api_client import git_url

    client = _get_client()
    if not client:
        return

    if token:
        payload = {
            "provider": provider,
            "accessToken": token,
        }
        console.print(f"[cyan]Connecting {provider} with token...[/cyan]")
        result = client.post(git_url(), payload)
        if result is None:
            return

        pid = result.get("_id") or result.get("id", "")
        console.print(f"[green]✓[/green] {provider} connected")
        if pid:
            console.print(f"  Provider ID: {pid}")
    else:
        # OAuth flow - redirect to PaaS OAuth endpoint
        from ..utils.api_client import PLATFORM_API_URL

        oauth_url = f"{PLATFORM_API_URL}/v1/user/git/connect/{provider}"
        console.print(f"[cyan]Opening browser for {provider} OAuth...[/cyan]")
        console.print(f"\n  {oauth_url}\n")

        try:
            import webbrowser

            webbrowser.open(oauth_url)
            console.print("[dim]Complete the OAuth flow in your browser.[/dim]")
            console.print("[dim]Then run 'hanzo git providers' to verify.[/dim]")
        except Exception:
            console.print("[yellow]Could not open browser. Visit the URL above manually.[/yellow]")


@git_group.command(name="providers")
def git_providers():
    """List connected git providers."""
    from ..utils.api_client import git_url

    client = _get_client()
    if not client:
        return

    data = client.get(git_url())
    if data is None:
        return

    providers = data if isinstance(data, list) else data.get("providers", data.get("data", []))

    if not providers:
        console.print("[dim]No git providers connected.[/dim]")
        console.print("[dim]Run 'hanzo git connect github' to get started.[/dim]")
        return

    table = Table(title="Git Providers", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Provider", style="white")
    table.add_column("Username", style="green")
    table.add_column("Status", style="dim")

    for p in providers:
        pid = p.get("_id") or p.get("id", "")
        prov = p.get("provider", p.get("gitProviderId", ""))
        user = p.get("username", p.get("providerUserId", ""))
        status = p.get("status", "connected")
        table.add_row(str(pid)[:12], prov, user, status)

    console.print(table)


@git_group.command(name="disconnect")
@click.argument("provider_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def git_disconnect(provider_id, force):
    """Disconnect a git provider."""
    from ..utils.api_client import git_url

    if not force:
        from rich.prompt import Confirm

        if not Confirm.ask(f"[red]Disconnect git provider '{provider_id}'?[/red]"):
            return

    client = _get_client()
    if not client:
        return

    result = client.delete(git_url(provider_id))
    if result is None:
        return

    console.print(f"[green]✓[/green] Git provider disconnected")


# ============================================================================
# Repos & Branches
# ============================================================================


@git_group.command(name="repos")
@click.option("--provider", "-p", help="Provider ID (uses first connected if omitted)")
def git_repos(provider):
    """List repos from connected git provider."""
    from ..utils.api_client import git_url

    client = _get_client()
    if not client:
        return

    # If no provider specified, find the first one
    if not provider:
        data = client.get(git_url())
        if data is None:
            return
        providers = data if isinstance(data, list) else data.get("providers", data.get("data", []))
        if not providers:
            console.print("[yellow]No git providers connected. Run 'hanzo git connect github' first.[/yellow]")
            return
        provider = str(providers[0].get("_id") or providers[0].get("id", ""))

    data = client.get(f"{git_url(provider)}/repo")
    if data is None:
        return

    repos = data if isinstance(data, list) else data.get("repos", data.get("data", []))

    if not repos:
        console.print("[dim]No repos found.[/dim]")
        return

    table = Table(title="Repositories", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Full Name", style="white")
    table.add_column("Default Branch", style="green")
    table.add_column("Private", style="dim")

    for r in repos:
        rname = r.get("name", "")
        rfull = r.get("fullName", r.get("full_name", ""))
        rbranch = r.get("defaultBranch", r.get("default_branch", "main"))
        rprivate = "Yes" if r.get("private", False) else "No"
        table.add_row(rname, rfull, rbranch, rprivate)

    console.print(table)


@git_group.command(name="branches")
@click.argument("repo")
@click.option("--provider", "-p", help="Provider ID")
def git_branches(repo, provider):
    """List branches for a repo."""
    from ..utils.api_client import git_url

    client = _get_client()
    if not client:
        return

    if not provider:
        data = client.get(git_url())
        if data is None:
            return
        providers = data if isinstance(data, list) else data.get("providers", data.get("data", []))
        if not providers:
            console.print("[yellow]No git providers connected.[/yellow]")
            return
        provider = str(providers[0].get("_id") or providers[0].get("id", ""))

    data = client.get(f"{git_url(provider)}/repo/branch", params={"repo": repo})
    if data is None:
        return

    branches = data if isinstance(data, list) else data.get("branches", data.get("data", []))

    if not branches:
        console.print(f"[dim]No branches found for '{repo}'.[/dim]")
        return

    table = Table(title=f"Branches for {repo}", box=box.ROUNDED)
    table.add_column("Branch", style="cyan")
    table.add_column("Default", style="green")

    for b in branches:
        bname = b.get("name", b) if isinstance(b, dict) else str(b)
        is_default = b.get("default", False) if isinstance(b, dict) else False
        table.add_row(bname, "Yes" if is_default else "")

    console.print(table)


@git_group.command(name="link")
@click.argument("repo")
@click.option("--container", "-c", required=True, help="Container name to link to")
@click.option("--branch", "-b", default="main", help="Branch to deploy from")
@click.option("--provider", "-p", help="Provider ID")
def git_link(repo, container, branch, provider):
    """Link a git repo to a container (sets up webhook for auto-deploy).

    \b
    Examples:
      hanzo git link org/repo --container my-app
      hanzo git link org/repo --container api --branch develop
    """
    from ..utils.api_client import git_url, container_url, require_context

    client = _get_client()
    if not client:
        return

    try:
        ctx = require_context()
    except SystemExit:
        return

    # Resolve provider if not given
    if not provider:
        data = client.get(git_url())
        if data is None:
            return
        providers = data if isinstance(data, list) else data.get("providers", data.get("data", []))
        if not providers:
            console.print("[yellow]No git providers connected.[/yellow]")
            return
        provider = str(providers[0].get("_id") or providers[0].get("id", ""))

    # Find the container
    base_url = container_url(ctx["org_id"], ctx["project_id"], ctx["env_id"])
    data = client.get(base_url)
    if data is None:
        return

    containers = data if isinstance(data, list) else data.get("containers", data.get("data", []))
    cid = None
    for c in containers:
        cname = c.get("name", "")
        if cname == container:
            cid = c.get("_id") or c.get("iid") or c.get("id", "")
            break

    if not cid:
        console.print(f"[yellow]Container '{container}' not found.[/yellow]")
        return

    # Update container to use repo source
    payload = {
        "repoOrRegistry": "repo",
        "repo": {
            "url": repo,
            "branch": branch,
            "gitProviderId": provider,
            "connected": True,
        },
    }

    result = client.put(f"{base_url}/{cid}", payload)
    if result is None:
        return

    console.print(f"[green]✓[/green] Linked '{repo}' -> '{container}'")
    console.print(f"  Branch: {branch}")
    console.print(f"  Auto-deploy: enabled")
    console.print(f"[dim]Push to '{branch}' to trigger a build.[/dim]")
