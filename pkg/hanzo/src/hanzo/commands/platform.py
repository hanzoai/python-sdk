"""Hanzo Platform - Infrastructure and security CLI.

Edge, HKE, networking, tunnel, DNS, guard.
"""

import os
import json

import click
import httpx
from rich import box
from rich.panel import Panel
from rich.table import Table

from .base import check_response, service_request
from ..utils.output import console

SERVICE_URL = os.getenv("HANZO_PLATFORM_URL", "https://platform.hanzo.ai")


def _request(method: str, path: str, **kwargs) -> httpx.Response:
    return service_request(SERVICE_URL, method, path, **kwargs)


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
    resp = _request("get", "/v1/edge/deployments")
    data = check_response(resp)

    table = Table(title="Edge Deployments", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("URL", style="white")
    table.add_column("Regions", style="dim")
    table.add_column("Status", style="green")

    for d in data.get("deployments", []):
        st = d.get("status", "active")
        st_style = "green" if st == "active" else "yellow"
        table.add_row(
            d.get("name", ""),
            d.get("url", ""),
            ", ".join(d.get("regions", [])),
            f"[{st_style}]{st}[/{st_style}]",
        )

    console.print(table)


@edge.command(name="deploy")
@click.option("--name", "-n", prompt=True, help="Deployment name")
@click.option("--dir", "-d", "source_dir", default=".", help="Directory to deploy")
@click.option(
    "--regions", "-r", default="all", help="Target regions (comma-separated or 'all')"
)
def edge_deploy(name: str, source_dir: str, regions: str):
    """Deploy to edge locations."""
    region_list = (
        [r.strip() for r in regions.split(",")] if regions != "all" else ["all"]
    )
    resp = _request(
        "post",
        "/v1/edge/deployments",
        json={
            "name": name,
            "source_dir": source_dir,
            "regions": region_list,
        },
    )
    data = check_response(resp)

    console.print(f"[green]✓[/green] Deployed '{name}' to edge")
    console.print(f"[dim]URL: {data.get('url', f'https://{name}.edge.hanzo.ai')}[/dim]")


@edge.command(name="purge")
@click.argument("name")
@click.option("--path", "-p", help="Specific path to purge")
def edge_purge(name: str, path: str):
    """Purge edge cache."""
    payload: dict = {}
    if path:
        payload["path"] = path
    resp = _request("post", f"/v1/edge/deployments/{name}/purge", json=payload)
    check_response(resp)
    if path:
        console.print(f"[green]✓[/green] Purged cache for {path}")
    else:
        console.print(f"[green]✓[/green] Purged all cache for {name}")


@edge.command(name="delete")
@click.argument("name")
def edge_delete(name: str):
    """Delete an edge deployment."""
    resp = _request("delete", f"/v1/edge/deployments/{name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Edge deployment '{name}' deleted")


@edge.command(name="stats")
@click.argument("name")
@click.option("--period", "-p", default="24h", help="Time period")
def edge_stats(name: str, period: str):
    """Show edge deployment statistics."""
    resp = _request(
        "get", f"/v1/edge/deployments/{name}/stats", params={"period": period}
    )
    data = check_response(resp)

    info = (
        f"[cyan]Deployment:[/cyan] {name}\n"
        f"[cyan]Requests:[/cyan] {data.get('requests', 0):,}\n"
        f"[cyan]Bandwidth:[/cyan] {data.get('bandwidth', 'N/A')}\n"
        f"[cyan]Cache Hit Rate:[/cyan] {data.get('cache_hit_rate', 0):.0f}%\n"
        f"[cyan]Avg Latency:[/cyan] {data.get('avg_latency', 'N/A')}"
    )
    console.print(Panel(info, title="Edge Stats", border_style="cyan"))


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
    resp = _request("get", "/v1/hke/clusters")
    data = check_response(resp)

    table = Table(title="HKE Clusters", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="white")
    table.add_column("Nodes", style="white")
    table.add_column("Status", style="green")
    table.add_column("Region", style="dim")

    for c in data.get("clusters", []):
        st = c.get("status", "running")
        st_style = {"running": "green", "provisioning": "yellow", "error": "red"}.get(
            st, "white"
        )
        table.add_row(
            c.get("name", ""),
            c.get("version", ""),
            str(c.get("node_count", 0)),
            f"[{st_style}]{st}[/{st_style}]",
            c.get("region", ""),
        )

    console.print(table)


@hke.command(name="create")
@click.option("--name", "-n", prompt=True, help="Cluster name")
@click.option("--version", "-v", default="1.29", help="Kubernetes version")
@click.option("--nodes", default=3, help="Number of nodes")
@click.option("--region", "-r", default="us-west-2", help="Region")
@click.option("--gpu", is_flag=True, help="Enable GPU node pool")
@click.option("--node-size", default="s-4vcpu-8gb", help="Node size")
def hke_create(
    name: str, version: str, nodes: int, region: str, gpu: bool, node_size: str
):
    """Create a Kubernetes cluster."""
    resp = _request(
        "post",
        "/v1/hke/clusters",
        json={
            "name": name,
            "version": version,
            "node_count": nodes,
            "region": region,
            "gpu": gpu,
            "node_size": node_size,
        },
    )
    data = check_response(resp)

    console.print(f"[green]✓[/green] Cluster '{name}' creation initiated")
    console.print(f"  Version: {version}")
    console.print(f"  Nodes: {nodes}")
    console.print(f"  Region: {region}")
    console.print(f"  GPU: {'Yes' if gpu else 'No'}")
    console.print(f"  ID: {data.get('id', '')}")


@hke.command(name="delete")
@click.argument("name")
@click.option("--confirm", "confirmed", is_flag=True, help="Skip confirmation")
def hke_delete(name: str, confirmed: bool):
    """Delete a Kubernetes cluster."""
    if not confirmed:
        from rich.prompt import Confirm

        if not Confirm.ask(
            f"[red]Delete cluster '{name}'? This cannot be undone.[/red]"
        ):
            return
    resp = _request("delete", f"/v1/hke/clusters/{name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Cluster '{name}' deletion initiated")


@hke.command(name="kubeconfig")
@click.argument("name")
@click.option("--output", "-o", help="Output file path")
def hke_kubeconfig(name: str, output: str):
    """Get kubeconfig for a cluster."""
    resp = _request("get", f"/v1/hke/clusters/{name}/kubeconfig")
    data = check_response(resp)

    kubeconfig = data.get("kubeconfig", "")
    if output:
        with open(output, "w") as f:
            f.write(kubeconfig)
        console.print(f"[green]✓[/green] Kubeconfig saved to {output}")
    else:
        import os as _os

        kube_path = _os.path.expanduser("~/.kube/config")
        with open(kube_path, "w") as f:
            f.write(kubeconfig)
        console.print(f"[green]✓[/green] Kubeconfig saved to ~/.kube/config")


@hke.command(name="scale")
@click.argument("name")
@click.option("--nodes", "-n", required=True, type=int, help="Target nodes")
def hke_scale(name: str, nodes: int):
    """Scale cluster nodes."""
    resp = _request(
        "post", f"/v1/hke/clusters/{name}/scale", json={"node_count": nodes}
    )
    check_response(resp)
    console.print(f"[green]✓[/green] Cluster '{name}' scaling to {nodes} nodes")


@hke.command(name="upgrade")
@click.argument("name")
@click.option("--version", "-v", required=True, help="Target Kubernetes version")
def hke_upgrade(name: str, version: str):
    """Upgrade cluster Kubernetes version."""
    resp = _request(
        "post", f"/v1/hke/clusters/{name}/upgrade", json={"version": version}
    )
    check_response(resp)
    console.print(f"[green]✓[/green] Cluster '{name}' upgrading to {version}")


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
    payload: dict = {"target": target}
    if name:
        payload["subdomain"] = name
    if auth:
        payload["auth_required"] = True

    resp = _request("post", "/v1/tunnels", json=payload)
    data = check_response(resp)

    subdomain = data.get("subdomain", name or "random")
    url = data.get("url", f"https://{subdomain}.tunnel.hanzo.ai")

    console.print(f"[green]✓[/green] Tunnel active")
    console.print(f"  [cyan]Public URL:[/cyan] {url}")
    console.print(f"  [cyan]Target:[/cyan] {target}")
    if auth:
        console.print(f"  [cyan]Auth:[/cyan] Required")
    console.print()
    console.print("Press Ctrl+C to stop")

    try:
        tunnel_id = data.get("id", "")
        import time

        while True:
            time.sleep(30)
            _request("post", f"/v1/tunnels/{tunnel_id}/keepalive")
    except KeyboardInterrupt:
        _request("delete", f"/v1/tunnels/{tunnel_id}")
        console.print("\n[dim]Tunnel closed[/dim]")


@tunnel.command(name="list")
def tunnel_list():
    """List active tunnels."""
    resp = _request("get", "/v1/tunnels")
    data = check_response(resp)

    table = Table(title="Active Tunnels", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Target", style="white")
    table.add_column("URL", style="dim")
    table.add_column("Status", style="green")

    for t in data.get("tunnels", []):
        st = t.get("status", "active")
        st_style = "green" if st == "active" else "yellow"
        table.add_row(
            t.get("subdomain", ""),
            t.get("target", ""),
            t.get("url", ""),
            f"[{st_style}]{st}[/{st_style}]",
        )

    console.print(table)


@tunnel.command(name="stop")
@click.argument("name")
def tunnel_stop(name: str):
    """Stop a tunnel."""
    resp = _request("delete", f"/v1/tunnels/{name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Tunnel '{name}' stopped")


# ============================================================================
# DNS
# ============================================================================


@platform_group.group()
def dns():
    """Manage DNS records."""
    pass


@dns.command(name="zones")
def dns_zones():
    """List DNS zones."""
    resp = _request("get", "/v1/dns/zones")
    data = check_response(resp)

    table = Table(title="DNS Zones", box=box.ROUNDED)
    table.add_column("Zone", style="cyan")
    table.add_column("Records", style="white")
    table.add_column("Status", style="green")

    for z in data.get("zones", []):
        table.add_row(
            z.get("name", ""),
            str(z.get("record_count", 0)),
            z.get("status", "active"),
        )

    console.print(table)


@dns.command(name="list")
@click.argument("zone", required=False)
def dns_list(zone: str):
    """List DNS records."""
    path = f"/v1/dns/zones/{zone}/records" if zone else "/v1/dns/records"
    resp = _request("get", path)
    data = check_response(resp)

    table = Table(title=f"DNS Records{' for ' + zone if zone else ''}", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Value", style="dim")
    table.add_column("TTL", style="dim")
    table.add_column("Proxied", style="green")

    for r in data.get("records", []):
        proxied = r.get("proxied", False)
        table.add_row(
            r.get("name", ""),
            r.get("type", ""),
            r.get("value", ""),
            str(r.get("ttl", 300)),
            "[green]yes[/green]" if proxied else "[dim]no[/dim]",
        )

    console.print(table)


@dns.command(name="create")
@click.option("--zone", "-z", required=True, help="DNS zone")
@click.option("--name", "-n", required=True, help="Record name")
@click.option(
    "--type", "-t", "record_type", required=True, help="Record type (A, CNAME, etc.)"
)
@click.option("--value", "-v", required=True, help="Record value")
@click.option("--ttl", default=300, help="TTL in seconds")
@click.option("--proxied", is_flag=True, help="Enable proxy")
def dns_create(
    zone: str, name: str, record_type: str, value: str, ttl: int, proxied: bool
):
    """Create a DNS record."""
    resp = _request(
        "post",
        f"/v1/dns/zones/{zone}/records",
        json={
            "name": name,
            "type": record_type,
            "value": value,
            "ttl": ttl,
            "proxied": proxied,
        },
    )
    check_response(resp)
    console.print(
        f"[green]✓[/green] DNS record created: {name}.{zone} {record_type} {value}"
    )


@dns.command(name="delete")
@click.option("--zone", "-z", required=True)
@click.option("--name", "-n", required=True)
@click.option("--type", "-t", "record_type", required=True)
def dns_delete(zone: str, name: str, record_type: str):
    """Delete a DNS record."""
    resp = _request(
        "delete",
        f"/v1/dns/zones/{zone}/records",
        params={"name": name, "type": record_type},
    )
    check_response(resp)
    console.print(f"[green]✓[/green] DNS record deleted: {name}.{zone} {record_type}")


# ============================================================================
# Guard (LLM Safety)
# ============================================================================


@platform_group.group()
def guard():
    """Manage LLM safety layer."""
    pass


@guard.command(name="enable")
@click.option("--project", "-p", help="Project ID")
@click.option(
    "--mode",
    "-m",
    type=click.Choice(["block", "warn", "log"]),
    default="block",
    help="Enforcement mode",
)
def guard_enable(project: str, mode: str):
    """Enable LLM guard for project."""
    payload: dict = {"enabled": True, "mode": mode}
    if project:
        payload["project_id"] = project
    resp = _request("post", "/v1/guard/config", json=payload)
    check_response(resp)
    console.print(f"[green]✓[/green] Guard enabled (mode: {mode})")
    console.print("[dim]All LLM requests will be scanned for:[/dim]")
    console.print("  - Prompt injection")
    console.print("  - PII leakage")
    console.print("  - Harmful content")


@guard.command(name="disable")
@click.option("--project", "-p", help="Project ID")
def guard_disable(project: str):
    """Disable LLM guard."""
    payload: dict = {"enabled": False}
    if project:
        payload["project_id"] = project
    resp = _request("post", "/v1/guard/config", json=payload)
    check_response(resp)
    console.print("[yellow]Guard disabled[/yellow]")


@guard.command(name="status")
@click.option("--project", "-p", help="Project ID")
def guard_status(project: str):
    """Show guard status and stats."""
    params: dict = {}
    if project:
        params["project_id"] = project
    resp = _request("get", "/v1/guard/status", params=params)
    data = check_response(resp)

    enabled = data.get("enabled", False)
    status_str = "[green]Active[/green]" if enabled else "[red]Disabled[/red]"

    info = (
        f"[cyan]Status:[/cyan] {status_str}\n"
        f"[cyan]Mode:[/cyan] {data.get('mode', 'N/A')}\n"
        f"[cyan]Requests scanned:[/cyan] {data.get('requests_scanned', 0):,}\n"
        f"[cyan]Threats blocked:[/cyan] {data.get('threats_blocked', 0):,}\n"
        f"[cyan]PII detected:[/cyan] {data.get('pii_detected', 0):,}\n"
        f"[cyan]Injections caught:[/cyan] {data.get('injections_caught', 0):,}"
    )
    console.print(Panel(info, title="Guard Status", border_style="cyan"))


@guard.command(name="logs")
@click.option("--limit", "-n", default=50, help="Number of logs")
@click.option(
    "--type",
    "-t",
    "log_type",
    type=click.Choice(["all", "blocked", "warned", "pii", "injection"]),
    default="all",
)
def guard_logs(limit: int, log_type: str):
    """View guard logs."""
    params: dict = {"limit": limit}
    if log_type != "all":
        params["type"] = log_type
    resp = _request("get", "/v1/guard/logs", params=params)
    data = check_response(resp)

    table = Table(title="Guard Logs", box=box.ROUNDED)
    table.add_column("Time", style="dim")
    table.add_column("Type", style="yellow")
    table.add_column("Action", style="green")
    table.add_column("Details", style="white")

    for entry in data.get("logs", []):
        action = entry.get("action", "log")
        action_style = {"blocked": "red", "warned": "yellow"}.get(action, "green")
        table.add_row(
            entry.get("timestamp", ""),
            entry.get("type", ""),
            f"[{action_style}]{action}[/{action_style}]",
            entry.get("details", ""),
        )

    console.print(table)


@guard.command(name="rules")
def guard_rules():
    """List guard rules."""
    resp = _request("get", "/v1/guard/rules")
    data = check_response(resp)

    table = Table(title="Guard Rules", box=box.ROUNDED)
    table.add_column("Rule", style="cyan")
    table.add_column("Category", style="white")
    table.add_column("Action", style="green")
    table.add_column("Status", style="dim")

    for r in data.get("rules", []):
        enabled = r.get("enabled", True)
        status_str = "[green]active[/green]" if enabled else "[dim]disabled[/dim]"
        table.add_row(
            r.get("name", ""),
            r.get("category", ""),
            r.get("action", "block"),
            status_str,
        )

    console.print(table)


# ============================================================================
# KMS (Secrets)
# ============================================================================


@platform_group.group()
def kms():
    """Manage secrets and encryption."""
    pass


@kms.command(name="list")
@click.option("--workspace", "-w", help="Workspace ID")
def kms_list(workspace: str):
    """List secrets."""
    params: dict = {}
    if workspace:
        params["workspace"] = workspace
    resp = _request("get", "/v1/kms/secrets", params=params)
    data = check_response(resp)

    table = Table(title="Secrets", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="white")
    table.add_column("Updated", style="dim")

    for s in data.get("secrets", []):
        table.add_row(
            s.get("name", ""),
            str(s.get("version", 1)),
            s.get("updated_at", ""),
        )

    console.print(table)


@kms.command(name="set")
@click.argument("name")
@click.option("--value", "-v", prompt=True, hide_input=True, help="Secret value")
@click.option("--workspace", "-w", help="Workspace ID")
def kms_set(name: str, value: str, workspace: str):
    """Set a secret."""
    payload: dict = {"name": name, "value": value}
    if workspace:
        payload["workspace"] = workspace
    resp = _request("post", "/v1/kms/secrets", json=payload)
    check_response(resp)
    console.print(f"[green]✓[/green] Secret '{name}' set")


@kms.command(name="get")
@click.argument("name")
@click.option("--workspace", "-w", help="Workspace ID")
@click.option("--reveal", is_flag=True, help="Show actual value")
def kms_get(name: str, workspace: str, reveal: bool):
    """Get a secret value."""
    params: dict = {}
    if workspace:
        params["workspace"] = workspace
    resp = _request("get", f"/v1/kms/secrets/{name}", params=params)
    data = check_response(resp)

    if reveal:
        console.print(f"[yellow]Secret value:[/yellow] {data.get('value', '')}")
    else:
        console.print(f"[yellow]Secret value:[/yellow] ********")
        console.print("[dim]Use --reveal to show actual value[/dim]")


@kms.command(name="delete")
@click.argument("name")
@click.option("--workspace", "-w", help="Workspace ID")
def kms_delete(name: str, workspace: str):
    """Delete a secret."""
    params: dict = {}
    if workspace:
        params["workspace"] = workspace
    resp = _request("delete", f"/v1/kms/secrets/{name}", params=params)
    check_response(resp)
    console.print(f"[green]✓[/green] Secret '{name}' deleted")


@kms.command(name="rotate")
@click.argument("name")
@click.option("--workspace", "-w", help="Workspace ID")
def kms_rotate(name: str, workspace: str):
    """Rotate a secret."""
    payload: dict = {}
    if workspace:
        payload["workspace"] = workspace
    resp = _request("post", f"/v1/kms/secrets/{name}/rotate", json=payload)
    check_response(resp)
    console.print(f"[green]✓[/green] Secret '{name}' rotated")
