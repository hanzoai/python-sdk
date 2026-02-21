"""Hanzo Auto - AI-powered workflow automation CLI.

Based on Activepieces with 280+ integrations.
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

AUTO_URL = os.getenv("HANZO_AUTO_URL", "https://auto.hanzo.ai")


def _request(method: str, path: str, **kwargs) -> httpx.Response:
    return service_request(AUTO_URL, method, path, **kwargs)


@click.group(name="auto")
def auto_group():
    """Hanzo Auto - AI-powered workflow automation.

    \b
    Build automations visually with drag-and-drop:

    \b
    Workflows:
      hanzo auto flows list        # List all flows
      hanzo auto flows create      # Create new flow
      hanzo auto flows run         # Run a flow

    \b
    Pieces (Integrations):
      hanzo auto pieces list       # List available pieces
      hanzo auto pieces install    # Install a piece

    \b
    Connections:
      hanzo auto connections list  # List connections
      hanzo auto connections add   # Add connection

    \b
    Local Development:
      hanzo auto init              # Initialize project
      hanzo auto dev               # Start dev server
      hanzo auto deploy            # Deploy flows
    """
    pass


# ============================================================================
# Flows
# ============================================================================


@auto_group.group()
def flows():
    """Manage automation flows."""
    pass


@flows.command(name="list")
@click.option("--status", type=click.Choice(["active", "inactive", "all"]), default="all")
def flows_list(status: str):
    """List all automation flows."""
    params = {}
    if status != "all":
        params["status"] = status

    resp = _request("get", "/v1/flows", params=params)
    data = check_response(resp)
    items = data.get("flows", data.get("items", []))

    table = Table(title="Automation Flows", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Trigger", style="white")
    table.add_column("Last Run", style="dim")
    table.add_column("Runs", style="dim")

    for f in items:
        f_status = f.get("status", "inactive")
        style = "green" if f_status == "active" else "yellow"
        table.add_row(
            f.get("name", ""),
            f"[{style}]{f_status}[/{style}]",
            f.get("trigger_type", "-"),
            str(f.get("last_run_at", ""))[:19],
            str(f.get("run_count", 0)),
        )

    console.print(table)
    if not items:
        console.print("[dim]No flows found. Create one with 'hanzo auto flows create'[/dim]")


@flows.command(name="create")
@click.option("--name", "-n", prompt=True, help="Flow name")
@click.option("--trigger", "-t", type=click.Choice(["webhook", "schedule", "manual"]), default="manual")
def flows_create(name: str, trigger: str):
    """Create a new automation flow."""
    body = {"name": name, "trigger_type": trigger}

    resp = _request("post", "/v1/flows", json=body)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Flow '{name}' created with {trigger} trigger")
    console.print(f"  ID: {data.get('id', '-')}")
    console.print()
    console.print("Next steps:")
    console.print("  1. [cyan]hanzo auto dev[/cyan] - Start visual editor")
    console.print("  2. Add steps to your flow")
    console.print("  3. [cyan]hanzo auto deploy[/cyan] - Deploy to production")


@flows.command(name="run")
@click.argument("flow_name")
@click.option("--input", "-i", help="JSON input for the flow")
def flows_run(flow_name: str, input: str):
    """Run an automation flow."""
    body = {}
    if input:
        body["input"] = json.loads(input)

    console.print(f"[cyan]Running flow '{flow_name}'...[/cyan]")
    resp = _request("post", f"/v1/flows/{flow_name}/run", json=body)
    data = check_response(resp)

    run_status = data.get("status", "completed")
    style = "green" if run_status in ("completed", "success") else "red"
    console.print(f"[{style}]✓[/{style}] Flow {run_status}")
    console.print(f"  Run ID: {data.get('id', data.get('run_id', '-'))}")
    if data.get("duration_ms"):
        console.print(f"  Duration: {data['duration_ms']}ms")


@flows.command(name="delete")
@click.argument("flow_name")
def flows_delete(flow_name: str):
    """Delete an automation flow."""
    from rich.prompt import Confirm

    if not Confirm.ask(f"[red]Delete flow '{flow_name}'?[/red]"):
        return

    resp = _request("delete", f"/v1/flows/{flow_name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Flow '{flow_name}' deleted")


@flows.command(name="enable")
@click.argument("flow_name")
def flows_enable(flow_name: str):
    """Enable an automation flow."""
    resp = _request("post", f"/v1/flows/{flow_name}/enable")
    check_response(resp)
    console.print(f"[green]✓[/green] Flow '{flow_name}' enabled")


@flows.command(name="disable")
@click.argument("flow_name")
def flows_disable(flow_name: str):
    """Disable an automation flow."""
    resp = _request("post", f"/v1/flows/{flow_name}/disable")
    check_response(resp)
    console.print(f"[green]✓[/green] Flow '{flow_name}' disabled")


# ============================================================================
# Pieces (Integrations)
# ============================================================================


@auto_group.group()
def pieces():
    """Manage automation pieces (integrations)."""
    pass


@pieces.command(name="list")
@click.option("--category", "-c", help="Filter by category")
@click.option("--search", "-s", help="Search pieces")
def pieces_list(category: str, search: str):
    """List available pieces."""
    params = {}
    if category:
        params["category"] = category
    if search:
        params["search"] = search

    resp = _request("get", "/v1/pieces", params=params)
    data = check_response(resp)
    items = data.get("pieces", data.get("items", []))

    table = Table(title="Available Pieces", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="white")
    table.add_column("Version", style="dim")
    table.add_column("Installed", style="green")

    for p in items:
        table.add_row(
            p.get("name", ""),
            p.get("category", "-"),
            p.get("version", "-"),
            "✓" if p.get("installed") else "",
        )

    console.print(table)
    if not items:
        console.print("[dim]No pieces found[/dim]")


@pieces.command(name="install")
@click.argument("piece_name")
def pieces_install(piece_name: str):
    """Install a piece."""
    console.print(f"[cyan]Installing piece '{piece_name}'...[/cyan]")
    resp = _request("post", f"/v1/pieces/{piece_name}/install")
    check_response(resp)
    console.print(f"[green]✓[/green] Piece '{piece_name}' installed")


@pieces.command(name="uninstall")
@click.argument("piece_name")
def pieces_uninstall(piece_name: str):
    """Uninstall a piece."""
    resp = _request("post", f"/v1/pieces/{piece_name}/uninstall")
    check_response(resp)
    console.print(f"[green]✓[/green] Piece '{piece_name}' uninstalled")


# ============================================================================
# Connections
# ============================================================================


@auto_group.group()
def connections():
    """Manage connections to external services."""
    pass


@connections.command(name="list")
def connections_list():
    """List all connections."""
    resp = _request("get", "/v1/connections")
    data = check_response(resp)
    items = data.get("connections", data.get("items", []))

    table = Table(title="Connections", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Piece", style="white")
    table.add_column("Status", style="green")
    table.add_column("Created", style="dim")

    for c in items:
        c_status = c.get("status", "active")
        style = "green" if c_status == "active" else "yellow"
        table.add_row(
            c.get("name", ""),
            c.get("piece", "-"),
            f"[{style}]{c_status}[/{style}]",
            str(c.get("created_at", ""))[:19],
        )

    console.print(table)
    if not items:
        console.print("[dim]No connections found. Add one with 'hanzo auto connections add'[/dim]")


@connections.command(name="add")
@click.argument("piece_name")
@click.option("--name", "-n", help="Connection name")
def connections_add(piece_name: str, name: str):
    """Add a new connection."""
    body = {"piece": piece_name}
    if name:
        body["name"] = name

    resp = _request("post", "/v1/connections", json=body)
    data = check_response(resp)

    auth_url = data.get("auth_url")
    if auth_url:
        console.print(f"[cyan]Authenticate at:[/cyan] {auth_url}")
    console.print(f"[green]✓[/green] Connection added")
    console.print(f"  ID: {data.get('id', '-')}")


@connections.command(name="delete")
@click.argument("connection_name")
def connections_delete(connection_name: str):
    """Delete a connection."""
    resp = _request("delete", f"/v1/connections/{connection_name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Connection '{connection_name}' deleted")


# ============================================================================
# Development
# ============================================================================


@auto_group.command()
def init():
    """Initialize Hanzo Auto project."""
    from pathlib import Path

    project_dir = Path.cwd() / ".hanzo" / "auto"
    project_dir.mkdir(parents=True, exist_ok=True)

    (project_dir / "flows").mkdir(exist_ok=True)
    (project_dir / "pieces").mkdir(exist_ok=True)

    console.print("[green]✓[/green] Hanzo Auto initialized")
    console.print()
    console.print("Next steps:")
    console.print("  1. [cyan]hanzo auto dev[/cyan] - Start development server")
    console.print("  2. Open http://localhost:8080 to build flows visually")


@auto_group.command()
@click.option("--port", "-p", default=8080, help="Port to run on")
def dev(port: int):
    """Start local development server."""
    console.print(f"[cyan]Starting Hanzo Auto development server on port {port}...[/cyan]")
    console.print()
    console.print(f"  [cyan]Visual Editor:[/cyan] http://localhost:{port}")
    console.print(f"  [cyan]API:[/cyan] http://localhost:{port}/api")
    console.print()
    console.print("Press Ctrl+C to stop")


@auto_group.command()
@click.option("--all", "deploy_all", is_flag=True, help="Deploy all flows")
@click.argument("flow_name", required=False)
def deploy(flow_name: str, deploy_all: bool):
    """Deploy flows to production."""
    if not flow_name and not deploy_all:
        raise click.ClickException("Specify a flow name or use --all")

    body = {}
    if deploy_all:
        body["all"] = True
        console.print("[cyan]Deploying all flows...[/cyan]")
    else:
        body["flow"] = flow_name
        console.print(f"[cyan]Deploying flow '{flow_name}'...[/cyan]")

    resp = _request("post", "/v1/flows/deploy", json=body)
    data = check_response(resp)
    console.print(f"[green]✓[/green] Deployed {data.get('deployed', 1)} flow(s)")


# ============================================================================
# Runs (Execution History)
# ============================================================================


@auto_group.group()
def runs():
    """View flow execution history."""
    pass


@runs.command(name="list")
@click.option("--flow", "-f", help="Filter by flow")
@click.option("--status", type=click.Choice(["success", "failed", "running", "all"]), default="all")
@click.option("--limit", "-n", default=50, help="Max results")
def runs_list(flow: str, status: str, limit: int):
    """List flow runs."""
    params = {"limit": limit}
    if flow:
        params["flow"] = flow
    if status != "all":
        params["status"] = status

    resp = _request("get", "/v1/runs", params=params)
    data = check_response(resp)
    items = data.get("runs", data.get("items", []))

    table = Table(title="Flow Runs", box=box.ROUNDED)
    table.add_column("Run ID", style="cyan")
    table.add_column("Flow", style="white")
    table.add_column("Status", style="green")
    table.add_column("Duration", style="yellow")
    table.add_column("Started", style="dim")

    for r in items:
        r_status = r.get("status", "unknown")
        status_style = {
            "success": "green",
            "completed": "green",
            "failed": "red",
            "running": "cyan",
        }.get(r_status, "white")

        table.add_row(
            str(r.get("id", ""))[:16],
            r.get("flow", "-"),
            f"[{status_style}]{r_status}[/{status_style}]",
            f"{r.get('duration_ms', '-')}ms" if r.get("duration_ms") else "-",
            str(r.get("started_at", ""))[:19],
        )

    console.print(table)
    if not items:
        console.print("[dim]No runs found[/dim]")


@runs.command(name="show")
@click.argument("run_id")
def runs_show(run_id: str):
    """Show run details."""
    resp = _request("get", f"/v1/runs/{run_id}")
    data = check_response(resp)

    run_status = data.get("status", "unknown")
    status_style = "green" if run_status in ("success", "completed") else "red" if run_status == "failed" else "cyan"

    console.print(
        Panel(
            f"[cyan]Run ID:[/cyan] {data.get('id', run_id)}\n"
            f"[cyan]Flow:[/cyan] {data.get('flow', '-')}\n"
            f"[cyan]Status:[/cyan] [{status_style}]{run_status}[/{status_style}]\n"
            f"[cyan]Duration:[/cyan] {data.get('duration_ms', '-')}ms\n"
            f"[cyan]Steps:[/cyan] {data.get('step_count', 0)}\n"
            f"[cyan]Started:[/cyan] {str(data.get('started_at', ''))[:19]}",
            title="Run Details",
            border_style="cyan",
        )
    )

    if data.get("error"):
        console.print(f"\n[red]Error:[/red] {data['error']}")


@runs.command(name="logs")
@click.argument("run_id")
@click.option("--step", "-s", help="Specific step")
def runs_logs(run_id: str, step: str):
    """View run logs."""
    params = {}
    if step:
        params["step"] = step

    resp = _request("get", f"/v1/runs/{run_id}/logs", params=params)
    data = check_response(resp)
    lines = data.get("logs", data.get("lines", []))

    console.print(f"[cyan]Logs for run {run_id}:[/cyan]")
    for line in lines:
        if isinstance(line, dict):
            ts = str(line.get("timestamp", ""))[:19]
            level = line.get("level", "info")
            msg = line.get("message", "")
            style = "red" if level == "error" else "yellow" if level == "warn" else "dim"
            console.print(f"[dim]{ts}[/dim] [{style}]{level}[/{style}] {msg}")
        else:
            console.print(str(line))

    if not lines:
        console.print("[dim]No logs available[/dim]")


@runs.command(name="retry")
@click.argument("run_id")
def runs_retry(run_id: str):
    """Retry a failed run."""
    resp = _request("post", f"/v1/runs/{run_id}/retry")
    data = check_response(resp)
    console.print(f"[green]✓[/green] Run restarted")
    console.print(f"  New Run ID: {data.get('id', data.get('run_id', '-'))}")


# ============================================================================
# Templates
# ============================================================================


@auto_group.group()
def templates():
    """Pre-built automation templates."""
    pass


@templates.command(name="list")
@click.option("--category", "-c", help="Filter by category")
def templates_list(category: str):
    """List available templates."""
    params = {}
    if category:
        params["category"] = category

    resp = _request("get", "/v1/templates", params=params)
    data = check_response(resp)
    items = data.get("templates", data.get("items", []))

    table = Table(title="Automation Templates", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="white")
    table.add_column("Pieces", style="green")
    table.add_column("Description", style="dim")

    for t in items:
        table.add_row(
            t.get("name", ""),
            t.get("category", "-"),
            str(t.get("piece_count", 0)),
            t.get("description", "-"),
        )

    console.print(table)
    if not items:
        console.print("[dim]No templates found[/dim]")


@templates.command(name="use")
@click.argument("template_name")
@click.option("--name", "-n", help="Flow name")
def templates_use(template_name: str, name: str):
    """Create flow from template."""
    body = {"template": template_name}
    if name:
        body["name"] = name

    resp = _request("post", "/v1/flows/from-template", json=body)
    data = check_response(resp)

    flow_name = data.get("name", name or template_name.lower().replace(" ", "-"))
    console.print(f"[green]✓[/green] Flow '{flow_name}' created from template")
    console.print(f"  ID: {data.get('id', '-')}")
    console.print("Configure connections with: hanzo auto connections add <piece>")


# ============================================================================
# Webhooks
# ============================================================================


@auto_group.group()
def webhooks():
    """Manage webhook triggers."""
    pass


@webhooks.command(name="list")
def webhooks_list():
    """List webhook endpoints."""
    resp = _request("get", "/v1/webhooks")
    data = check_response(resp)
    items = data.get("webhooks", data.get("items", []))

    table = Table(title="Webhooks", box=box.ROUNDED)
    table.add_column("Flow", style="cyan")
    table.add_column("URL", style="white")
    table.add_column("Method", style="green")
    table.add_column("Calls", style="dim")

    for w in items:
        table.add_row(
            w.get("flow", ""),
            w.get("url", "-"),
            w.get("method", "POST"),
            str(w.get("call_count", 0)),
        )

    console.print(table)
    if not items:
        console.print("[dim]No webhooks found[/dim]")


@webhooks.command(name="test")
@click.argument("flow_name")
@click.option("--data", "-d", help="JSON payload")
def webhooks_test(flow_name: str, data: str):
    """Test webhook endpoint."""
    body = {}
    if data:
        body = json.loads(data)

    console.print(f"[cyan]Testing webhook for '{flow_name}'...[/cyan]")
    resp = _request("post", f"/v1/webhooks/{flow_name}/test", json=body)
    result = check_response(resp)

    console.print(f"[green]✓[/green] Webhook triggered successfully")
    console.print(f"  Status: {result.get('status_code', '-')}")
    if result.get("run_id"):
        console.print(f"  Run ID: {result['run_id']}")


# ============================================================================
# AI Actions
# ============================================================================


@auto_group.group()
def ai():
    """AI-powered automation actions."""
    pass


@ai.command(name="generate")
@click.option("--prompt", "-p", required=True, help="What to automate")
@click.option("--name", "-n", help="Flow name")
def ai_generate(prompt: str, name: str):
    """Generate automation flow with AI.

    \b
    Examples:
      hanzo auto ai generate -p "When I get an email from a customer, summarize it and post to Slack"
      hanzo auto ai generate -p "Every morning, send me a summary of GitHub issues"
    """
    body = {"prompt": prompt}
    if name:
        body["name"] = name

    console.print("[cyan]Generating flow from prompt...[/cyan]")
    resp = _request("post", "/v1/ai/generate", json=body)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Flow generated")
    console.print(f"  Name: {data.get('name', '-')}")
    console.print(f"  Steps: {data.get('step_count', 0)}")
    if data.get("pieces"):
        console.print(f"  Pieces: {', '.join(data['pieces'])}")


@ai.command(name="suggest")
@click.argument("flow_name")
def ai_suggest(flow_name: str):
    """Get AI suggestions to improve a flow."""
    console.print(f"[cyan]Analyzing flow '{flow_name}'...[/cyan]")
    resp = _request("post", f"/v1/ai/suggest", json={"flow": flow_name})
    data = check_response(resp)

    suggestions = data.get("suggestions", [])
    if suggestions:
        console.print()
        console.print("[cyan]Suggestions:[/cyan]")
        for i, s in enumerate(suggestions, 1):
            console.print(f"  {i}. {s}")
    else:
        console.print("[dim]No suggestions at this time[/dim]")


@ai.command(name="explain")
@click.argument("flow_name")
def ai_explain(flow_name: str):
    """Get AI explanation of what a flow does."""
    console.print(f"[cyan]Explaining flow '{flow_name}'...[/cyan]")
    resp = _request("post", f"/v1/ai/explain", json={"flow": flow_name})
    data = check_response(resp)

    explanation = data.get("explanation", "No explanation available")
    console.print()
    console.print(explanation)
