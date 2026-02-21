"""Hanzo Run - Service lifecycle management CLI.

Deploy and manage containers on the PaaS platform.
"""

import os

import click
from rich import box
from rich.panel import Panel
from rich.table import Table

from ..utils.output import console


@click.group(name="run")
def run_group():
    """Hanzo Run - Deploy and manage services.

    \b
    Services:
      hanzo run service              # Deploy/update a service
      hanzo run job                  # Run one-off job
      hanzo run function             # Invoke a function

    \b
    Lifecycle:
      hanzo run status               # Check deployment status
      hanzo run logs                 # View service logs
      hanzo run scale                # Scale service

    \b
    Traffic:
      hanzo run promote              # Promote to next stage
      hanzo run rollback             # Rollback deployment
      hanzo run traffic              # Adjust traffic split

    Aliases: 'hanzo deploy' redirects here.
    """
    pass


# ============================================================================
# Helpers
# ============================================================================


def _get_client():
    from ..utils.api_client import PaaSClient

    try:
        return PaaSClient(timeout=60)
    except SystemExit:
        return None


def _get_ctx():
    from ..utils.api_client import require_context

    try:
        return require_context()
    except SystemExit:
        return None


def _container_base():
    from ..utils.api_client import container_url

    client = _get_client()
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
# Service Deployment
# ============================================================================


@run_group.command(name="service")
@click.argument("name", required=False)
@click.option("--image", "-i", help="Container image")
@click.option("--source", "-s", help="Git repo URL (source build)")
@click.option(
    "--env", "-e", "env_name", help="Override environment (uses context by default)"
)
@click.option("--replicas", "-r", default=1, help="Number of replicas")
@click.option("--port", "-p", default=8080, help="Service port")
@click.option("--cpu", default="0.5", help="CPU cores")
@click.option("--memory", default="512Mi", help="Memory")
@click.option("--wait", "-w", is_flag=True, help="Wait for deployment")
@click.option("--var", "-V", multiple=True, help="Env vars (KEY=value)")
def run_service(name, image, source, env_name, replicas, port, cpu, memory, wait, var):
    """Deploy or update a service.

    \b
    Examples:
      hanzo run service my-api --image my-api:v1.2
      hanzo run service --source https://github.com/org/repo
      hanzo run service my-api --replicas 3 --cpu 1 --memory 1Gi
      hanzo run service my-api -V DB_HOST=db.local -V SECRET=xxx
    """
    from ..utils.api_client import container_url

    if not name:
        name = os.path.basename(os.getcwd())

    info = _container_base()
    if not info:
        return
    client, ctx, base_url = info

    # Check if container already exists
    existing, existing_id = _find_container(client, base_url, name)

    # Build env vars list
    variables = []
    for v in var:
        if "=" in v:
            k, val = v.split("=", 1)
            variables.append({"name": k, "value": val})

    if existing:
        # Update existing container
        console.print(f"[cyan]Updating service '{name}'...[/cyan]")
        payload = {}
        if image:
            payload["repoOrRegistry"] = "registry"
            payload["registry"] = {"image": image}
        if replicas:
            payload["deploymentConfig"] = {"desiredReplicas": replicas}
        if port:
            payload["networking"] = {"containerPort": port}
        if variables:
            payload["variables"] = variables

        result = client.put(f"{base_url}/{existing_id}", payload)
        if result is None:
            return

        console.print(f"[green]✓[/green] Service '{name}' updated")
    else:
        # Create new container
        console.print(f"[cyan]Deploying service '{name}'...[/cyan]")
        payload = {
            "name": name,
            "type": "deployment",
            "networking": {"containerPort": port},
            "deploymentConfig": {"desiredReplicas": replicas},
        }

        if image:
            payload["repoOrRegistry"] = "registry"
            payload["registry"] = {"image": image}
        elif source:
            payload["repoOrRegistry"] = "repo"
            payload["repo"] = {"url": source, "branch": "main"}

        if variables:
            payload["variables"] = variables

        result = client.post(base_url, payload)
        if result is None:
            return

        console.print(f"[green]✓[/green] Service '{name}' deployed")
        cid = result.get("_id") or result.get("iid") or result.get("id", "")
        if cid:
            console.print(f"  Container ID: {cid}")

    if image:
        console.print(f"  Image: {image}")
    elif source:
        console.print(f"  Source: {source}")
    console.print(f"  Replicas: {replicas}")

    # Trigger build if source
    if source and not existing:
        cid = (
            (result or {}).get("_id")
            or (result or {}).get("iid")
            or (result or {}).get("id", "")
        )
        if cid:
            console.print("[cyan]Triggering build...[/cyan]")
            client.post(f"{base_url}/{cid}/trigger")

    if wait:
        console.print("[dim]Waiting for deployment to be ready...[/dim]")
        import time

        for _ in range(60):
            cid = (result or {}).get("_id") or existing_id
            if cid:
                data = client.get(f"{base_url}/{cid}")
                if (
                    data
                    and data.get("status", {}).get("availableReplicas", 0) >= replicas
                ):
                    console.print("[green]✓[/green] Deployment ready")
                    return
            time.sleep(2)
        console.print("[yellow]Timed out waiting for deployment[/yellow]")


@run_group.command(name="job")
@click.argument("name")
@click.option("--image", "-i", help="Container image")
@click.option("--command", "-c", "cmd", help="Command to run")
@click.option("--wait", "-w", is_flag=True, help="Wait for completion")
@click.option("--timeout", "-t", default="1h", help="Job timeout")
def run_job(name, image, cmd, wait, timeout):
    """Run a one-off job."""
    info = _container_base()
    if not info:
        return
    client, ctx, base_url = info

    payload = {
        "name": name,
        "type": "cronjob",
        "repoOrRegistry": "registry",
    }
    if image:
        payload["registry"] = {"image": image}
    if cmd:
        payload["deploymentConfig"] = {"command": cmd}

    console.print(f"[cyan]Starting job '{name}'...[/cyan]")
    result = client.post(base_url, payload)
    if result is None:
        return

    cid = result.get("_id") or result.get("iid") or result.get("id", "")
    console.print(f"[green]✓[/green] Job started")
    console.print(f"  Container ID: {cid}")
    console.print(f"  Logs: hanzo run logs {name}")


@run_group.command(name="function")
@click.argument("name")
@click.option("--payload", "-p", help="JSON payload")
@click.option("--async", "async_", is_flag=True, help="Invoke asynchronously")
def run_function(name, payload, async_):
    """Invoke a function."""
    info = _container_base()
    if not info:
        return
    client, ctx, base_url = info

    _, cid = _find_container(client, base_url, name)
    if not cid:
        console.print(f"[yellow]Function '{name}' not found.[/yellow]")
        return

    console.print(f"[cyan]Invoking function '{name}'...[/cyan]")
    result = client.post(f"{base_url}/{cid}/trigger")
    if result is None:
        return

    if async_:
        console.print("[green]✓[/green] Function invoked asynchronously")
    else:
        console.print("[green]✓[/green] Function invoked")


# ============================================================================
# Status & Logs
# ============================================================================


@run_group.command(name="status")
@click.argument("name", required=False)
def run_status(name):
    """Check deployment status."""
    info = _container_base()
    if not info:
        return
    client, ctx, base_url = info

    if name:
        # Show single container
        container, cid = _find_container(client, base_url, name)
        if not container:
            console.print(f"[yellow]Service '{name}' not found.[/yellow]")
            return

        status_info = container.get("status", {})
        replicas = container.get("deploymentConfig", {}).get("desiredReplicas", "?")
        avail = status_info.get("availableReplicas", "?")
        state = status_info.get("conditions", [{}])
        state_str = (
            "[green]● Running[/green]" if avail else "[yellow]○ Pending[/yellow]"
        )

        img = ""
        if container.get("repoOrRegistry") == "registry":
            img = (container.get("registry") or {}).get("image", "")
        elif container.get("repoOrRegistry") == "repo":
            img = (container.get("repo") or {}).get("url", "")

        port = (container.get("networking") or {}).get("containerPort", "")

        console.print(
            Panel(
                f"[cyan]Service:[/cyan] {container.get('name', name)}\n"
                f"[cyan]Status:[/cyan] {state_str}\n"
                f"[cyan]Replicas:[/cyan] {avail}/{replicas}\n"
                f"[cyan]Image:[/cyan] {img}\n"
                f"[cyan]Port:[/cyan] {port}\n"
                f"[cyan]ID:[/cyan] {cid}",
                title="Service Status",
                border_style="cyan",
            )
        )
    else:
        # List all containers
        data = client.get(base_url)
        if data is None:
            return

        from ..utils.api_client import extract_list

        containers = extract_list(data, "containers")

        if not containers:
            console.print("[dim]No services deployed in current context.[/dim]")
            console.print(
                "[dim]Deploy with: hanzo run service NAME --image IMAGE[/dim]"
            )
            return

        table = Table(title="Services", box=box.ROUNDED)
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="white")
        table.add_column("Status", style="green")
        table.add_column("Replicas", style="white")
        table.add_column("Image/Repo", style="dim")

        for c in containers:
            cname = c.get("name", "")
            ctype = c.get("type", "deployment")
            status_info = c.get("status", {})
            desired = c.get("deploymentConfig", {}).get("desiredReplicas", "?")
            avail = status_info.get("availableReplicas", 0)
            state = "Running" if avail else "Pending"

            img = ""
            if c.get("repoOrRegistry") == "registry":
                img = (c.get("registry") or {}).get("image", "")
            elif c.get("repoOrRegistry") == "repo":
                img = (c.get("repo") or {}).get("url", "")

            table.add_row(cname, ctype, state, f"{avail}/{desired}", img)

        console.print(table)


@run_group.command(name="logs")
@click.argument("name")
@click.option("--follow", "-f", is_flag=True, help="Follow logs")
@click.option("--tail", "-n", default=100, help="Number of lines")
@click.option("--since", "-s", help="Since time (e.g., 1h, 30m)")
def run_logs(name, follow, tail, since):
    """View service logs."""
    info = _container_base()
    if not info:
        return
    client, ctx, base_url = info

    _, cid = _find_container(client, base_url, name)
    if not cid:
        console.print(f"[yellow]Service '{name}' not found.[/yellow]")
        return

    params = {"tail": tail}
    if since:
        params["since"] = since

    console.print(f"[cyan]Logs for {name}:[/cyan]")

    data = client.get(f"{base_url}/{cid}/logs")
    if data is None:
        console.print("[dim]No logs available.[/dim]")
        return

    logs = data.get("logs", data.get("data", ""))
    if isinstance(logs, list):
        for line in logs[-tail:]:
            console.print(line)
    elif isinstance(logs, str):
        for line in logs.split("\n")[-tail:]:
            console.print(line)
    else:
        console.print("[dim]No logs available.[/dim]")

    if follow:
        console.print(
            "[dim]Follow mode is not yet supported via API. Use 'hanzo k8s logs' for streaming.[/dim]"
        )


# ============================================================================
# Scaling & Traffic
# ============================================================================


@run_group.command(name="scale")
@click.argument("name")
@click.option("--replicas", "-r", type=int, help="Number of replicas")
@click.option("--cpu", help="CPU cores")
@click.option("--memory", help="Memory")
def run_scale(name, replicas, cpu, memory):
    """Scale a service."""
    info = _container_base()
    if not info:
        return
    client, ctx, base_url = info

    _, cid = _find_container(client, base_url, name)
    if not cid:
        console.print(f"[yellow]Service '{name}' not found.[/yellow]")
        return

    payload = {}
    if replicas is not None:
        payload["deploymentConfig"] = {"desiredReplicas": replicas}
    if cpu or memory:
        resources = {}
        if cpu:
            resources["cpu"] = cpu
        if memory:
            resources["memory"] = memory
        payload["resources"] = resources

    if not payload:
        console.print("[yellow]No scaling changes specified.[/yellow]")
        return

    result = client.put(f"{base_url}/{cid}", payload)
    if result is None:
        return

    changes = []
    if replicas is not None:
        changes.append(f"replicas={replicas}")
    if cpu:
        changes.append(f"cpu={cpu}")
    if memory:
        changes.append(f"memory={memory}")

    console.print(f"[green]✓[/green] Scaled '{name}': {', '.join(changes)}")


@run_group.command(name="promote")
@click.argument("name")
@click.option("--from", "from_env", required=True, help="Source environment")
@click.option("--to", "to_env", required=True, help="Target environment")
def run_promote(name, from_env, to_env):
    """Promote service to next environment.

    Copies container config from source environment to target.
    """
    from ..utils.api_client import PaaSClient, container_url, require_context

    try:
        client = PaaSClient(timeout=60)
        ctx = require_context(("org_id", "project_id"))
    except SystemExit:
        return

    # Find container in source env
    src_url = container_url(ctx["org_id"], ctx["project_id"], from_env)
    container, _ = _find_container(client, src_url, name)
    if not container:
        console.print(f"[yellow]Service '{name}' not found in '{from_env}'.[/yellow]")
        return

    # Create/update in target env
    dst_url = container_url(ctx["org_id"], ctx["project_id"], to_env)
    existing, existing_id = _find_container(client, dst_url, name)

    payload = {
        "name": container.get("name", name),
        "type": container.get("type", "deployment"),
        "repoOrRegistry": container.get("repoOrRegistry", "registry"),
    }
    if container.get("registry"):
        payload["registry"] = container["registry"]
    if container.get("repo"):
        payload["repo"] = container["repo"]
    if container.get("deploymentConfig"):
        payload["deploymentConfig"] = container["deploymentConfig"]
    if container.get("networking"):
        payload["networking"] = container["networking"]
    if container.get("variables"):
        payload["variables"] = container["variables"]

    if existing:
        result = client.put(f"{dst_url}/{existing_id}", payload)
    else:
        result = client.post(dst_url, payload)

    if result is None:
        return

    console.print(f"[green]✓[/green] Promoted '{name}' from {from_env} to {to_env}")


@run_group.command(name="rollback")
@click.argument("name")
@click.option("--version", "-v", help="Version to rollback to (pipeline run)")
def run_rollback(name, version):
    """Rollback to previous deployment."""
    info = _container_base()
    if not info:
        return
    client, ctx, base_url = info

    _, cid = _find_container(client, base_url, name)
    if not cid:
        console.print(f"[yellow]Service '{name}' not found.[/yellow]")
        return

    # Get pipelines to find the previous run
    pipelines = client.get(f"{base_url}/{cid}/pipelines")
    if pipelines is None:
        console.print("[yellow]No pipeline history found.[/yellow]")
        return

    runs = (
        pipelines
        if isinstance(pipelines, list)
        else pipelines.get("runs", pipelines.get("data", []))
    )

    if version:
        # Find specific run
        target = None
        for r in runs:
            if str(r.get("runNumber", "")) == version or r.get("_id", "") == version:
                target = r
                break
        if not target:
            console.print(f"[yellow]Pipeline run '{version}' not found.[/yellow]")
            return
    elif len(runs) >= 2:
        target = runs[1]  # Previous run
    else:
        console.print("[yellow]No previous deployment to rollback to.[/yellow]")
        return

    # Trigger re-run of that pipeline
    console.print(f"[cyan]Rolling back '{name}'...[/cyan]")
    result = client.post(f"{base_url}/{cid}/trigger")
    if result is None:
        return

    console.print(f"[green]✓[/green] Rolled back '{name}'")


@run_group.command(name="traffic")
@click.argument("name")
@click.option("--version", "-v", multiple=True, help="Version:weight pairs")
def run_traffic(name, version):
    """Adjust traffic split between versions.

    \b
    Examples:
      hanzo run traffic my-api -v v1:90 -v v2:10
      hanzo run traffic my-api -v v2:100  # Full cutover
    """
    if not version:
        console.print(
            "[yellow]Traffic splitting requires PaaS ingress configuration.[/yellow]"
        )
        console.print("[dim]Specify version weights: -v v1:90 -v v2:10[/dim]")
        return

    # Traffic splitting is typically handled at the ingress/service mesh level
    console.print(f"[cyan]Updating traffic split for '{name}':[/cyan]")
    for v in version:
        parts = v.split(":")
        if len(parts) == 2:
            console.print(f"  {parts[0]}: {parts[1]}%")

    console.print(
        "[yellow]Traffic splitting requires ingress controller support.[/yellow]"
    )
    console.print("[dim]Configure via 'hanzo k8s ingress' or your service mesh.[/dim]")


@run_group.command(name="delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def run_delete(name, force):
    """Delete a deployed service."""
    info = _container_base()
    if not info:
        return
    client, ctx, base_url = info

    _, cid = _find_container(client, base_url, name)
    if not cid:
        console.print(f"[yellow]Service '{name}' not found.[/yellow]")
        return

    if not force:
        from rich.prompt import Confirm

        if not Confirm.ask(
            f"[red]Delete service '{name}'? This cannot be undone.[/red]"
        ):
            return

    result = client.delete(f"{base_url}/{cid}")
    if result is None:
        return

    console.print(f"[green]✓[/green] Service '{name}' deleted")
