"""Hanzo Flow - Visual LLM workflow builder CLI.

Build and deploy LLM applications with a visual interface (Langflow-compatible).
"""

import os
import json

import click
import httpx
from rich import box
from rich.panel import Panel
from rich.table import Table

from ..utils.output import console
from .base import service_request, check_response

FLOW_URL = os.getenv("HANZO_FLOW_URL", "https://flow.hanzo.ai")


def _request(method: str, path: str, **kwargs) -> httpx.Response:
    return service_request(FLOW_URL, method, path, **kwargs)


@click.group(name="flow")
def flow_group():
    """Hanzo Flow - Visual LLM workflow builder (Langflow-compatible).

    \b
    Flows:
      hanzo flow create            # Create LLM flow
      hanzo flow list              # List flows
      hanzo flow run               # Run a flow
      hanzo flow export            # Export flow definition

    \b
    Components:
      hanzo flow components        # List available components
      hanzo flow custom            # Manage custom components

    \b
    Development:
      hanzo flow dev               # Start visual editor
      hanzo flow deploy            # Deploy to production

    \b
    API:
      hanzo flow api               # Manage flow APIs
      hanzo flow playground        # Interactive playground
    """
    pass


# ============================================================================
# Flow Management
# ============================================================================


@flow_group.command(name="create")
@click.argument("name")
@click.option("--template", "-t", help="Start from template")
@click.option("--description", "-d", help="Flow description")
def flow_create(name: str, template: str, description: str):
    """Create a new LLM flow.

    \b
    Examples:
      hanzo flow create chatbot
      hanzo flow create rag-assistant --template rag
      hanzo flow create summarizer --template chain
    """
    body = {"name": name}
    if template:
        body["template"] = template
    if description:
        body["description"] = description

    resp = _request("post", "/v1/flows", json=body)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Flow '{name}' created")
    console.print(f"  ID: {data.get('id', '-')}")
    if template:
        console.print(f"  Template: {template}")
    console.print()
    console.print("Next steps:")
    console.print("  1. [cyan]hanzo flow dev[/cyan] - Open visual editor")
    console.print("  2. Add components to your flow")
    console.print(f"  3. [cyan]hanzo flow deploy {name}[/cyan] - Deploy to production")


@flow_group.command(name="list")
@click.option("--status", type=click.Choice(["deployed", "draft", "all"]), default="all")
def flow_list(status: str):
    """List LLM flows."""
    params = {}
    if status != "all":
        params["status"] = status

    resp = _request("get", "/v1/flows", params=params)
    data = check_response(resp)
    items = data.get("flows", data.get("items", []))

    table = Table(title="LLM Flows", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Components", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Endpoint", style="white")
    table.add_column("Updated", style="dim")

    for f in items:
        f_status = f.get("status", "draft")
        style = "green" if f_status == "deployed" else "yellow"
        table.add_row(
            f.get("name", ""),
            str(f.get("component_count", 0)),
            f"[{style}]{f_status}[/{style}]",
            f.get("endpoint", "-"),
            str(f.get("updated_at", ""))[:19],
        )

    console.print(table)
    if not items:
        console.print("[dim]No flows found. Create one with 'hanzo flow create'[/dim]")


@flow_group.command(name="describe")
@click.argument("name")
def flow_describe(name: str):
    """Show flow details."""
    resp = _request("get", f"/v1/flows/{name}")
    data = check_response(resp)

    status = data.get("status", "draft")
    status_style = "green" if status == "deployed" else "yellow"

    console.print(
        Panel(
            f"[cyan]Name:[/cyan] {data.get('name', name)}\n"
            f"[cyan]Status:[/cyan] [{status_style}]{status}[/{status_style}]\n"
            f"[cyan]Components:[/cyan] {data.get('component_count', 0)}\n"
            f"[cyan]Endpoint:[/cyan] {data.get('endpoint', '-')}\n"
            f"[cyan]Calls (24h):[/cyan] {data.get('calls_24h', 0):,}\n"
            f"[cyan]Avg Latency:[/cyan] {data.get('avg_latency_ms', 0)}ms\n"
            f"[cyan]Created:[/cyan] {str(data.get('created_at', ''))[:19]}",
            title="Flow Details",
            border_style="cyan",
        )
    )


@flow_group.command(name="run")
@click.argument("name")
@click.option("--input", "-i", "input_data", required=True, help="Input JSON or text")
@click.option("--stream", "-s", is_flag=True, help="Stream output")
@click.option("--verbose", "-v", is_flag=True, help="Show component outputs")
def flow_run(name: str, input_data: str, stream: bool, verbose: bool):
    """Run a flow locally.

    \b
    Examples:
      hanzo flow run chatbot -i "What is machine learning?"
      hanzo flow run rag -i '{"query": "How do I reset my password?"}'
      hanzo flow run summarizer -i @document.txt --stream
    """
    body = {"input": input_data}
    if stream:
        body["stream"] = True
    if verbose:
        body["verbose"] = True

    console.print(f"[cyan]Running flow '{name}'...[/cyan]")
    resp = _request("post", f"/v1/flows/{name}/run", json=body)
    data = check_response(resp)

    if verbose and data.get("steps"):
        for step in data["steps"]:
            console.print(f"  [dim]→ {step.get('name', 'step')}: {step.get('status', 'done')}[/dim]")

    console.print()
    console.print("[green]Output:[/green]")
    output = data.get("output", data.get("result", ""))
    console.print(str(output))


@flow_group.command(name="delete")
@click.argument("name")
@click.option("--force", "-f", is_flag=True)
def flow_delete(name: str, force: bool):
    """Delete a flow."""
    if not force:
        from rich.prompt import Confirm

        if not Confirm.ask(f"[red]Delete flow '{name}'?[/red]"):
            return

    resp = _request("delete", f"/v1/flows/{name}")
    check_response(resp)
    console.print(f"[green]✓[/green] Flow '{name}' deleted")


@flow_group.command(name="export")
@click.argument("name")
@click.option("--output", "-o", help="Output file")
@click.option("--format", "fmt", type=click.Choice(["json", "yaml"]), default="json")
def flow_export(name: str, output: str, fmt: str):
    """Export flow definition."""
    resp = _request("get", f"/v1/flows/{name}/export", params={"format": fmt})
    data = check_response(resp)

    out_file = output or f"{name}.{fmt}"
    with open(out_file, "w") as f:
        if fmt == "json":
            json.dump(data, f, indent=2, default=str)
        else:
            f.write(str(data.get("yaml", data.get("definition", ""))))

    console.print(f"[green]✓[/green] Flow exported to '{out_file}'")


@flow_group.command(name="import")
@click.argument("file")
@click.option("--name", "-n", help="Override flow name")
def flow_import(file: str, name: str):
    """Import flow from file."""
    with open(file) as f:
        definition = json.load(f)

    body = {"definition": definition}
    if name:
        body["name"] = name

    console.print(f"[cyan]Importing flow from '{file}'...[/cyan]")
    resp = _request("post", "/v1/flows/import", json=body)
    data = check_response(resp)
    console.print(f"[green]✓[/green] Flow '{data.get('name', name or 'imported')}' imported")


# ============================================================================
# Components
# ============================================================================


@flow_group.group()
def components():
    """Manage flow components."""
    pass


@components.command(name="list")
@click.option("--category", "-c", help="Filter by category")
@click.option("--search", "-s", help="Search components")
def components_list(category: str, search: str):
    """List available components."""
    params = {}
    if category:
        params["category"] = category
    if search:
        params["search"] = search

    resp = _request("get", "/v1/components", params=params)
    data = check_response(resp)
    items = data.get("components", data.get("items", []))

    table = Table(title="Flow Components", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="white")
    table.add_column("Description", style="dim")

    for c in items:
        table.add_row(
            c.get("name", ""),
            c.get("category", "-"),
            c.get("description", "-"),
        )

    console.print(table)
    if not items:
        console.print("[dim]No components found[/dim]")


@components.command(name="describe")
@click.argument("name")
def components_describe(name: str):
    """Show component details."""
    resp = _request("get", f"/v1/components/{name}")
    data = check_response(resp)

    inputs = ", ".join(data.get("inputs", [])) or "-"
    outputs = ", ".join(data.get("outputs", [])) or "-"
    config = ", ".join(data.get("config", [])) or "-"

    console.print(
        Panel(
            f"[cyan]Name:[/cyan] {data.get('name', name)}\n"
            f"[cyan]Category:[/cyan] {data.get('category', '-')}\n"
            f"[cyan]Inputs:[/cyan] {inputs}\n"
            f"[cyan]Outputs:[/cyan] {outputs}\n"
            f"[cyan]Config:[/cyan] {config}\n"
            f"[cyan]Description:[/cyan] {data.get('description', '-')}",
            title="Component Details",
            border_style="cyan",
        )
    )


# ============================================================================
# Custom Components
# ============================================================================


@flow_group.group()
def custom():
    """Manage custom components."""
    pass


@custom.command(name="create")
@click.argument("name")
@click.option("--template", "-t", type=click.Choice(["tool", "chain", "agent"]), default="tool")
def custom_create(name: str, template: str):
    """Create a custom component."""
    body = {"name": name, "template": template}

    resp = _request("post", "/v1/components/custom", json=body)
    data = check_response(resp)

    console.print(f"[green]✓[/green] Custom component '{name}' created")
    console.print(f"  Template: {template}")
    console.print(f"  File: {data.get('file', f'components/{name}.py')}")


@custom.command(name="list")
def custom_list():
    """List custom components."""
    resp = _request("get", "/v1/components/custom")
    data = check_response(resp)
    items = data.get("components", data.get("items", []))

    table = Table(title="Custom Components", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("File", style="dim")

    for c in items:
        table.add_row(
            c.get("name", ""),
            c.get("type", "-"),
            c.get("file", "-"),
        )

    console.print(table)
    if not items:
        console.print("[dim]No custom components found[/dim]")


@custom.command(name="publish")
@click.argument("name")
def custom_publish(name: str):
    """Publish component to registry."""
    console.print(f"[cyan]Publishing component '{name}'...[/cyan]")
    resp = _request("post", f"/v1/components/custom/{name}/publish")
    check_response(resp)
    console.print(f"[green]✓[/green] Component published")


# ============================================================================
# Development
# ============================================================================


@flow_group.command(name="dev")
@click.option("--port", "-p", default=7860, help="Port to run on")
@click.option("--flow", "-f", help="Open specific flow")
def flow_dev(port: int, flow: str):
    """Start visual flow editor."""
    console.print(f"[cyan]Starting Hanzo Flow editor on port {port}...[/cyan]")
    console.print()
    console.print(f"  [cyan]Editor:[/cyan] http://localhost:{port}")
    if flow:
        console.print(f"  [cyan]Flow:[/cyan] {flow}")
    console.print()
    console.print("Press Ctrl+C to stop")


@flow_group.command(name="deploy")
@click.argument("name")
@click.option("--env", "-e", default="production", help="Environment")
def flow_deploy(name: str, env: str):
    """Deploy flow to production."""
    console.print(f"[cyan]Deploying flow '{name}' to {env}...[/cyan]")
    resp = _request("post", f"/v1/flows/{name}/deploy", json={"environment": env})
    data = check_response(resp)

    console.print(f"[green]✓[/green] Flow deployed")
    console.print(f"  Endpoint: {data.get('endpoint', f'{FLOW_URL}/{name}')}")
    if data.get("api_key"):
        console.print(f"  API Key: {data['api_key'][:12]}***")


@flow_group.command(name="undeploy")
@click.argument("name")
def flow_undeploy(name: str):
    """Undeploy a flow."""
    resp = _request("post", f"/v1/flows/{name}/undeploy")
    check_response(resp)
    console.print(f"[green]✓[/green] Flow '{name}' undeployed")


# ============================================================================
# API Management
# ============================================================================


@flow_group.group()
def api():
    """Manage flow APIs."""
    pass


@api.command(name="keys")
@click.argument("flow_name")
def api_keys(flow_name: str):
    """List API keys for a flow."""
    resp = _request("get", f"/v1/flows/{flow_name}/keys")
    data = check_response(resp)
    items = data.get("keys", data.get("items", []))

    table = Table(title=f"API Keys for '{flow_name}'", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Key", style="white")
    table.add_column("Created", style="dim")
    table.add_column("Last Used", style="dim")

    for k in items:
        table.add_row(
            k.get("name", ""),
            k.get("key_prefix", "****"),
            str(k.get("created_at", ""))[:19],
            str(k.get("last_used_at", "-"))[:19],
        )

    console.print(table)
    if not items:
        console.print("[dim]No API keys found[/dim]")


@api.command(name="create-key")
@click.argument("flow_name")
@click.option("--name", "-n", default="default", help="Key name")
def api_create_key(flow_name: str, name: str):
    """Create API key for a flow."""
    resp = _request("post", f"/v1/flows/{flow_name}/keys", json={"name": name})
    data = check_response(resp)

    console.print(f"[green]✓[/green] API key created for '{flow_name}'")
    console.print(f"  Name: {name}")
    console.print(f"  Key: {data.get('key', '-')}")
    console.print("[yellow]Save this key - it won't be shown again[/yellow]")


@api.command(name="revoke-key")
@click.argument("flow_name")
@click.argument("key_name")
def api_revoke_key(flow_name: str, key_name: str):
    """Revoke an API key."""
    resp = _request("delete", f"/v1/flows/{flow_name}/keys/{key_name}")
    check_response(resp)
    console.print(f"[green]✓[/green] API key '{key_name}' revoked")


@api.command(name="test")
@click.argument("flow_name")
@click.option("--input", "-i", "input_data", required=True, help="Test input")
def api_test(flow_name: str, input_data: str):
    """Test flow API endpoint."""
    console.print(f"[cyan]Testing API for '{flow_name}'...[/cyan]")
    resp = _request("post", f"/v1/flows/{flow_name}/test", json={"input": input_data})
    data = check_response(resp)

    console.print(f"[green]✓[/green] API responded successfully")
    console.print(f"  Status: {data.get('status_code', 200)}")
    console.print(f"  Latency: {data.get('latency_ms', '-')}ms")
    if data.get("output"):
        console.print(f"  Output: {json.dumps(data['output'], default=str)[:200]}")


# ============================================================================
# Playground
# ============================================================================


@flow_group.command(name="playground")
@click.argument("name")
@click.option("--port", "-p", default=7861, help="Port")
def flow_playground(name: str, port: int):
    """Open interactive playground for a flow."""
    console.print(f"[cyan]Opening playground for '{name}'...[/cyan]")
    console.print(f"  URL: http://localhost:{port}/playground/{name}")


# ============================================================================
# Templates
# ============================================================================


@flow_group.group()
def templates():
    """Pre-built flow templates."""
    pass


@templates.command(name="list")
def templates_list():
    """List available templates."""
    resp = _request("get", "/v1/templates")
    data = check_response(resp)
    items = data.get("templates", data.get("items", []))

    table = Table(title="Flow Templates", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Components", style="dim")

    for t in items:
        table.add_row(
            t.get("name", ""),
            t.get("description", "-"),
            t.get("components", "-"),
        )

    console.print(table)
    if not items:
        console.print("[dim]No templates found[/dim]")


@templates.command(name="use")
@click.argument("template")
@click.option("--name", "-n", required=True, help="Flow name")
def templates_use(template: str, name: str):
    """Create flow from template."""
    console.print(f"[cyan]Creating flow '{name}' from template '{template}'...[/cyan]")
    resp = _request("post", "/v1/flows/from-template", json={"template": template, "name": name})
    data = check_response(resp)

    console.print(f"[green]✓[/green] Flow created")
    console.print(f"  ID: {data.get('id', '-')}")
    console.print()
    console.print("Next steps:")
    console.print(f"  1. [cyan]hanzo flow dev -f {name}[/cyan] - Edit in visual editor")
    console.print(f"  2. [cyan]hanzo flow deploy {name}[/cyan] - Deploy to production")


# ============================================================================
# Versions & History
# ============================================================================


@flow_group.command(name="versions")
@click.argument("name")
def flow_versions(name: str):
    """List flow versions."""
    resp = _request("get", f"/v1/flows/{name}/versions")
    data = check_response(resp)
    items = data.get("versions", data.get("items", []))

    table = Table(title=f"Versions of '{name}'", box=box.ROUNDED)
    table.add_column("Version", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Created", style="dim")
    table.add_column("Note", style="dim")

    for v in items:
        v_status = v.get("status", "inactive")
        style = "green" if v_status == "active" else "dim"
        table.add_row(
            str(v.get("version", "")),
            f"[{style}]{v_status}[/{style}]",
            str(v.get("created_at", ""))[:19],
            v.get("note", "-"),
        )

    console.print(table)
    if not items:
        console.print("[dim]No versions found[/dim]")


@flow_group.command(name="rollback")
@click.argument("name")
@click.option("--version", "-v", required=True, help="Target version")
def flow_rollback(name: str, version: str):
    """Rollback to a previous version."""
    console.print(f"[cyan]Rolling back '{name}' to version {version}...[/cyan]")
    resp = _request("post", f"/v1/flows/{name}/rollback", json={"version": version})
    check_response(resp)
    console.print(f"[green]✓[/green] Rolled back successfully")
