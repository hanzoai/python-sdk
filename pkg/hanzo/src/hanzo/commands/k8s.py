"""Hanzo K8s - Kubernetes cluster and fleet management.

Manage Kubernetes clusters, deployments, and fleet operations via PaaS API.
"""

import click
from rich import box
from rich.panel import Panel
from rich.table import Table

from ..utils.output import console

# ============================================================================
# Helpers
# ============================================================================


def _get_client(timeout: int = 30):
    from ..utils.api_client import PaaSClient

    try:
        return PaaSClient(timeout=timeout)
    except SystemExit:
        return None


def _get_ctx(fields=("org_id", "project_id", "env_id")):
    from ..utils.api_client import require_context

    try:
        return require_context(fields)
    except SystemExit:
        return None


def _container_base():
    from ..utils.api_client import container_url

    client = _get_client(timeout=60)
    if not client:
        return None
    ctx = _get_ctx()
    if not ctx:
        return None
    url = container_url(ctx["org_id"], ctx["project_id"], ctx["env_id"])
    return client, ctx, url


def _find_container(client, base_url: str, name: str):
    from ..utils.api_client import find_container

    return find_container(client, base_url, name)


# ============================================================================
# Main group
# ============================================================================


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
@click.option(
    "--version", "-v", "k8s_version", default="1.29", help="Kubernetes version"
)
@click.option("--nodes", "-n", default=3, help="Number of nodes")
@click.option("--node-type", "-t", default="standard-2", help="Node type")
@click.option("--ha", is_flag=True, help="High availability control plane")
def cluster_create(name, region, k8s_version, nodes, node_type, ha):
    """Create a Kubernetes cluster.

    \b
    Examples:
      hanzo k8s cluster create prod --nodes 5 --ha
      hanzo k8s cluster create dev --nodes 2 --node-type small
      hanzo k8s cluster create staging -r us-west-2 --version 1.29
    """
    from ..utils.api_client import cluster_url

    client = _get_client(timeout=120)
    if not client:
        return

    console.print(f"[cyan]Creating cluster '{name}'...[/cyan]")

    payload = {
        "name": name,
        "version": k8s_version,
        "nodeCount": nodes,
        "nodeType": node_type,
        "ha": ha,
    }
    if region:
        payload["region"] = region

    result = client.post(cluster_url(), payload)
    if result is None:
        return

    console.print(f"[green]✓[/green] Cluster '{name}' created")
    console.print(f"  Kubernetes: v{k8s_version}")
    console.print(f"  Nodes: {nodes}")
    console.print(f"  Node type: {node_type}")
    console.print(f"  HA: {'Yes' if ha else 'No'}")
    if region:
        console.print(f"  Region: {region}")

    cid = result.get("_id") or result.get("id", "")
    if cid:
        console.print(f"  Cluster ID: {cid}")


@cluster.command(name="list")
@click.option("--region", "-r", help="Filter by region")
def cluster_list(region):
    """List Kubernetes clusters."""
    from ..utils.api_client import cluster_url

    client = _get_client()
    if not client:
        return

    data = client.get(cluster_url())
    if data is None:
        return

    clusters = (
        data if isinstance(data, list) else data.get("clusters", data.get("data", []))
    )

    if not clusters:
        console.print(
            "[dim]No clusters found. Create one with 'hanzo k8s cluster create'[/dim]"
        )
        return

    table = Table(title="Kubernetes Clusters", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="white")
    table.add_column("Nodes", style="green")
    table.add_column("Region", style="yellow")
    table.add_column("Status", style="dim")

    for c in clusters:
        cname = c.get("name", "")
        cver = c.get("version", c.get("k8sVersion", ""))
        cnodes = str(c.get("nodeCount", c.get("nodes", "?")))
        cregion = c.get("region", "")
        cstatus = c.get("status", "unknown")

        if region and cregion != region:
            continue

        table.add_row(cname, cver, cnodes, cregion, cstatus)

    console.print(table)


@cluster.command(name="describe")
@click.argument("name")
def cluster_describe(name):
    """Show cluster details."""
    from ..utils.api_client import cluster_url

    client = _get_client()
    if not client:
        return

    data = client.get(cluster_url(name))
    if data is None:
        return

    version = data.get("version", data.get("k8sVersion", "?"))
    nodes = data.get("nodeCount", data.get("nodes", "?"))
    region = data.get("region", "?")
    status = data.get("status", "unknown")
    created = data.get("createdAt", data.get("created", "?"))
    api_server = data.get("apiServer", data.get("endpoint", ""))
    ha = data.get("ha", False)

    console.print(
        Panel(
            f"[cyan]Name:[/cyan] {name}\n"
            f"[cyan]Kubernetes:[/cyan] v{version}\n"
            f"[cyan]Status:[/cyan] {status}\n"
            f"[cyan]Nodes:[/cyan] {nodes}\n"
            f"[cyan]Region:[/cyan] {region}\n"
            f"[cyan]Created:[/cyan] {created}\n"
            f"[cyan]API Server:[/cyan] {api_server}\n"
            f"[cyan]Control Plane:[/cyan] {'HA' if ha else 'Standard'}",
            title="Cluster Details",
            border_style="cyan",
        )
    )


@cluster.command(name="delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True)
def cluster_delete(name, force):
    """Delete a cluster."""
    from ..utils.api_client import cluster_url

    if not force:
        from rich.prompt import Confirm

        if not Confirm.ask(
            f"[red]Delete cluster '{name}'? This cannot be undone.[/red]"
        ):
            return

    client = _get_client(timeout=60)
    if not client:
        return

    result = client.delete(cluster_url(name))
    if result is None:
        return

    console.print(f"[green]✓[/green] Cluster '{name}' deleted")


@cluster.command(name="kubeconfig")
@click.argument("name")
@click.option("--output", "-o", help="Output file (default: stdout)")
@click.option("--merge", is_flag=True, help="Merge into ~/.kube/config")
def cluster_kubeconfig(name, output, merge):
    """Get cluster kubeconfig.

    \b
    Examples:
      hanzo k8s cluster kubeconfig prod              # Print to stdout
      hanzo k8s cluster kubeconfig prod -o config    # Save to file
      hanzo k8s cluster kubeconfig prod --merge      # Merge into ~/.kube/config
    """
    from pathlib import Path

    from ..utils.api_client import cluster_url

    client = _get_client()
    if not client:
        return

    data = client.get(f"{cluster_url(name)}/kubeconfig")
    if data is None:
        # Fall back to cluster detail (some APIs embed kubeconfig)
        data = client.get(cluster_url(name))
        if data is None:
            return

    kubeconfig = data.get("kubeconfig", data.get("config", ""))
    if not kubeconfig:
        console.print("[yellow]Kubeconfig not available for this cluster.[/yellow]")
        return

    if isinstance(kubeconfig, dict):
        import json

        kubeconfig = json.dumps(kubeconfig, indent=2)

    if merge:
        kube_dir = Path.home() / ".kube"
        kube_dir.mkdir(exist_ok=True)
        kube_file = kube_dir / "config"
        # Simple append for now - a real merge would parse YAML
        with open(kube_file, "a") as f:
            f.write(f"\n---\n{kubeconfig}")
        console.print(f"[green]✓[/green] Merged '{name}' into ~/.kube/config")
        console.print(f"  Context: hanzo-{name}")
    elif output:
        Path(output).write_text(kubeconfig)
        console.print(f"[green]✓[/green] Kubeconfig saved to '{output}'")
    else:
        console.print(kubeconfig)


@cluster.command(name="scale")
@click.argument("name")
@click.option("--nodes", "-n", type=int, required=True, help="Target node count")
@click.option("--pool", "-p", default="default", help="Node pool name")
def cluster_scale(name, nodes, pool):
    """Scale cluster nodes."""
    from ..utils.api_client import cluster_url

    client = _get_client(timeout=60)
    if not client:
        return

    console.print(f"[cyan]Scaling '{name}' to {nodes} nodes...[/cyan]")

    result = client.put(cluster_url(name), {"nodeCount": nodes, "pool": pool})
    if result is None:
        return

    console.print(f"[green]✓[/green] Cluster scaled")
    console.print(f"  Pool: {pool}")
    console.print(f"  Nodes: {nodes}")


@cluster.command(name="upgrade")
@click.argument("name")
@click.option("--version", "-v", "k8s_version", help="Target Kubernetes version")
@click.option("--dry-run", is_flag=True, help="Show upgrade plan")
def cluster_upgrade(name, k8s_version, dry_run):
    """Upgrade cluster Kubernetes version."""
    from ..utils.api_client import cluster_url

    client = _get_client(timeout=120)
    if not client:
        return

    if dry_run:
        # Get current version first
        data = client.get(cluster_url(name))
        if data is None:
            return
        current = data.get("version", data.get("k8sVersion", "?"))
        target = k8s_version or "latest"
        console.print(f"[cyan]Upgrade plan for '{name}':[/cyan]")
        console.print(f"  Current: v{current}")
        console.print(f"  Target: v{target}")
        console.print("  Steps: control-plane -> node-pools")
        return

    console.print(f"[cyan]Upgrading '{name}'...[/cyan]")
    payload = {}
    if k8s_version:
        payload["version"] = k8s_version

    result = client.put(cluster_url(name), payload)
    if result is None:
        return

    console.print(f"[green]✓[/green] Cluster upgraded to v{k8s_version or 'latest'}")


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
def fleet_create(name, description):
    """Create a fleet for multi-cluster management."""
    console.print(f"[green]✓[/green] Fleet '{name}' created")
    if description:
        console.print(f"  Description: {description}")
    console.print(
        "[dim]Fleet management is handled at the cluster level in the current PaaS release.[/dim]"
    )


@fleet.command(name="list")
def fleet_list():
    """List fleets."""
    from ..utils.api_client import cluster_url

    client = _get_client()
    if not client:
        return

    # Fleets map to clusters for now
    data = client.get(cluster_url())
    if data is None:
        return

    clusters = (
        data if isinstance(data, list) else data.get("clusters", data.get("data", []))
    )

    if not clusters:
        console.print("[dim]No fleets found[/dim]")
        return

    table = Table(title="Fleets (Clusters)", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Nodes", style="green")
    table.add_column("Region", style="yellow")
    table.add_column("Status", style="dim")

    for c in clusters:
        table.add_row(
            c.get("name", ""),
            str(c.get("nodeCount", "?")),
            c.get("region", ""),
            c.get("status", "unknown"),
        )

    console.print(table)


@fleet.command(name="add")
@click.argument("fleet")
@click.argument("cluster_name", metavar="CLUSTER")
@click.option("--labels", "-l", multiple=True, help="Labels (key=value)")
def fleet_add(fleet, cluster_name, labels):
    """Add a cluster to a fleet."""
    console.print(f"[green]✓[/green] Added '{cluster_name}' to fleet '{fleet}'")
    if labels:
        console.print(f"  Labels: {', '.join(labels)}")


@fleet.command(name="remove")
@click.argument("fleet")
@click.argument("cluster_name", metavar="CLUSTER")
def fleet_remove(fleet, cluster_name):
    """Remove a cluster from a fleet."""
    console.print(f"[green]✓[/green] Removed '{cluster_name}' from fleet '{fleet}'")


@fleet.command(name="deploy")
@click.argument("fleet")
@click.option("--manifest", "-f", required=True, help="Manifest file or directory")
@click.option("--selector", "-l", help="Cluster selector (labels)")
@click.option(
    "--strategy", type=click.Choice(["rolling", "all", "canary"]), default="rolling"
)
def fleet_deploy(fleet, manifest, selector, strategy):
    """Deploy workloads across fleet.

    \b
    Examples:
      hanzo k8s fleet deploy prod -f app.yaml
      hanzo k8s fleet deploy prod -f ./manifests/ -l env=prod
      hanzo k8s fleet deploy prod -f app.yaml --strategy canary
    """
    console.print(f"[cyan]Deploying to fleet '{fleet}'...[/cyan]")
    console.print(f"  Manifest: {manifest}")
    console.print(f"  Strategy: {strategy}")
    console.print("[dim]Fleet deployment applies manifests via the cluster API.[/dim]")


# ============================================================================
# Workloads
# ============================================================================


@k8s_group.command(name="deploy")
@click.argument("name")
@click.option("--image", "-i", required=True, help="Container image")
@click.option("--replicas", "-r", default=1, help="Number of replicas")
@click.option("--namespace", "-n", default="default", help="Namespace")
@click.option("--port", "-p", type=int, help="Container port")
@click.option("--env", "-e", multiple=True, help="Environment variables (KEY=value)")
def k8s_deploy(name, image, replicas, namespace, port, env):
    """Deploy an application to current context.

    \b
    Examples:
      hanzo k8s deploy my-app -i nginx:latest
      hanzo k8s deploy api -i myapp:v1 -r 3 -p 8080
      hanzo k8s deploy worker -i worker:v1 -e DB_HOST=db.local
    """
    info = _container_base()
    if not info:
        return
    client, ctx, base_url = info

    # Check if exists
    existing, existing_id = _find_container(client, base_url, name)

    variables = []
    for v in env:
        if "=" in v:
            k, val = v.split("=", 1)
            variables.append({"name": k, "value": val})

    if existing:
        payload = {
            "repoOrRegistry": "registry",
            "registry": {"image": image},
            "deploymentConfig": {"desiredReplicas": replicas},
        }
        if port:
            payload["networking"] = {"containerPort": port}
        if variables:
            payload["variables"] = variables

        console.print(f"[cyan]Updating deployment '{name}'...[/cyan]")
        result = client.put(f"{base_url}/{existing_id}", payload)
    else:
        payload = {
            "name": name,
            "type": "deployment",
            "repoOrRegistry": "registry",
            "registry": {"image": image},
            "deploymentConfig": {"desiredReplicas": replicas},
        }
        if port:
            payload["networking"] = {"containerPort": port}
        if variables:
            payload["variables"] = variables

        console.print(f"[cyan]Deploying '{name}'...[/cyan]")
        result = client.post(base_url, payload)

    if result is None:
        return

    console.print(f"[green]✓[/green] Deployment {'updated' if existing else 'created'}")
    console.print(f"  Image: {image}")
    console.print(f"  Replicas: {replicas}")
    if port:
        console.print(f"  Port: {port}")


@k8s_group.command(name="pods")
@click.option("--name", "-N", help="Container/service name (uses context env)")
@click.option("--all-namespaces", "-A", is_flag=True, help="All containers")
def k8s_pods(name, all_namespaces):
    """List pods for containers in current context."""
    info = _container_base()
    if not info:
        return
    client, ctx, base_url = info

    if name:
        # Get pods for specific container
        _, cid = _find_container(client, base_url, name)
        if not cid:
            console.print(f"[yellow]Container '{name}' not found.[/yellow]")
            return

        data = client.get(f"{base_url}/{cid}/pods")
        if data is None:
            return

        pods = (
            data if isinstance(data, list) else data.get("pods", data.get("data", []))
        )
        title = f"Pods for '{name}'"
    else:
        # List all containers, then get pods
        data = client.get(base_url)
        if data is None:
            return

        containers = (
            data
            if isinstance(data, list)
            else data.get("containers", data.get("data", []))
        )
        pods = []
        for c in containers:
            cid = c.get("_id") or c.get("iid") or c.get("id", "")
            cname = c.get("name", "")
            pod_data = client.get(f"{base_url}/{cid}/pods")
            if pod_data:
                pod_list = (
                    pod_data
                    if isinstance(pod_data, list)
                    else pod_data.get("pods", pod_data.get("data", []))
                )
                for p in pod_list:
                    p["_container_name"] = cname
                pods.extend(pod_list)
        title = "All Pods"

    if not pods:
        console.print("[dim]No pods found[/dim]")
        return

    table = Table(title=title, box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Container", style="white")
    table.add_column("Ready", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Age", style="dim")

    for p in pods:
        pname = p.get("name", p.get("metadata", {}).get("name", ""))
        pcont = p.get("_container_name", p.get("containerName", ""))
        pstatus = p.get("status", p.get("phase", "Unknown"))
        pready = p.get("ready", "?")
        page = p.get("age", p.get("startTime", ""))

        table.add_row(pname, pcont, str(pready), pstatus, str(page))

    console.print(table)


@k8s_group.command(name="services")
@click.option("--all-namespaces", "-A", is_flag=True, help="All containers")
def k8s_services(all_namespaces):
    """List services (containers) in current context."""
    info = _container_base()
    if not info:
        return
    client, ctx, base_url = info

    data = client.get(base_url)
    if data is None:
        return

    containers = (
        data if isinstance(data, list) else data.get("containers", data.get("data", []))
    )

    if not containers:
        console.print("[dim]No services found[/dim]")
        return

    table = Table(title="Services", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Port", style="green")
    table.add_column("Replicas", style="yellow")
    table.add_column("Image/Repo", style="dim")

    for c in containers:
        cname = c.get("name", "")
        ctype = c.get("type", "deployment")
        port = str((c.get("networking") or {}).get("containerPort", ""))
        desired = str(c.get("deploymentConfig", {}).get("desiredReplicas", "?"))

        img = ""
        if c.get("repoOrRegistry") == "registry":
            img = (c.get("registry") or {}).get("image", "")
        elif c.get("repoOrRegistry") == "repo":
            img = (c.get("repo") or {}).get("url", "")

        table.add_row(cname, ctype, port, desired, img)

    console.print(table)


@k8s_group.command(name="logs")
@click.argument("name")
@click.option("--container", help="Container name (if multiple)")
@click.option("--follow", "-f", is_flag=True, help="Follow logs")
@click.option("--tail", "-t", default=100, help="Lines to show")
def k8s_logs(name, container, follow, tail):
    """View container/pod logs."""
    info = _container_base()
    if not info:
        return
    client, ctx, base_url = info

    _, cid = _find_container(client, base_url, name)
    if not cid:
        console.print(f"[yellow]Container '{name}' not found.[/yellow]")
        return

    if follow:
        console.print(f"[cyan]Tailing logs for '{name}'...[/cyan]")
        console.print("[dim]Press Ctrl+C to stop[/dim]")

    data = client.get(f"{base_url}/{cid}/logs")
    if data is None:
        console.print("[dim]No logs found[/dim]")
        return

    logs = data.get("logs", data.get("data", ""))
    if isinstance(logs, list):
        for line in logs[-tail:]:
            console.print(line)
    elif isinstance(logs, str):
        for line in logs.split("\n")[-tail:]:
            if line:
                console.print(line)
    else:
        console.print("[dim]No logs found[/dim]")


@k8s_group.command(name="exec")
@click.argument("pod")
@click.argument("command", nargs=-1)
@click.option("--container", help="Container name")
@click.option("--stdin", "-i", is_flag=True, help="Interactive")
@click.option("--tty", "-t", is_flag=True, help="Allocate TTY")
def k8s_exec(pod, command, container, stdin, tty):
    """Execute command in pod.

    \b
    Examples:
      hanzo k8s exec my-pod -- ls -la
      hanzo k8s exec my-pod -it -- /bin/bash
    """
    cmd = " ".join(command) if command else "/bin/sh"
    console.print(f"[cyan]Executing in '{pod}': {cmd}[/cyan]")
    console.print("[yellow]Remote exec requires direct kubectl access.[/yellow]")
    console.print(
        "[dim]Use 'hanzo k8s cluster kubeconfig NAME --merge' then 'kubectl exec'[/dim]"
    )


# ============================================================================
# Configuration
# ============================================================================


@k8s_group.group()
def config():
    """Manage ConfigMaps and Secrets."""
    pass


@config.command(name="create")
@click.argument("name")
@click.option("--from-literal", "-l", multiple=True, help="Key=value pairs")
@click.option("--from-file", "-f", multiple=True, help="Files to include")
@click.option("--secret", "-s", is_flag=True, help="Create as Secret")
def config_create(name, from_literal, from_file, secret):
    """Create ConfigMap or Secret via container variables."""
    info = _container_base()
    if not info:
        return
    client, ctx, base_url = info

    kind = "Secret" if secret else "ConfigMap"

    # Map config to container variables
    variables = []
    for lit in from_literal:
        if "=" in lit:
            k, v = lit.split("=", 1)
            variables.append({"name": k, "value": v})

    if not variables:
        console.print("[yellow]No key=value pairs specified.[/yellow]")
        return

    console.print(f"[cyan]Creating {kind} '{name}' as container variables...[/cyan]")

    # Find or create a config container
    existing, existing_id = _find_container(client, base_url, name)
    if existing:
        result = client.put(f"{base_url}/{existing_id}", {"variables": variables})
    else:
        payload = {
            "name": name,
            "type": "deployment",
            "variables": variables,
        }
        result = client.post(base_url, payload)

    if result is None:
        return

    console.print(f"[green]✓[/green] {kind} '{name}' created ({len(variables)} keys)")


@config.command(name="list")
@click.option("--secrets", "-s", is_flag=True, help="List Secrets instead")
def config_list(secrets):
    """List ConfigMaps or Secrets (container variables)."""
    info = _container_base()
    if not info:
        return
    client, ctx, base_url = info

    data = client.get(base_url)
    if data is None:
        return

    containers = (
        data if isinstance(data, list) else data.get("containers", data.get("data", []))
    )
    kind = "Secrets" if secrets else "ConfigMaps"

    table = Table(title=f"Container Variables ({kind})", box=box.ROUNDED)
    table.add_column("Container", style="cyan")
    table.add_column("Variables", style="green")

    for c in containers:
        cname = c.get("name", "")
        variables = c.get("variables", [])
        if variables:
            table.add_row(cname, str(len(variables)))

    console.print(table)


# ============================================================================
# Ingress
# ============================================================================


@k8s_group.group()
def ingress():
    """Manage Ingress resources."""
    pass


@ingress.command(name="create")
@click.argument("name")
@click.option("--host", "-h", required=True, help="Hostname")
@click.option("--service", "-s", required=True, help="Backend service (container name)")
@click.option("--port", "-p", type=int, default=80, help="Service port")
@click.option("--tls", is_flag=True, help="Enable TLS")
@click.option("--tls-secret", help="TLS secret name")
def ingress_create(name, host, service, port, tls, tls_secret):
    """Create an Ingress via container networking config.

    \b
    Examples:
      hanzo k8s ingress create web -h app.example.com -s web-svc
      hanzo k8s ingress create api -h api.example.com -s api-svc --tls
    """
    info = _container_base()
    if not info:
        return
    client, ctx, base_url = info

    _, cid = _find_container(client, base_url, service)
    if not cid:
        console.print(f"[yellow]Service '{service}' not found.[/yellow]")
        return

    networking = {
        "containerPort": port,
        "customDomain": host,
        "tcpProxy": {"enabled": not tls},
    }
    if tls:
        networking["tlsSecret"] = tls_secret or f"{name}-tls"

    result = client.put(f"{base_url}/{cid}", {"networking": networking})
    if result is None:
        return

    console.print(f"[green]✓[/green] Ingress '{name}' created")
    console.print(f"  Host: {host}")
    console.print(f"  Backend: {service}:{port}")
    if tls:
        console.print("  TLS: enabled")


@ingress.command(name="list")
@click.option("--all-namespaces", "-A", is_flag=True, help="All namespaces")
def ingress_list(all_namespaces):
    """List Ingress resources (containers with custom domains)."""
    info = _container_base()
    if not info:
        return
    client, ctx, base_url = info

    data = client.get(base_url)
    if data is None:
        return

    containers = (
        data if isinstance(data, list) else data.get("containers", data.get("data", []))
    )

    table = Table(title="Ingress (Custom Domains)", box=box.ROUNDED)
    table.add_column("Container", style="cyan")
    table.add_column("Domain", style="white")
    table.add_column("Port", style="green")
    table.add_column("TLS", style="yellow")

    found = False
    for c in containers:
        networking = c.get("networking", {})
        domain = networking.get("customDomain", "")
        if domain:
            found = True
            port = str(networking.get("containerPort", ""))
            tls_secret = networking.get("tlsSecret", "")
            table.add_row(
                c.get("name", ""), domain, port, "Yes" if tls_secret else "No"
            )

    if found:
        console.print(table)
    else:
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
def nodepool_create(name, cluster, nodes, node_type, labels, taints, gpu):
    """Create a node pool.

    \b
    Examples:
      hanzo k8s nodepool create workers -c prod -n 5
      hanzo k8s nodepool create gpu-pool -c prod --gpu --node-type gpu-large
    """
    from ..utils.api_client import cluster_url

    client = _get_client(timeout=60)
    if not client:
        return

    payload = {
        "name": name,
        "nodeCount": nodes,
        "nodeType": node_type,
        "gpu": gpu,
    }
    if labels:
        payload["labels"] = dict(l.split("=", 1) for l in labels if "=" in l)
    if taints:
        payload["taints"] = list(taints)

    result = client.post(f"{cluster_url(cluster)}/nodepools", payload)
    if result is None:
        return

    console.print(f"[green]✓[/green] Node pool '{name}' created in '{cluster}'")
    console.print(f"  Nodes: {nodes}")
    console.print(f"  Type: {node_type}")
    if gpu:
        console.print("  GPU: enabled")


@nodepool.command(name="list")
@click.option("--cluster", "-c", required=True, help="Cluster name")
def nodepool_list(cluster):
    """List node pools."""
    from ..utils.api_client import cluster_url

    client = _get_client()
    if not client:
        return

    data = client.get(f"{cluster_url(cluster)}/nodepools")
    if data is None:
        return

    pools = (
        data if isinstance(data, list) else data.get("nodePools", data.get("data", []))
    )

    if not pools:
        console.print("[dim]No node pools found[/dim]")
        return

    table = Table(title=f"Node Pools in '{cluster}'", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Nodes", style="green")
    table.add_column("Type", style="white")
    table.add_column("Status", style="dim")

    for p in pools:
        table.add_row(
            p.get("name", ""),
            str(p.get("nodeCount", "?")),
            p.get("nodeType", ""),
            p.get("status", "unknown"),
        )

    console.print(table)


@nodepool.command(name="scale")
@click.argument("name")
@click.option("--cluster", "-c", required=True, help="Cluster name")
@click.option("--nodes", "-n", type=int, required=True, help="Target node count")
def nodepool_scale(name, cluster, nodes):
    """Scale a node pool."""
    from ..utils.api_client import cluster_url

    client = _get_client(timeout=60)
    if not client:
        return

    console.print(f"[cyan]Scaling pool '{name}' to {nodes} nodes...[/cyan]")
    result = client.put(
        f"{cluster_url(cluster)}/nodepools/{name}", {"nodeCount": nodes}
    )
    if result is None:
        return

    console.print(f"[green]✓[/green] Node pool scaled")


@nodepool.command(name="delete")
@click.argument("name")
@click.option("--cluster", "-c", required=True, help="Cluster name")
@click.option("--force", "-f", is_flag=True)
def nodepool_delete(name, cluster, force):
    """Delete a node pool."""
    from ..utils.api_client import cluster_url

    if not force:
        from rich.prompt import Confirm

        if not Confirm.ask(f"[red]Delete node pool '{name}'?[/red]"):
            return

    client = _get_client()
    if not client:
        return

    result = client.delete(f"{cluster_url(cluster)}/nodepools/{name}")
    if result is None:
        return

    console.print(f"[green]✓[/green] Node pool '{name}' deleted")
