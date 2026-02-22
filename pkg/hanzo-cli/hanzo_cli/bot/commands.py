"""Hanzo CLI — Bot gateway management.

Manage the Hanzo bot-gateway deployment via PaaS API.
Defaults to the Hanzo production bot container.

Usage:
    hanzo bot status                    Show container + pod status
    hanzo bot logs [--tail N]           View recent logs
    hanzo bot deploy                    Trigger redeploy
    hanzo bot env [KEY=VAL ...]         Show/set env vars
    hanzo bot events                    Show container events
"""

from __future__ import annotations

import json
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from hanzo_cli.paas.client import PaaSClient
from hanzo_cli.paas.context import resolve

console = Console()

# ── defaults ──────────────────────────────────────────────────────────

# Known Hanzo production bot container context.
# These can be overridden via --org / --project / --env flags.
DEFAULT_BOT_ORG = "698cda6739f65183b3009313"
DEFAULT_BOT_PROJECT = "698cda6739f65183b3009318"
DEFAULT_BOT_ENV = "698cda6739f65183b300931c"
DEFAULT_BOT_NAME = "bot"


# ── shared options ────────────────────────────────────────────────────


def _org_option(fn):
    return click.option(
        "--org", default=None, help="Organization ID (default: Hanzo)."
    )(fn)


def _project_option(fn):
    return click.option(
        "--project", default=None, help="Project ID (default: Platform)."
    )(fn)


def _env_option(fn):
    return click.option(
        "--env", "env_id", default=None, help="Environment ID (default: production)."
    )(fn)


def _name_option(fn):
    return click.option(
        "--name",
        "-n",
        default=DEFAULT_BOT_NAME,
        help="Container name (default: bot).",
    )(fn)


def _resolve_bot(
    org: str | None,
    project: str | None,
    env_id: str | None,
) -> tuple[str, str, str]:
    """Resolve org/project/env, falling back to bot defaults."""
    ctx_org, ctx_proj, ctx_env = resolve(org, project, env_id)
    return (
        ctx_org or DEFAULT_BOT_ORG,
        ctx_proj or DEFAULT_BOT_PROJECT,
        ctx_env or DEFAULT_BOT_ENV,
    )


def _find_container(
    client: PaaSClient,
    org_id: str,
    project_id: str,
    env_id: str,
    name: str,
) -> dict[str, Any]:
    """Look up a container by name."""
    containers = client.list_containers(org_id, project_id, env_id)
    items = (
        containers
        if isinstance(containers, list)
        else containers.get("data", containers)
    )
    for c in items:
        if c.get("iid") == name or c.get("name") == name or c.get("slug") == name:
            return c
    console.print(f"[red]Bot container '{name}' not found.[/red]")
    raise SystemExit(1)


# ── group ─────────────────────────────────────────────────────────────


@click.group()
def bot() -> None:
    """Manage the Hanzo bot-gateway deployment."""


# ── status ────────────────────────────────────────────────────────────


@bot.command("status")
@_name_option
@_org_option
@_project_option
@_env_option
def bot_status(
    name: str,
    org: str | None,
    project: str | None,
    env_id: str | None,
) -> None:
    """Show bot container status and pods."""
    org_id, project_id, env_id = _resolve_bot(org, project, env_id)

    client = PaaSClient.from_auth()
    try:
        container = _find_container(client, org_id, project_id, env_id, name)
        cid = str(container.get("_id", container.get("id")))

        # Container info
        table = Table(title=f"Bot: {name}")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("ID", cid)
        table.add_row("Type", container.get("type", "—"))

        pipeline = container.get("pipelineStatus", "—")
        if isinstance(pipeline, dict):
            pipeline = pipeline.get("status", str(pipeline))
        table.add_row("Pipeline", str(pipeline))

        reg = container.get("registry", {})
        if isinstance(reg, dict) and reg.get("imageUrl"):
            table.add_row("Image", reg["imageUrl"])

        status = container.get("status", {})
        if isinstance(status, dict):
            table.add_row("Desired", str(status.get("desiredReplicas", "—")))
            table.add_row("Ready", str(status.get("readyReplicas", "—")))
            table.add_row("Available", str(status.get("availableReplicas", "—")))
        console.print(table)

        # Pods
        try:
            pods_data = client.get_container_pods(org_id, project_id, env_id, cid)
            pods = (
                pods_data if isinstance(pods_data, list) else pods_data.get("data", [])
            )
            if pods:
                pod_table = Table(title="Pods")
                pod_table.add_column("Name", style="cyan")
                pod_table.add_column("Status", style="green")
                pod_table.add_column("Restarts", style="yellow", justify="right")
                pod_table.add_column("Age", style="dim")
                for p in pods:
                    pod_table.add_row(
                        p.get("name", "—"),
                        p.get("status", "—"),
                        str(p.get("restartCount", 0)),
                        p.get("age", "—"),
                    )
                console.print(pod_table)
            else:
                console.print("[yellow]No pods found.[/yellow]")
        except Exception:
            pass
    finally:
        client.close()


# ── logs ──────────────────────────────────────────────────────────────


@bot.command("logs")
@click.option("--tail", "-t", type=int, default=100, help="Number of lines to show.")
@_name_option
@_org_option
@_project_option
@_env_option
def bot_logs(
    tail: int,
    name: str,
    org: str | None,
    project: str | None,
    env_id: str | None,
) -> None:
    """Show bot container logs."""
    org_id, project_id, env_id = _resolve_bot(org, project, env_id)

    client = PaaSClient.from_auth()
    try:
        container = _find_container(client, org_id, project_id, env_id, name)
        cid = str(container.get("_id", container.get("id")))
        logs_data = client.get_container_logs(org_id, project_id, env_id, cid)

        if isinstance(logs_data, dict) and "logs" in logs_data:
            pod_logs = logs_data["logs"]
            if isinstance(pod_logs, list):
                for pod in pod_logs:
                    if isinstance(pod, dict):
                        pod_name = pod.get("podName", "?")
                        lines = pod.get("logs", [])
                        if len(pod_logs) > 1:
                            click.echo(click.style(f"--- {pod_name} ---", fg="cyan"))
                        shown = lines[-tail:] if tail else lines
                        for line in shown:
                            if line:
                                click.echo(line)
                    else:
                        click.echo(str(pod))
            else:
                click.echo(str(pod_logs))
        elif isinstance(logs_data, str):
            lines = logs_data.splitlines()
            for line in lines[-tail:]:
                click.echo(line)
        elif isinstance(logs_data, list):
            for line in logs_data[-tail:]:
                click.echo(line)
        else:
            click.echo(json.dumps(logs_data, indent=2))
    finally:
        client.close()


# ── deploy ────────────────────────────────────────────────────────────


@bot.command("deploy")
@_name_option
@_org_option
@_project_option
@_env_option
def bot_deploy(
    name: str,
    org: str | None,
    project: str | None,
    env_id: str | None,
) -> None:
    """Trigger a redeploy of the bot container."""
    org_id, project_id, env_id = _resolve_bot(org, project, env_id)

    client = PaaSClient.from_auth()
    try:
        container = _find_container(client, org_id, project_id, env_id, name)
        cid = str(container.get("_id", container.get("id")))
        client.redeploy_container(org_id, project_id, env_id, cid)
    finally:
        client.close()

    console.print(f"[green]Redeployment triggered for '{name}'.[/green]")


# ── env ───────────────────────────────────────────────────────────────


@bot.command("env")
@click.argument("vars", nargs=-1)
@_name_option
@_org_option
@_project_option
@_env_option
def bot_env(
    vars: tuple[str, ...],
    name: str,
    org: str | None,
    project: str | None,
    env_id: str | None,
) -> None:
    """Show or set bot environment variables.

    Without arguments, shows current vars. With KEY=VAL pairs, sets them.

    \b
    Examples:
        hanzo bot env                              Show current vars
        hanzo bot env NODE_ENV=production           Set a var
        hanzo bot env BOT_TOKEN=xxx LOG_LEVEL=debug Set multiple
    """
    org_id, project_id, env_id = _resolve_bot(org, project, env_id)

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
            # Set vars
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
            container["variables"] = merged
            client.update_container(org_id, project_id, env_id, cid, container)
            console.print(
                f"[green]Set {len(new_vars)} variable(s) on '{name}'.[/green]"
            )
    finally:
        client.close()


# ── events ────────────────────────────────────────────────────────────


@bot.command("events")
@_name_option
@_org_option
@_project_option
@_env_option
def bot_events(
    name: str,
    org: str | None,
    project: str | None,
    env_id: str | None,
) -> None:
    """Show bot container events."""
    org_id, project_id, env_id = _resolve_bot(org, project, env_id)

    client = PaaSClient.from_auth()
    try:
        container = _find_container(client, org_id, project_id, env_id, name)
        cid = str(container.get("_id", container.get("id")))
        events_data = client.get_container_events(org_id, project_id, env_id, cid)

        events = (
            events_data
            if isinstance(events_data, list)
            else events_data.get("data", [])
        )
        if not events:
            console.print("[yellow]No events found.[/yellow]")
            return

        table = Table(title=f"Events: {name}")
        table.add_column("Type", style="cyan")
        table.add_column("Reason", style="yellow")
        table.add_column("Message", style="white")
        table.add_column("Age", style="dim")

        for e in events:
            table.add_row(
                e.get("type", "—"),
                e.get("reason", "—"),
                e.get("message", "—"),
                e.get("age", e.get("lastTimestamp", "—")),
            )
        console.print(table)
    finally:
        client.close()
