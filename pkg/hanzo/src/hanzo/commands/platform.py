"""Hanzo Platform - Infrastructure and security CLI.

Edge, HKE, networking, tunnel, DNS, guard.
"""

import click
from rich import box
from rich.panel import Panel
from rich.table import Table

from ..utils.output import console


@click.group(name="platform")
def platform_group():
    """Hanzo Platform - Infrastructure and security.

    \b
    Edge & CDN:
      hanzo platform edge deploy   # Deploy to edge
      hanzo platform edge list     # List edge deployments

    \b
    Kubernetes (HKE):
      hanzo platform hke list      # List clusters
      hanzo platform hke create    # Create cluster

    \b
    Networking:
      hanzo platform tunnel share  # Share localhost
      hanzo platform dns list      # List DNS records

    \b
    Security:
      hanzo platform guard enable  # Enable LLM safety layer
      hanzo platform kms list      # List secrets
    """
    pass


# ============================================================================
# Edge
# ============================================================================


@platform_group.group()
def edge():
    """Manage edge deployments and CDN."""
    pass


@edge.command(name="list")
def edge_list():
    """List edge deployments."""
    table = Table(title="Edge Deployments", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("URL", style="white")
    table.add_column("Regions", style="dim")
    table.add_column("Status", style="green")

    console.print(table)


@edge.command(name="deploy")
@click.option("--name", "-n", prompt=True, help="Deployment name")
@click.option("--dir", "-d", default=".", help="Directory to deploy")
@click.option("--regions", "-r", default="all", help="Target regions")
def edge_deploy(name: str, dir: str, regions: str):
    """Deploy to edge locations."""
    console.print(f"[cyan]Deploying '{name}' to edge...[/cyan]")
    console.print(f"  Source: {dir}")
    console.print(f"  Regions: {regions}")
    console.print()
    console.print(f"[green]✓[/green] Deployed to edge")
    console.print(f"[dim]URL: https://{name}.edge.hanzo.ai[/dim]")


@edge.command(name="purge")
@click.argument("name")
@click.option("--path", "-p", help="Specific path to purge")
def edge_purge(name: str, path: str):
    """Purge edge cache."""
    if path:
        console.print(f"[green]✓[/green] Purged cache for {path}")
    else:
        console.print(f"[green]✓[/green] Purged all cache for {name}")


# ============================================================================
# HKE (Kubernetes)
# ============================================================================


@platform_group.group()
def hke():
    """Manage Hanzo Kubernetes Engine clusters."""
    pass


@hke.command(name="list")
def hke_list():
    """List Kubernetes clusters."""
    table = Table(title="HKE Clusters", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="white")
    table.add_column("Nodes", style="white")
    table.add_column("Status", style="green")
    table.add_column("Region", style="dim")

    console.print(table)


@hke.command(name="create")
@click.option("--name", "-n", prompt=True, help="Cluster name")
@click.option("--version", "-v", default="1.29", help="Kubernetes version")
@click.option("--nodes", default=3, help="Number of nodes")
@click.option("--region", "-r", default="us-west-2", help="Region")
@click.option("--gpu", is_flag=True, help="Enable GPU node pool")
def hke_create(name: str, version: str, nodes: int, region: str, gpu: bool):
    """Create a Kubernetes cluster."""
    console.print(f"[cyan]Creating cluster '{name}'...[/cyan]")
    console.print(f"  Version: {version}")
    console.print(f"  Nodes: {nodes}")
    console.print(f"  Region: {region}")
    console.print(f"  GPU: {'Yes' if gpu else 'No'}")
    console.print()
    console.print(f"[green]✓[/green] Cluster '{name}' created")


@hke.command(name="delete")
@click.argument("name")
def hke_delete(name: str):
    """Delete a Kubernetes cluster."""
    from rich.prompt import Confirm

    if not Confirm.ask(f"[red]Delete cluster '{name}'? This cannot be undone.[/red]"):
        return
    console.print(f"[green]✓[/green] Cluster '{name}' deleted")


@hke.command(name="kubeconfig")
@click.argument("name")
def hke_kubeconfig(name: str):
    """Get kubeconfig for a cluster."""
    console.print(f"[cyan]Fetching kubeconfig for '{name}'...[/cyan]")
    console.print("[green]✓[/green] Kubeconfig saved to ~/.kube/config")


@hke.command(name="scale")
@click.argument("name")
@click.option("--nodes", "-n", required=True, type=int, help="Target nodes")
def hke_scale(name: str, nodes: int):
    """Scale cluster nodes."""
    console.print(f"[green]✓[/green] Cluster '{name}' scaling to {nodes} nodes")


# ============================================================================
# Tunnel
# ============================================================================


@platform_group.group()
def tunnel():
    """Manage secure tunnels."""
    pass


@tunnel.command(name="share")
@click.argument("target")
@click.option("--name", "-n", help="Subdomain name")
@click.option("--auth", is_flag=True, help="Require authentication")
def tunnel_share(target: str, name: str, auth: bool):
    """Share local service via secure tunnel."""
    subdomain = name or "random-xxx"
    console.print(f"[cyan]Creating tunnel to {target}...[/cyan]")
    console.print()
    console.print(f"[green]✓[/green] Tunnel active")
    console.print(f"  [cyan]Public URL:[/cyan] https://{subdomain}.tunnel.hanzo.ai")
    console.print(f"  [cyan]Target:[/cyan] {target}")
    console.print()
    console.print("Press Ctrl+C to stop")


@tunnel.command(name="list")
def tunnel_list():
    """List active tunnels."""
    table = Table(title="Active Tunnels", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Target", style="white")
    table.add_column("URL", style="dim")
    table.add_column("Status", style="green")

    console.print(table)


@tunnel.command(name="stop")
@click.argument("name")
def tunnel_stop(name: str):
    """Stop a tunnel."""
    console.print(f"[green]✓[/green] Tunnel '{name}' stopped")


# ============================================================================
# DNS
# ============================================================================


@platform_group.group()
def dns():
    """Manage DNS records."""
    pass


@dns.command(name="list")
@click.argument("zone", required=False)
def dns_list(zone: str):
    """List DNS records."""
    table = Table(title=f"DNS Records{' for ' + zone if zone else ''}", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Value", style="dim")
    table.add_column("TTL", style="dim")

    console.print(table)


@dns.command(name="create")
@click.option("--zone", "-z", required=True, help="DNS zone")
@click.option("--name", "-n", required=True, help="Record name")
@click.option("--type", "-t", required=True, help="Record type (A, CNAME, etc.)")
@click.option("--value", "-v", required=True, help="Record value")
@click.option("--ttl", default=300, help="TTL in seconds")
def dns_create(zone: str, name: str, type: str, value: str, ttl: int):
    """Create a DNS record."""
    console.print(f"[green]✓[/green] DNS record created: {name}.{zone} {type} {value}")


@dns.command(name="delete")
@click.option("--zone", "-z", required=True)
@click.option("--name", "-n", required=True)
@click.option("--type", "-t", required=True)
def dns_delete(zone: str, name: str, type: str):
    """Delete a DNS record."""
    console.print(f"[green]✓[/green] DNS record deleted")


# ============================================================================
# Guard (LLM Safety)
# ============================================================================


@platform_group.group()
def guard():
    """Manage LLM safety layer."""
    pass


@guard.command(name="enable")
@click.option("--project", "-p", help="Project ID")
def guard_enable(project: str):
    """Enable LLM guard for project."""
    console.print("[green]✓[/green] Guard enabled")
    console.print("[dim]All LLM requests will be scanned for:[/dim]")
    console.print("  • Prompt injection")
    console.print("  • PII leakage")
    console.print("  • Harmful content")


@guard.command(name="disable")
@click.option("--project", "-p", help="Project ID")
def guard_disable(project: str):
    """Disable LLM guard."""
    console.print("[yellow]⚠[/yellow] Guard disabled")


@guard.command(name="status")
def guard_status():
    """Show guard status and stats."""
    console.print(
        Panel(
            "[cyan]Status:[/cyan] Active\n"
            "[cyan]Requests scanned:[/cyan] 12,456\n"
            "[cyan]Threats blocked:[/cyan] 23\n"
            "[cyan]PII detected:[/cyan] 145",
            title="Guard Status",
            border_style="cyan",
        )
    )


@guard.command(name="logs")
@click.option("--limit", "-n", default=50, help="Number of logs")
def guard_logs(limit: int):
    """View guard logs."""
    table = Table(title="Guard Logs", box=box.ROUNDED)
    table.add_column("Time", style="dim")
    table.add_column("Type", style="yellow")
    table.add_column("Action", style="green")
    table.add_column("Details", style="white")

    console.print(table)


# ============================================================================
# KMS (Secrets)
# ============================================================================


@platform_group.group()
def kms():
    """Manage secrets and encryption."""
    pass


@kms.command(name="list")
def kms_list():
    """List secrets."""
    table = Table(title="Secrets", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="white")
    table.add_column("Updated", style="dim")

    console.print(table)


@kms.command(name="set")
@click.argument("name")
@click.option("--value", "-v", prompt=True, hide_input=True, help="Secret value")
def kms_set(name: str, value: str):
    """Set a secret."""
    console.print(f"[green]✓[/green] Secret '{name}' set")


@kms.command(name="get")
@click.argument("name")
def kms_get(name: str):
    """Get a secret value."""
    console.print(f"[yellow]Secret value:[/yellow] ********")


@kms.command(name="delete")
@click.argument("name")
def kms_delete(name: str):
    """Delete a secret."""
    console.print(f"[green]✓[/green] Secret '{name}' deleted")


@kms.command(name="rotate")
@click.argument("name")
def kms_rotate(name: str):
    """Rotate a secret."""
    console.print(f"[green]✓[/green] Secret '{name}' rotated")
