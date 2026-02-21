"""Hanzo CLI — PaaS subcommands for platform management.

Context is sticky: run ``hanzo paas use --org X --project Y --env Z``
once, then subsequent commands remember.  CLI flags always override.

Usage:
    hanzo paas use --org O --project P --env E
    hanzo paas orgs
    hanzo paas projects
    hanzo paas envs
    hanzo paas deploy list
    hanzo paas deploy create <name> --repo <url> [--branch main]
    hanzo paas deploy status <name>
    hanzo paas deploy logs <name>
    hanzo paas deploy redeploy <name>
    hanzo paas deploy env <name> [KEY=VAL ...]
    hanzo paas deploy delete <name>
"""

from __future__ import annotations

import json
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from hanzo_cli.paas.client import PaaSClient
from hanzo_cli.paas.context import clear_context, load_context, resolve, save_context

console = Console()


# ── shared option decorators ────────────────────────────────────────────


def _org_option(fn):
    return click.option("--org", default=None, help="Organization ID (or from context).")(fn)


def _project_option(fn):
    return click.option("--project", default=None, help="Project ID (or from context).")(fn)


def _env_option(fn):
    return click.option("--env", "env_id", default=None, help="Environment ID (or from context).")(
        fn
    )


def _require(label: str, value: str | None) -> str:
    """Ensure a value is set; exit with a helpful message if not."""
    if not value:
        console.print(f"[red]{label} is required.[/red] Pass it via flag or run 'hanzo paas use'.")
        raise SystemExit(1)
    return value


def _find_container(
    client: PaaSClient,
    org_id: str,
    project_id: str,
    env_id: str,
    name: str,
) -> dict[str, Any]:
    """Look up a container by name within the current context."""
    containers = client.list_containers(org_id, project_id, env_id)
    # list may be wrapped in {"data": [...]} or raw [...]
    items = containers if isinstance(containers, list) else containers.get("data", containers)
    for c in items:
        if c.get("iid") == name or c.get("name") == name or c.get("slug") == name:
            return c
    console.print(f"[red]Container '{name}' not found.[/red]")
    raise SystemExit(1)


# ═══════════════════════════════════════════════════════════════════════
# Root group
# ═══════════════════════════════════════════════════════════════════════


@click.group()
def paas() -> None:
    """Manage the Hanzo PaaS — orgs, projects, deployments."""


# ── context ─────────────────────────────────────────────────────────────


@paas.command("use")
@click.option("--org", default=None, help="Organization ID to remember.")
@click.option("--project", default=None, help="Project ID to remember.")
@click.option("--env", "env_id", default=None, help="Environment ID to remember.")
@click.option("--clear", is_flag=True, help="Clear stored context.")
def use_context(org: str | None, project: str | None, env_id: str | None, clear: bool) -> None:
    """Set the default org / project / environment context."""
    if clear:
        clear_context()
        console.print("Context cleared.")
        return

    ctx = load_context()
    if org:
        ctx["org_id"] = org
    if project:
        ctx["project_id"] = project
    if env_id:
        ctx["env_id"] = env_id

    save_context(ctx)

    table = Table(title="PaaS Context")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("org", ctx.get("org_id", "—"))
    table.add_row("project", ctx.get("project_id", "—"))
    table.add_row("env", ctx.get("env_id", "—"))
    console.print(table)


@paas.command("context")
def show_context() -> None:
    """Show current PaaS context."""
    ctx = load_context()
    if not ctx:
        console.print("[yellow]No context set.[/yellow] Run 'hanzo paas use'.")
        return

    table = Table(title="PaaS Context")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("org", ctx.get("org_id", "—"))
    table.add_row("project", ctx.get("project_id", "—"))
    table.add_row("env", ctx.get("env_id", "—"))
    console.print(table)


# ═══════════════════════════════════════════════════════════════════════
# Orgs / Projects / Environments
# ═══════════════════════════════════════════════════════════════════════


@paas.command("orgs")
def list_orgs() -> None:
    """List organizations."""
    client = PaaSClient.from_auth()
    try:
        data = client.list_orgs()
    finally:
        client.close()

    items = data if isinstance(data, list) else data.get("data", data)
    if not items:
        console.print("[yellow]No organizations.[/yellow]")
        return

    table = Table(title=f"Organizations ({len(items)})")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Slug", style="white")

    for o in items:
        table.add_row(
            str(o.get("_id", o.get("id", "—"))),
            o.get("name", "—"),
            o.get("iid", "—"),
        )
    console.print(table)


@paas.command("projects")
@_org_option
def list_projects(org: str | None) -> None:
    """List projects in an organization."""
    org_id, _, _ = resolve(org, None, None)
    org_id = _require("--org", org_id)

    client = PaaSClient.from_auth()
    try:
        data = client.list_projects(org_id)
    finally:
        client.close()

    items = data if isinstance(data, list) else data.get("data", data)
    if not items:
        console.print("[yellow]No projects.[/yellow]")
        return

    table = Table(title=f"Projects ({len(items)})")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Slug", style="white")

    for p in items:
        table.add_row(
            str(p.get("_id", p.get("id", "—"))),
            p.get("name", "—"),
            p.get("iid", "—"),
        )
    console.print(table)


@paas.command("envs")
@_org_option
@_project_option
def list_envs(org: str | None, project: str | None) -> None:
    """List environments in a project."""
    org_id, project_id, _ = resolve(org, project, None)
    org_id = _require("--org", org_id)
    project_id = _require("--project", project_id)

    client = PaaSClient.from_auth()
    try:
        data = client.list_envs(org_id, project_id)
    finally:
        client.close()

    items = data if isinstance(data, list) else data.get("data", data)
    if not items:
        console.print("[yellow]No environments.[/yellow]")
        return

    table = Table(title=f"Environments ({len(items)})")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Slug", style="white")

    for e in items:
        table.add_row(
            str(e.get("_id", e.get("id", "—"))),
            e.get("name", "—"),
            e.get("iid", "—"),
        )
    console.print(table)


# ═══════════════════════════════════════════════════════════════════════
# Deploy sub-group
# ═══════════════════════════════════════════════════════════════════════


@paas.group("deploy")
def deploy() -> None:
    """Manage container deployments."""


# ── deploy list ─────────────────────────────────────────────────────────


@deploy.command("list")
@_org_option
@_project_option
@_env_option
def deploy_list(org: str | None, project: str | None, env_id: str | None) -> None:
    """List deployed containers."""
    org_id, project_id, env_id = resolve(org, project, env_id)
    org_id = _require("--org", org_id)
    project_id = _require("--project", project_id)
    env_id = _require("--env", env_id)

    client = PaaSClient.from_auth()
    try:
        data = client.list_containers(org_id, project_id, env_id)
    finally:
        client.close()

    items = data if isinstance(data, list) else data.get("data", data)
    if not items:
        console.print("[yellow]No containers.[/yellow]")
        return

    table = Table(title=f"Containers ({len(items)})")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Repo", style="dim")
    table.add_column("Status", style="green")

    for c in items:
        name = c.get("iid", c.get("name", "—"))
        ctype = c.get("type", "—")
        repo = c.get("repo", {})
        repo_str = repo.get("name", "—") if isinstance(repo, dict) else "—"
        status = c.get("pipelineStatus", c.get("status", "—"))
        if isinstance(status, dict):
            status = status.get("status", "—")
        table.add_row(name, ctype, repo_str, str(status))

    console.print(table)


# ── deploy create ───────────────────────────────────────────────────────


@deploy.command("create")
@click.argument("name")
@click.option(
    "--image", default=None, help="Docker image URL (e.g. nginx:latest, ghcr.io/org/app:v1)."
)
@click.option("--repo", default=None, help="Git repository (owner/repo).")
@click.option("--branch", default="main", help="Branch to deploy (with --repo).")
@click.option("--dockerfile", default="Dockerfile", help="Dockerfile path (with --repo).")
@click.option("--port", type=int, default=3000, help="Container port.")
@click.option("--replicas", type=int, default=1, help="Desired replica count.")
@click.option(
    "--type",
    "deploy_type",
    default="deployment",
    type=click.Choice(["deployment", "statefulset", "cronjob"]),
)
@_org_option
@_project_option
@_env_option
def deploy_create(
    name: str,
    image: str | None,
    repo: str | None,
    branch: str,
    dockerfile: str,
    port: int,
    replicas: int,
    deploy_type: str,
    org: str | None,
    project: str | None,
    env_id: str | None,
) -> None:
    """Create a new container deployment from a Docker image or git repo.

    Examples:
        hanzo paas deploy create myapp --image nginx:latest --port 80
        hanzo paas deploy create myapp --image ghcr.io/org/app:v1 --port 8080
        hanzo paas deploy create myapp --repo hanzoai/app --branch main
    """
    if not image and not repo:
        console.print("[red]Specify --image or --repo.[/red]")
        raise SystemExit(1)

    org_id, project_id, env_id = resolve(org, project, env_id)
    org_id = _require("--org", org_id)
    project_id = _require("--project", project_id)
    env_id = _require("--env", env_id)

    # Resolve public registry ID for image deployments
    registry_id = None
    if image:
        client_pre = PaaSClient.from_auth()
        try:
            regs = client_pre.http.get("/v1/registry")
            regs.raise_for_status()
            for reg in regs.json():
                if reg.get("type") == "Public":
                    registry_id = str(reg["_id"])
                    break
        except Exception:
            pass
        finally:
            client_pre.close()

    payload: dict[str, Any] = {
        "name": name,
        "type": deploy_type,
        "networking": {
            "containerPort": port,
            "ingress": {"enabled": False},
            "customDomain": {"enabled": False},
            "tcpProxy": {"enabled": False},
        },
        "podConfig": {
            "restartPolicy": "Always",
            "cpuRequest": 100,
            "cpuRequestType": "millicores",
            "cpuLimit": 200,
            "cpuLimitType": "millicores",
            "memoryRequest": 128,
            "memoryRequestType": "mebibyte",
            "memoryLimit": 256,
            "memoryLimitType": "mebibyte",
        },
        "storageConfig": {"enabled": False},
        "probes": {
            "startup": {"enabled": False},
            "readiness": {"enabled": False},
            "liveness": {"enabled": False},
        },
    }

    if deploy_type == "deployment":
        payload["deploymentConfig"] = {
            "desiredReplicas": replicas,
            "strategy": "RollingUpdate",
            "rollingUpdate": {
                "maxSurge": 30,
                "maxSurgeType": "percentage",
                "maxUnavailable": 0,
                "maxUnavailableType": "number",
            },
            "revisionHistoryLimit": 10,
            "cpuMetric": {"enabled": False},
            "memoryMetric": {"enabled": False},
        }

    if image:
        payload["repoOrRegistry"] = "registry"
        reg_obj: dict[str, Any] = {"imageUrl": image}
        if registry_id:
            reg_obj["registryId"] = registry_id
        payload["registry"] = reg_obj
    else:
        payload["repoOrRegistry"] = "repo"
        payload["repo"] = {
            "name": repo,
            "branch": branch,
            "dockerfile": dockerfile,
        }

    client = PaaSClient.from_auth()
    try:
        data = client.create_container(org_id, project_id, env_id, payload)
    finally:
        client.close()

    console.print(f"[green]Created container '{name}'[/green]")
    cid = data.get("_id", data.get("id", ""))
    if cid:
        console.print(f"ID: {cid}")


# ── deploy status ───────────────────────────────────────────────────────


@deploy.command("status")
@click.argument("name")
@_org_option
@_project_option
@_env_option
def deploy_status(
    name: str,
    org: str | None,
    project: str | None,
    env_id: str | None,
) -> None:
    """Show container status and pods."""
    org_id, project_id, env_id = resolve(org, project, env_id)
    org_id = _require("--org", org_id)
    project_id = _require("--project", project_id)
    env_id = _require("--env", env_id)

    client = PaaSClient.from_auth()
    try:
        container = _find_container(client, org_id, project_id, env_id, name)
        cid = str(container.get("_id", container.get("id")))

        # Container info
        table = Table(title=f"Container: {name}")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("ID", cid)
        table.add_row("Type", container.get("type", "—"))
        table.add_row("Pipeline", str(container.get("pipelineStatus", "—")))

        status = container.get("status", {})
        if isinstance(status, dict):
            table.add_row("Desired Replicas", str(status.get("desiredReplicas", "—")))
            table.add_row("Ready Replicas", str(status.get("readyReplicas", "—")))
            table.add_row("Available Replicas", str(status.get("availableReplicas", "—")))
        console.print(table)

        # Pods
        try:
            pods_data = client.get_container_pods(org_id, project_id, env_id, cid)
            pods = pods_data if isinstance(pods_data, list) else pods_data.get("data", [])
            if pods:
                pod_table = Table(title="Pods")
                pod_table.add_column("Name", style="cyan")
                pod_table.add_column("Status", style="green")
                pod_table.add_column("Restarts", style="yellow", justify="right")
                for p in pods:
                    pod_table.add_row(
                        p.get("name", "—"),
                        p.get("status", "—"),
                        str(p.get("restartCount", 0)),
                    )
                console.print(pod_table)
        except Exception:
            pass  # pods endpoint may not be available
    finally:
        client.close()


# ── deploy logs ─────────────────────────────────────────────────────────


@deploy.command("logs")
@click.argument("name")
@_org_option
@_project_option
@_env_option
def deploy_logs(
    name: str,
    org: str | None,
    project: str | None,
    env_id: str | None,
) -> None:
    """Show container logs."""
    org_id, project_id, env_id = resolve(org, project, env_id)
    org_id = _require("--org", org_id)
    project_id = _require("--project", project_id)
    env_id = _require("--env", env_id)

    client = PaaSClient.from_auth()
    try:
        container = _find_container(client, org_id, project_id, env_id, name)
        cid = str(container.get("_id", container.get("id")))
        logs_data = client.get_container_logs(org_id, project_id, env_id, cid)

        # PaaS returns {pods: [...], logs: [{podName, logs: [line, ...]}, ...]}
        if isinstance(logs_data, dict) and "logs" in logs_data:
            pod_logs = logs_data["logs"]
            if isinstance(pod_logs, list):
                for pod in pod_logs:
                    if isinstance(pod, dict):
                        pod_name = pod.get("podName", "?")
                        lines = pod.get("logs", [])
                        if len(pod_logs) > 1:
                            click.echo(click.style(f"─── {pod_name} ───", fg="cyan"))
                        for line in lines:
                            if line:
                                click.echo(line)
                    else:
                        click.echo(str(pod))
            else:
                click.echo(str(pod_logs))
        elif isinstance(logs_data, str):
            click.echo(logs_data)
        elif isinstance(logs_data, list):
            for line in logs_data:
                click.echo(line)
        else:
            click.echo(json.dumps(logs_data, indent=2))
    finally:
        client.close()


# ── deploy redeploy ─────────────────────────────────────────────────────


@deploy.command("redeploy")
@click.argument("name")
@_org_option
@_project_option
@_env_option
def deploy_redeploy(
    name: str,
    org: str | None,
    project: str | None,
    env_id: str | None,
) -> None:
    """Trigger a rebuild and redeploy of a container."""
    org_id, project_id, env_id = resolve(org, project, env_id)
    org_id = _require("--org", org_id)
    project_id = _require("--project", project_id)
    env_id = _require("--env", env_id)

    client = PaaSClient.from_auth()
    try:
        container = _find_container(client, org_id, project_id, env_id, name)
        cid = str(container.get("_id", container.get("id")))
        client.redeploy_container(org_id, project_id, env_id, cid)
    finally:
        client.close()

    console.print(f"[green]Redeployment triggered for '{name}'.[/green]")


# ── deploy env ──────────────────────────────────────────────────────────


@deploy.command("env")
@click.argument("name")
@click.argument("vars", nargs=-1)
@_org_option
@_project_option
@_env_option
def deploy_env(
    name: str,
    vars: tuple[str, ...],
    org: str | None,
    project: str | None,
    env_id: str | None,
) -> None:
    """Show or set environment variables on a container.

    Without arguments, shows current vars.  With KEY=VAL pairs, sets them.

    Examples:
        hanzo paas deploy env myapp
        hanzo paas deploy env myapp DATABASE_URL=postgres://... NODE_ENV=production
    """
    org_id, project_id, env_id = resolve(org, project, env_id)
    org_id = _require("--org", org_id)
    project_id = _require("--project", project_id)
    env_id = _require("--env", env_id)

    client = PaaSClient.from_auth()
    try:
        container = _find_container(client, org_id, project_id, env_id, name)
        cid = str(container.get("_id", container.get("id")))

        if not vars:
            # Show current vars
            variables = container.get("variables", [])
            if not variables:
                console.print("[yellow]No environment variables set.[/yellow]")
                return
            table = Table(title=f"Env vars: {name}")
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="dim")
            for v in variables:
                val = v.get("value", "")
                masked = f"{val[:4]}***" if len(val) > 4 else val
                table.add_row(v.get("name", "—"), masked)
            console.print(table)
        else:
            # Set vars: parse KEY=VAL pairs
            new_vars = []
            for kv in vars:
                if "=" not in kv:
                    console.print(f"[red]Invalid format: '{kv}'. Use KEY=VALUE.[/red]")
                    raise SystemExit(1)
                k, v = kv.split("=", 1)
                new_vars.append({"name": k, "value": v})

            # Merge with existing
            existing = {v["name"]: v["value"] for v in container.get("variables", [])}
            for nv in new_vars:
                existing[nv["name"]] = nv["value"]

            merged = [{"name": k, "value": v} for k, v in existing.items()]

            # PaaS requires the full container payload on PUT — merge vars into it
            container["variables"] = merged
            client.update_container(
                org_id,
                project_id,
                env_id,
                cid,
                container,
            )
            console.print(f"[green]Set {len(new_vars)} variable(s) on '{name}'.[/green]")
    finally:
        client.close()


# ── deploy delete ───────────────────────────────────────────────────────


@deploy.command("delete")
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation.")
@_org_option
@_project_option
@_env_option
def deploy_delete(
    name: str,
    yes: bool,
    org: str | None,
    project: str | None,
    env_id: str | None,
) -> None:
    """Delete a container deployment."""
    if not yes:
        click.confirm(f"Delete container '{name}'?", abort=True)

    org_id, project_id, env_id = resolve(org, project, env_id)
    org_id = _require("--org", org_id)
    project_id = _require("--project", project_id)
    env_id = _require("--env", env_id)

    client = PaaSClient.from_auth()
    try:
        container = _find_container(client, org_id, project_id, env_id, name)
        cid = str(container.get("_id", container.get("id")))
        client.delete_container(org_id, project_id, env_id, cid)
    finally:
        client.close()

    console.print(f"[green]Deleted '{name}'.[/green]")
