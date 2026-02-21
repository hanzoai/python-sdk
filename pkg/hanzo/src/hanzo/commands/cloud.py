"""Cloud infrastructure management commands for Hanzo CLI.

Follows gcloud idioms: hanzo cloud <service> <verb>

Canonical verbs:
  - list, describe, create, delete, update
  - connect, env, status (Hanzo-specific)

Lifecycle verbs (resource-dependent):
  - start, stop, restart (stateful services)
  - enable, disable (functions, cron)
  - pause, resume (queues)
"""

import os
import json
from typing import Optional
from pathlib import Path

import click
import httpx
from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm

from ..utils.output import console

HANZO_API_URL = os.getenv("HANZO_API_URL", "https://api.hanzo.ai")

# Service definitions with lifecycle capabilities
SERVICES = {
    "vector": {
        "name": "Vector Database",
        "description": "Qdrant vector similarity search",
        "env_prefix": "QDRANT",
        "default_port": 6333,
        "lifecycle": ["start", "stop", "restart"],
    },
    "kv": {
        "name": "Key-Value Store",
        "description": "Redis/Valkey for caching and state",
        "env_prefix": "REDIS",
        "default_port": 6379,
        "lifecycle": ["start", "stop", "restart"],
    },
    "documentdb": {
        "name": "Document Database",
        "description": "MongoDB for document storage",
        "env_prefix": "MONGODB",
        "default_port": 27017,
        "lifecycle": ["start", "stop", "restart"],
    },
    "storage": {
        "name": "Object Storage",
        "description": "S3-compatible storage (MinIO)",
        "env_prefix": "S3",
        "default_port": 9000,
        "lifecycle": ["start", "stop", "restart"],
    },
    "search": {
        "name": "Full-Text Search",
        "description": "Meilisearch for fast search",
        "env_prefix": "MEILI",
        "default_port": 7700,
        "lifecycle": ["start", "stop", "restart"],
    },
    "pubsub": {
        "name": "Pub/Sub Messaging",
        "description": "NATS for event streaming",
        "env_prefix": "NATS",
        "default_port": 4222,
        "lifecycle": ["start", "stop", "restart"],
    },
    "tasks": {
        "name": "Workflow Engine",
        "description": "Temporal for durable workflows",
        "env_prefix": "TEMPORAL",
        "default_port": 7233,
        "lifecycle": ["start", "stop", "restart"],
    },
    "queues": {
        "name": "Job Queues",
        "description": "Distributed work queues",
        "env_prefix": "QUEUE",
        "default_port": 6379,
        "lifecycle": ["pause", "resume"],
    },
    "cron": {
        "name": "Scheduled Jobs",
        "description": "Cron-based job scheduling",
        "env_prefix": "CRON",
        "default_port": 6379,
        "lifecycle": ["enable", "disable"],
    },
    "functions": {
        "name": "Serverless Functions",
        "description": "Nuclio function runtime",
        "env_prefix": "NUCLIO",
        "default_port": 8070,
        "lifecycle": ["enable", "disable"],
    },
}

SERVICE_NAMES = tuple(SERVICES.keys())


def get_api_key() -> Optional[str]:
    """Get Hanzo API key from env or auth file."""
    if os.getenv("HANZO_API_KEY"):
        return os.getenv("HANZO_API_KEY")

    auth_file = Path.home() / ".hanzo" / "auth.json"
    if auth_file.exists():
        try:
            auth = json.loads(auth_file.read_text())
            return auth.get("api_key")
        except Exception:
            pass
    return None


def get_cloud_config() -> dict:
    """Load cloud configuration."""
    config_file = Path.home() / ".hanzo" / "cloud.json"
    if config_file.exists():
        try:
            return json.loads(config_file.read_text())
        except Exception:
            pass
    return {"instances": {}}


def save_cloud_config(config: dict):
    """Save cloud configuration."""
    config_dir = Path.home() / ".hanzo"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "cloud.json"
    config_file.write_text(json.dumps(config, indent=2))


# ============================================================================
# Main cloud group
# ============================================================================


@click.group(name="cloud")
def cloud_group():
    """Manage Hanzo Cloud infrastructure.

    \b
    Structure: hanzo cloud <service> <verb>

    \b
    Discovery:
      hanzo cloud services list       # Available service types
      hanzo cloud instances list      # Your provisioned instances

    \b
    Per-service commands:
      hanzo cloud vector create       # Create a vector DB
      hanzo cloud vector describe     # Show instance details
      hanzo cloud vector delete       # Delete instance
      hanzo cloud vector connect      # Connection details
      hanzo cloud vector env          # Export env vars
      hanzo cloud vector status       # Health check

    \b
    Services: vector, kv, documentdb, storage, search,
              pubsub, tasks, queues, cron, functions
    """
    pass


# ============================================================================
# Services subgroup - list available service types
# ============================================================================


@cloud_group.group(name="services")
def services_group():
    """Manage available service types."""
    pass


@services_group.command(name="list")
def services_list():
    """List available infrastructure service types."""
    table = Table(title="Available Services", box=box.ROUNDED)
    table.add_column("Service", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Description", style="dim")
    table.add_column("Lifecycle", style="yellow")

    for key, info in SERVICES.items():
        lifecycle = ", ".join(info.get("lifecycle", []))
        table.add_row(key, info["name"], info["description"], lifecycle or "-")

    console.print(table)


# ============================================================================
# Instances subgroup - list/describe provisioned instances
# ============================================================================


@cloud_group.group(name="instances")
def instances_group():
    """Manage provisioned instances."""
    pass


@instances_group.command(name="list")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
def instances_list(fmt: str):
    """List all provisioned instances."""
    config = get_cloud_config()
    instances = config.get("instances", {})

    if fmt == "json":
        console.print_json(json.dumps(instances))
        return

    if not instances:
        console.print("[yellow]No instances provisioned.[/yellow]")
        console.print("Run 'hanzo cloud <service> create' to get started.")
        return

    table = Table(title="Provisioned Instances", box=box.ROUNDED)
    table.add_column("Service", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Region", style="dim")
    table.add_column("Tier", style="green")
    table.add_column("Status", style="yellow")

    for svc_name, svc_config in instances.items():
        table.add_row(
            svc_name,
            svc_config.get("name", "default"),
            svc_config.get("region", "us-west-2"),
            svc_config.get("tier", "free"),
            svc_config.get("status", "unknown"),
        )

    console.print(table)


@instances_group.command(name="describe")
@click.argument("service", type=click.Choice(SERVICE_NAMES))
@click.option("--name", default="default", help="Instance name")
def instances_describe(service: str, name: str):
    """Describe a provisioned instance."""
    config = get_cloud_config()
    instances = config.get("instances", {})

    if service not in instances:
        console.print(f"[yellow]No {service} instance found.[/yellow]")
        return

    svc_config = instances[service]
    info = SERVICES[service]

    console.print(
        Panel(
            f"[cyan]Service:[/cyan] {info['name']}\n"
            f"[cyan]Name:[/cyan] {svc_config.get('name', 'default')}\n"
            f"[cyan]ID:[/cyan] {svc_config.get('id', 'N/A')}\n"
            f"[cyan]URL:[/cyan] {svc_config.get('url', 'N/A')}\n"
            f"[cyan]Host:[/cyan] {svc_config.get('host', 'N/A')}\n"
            f"[cyan]Port:[/cyan] {svc_config.get('port', 'N/A')}\n"
            f"[cyan]Tier:[/cyan] {svc_config.get('tier', 'free')}\n"
            f"[cyan]Region:[/cyan] {svc_config.get('region', 'N/A')}\n"
            f"[cyan]Status:[/cyan] {svc_config.get('status', 'unknown')}",
            title=f"[bold]{service}[/bold]",
            border_style="cyan",
        )
    )


# ============================================================================
# Operations subgroup - async operation tracking
# ============================================================================


@cloud_group.group(name="operations")
def operations_group():
    """Track async operations."""
    pass


@operations_group.command(name="list")
def operations_list():
    """List recent operations."""
    api_key = get_api_key()
    if not api_key:
        console.print("[red]Not authenticated. Run 'hanzo auth login' first.[/red]")
        return

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(
                f"{HANZO_API_URL}/v1/cloud/operations",
                headers={"Authorization": f"Bearer {api_key}"},
            )

            if resp.status_code >= 400:
                console.print(f"[red]Error: {resp.text}[/red]")
                return

            data = resp.json()
            operations = data.get("operations", [])

            if not operations:
                console.print("[dim]No recent operations.[/dim]")
                return

            table = Table(title="Operations", box=box.ROUNDED)
            table.add_column("ID", style="cyan")
            table.add_column("Type", style="white")
            table.add_column("Resource", style="dim")
            table.add_column("Status", style="yellow")

            for op in operations:
                table.add_row(
                    op.get("id", "")[:12],
                    op.get("type", ""),
                    op.get("resource", ""),
                    op.get("status", ""),
                )

            console.print(table)

    except httpx.ConnectError:
        console.print("[red]Could not connect to Hanzo API.[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@operations_group.command(name="describe")
@click.argument("operation_id")
def operations_describe(operation_id: str):
    """Describe an operation."""
    api_key = get_api_key()
    if not api_key:
        console.print("[red]Not authenticated.[/red]")
        return

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(
                f"{HANZO_API_URL}/v1/cloud/operations/{operation_id}",
                headers={"Authorization": f"Bearer {api_key}"},
            )

            if resp.status_code >= 400:
                console.print(f"[red]Error: {resp.text}[/red]")
                return

            data = resp.json()
            console.print_json(json.dumps(data, indent=2))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@operations_group.command(name="wait")
@click.argument("operation_id")
@click.option("--timeout", default=300, help="Timeout in seconds")
def operations_wait(operation_id: str, timeout: int):
    """Wait for an operation to complete."""
    api_key = get_api_key()
    if not api_key:
        console.print("[red]Not authenticated.[/red]")
        return

    import time

    start = time.time()

    with console.status(f"Waiting for operation {operation_id[:12]}..."):
        while time.time() - start < timeout:
            try:
                with httpx.Client(timeout=30) as client:
                    resp = client.get(
                        f"{HANZO_API_URL}/v1/cloud/operations/{operation_id}",
                        headers={"Authorization": f"Bearer {api_key}"},
                    )

                    if resp.status_code >= 400:
                        console.print(f"[red]Error: {resp.text}[/red]")
                        return

                    data = resp.json()
                    status = data.get("status", "")

                    if status in ("done", "completed", "succeeded"):
                        console.print("[green]✓ Operation completed[/green]")
                        return
                    elif status in ("failed", "error"):
                        console.print(f"[red]✗ Operation failed: {data.get('error', 'Unknown error')}[/red]")
                        return

                    time.sleep(2)

            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                return

    console.print("[yellow]Timeout waiting for operation[/yellow]")


# ============================================================================
# Per-service command factory
# ============================================================================


def create_service_group(service_key: str, service_info: dict):
    """Create a command group for a specific service."""

    @click.group(name=service_key)
    def service_group():
        pass

    service_group.__doc__ = f"Manage {service_info['name']} instances."

    # create command
    @service_group.command(name="create")
    @click.option("--name", default="default", help="Instance name")
    @click.option("--tier", type=click.Choice(["free", "pro", "enterprise"]), default="free")
    @click.option("--region", default="us-west-2", help="Deployment region")
    def create(name: str, tier: str, region: str):
        """Create a new instance."""
        _create_instance(service_key, name, tier, region)

    # describe command
    @service_group.command(name="describe")
    @click.option("--name", default="default", help="Instance name")
    def describe(name: str):
        """Show instance details."""
        _describe_instance(service_key, name)

    # list command
    @service_group.command(name="list")
    def list_cmd():
        """List instances of this service type."""
        _list_service_instances(service_key)

    # delete command
    @service_group.command(name="delete")
    @click.option("--name", default="default", help="Instance name")
    @click.option("--force", is_flag=True, help="Skip confirmation")
    def delete(name: str, force: bool):
        """Delete an instance."""
        _delete_instance(service_key, name, force)

    # connect command
    @service_group.command(name="connect")
    @click.option("--name", default="default", help="Instance name")
    def connect(name: str):
        """Show connection details."""
        _connect_instance(service_key, name)

    # env command
    @service_group.command(name="env")
    @click.option("--name", default="default", help="Instance name")
    @click.option("--shell", type=click.Choice(["bash", "zsh", "fish", "powershell"]), default="bash")
    @click.option("--export", "do_export", is_flag=True, help="Print export statements")
    def env(name: str, shell: str, do_export: bool):
        """Show/export environment variables."""
        _env_instance(service_key, name, shell, do_export)

    # status command
    @service_group.command(name="status")
    @click.option("--name", default="default", help="Instance name")
    def status(name: str):
        """Check instance health."""
        _status_instance(service_key, name)

    # update command
    @service_group.command(name="update")
    @click.option("--name", default="default", help="Instance name")
    @click.option("--tier", type=click.Choice(["free", "pro", "enterprise"]))
    def update(name: str, tier: Optional[str]):
        """Update instance configuration."""
        _update_instance(service_key, name, tier)

    # Add lifecycle commands based on service capabilities
    lifecycle = service_info.get("lifecycle", [])

    if "start" in lifecycle:

        @service_group.command(name="start")
        @click.option("--name", default="default")
        def start(name: str):
            """Start a stopped instance."""
            _lifecycle_action(service_key, name, "start")

    if "stop" in lifecycle:

        @service_group.command(name="stop")
        @click.option("--name", default="default")
        def stop(name: str):
            """Stop a running instance."""
            _lifecycle_action(service_key, name, "stop")

    if "restart" in lifecycle:

        @service_group.command(name="restart")
        @click.option("--name", default="default")
        def restart(name: str):
            """Restart an instance."""
            _lifecycle_action(service_key, name, "restart")

    if "enable" in lifecycle:

        @service_group.command(name="enable")
        @click.option("--name", default="default")
        def enable(name: str):
            """Enable the service."""
            _lifecycle_action(service_key, name, "enable")

    if "disable" in lifecycle:

        @service_group.command(name="disable")
        @click.option("--name", default="default")
        def disable(name: str):
            """Disable the service."""
            _lifecycle_action(service_key, name, "disable")

    if "pause" in lifecycle:

        @service_group.command(name="pause")
        @click.option("--name", default="default")
        def pause(name: str):
            """Pause the service (retain data)."""
            _lifecycle_action(service_key, name, "pause")

    if "resume" in lifecycle:

        @service_group.command(name="resume")
        @click.option("--name", default="default")
        def resume(name: str):
            """Resume a paused service."""
            _lifecycle_action(service_key, name, "resume")

    return service_group


# ============================================================================
# Implementation functions
# ============================================================================


def _create_instance(service: str, name: str, tier: str, region: str):
    """Create a new instance."""
    api_key = get_api_key()
    if not api_key:
        console.print("[red]Not authenticated. Run 'hanzo auth login' first.[/red]")
        return

    info = SERVICES[service]
    console.print(f"[cyan]Creating {info['name']} instance '{name}'...[/cyan]")

    try:
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{HANZO_API_URL}/v1/cloud/{service}",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "name": name,
                    "tier": tier,
                    "region": region,
                },
            )

            if resp.status_code == 401:
                console.print("[red]Authentication failed. Run 'hanzo auth login'.[/red]")
                return

            if resp.status_code == 402:
                console.print("[yellow]Upgrade required for this tier.[/yellow]")
                console.print("Visit https://hanzo.ai/pricing to upgrade.")
                return

            if resp.status_code == 409:
                console.print(f"[yellow]Instance '{name}' already exists. Use 'update' to modify.[/yellow]")
                return

            if resp.status_code >= 400:
                console.print(f"[red]Error: {resp.text}[/red]")
                return

            data = resp.json()

            # Save to config
            config = get_cloud_config()
            config["instances"][service] = {
                "id": data.get("id"),
                "name": name,
                "url": data.get("url"),
                "host": data.get("host"),
                "port": data.get("port"),
                "credentials": data.get("credentials", {}),
                "tier": tier,
                "region": region,
                "status": "running",
            }
            save_cloud_config(config)

            console.print(f"[green]✓ {info['name']} created successfully![/green]")
            console.print()
            console.print(f"[cyan]URL:[/cyan] {data.get('url')}")
            console.print()
            console.print(f"[dim]Run 'hanzo cloud {service} env --export' for environment variables[/dim]")

    except httpx.ConnectError:
        console.print("[red]Could not connect to Hanzo API.[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def _describe_instance(service: str, name: str):
    """Describe an instance."""
    config = get_cloud_config()
    instances = config.get("instances", {})

    if service not in instances:
        console.print(f"[yellow]No {service} instance found.[/yellow]")
        console.print(f"Run 'hanzo cloud {service} create' to create one.")
        return

    svc_config = instances[service]
    info = SERVICES[service]

    console.print(
        Panel(
            f"[cyan]Service:[/cyan] {info['name']}\n"
            f"[cyan]Name:[/cyan] {svc_config.get('name', 'default')}\n"
            f"[cyan]ID:[/cyan] {svc_config.get('id', 'N/A')}\n"
            f"[cyan]URL:[/cyan] {svc_config.get('url', 'N/A')}\n"
            f"[cyan]Host:[/cyan] {svc_config.get('host', 'N/A')}\n"
            f"[cyan]Port:[/cyan] {svc_config.get('port', 'N/A')}\n"
            f"[cyan]Tier:[/cyan] {svc_config.get('tier', 'free')}\n"
            f"[cyan]Region:[/cyan] {svc_config.get('region', 'N/A')}\n"
            f"[cyan]Status:[/cyan] {svc_config.get('status', 'unknown')}",
            title=f"[bold]{service}[/bold]",
            border_style="cyan",
        )
    )


def _list_service_instances(service: str):
    """List instances of a specific service type."""
    config = get_cloud_config()
    instances = config.get("instances", {})

    if service not in instances:
        console.print(f"[yellow]No {service} instances.[/yellow]")
        console.print(f"Run 'hanzo cloud {service} create' to create one.")
        return

    svc_config = instances[service]
    info = SERVICES[service]

    table = Table(title=f"{info['name']} Instances", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Region", style="dim")
    table.add_column("Tier", style="green")
    table.add_column("Status", style="yellow")

    table.add_row(
        svc_config.get("name", "default"),
        svc_config.get("region", "us-west-2"),
        svc_config.get("tier", "free"),
        svc_config.get("status", "unknown"),
    )

    console.print(table)


def _delete_instance(service: str, name: str, force: bool):
    """Delete an instance."""
    config = get_cloud_config()
    instances = config.get("instances", {})

    if service not in instances:
        console.print(f"[yellow]{service} not provisioned.[/yellow]")
        return

    info = SERVICES[service]

    if not force:
        if not Confirm.ask(f"[red]Delete {info['name']} '{name}'? This cannot be undone.[/red]"):
            console.print("Cancelled.")
            return

    api_key = get_api_key()
    if not api_key:
        console.print("[red]Not authenticated.[/red]")
        return

    try:
        with httpx.Client(timeout=30) as client:
            svc_id = instances[service].get("id")
            resp = client.delete(
                f"{HANZO_API_URL}/v1/cloud/{service}/{svc_id}",
                headers={"Authorization": f"Bearer {api_key}"},
            )

            if resp.status_code >= 400 and resp.status_code != 404:
                console.print(f"[red]Error: {resp.text}[/red]")
                return

        # Remove from config
        del config["instances"][service]
        save_cloud_config(config)

        console.print(f"[green]✓ {info['name']} deleted.[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def _connect_instance(service: str, name: str):
    """Show connection details."""
    config = get_cloud_config()
    instances = config.get("instances", {})

    if service not in instances:
        console.print(f"[yellow]No {service} instance found.[/yellow]")
        return

    svc_config = instances[service]
    info = SERVICES[service]

    console.print(
        Panel(
            f"[cyan]URL:[/cyan] {svc_config.get('url', 'N/A')}\n"
            f"[cyan]Host:[/cyan] {svc_config.get('host', 'N/A')}\n"
            f"[cyan]Port:[/cyan] {svc_config.get('port', 'N/A')}",
            title=f"[bold]{info['name']} Connection[/bold]",
            border_style="cyan",
        )
    )


def _env_instance(service: str, name: str, shell: str, do_export: bool):
    """Show/export environment variables."""
    config = get_cloud_config()
    instances = config.get("instances", {})

    if service not in instances:
        console.print(f"[yellow]No {service} instance found.[/yellow]")
        return

    svc_config = instances[service]
    info = SERVICES[service]
    prefix = info["env_prefix"]

    env_vars = []
    if svc_config.get("url"):
        env_vars.append((f"{prefix}_URL", svc_config["url"]))
    if svc_config.get("host"):
        env_vars.append((f"{prefix}_HOST", svc_config["host"]))
    if svc_config.get("port"):
        env_vars.append((f"{prefix}_PORT", str(svc_config["port"])))

    creds = svc_config.get("credentials", {})
    if creds.get("api_key"):
        env_vars.append((f"{prefix}_API_KEY", creds["api_key"]))
    if creds.get("password"):
        env_vars.append((f"{prefix}_PASSWORD", creds["password"]))
    if creds.get("username"):
        env_vars.append((f"{prefix}_USERNAME", creds["username"]))

    if do_export:
        if shell in ("bash", "zsh"):
            for key, value in env_vars:
                console.print(f'export {key}="{value}"')
        elif shell == "fish":
            for key, value in env_vars:
                console.print(f'set -gx {key} "{value}"')
        elif shell == "powershell":
            for key, value in env_vars:
                console.print(f'$env:{key} = "{value}"')
    else:
        table = Table(title=f"{info['name']} Environment", box=box.ROUNDED)
        table.add_column("Variable", style="cyan")
        table.add_column("Value", style="green")

        for key, value in env_vars:
            if "KEY" in key or "PASSWORD" in key or "SECRET" in key:
                display = value[:8] + "..." if len(value) > 8 else "***"
            else:
                display = value
            table.add_row(key, display)

        console.print(table)
        console.print()
        console.print(f"[dim]Run 'hanzo cloud {service} env --export' for export statements[/dim]")


def _status_instance(service: str, name: str):
    """Check instance health."""
    config = get_cloud_config()
    instances = config.get("instances", {})

    if service not in instances:
        console.print(f"[yellow]No {service} instance found.[/yellow]")
        return

    svc_config = instances[service]
    info = SERVICES[service]
    api_key = get_api_key()

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                f"{HANZO_API_URL}/v1/cloud/{service}/{svc_config.get('id')}/health",
                headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
            )

            if resp.status_code == 200:
                data = resp.json()
                status = "[green]● Healthy[/green]"
                latency = f"{data.get('latency_ms', '?')}ms"
            else:
                status = "[yellow]○ Unknown[/yellow]"
                latency = "-"
    except Exception:
        status = "[red]✗ Unreachable[/red]"
        latency = "-"

    console.print(f"{info['name']}: {status} ({latency})")


def _update_instance(service: str, name: str, tier: Optional[str]):
    """Update instance configuration."""
    if not tier:
        console.print("[yellow]No updates specified.[/yellow]")
        console.print("Use --tier to change the service tier.")
        return

    api_key = get_api_key()
    if not api_key:
        console.print("[red]Not authenticated.[/red]")
        return

    config = get_cloud_config()
    instances = config.get("instances", {})

    if service not in instances:
        console.print(f"[yellow]No {service} instance found.[/yellow]")
        return

    svc_config = instances[service]
    info = SERVICES[service]

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.patch(
                f"{HANZO_API_URL}/v1/cloud/{service}/{svc_config.get('id')}",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"tier": tier} if tier else {},
            )

            if resp.status_code >= 400:
                console.print(f"[red]Error: {resp.text}[/red]")
                return

            # Update local config
            if tier:
                config["instances"][service]["tier"] = tier
            save_cloud_config(config)

            console.print(f"[green]✓ {info['name']} updated.[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def _lifecycle_action(service: str, name: str, action: str):
    """Execute a lifecycle action."""
    api_key = get_api_key()
    if not api_key:
        console.print("[red]Not authenticated.[/red]")
        return

    config = get_cloud_config()
    instances = config.get("instances", {})

    if service not in instances:
        console.print(f"[yellow]No {service} instance found.[/yellow]")
        return

    svc_config = instances[service]
    info = SERVICES[service]

    console.print(f"[cyan]{action.capitalize()}ing {info['name']}...[/cyan]")

    try:
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{HANZO_API_URL}/v1/cloud/{service}/{svc_config.get('id')}/{action}",
                headers={"Authorization": f"Bearer {api_key}"},
            )

            if resp.status_code >= 400:
                console.print(f"[red]Error: {resp.text}[/red]")
                return

            # Update local status
            status_map = {
                "start": "running",
                "stop": "stopped",
                "restart": "running",
                "enable": "enabled",
                "disable": "disabled",
                "pause": "paused",
                "resume": "running",
            }
            config["instances"][service]["status"] = status_map.get(action, "unknown")
            save_cloud_config(config)

            console.print(f"[green]✓ {info['name']} {action}ed.[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


# ============================================================================
# Register all service groups
# ============================================================================

for svc_key, svc_info in SERVICES.items():
    service_cmd = create_service_group(svc_key, svc_info)
    cloud_group.add_command(service_cmd)


# ============================================================================
# Init command
# ============================================================================


@cloud_group.command(name="init")
def init():
    """Initialize infrastructure from hanzo.yaml config file."""
    config_paths = [
        Path.cwd() / "hanzo.yaml",
        Path.cwd() / "hanzo.yml",
        Path.cwd() / ".hanzo.yaml",
    ]

    config_file = None
    for p in config_paths:
        if p.exists():
            config_file = p
            break

    if not config_file:
        console.print("[yellow]No hanzo.yaml found in current directory.[/yellow]")
        console.print()
        console.print("Create one with:")
        console.print()
        console.print("[cyan]# hanzo.yaml[/cyan]")
        console.print("cloud:")
        console.print("  vector: true")
        console.print("  kv: true")
        console.print("  search: true")
        return

    import yaml

    try:
        config = yaml.safe_load(config_file.read_text())
    except Exception as e:
        console.print(f"[red]Error parsing {config_file}: {e}[/red]")
        return

    cloud_config = config.get("cloud", {})
    if not cloud_config:
        console.print("[yellow]No 'cloud' section in config file.[/yellow]")
        return

    console.print(f"[cyan]Initializing cloud services from {config_file}...[/cyan]")

    for service, enabled in cloud_config.items():
        if service in SERVICES and enabled:
            console.print(f"  Creating {service}...")
            _create_instance(service, "default", "free", "us-west-2")

    console.print("[green]✓ Cloud infrastructure initialized![/green]")
