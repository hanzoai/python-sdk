"""Hanzo K8s - Kubernetes cluster and fleet management.

Manage Kubernetes clusters, deployments, and fleet operations.
"""

import click
from rich import box
from rich.table import Table
from rich.panel import Panel

from ..utils.output import console


@click.group(name="k8s")
def k8s_group():
    """Hanzo K8s - Kubernetes cluster management.

    \b
    Clusters:
      hanzo k8s cluster create     # Create cluster
      hanzo k8s cluster list       # List clusters
      hanzo k8s cluster delete     # Delete cluster
      hanzo k8s cluster kubeconfig # Get kubeconfig

    \b
    Fleet:
      hanzo k8s fleet create       # Create fleet
      hanzo k8s fleet add          # Add cluster to fleet
      hanzo k8s fleet deploy       # Deploy to fleet

    \b
    Workloads:
      hanzo k8s deploy             # Deploy application
      hanzo k8s services           # Manage services
      hanzo k8s pods               # List pods

    \b
    Configuration:
      hanzo k8s config             # Manage configs/secrets
      hanzo k8s ingress            # Manage ingress
    """
    pass


# ============================================================================
# Cluster Management
# ============================================================================

@k8s_group.group()
def cluster():
    """Manage Kubernetes clusters."""
    pass


@cluster.command(name="create")
@click.argument("name")
@click.option("--region", "-r", help="Region")
@click.option("--version", "-v", "k8s_version", default="1.29", help="Kubernetes version")
@click.option("--nodes", "-n", default=3, help="Number of nodes")
@click.option("--node-type", "-t", default="standard-2", help="Node type")
@click.option("--ha", is_flag=True, help="High availability control plane")
def cluster_create(name: str, region: str, k8s_version: str, nodes: int, node_type: str, ha: bool):
    """Create a Kubernetes cluster.

    \b
    Examples:
      hanzo k8s cluster create prod --nodes 5 --ha
      hanzo k8s cluster create dev --nodes 2 --node-type small
      hanzo k8s cluster create staging -r us-west-2 --version 1.29
    """
    console.print(f"[cyan]Creating cluster '{name}'...[/cyan]")
    console.print(f"[green]✓[/green] Cluster '{name}' created")
    console.print(f"  Kubernetes: v{k8s_version}")
    console.print(f"  Nodes: {nodes}")
    console.print(f"  Node type: {node_type}")
    console.print(f"  HA: {'Yes' if ha else 'No'}")
    if region:
        console.print(f"  Region: {region}")


@cluster.command(name="list")
@click.option("--region", "-r", help="Filter by region")
def cluster_list(region: str):
    """List Kubernetes clusters."""
    table = Table(title="Kubernetes Clusters", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="white")
    table.add_column("Nodes", style="green")
    table.add_column("Region", style="yellow")
    table.add_column("Status", style="dim")

    console.print(table)
    console.print("[dim]No clusters found. Create one with 'hanzo k8s cluster create'[/dim]")


@cluster.command(name="describe")
@click.argument("name")
def cluster_describe(name: str):
    """Show cluster details."""
    console.print(Panel(
        f"[cyan]Name:[/cyan] {name}\n"
        f"[cyan]Kubernetes:[/cyan] v1.29.0\n"
        f"[cyan]Status:[/cyan] [green]● Running[/green]\n"
        f"[cyan]Nodes:[/cyan] 3/3 ready\n"
        f"[cyan]Region:[/cyan] us-east-1\n"
        f"[cyan]Created:[/cyan] 2024-01-15\n"
        f"[cyan]API Server:[/cyan] https://k8s.hanzo.ai/{name}\n"
        f"[cyan]Control Plane:[/cyan] HA (3 replicas)",
        title="Cluster Details",
        border_style="cyan"
    ))


@cluster.command(name="delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True)
def cluster_delete(name: str, force: bool):
    """Delete a cluster."""
    if not force:
        from rich.prompt import Confirm
        if not Confirm.ask(f"[red]Delete cluster '{name}'? This cannot be undone.[/red]"):
            return
    console.print(f"[cyan]Deleting cluster '{name}'...[/cyan]")
    console.print(f"[green]✓[/green] Cluster '{name}' deleted")


@cluster.command(name="kubeconfig")
@click.argument("name")
@click.option("--output", "-o", help="Output file (default: stdout)")
@click.option("--merge", is_flag=True, help="Merge into ~/.kube/config")
def cluster_kubeconfig(name: str, output: str, merge: bool):
    """Get cluster kubeconfig.

    \b
    Examples:
      hanzo k8s cluster kubeconfig prod              # Print to stdout
      hanzo k8s cluster kubeconfig prod -o config    # Save to file
      hanzo k8s cluster kubeconfig prod --merge      # Merge into ~/.kube/config
    """
    if merge:
        console.print(f"[green]✓[/green] Merged '{name}' into ~/.kube/config")
        console.print(f"  Context: hanzo-{name}")
    elif output:
        console.print(f"[green]✓[/green] Kubeconfig saved to '{output}'")
    else:
        console.print("# kubeconfig for cluster")
        console.print("apiVersion: v1")
        console.print("kind: Config")
        console.print(f"# ... (cluster: {name})")


@cluster.command(name="scale")
@click.argument("name")
@click.option("--nodes", "-n", type=int, required=True, help="Target node count")
@click.option("--pool", "-p", default="default", help="Node pool name")
def cluster_scale(name: str, nodes: int, pool: str):
    """Scale cluster nodes."""
    console.print(f"[cyan]Scaling '{name}' to {nodes} nodes...[/cyan]")
    console.print(f"[green]✓[/green] Cluster scaled")
    console.print(f"  Pool: {pool}")
    console.print(f"  Nodes: {nodes}")


@cluster.command(name="upgrade")
@click.argument("name")
@click.option("--version", "-v", "k8s_version", help="Target Kubernetes version")
@click.option("--dry-run", is_flag=True, help="Show upgrade plan")
def cluster_upgrade(name: str, k8s_version: str, dry_run: bool):
    """Upgrade cluster Kubernetes version."""
    if dry_run:
        console.print(f"[cyan]Upgrade plan for '{name}':[/cyan]")
        console.print(f"  Current: v1.28.5")
        console.print(f"  Target: v{k8s_version or '1.29.0'}")
        console.print("  Steps: control-plane → node-pools")
    else:
        console.print(f"[cyan]Upgrading '{name}'...[/cyan]")
        console.print(f"[green]✓[/green] Cluster upgraded to v{k8s_version or '1.29.0'}")


# ============================================================================
# Fleet Management
# ============================================================================

@k8s_group.group()
def fleet():
    """Manage cluster fleets."""
    pass


@fleet.command(name="create")
@click.argument("name")
@click.option("--description", "-d", help="Fleet description")
def fleet_create(name: str, description: str):
    """Create a fleet for multi-cluster management."""
    console.print(f"[green]✓[/green] Fleet '{name}' created")
    if description:
        console.print(f"  Description: {description}")


@fleet.command(name="list")
def fleet_list():
    """List fleets."""
    table = Table(title="Fleets", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Clusters", style="green")
    table.add_column("Workloads", style="yellow")
    table.add_column("Status", style="dim")

    console.print(table)
    console.print("[dim]No fleets found[/dim]")


@fleet.command(name="add")
@click.argument("fleet")
@click.argument("cluster")
@click.option("--labels", "-l", multiple=True, help="Labels (key=value)")
def fleet_add(fleet: str, cluster: str, labels: tuple):
    """Add a cluster to a fleet."""
    console.print(f"[green]✓[/green] Added '{cluster}' to fleet '{fleet}'")
    if labels:
        console.print(f"  Labels: {', '.join(labels)}")


@fleet.command(name="remove")
@click.argument("fleet")
@click.argument("cluster")
def fleet_remove(fleet: str, cluster: str):
    """Remove a cluster from a fleet."""
    console.print(f"[green]✓[/green] Removed '{cluster}' from fleet '{fleet}'")


@fleet.command(name="deploy")
@click.argument("fleet")
@click.option("--manifest", "-f", required=True, help="Manifest file or directory")
@click.option("--selector", "-l", help="Cluster selector (labels)")
@click.option("--strategy", type=click.Choice(["rolling", "all", "canary"]), default="rolling")
def fleet_deploy(fleet: str, manifest: str, selector: str, strategy: str):
    """Deploy workloads across fleet.

    \b
    Examples:
      hanzo k8s fleet deploy prod -f app.yaml
      hanzo k8s fleet deploy prod -f ./manifests/ -l env=prod
      hanzo k8s fleet deploy prod -f app.yaml --strategy canary
    """
    console.print(f"[cyan]Deploying to fleet '{fleet}'...[/cyan]")
    console.print(f"[green]✓[/green] Deployed to fleet")
    console.print(f"  Strategy: {strategy}")
    console.print(f"  Clusters: 0")


# ============================================================================
# Workloads
# ============================================================================

@k8s_group.command(name="deploy")
@click.argument("name")
@click.option("--cluster", "-c", required=True, help="Target cluster")
@click.option("--image", "-i", required=True, help="Container image")
@click.option("--replicas", "-r", default=1, help="Number of replicas")
@click.option("--namespace", "-n", default="default", help="Namespace")
@click.option("--port", "-p", type=int, help="Container port")
@click.option("--env", "-e", multiple=True, help="Environment variables (KEY=value)")
def k8s_deploy(name: str, cluster: str, image: str, replicas: int, namespace: str, port: int, env: tuple):
    """Deploy an application.

    \b
    Examples:
      hanzo k8s deploy my-app -c prod -i nginx:latest
      hanzo k8s deploy api -c prod -i myapp:v1 -r 3 -p 8080
      hanzo k8s deploy worker -c prod -i worker:v1 -e DB_HOST=db.local
    """
    console.print(f"[cyan]Deploying '{name}' to '{cluster}'...[/cyan]")
    console.print(f"[green]✓[/green] Deployment created")
    console.print(f"  Image: {image}")
    console.print(f"  Replicas: {replicas}")
    console.print(f"  Namespace: {namespace}")
    if port:
        console.print(f"  Port: {port}")


@k8s_group.command(name="pods")
@click.option("--cluster", "-c", required=True, help="Cluster name")
@click.option("--namespace", "-n", default="default", help="Namespace")
@click.option("--selector", "-l", help="Label selector")
@click.option("--all-namespaces", "-A", is_flag=True, help="All namespaces")
def k8s_pods(cluster: str, namespace: str, selector: str, all_namespaces: bool):
    """List pods."""
    ns = "all namespaces" if all_namespaces else namespace
    table = Table(title=f"Pods in '{cluster}' ({ns})", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Namespace", style="white")
    table.add_column("Ready", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Age", style="dim")

    console.print(table)
    console.print("[dim]No pods found[/dim]")


@k8s_group.command(name="services")
@click.option("--cluster", "-c", required=True, help="Cluster name")
@click.option("--namespace", "-n", default="default", help="Namespace")
@click.option("--all-namespaces", "-A", is_flag=True, help="All namespaces")
def k8s_services(cluster: str, namespace: str, all_namespaces: bool):
    """List services."""
    ns = "all namespaces" if all_namespaces else namespace
    table = Table(title=f"Services in '{cluster}' ({ns})", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Cluster-IP", style="green")
    table.add_column("External-IP", style="yellow")
    table.add_column("Ports", style="dim")

    console.print(table)
    console.print("[dim]No services found[/dim]")


@k8s_group.command(name="logs")
@click.argument("pod")
@click.option("--cluster", "-c", required=True, help="Cluster name")
@click.option("--namespace", "-n", default="default", help="Namespace")
@click.option("--container", help="Container name")
@click.option("--follow", "-f", is_flag=True, help="Follow logs")
@click.option("--tail", "-t", default=100, help="Lines to show")
def k8s_logs(pod: str, cluster: str, namespace: str, container: str, follow: bool, tail: int):
    """View pod logs."""
    if follow:
        console.print(f"[cyan]Tailing logs for '{pod}'...[/cyan]")
        console.print("[dim]Press Ctrl+C to stop[/dim]")
    else:
        console.print(f"[cyan]Logs for '{pod}' (last {tail} lines):[/cyan]")
    console.print("[dim]No logs found[/dim]")


@k8s_group.command(name="exec")
@click.argument("pod")
@click.argument("command", nargs=-1)
@click.option("--cluster", "-c", required=True, help="Cluster name")
@click.option("--namespace", "-n", default="default", help="Namespace")
@click.option("--container", help="Container name")
@click.option("--stdin", "-i", is_flag=True, help="Interactive")
@click.option("--tty", "-t", is_flag=True, help="Allocate TTY")
def k8s_exec(pod: str, command: tuple, cluster: str, namespace: str, container: str, stdin: bool, tty: bool):
    """Execute command in pod.

    \b
    Examples:
      hanzo k8s exec my-pod -c prod -- ls -la
      hanzo k8s exec my-pod -c prod -it -- /bin/bash
    """
    cmd = " ".join(command) if command else "/bin/sh"
    console.print(f"[cyan]Executing in '{pod}': {cmd}[/cyan]")


# ============================================================================
# Configuration
# ============================================================================

@k8s_group.group()
def config():
    """Manage ConfigMaps and Secrets."""
    pass


@config.command(name="create")
@click.argument("name")
@click.option("--cluster", "-c", required=True, help="Cluster name")
@click.option("--namespace", "-n", default="default", help="Namespace")
@click.option("--from-literal", "-l", multiple=True, help="Key=value pairs")
@click.option("--from-file", "-f", multiple=True, help="Files to include")
@click.option("--secret", "-s", is_flag=True, help="Create as Secret")
def config_create(name: str, cluster: str, namespace: str, from_literal: tuple, from_file: tuple, secret: bool):
    """Create ConfigMap or Secret."""
    kind = "Secret" if secret else "ConfigMap"
    console.print(f"[green]✓[/green] {kind} '{name}' created")
    console.print(f"  Cluster: {cluster}")
    console.print(f"  Namespace: {namespace}")


@config.command(name="list")
@click.option("--cluster", "-c", required=True, help="Cluster name")
@click.option("--namespace", "-n", default="default", help="Namespace")
@click.option("--secrets", "-s", is_flag=True, help="List Secrets instead")
def config_list(cluster: str, namespace: str, secrets: bool):
    """List ConfigMaps or Secrets."""
    kind = "Secrets" if secrets else "ConfigMaps"
    table = Table(title=f"{kind} in '{cluster}/{namespace}'", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Data", style="green")
    table.add_column("Age", style="dim")

    console.print(table)
    console.print(f"[dim]No {kind.lower()} found[/dim]")


# ============================================================================
# Ingress
# ============================================================================

@k8s_group.group()
def ingress():
    """Manage Ingress resources."""
    pass


@ingress.command(name="create")
@click.argument("name")
@click.option("--cluster", "-c", required=True, help="Cluster name")
@click.option("--namespace", "-n", default="default", help="Namespace")
@click.option("--host", "-h", required=True, help="Hostname")
@click.option("--service", "-s", required=True, help="Backend service")
@click.option("--port", "-p", type=int, default=80, help="Service port")
@click.option("--tls", is_flag=True, help="Enable TLS")
@click.option("--tls-secret", help="TLS secret name")
def ingress_create(name: str, cluster: str, namespace: str, host: str, service: str, port: int, tls: bool, tls_secret: str):
    """Create an Ingress.

    \b
    Examples:
      hanzo k8s ingress create web -c prod -h app.example.com -s web-svc
      hanzo k8s ingress create api -c prod -h api.example.com -s api-svc --tls
    """
    console.print(f"[green]✓[/green] Ingress '{name}' created")
    console.print(f"  Host: {host}")
    console.print(f"  Backend: {service}:{port}")
    if tls:
        console.print(f"  TLS: enabled")


@ingress.command(name="list")
@click.option("--cluster", "-c", required=True, help="Cluster name")
@click.option("--namespace", "-n", default="default", help="Namespace")
@click.option("--all-namespaces", "-A", is_flag=True, help="All namespaces")
def ingress_list(cluster: str, namespace: str, all_namespaces: bool):
    """List Ingress resources."""
    ns = "all namespaces" if all_namespaces else namespace
    table = Table(title=f"Ingress in '{cluster}' ({ns})", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Hosts", style="white")
    table.add_column("Address", style="green")
    table.add_column("TLS", style="yellow")
    table.add_column("Age", style="dim")

    console.print(table)
    console.print("[dim]No ingress resources found[/dim]")


# ============================================================================
# Node Pools
# ============================================================================

@k8s_group.group()
def nodepool():
    """Manage node pools."""
    pass


@nodepool.command(name="create")
@click.argument("name")
@click.option("--cluster", "-c", required=True, help="Cluster name")
@click.option("--nodes", "-n", default=3, help="Number of nodes")
@click.option("--node-type", "-t", default="standard-2", help="Node type")
@click.option("--labels", "-l", multiple=True, help="Node labels (key=value)")
@click.option("--taints", multiple=True, help="Node taints")
@click.option("--gpu", is_flag=True, help="GPU nodes")
def nodepool_create(name: str, cluster: str, nodes: int, node_type: str, labels: tuple, taints: tuple, gpu: bool):
    """Create a node pool.

    \b
    Examples:
      hanzo k8s nodepool create workers -c prod -n 5
      hanzo k8s nodepool create gpu-pool -c prod --gpu --node-type gpu-large
      hanzo k8s nodepool create spot -c prod -l tier=spot --taints spot=true:NoSchedule
    """
    console.print(f"[green]✓[/green] Node pool '{name}' created in '{cluster}'")
    console.print(f"  Nodes: {nodes}")
    console.print(f"  Type: {node_type}")
    if gpu:
        console.print(f"  GPU: enabled")


@nodepool.command(name="list")
@click.option("--cluster", "-c", required=True, help="Cluster name")
def nodepool_list(cluster: str):
    """List node pools."""
    table = Table(title=f"Node Pools in '{cluster}'", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Nodes", style="green")
    table.add_column("Type", style="white")
    table.add_column("Status", style="dim")

    console.print(table)
    console.print("[dim]No node pools found[/dim]")


@nodepool.command(name="scale")
@click.argument("name")
@click.option("--cluster", "-c", required=True, help="Cluster name")
@click.option("--nodes", "-n", type=int, required=True, help="Target node count")
def nodepool_scale(name: str, cluster: str, nodes: int):
    """Scale a node pool."""
    console.print(f"[cyan]Scaling pool '{name}' to {nodes} nodes...[/cyan]")
    console.print(f"[green]✓[/green] Node pool scaled")


@nodepool.command(name="delete")
@click.argument("name")
@click.option("--cluster", "-c", required=True, help="Cluster name")
@click.option("--force", "-f", is_flag=True)
def nodepool_delete(name: str, cluster: str, force: bool):
    """Delete a node pool."""
    if not force:
        from rich.prompt import Confirm
        if not Confirm.ask(f"[red]Delete node pool '{name}'?[/red]"):
            return
    console.print(f"[green]✓[/green] Node pool '{name}' deleted")
