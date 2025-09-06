"""Node management commands."""

from typing import List, Optional

import click
from rich.table import Table
from rich.progress import Progress, TextColumn, SpinnerColumn

from ..utils.output import console


@click.group(name="node")
def cluster():
    """Manage local AI node."""
    pass


@cluster.command()
@click.option("--name", "-n", default="hanzo-local", help="Node name")
@click.option("--port", "-p", default=8000, type=int, help="API port")
@click.option("--models", "-m", multiple=True, help="Models to load")
@click.option(
    "--device",
    type=click.Choice(["cpu", "gpu", "auto"]),
    default="auto",
    help="Device to use",
)
@click.pass_context
async def start(ctx, name: str, port: int, models: tuple, device: str):
    """Start local AI node."""
    await start_node(ctx, name, port, list(models) if models else None, device)


async def start_node(
    ctx, name: str, port: int, models: Optional[List[str]] = None, device: str = "auto"
):
    """Start a local node via hanzo-cluster."""
    try:
        from hanzo_cluster import HanzoCluster
    except ImportError:
        console.print("[red]Error:[/red] hanzo-cluster not installed")
        console.print("Install with: pip install hanzo[cluster]")
        return

    node = HanzoCluster(name=name, port=port, device=device)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Starting node...", total=None)

        try:
            await node.start(models=models)
            progress.update(task, completed=True)
        except Exception as e:
            progress.stop()
            console.print(f"[red]Failed to start node: {e}[/red]")
            return

    console.print(f"[green]✓[/green] Node started at http://localhost:{port}")
    console.print("Press Ctrl+C to stop\n")

    # Show node info
    info = await node.info()
    console.print("[cyan]Node Information:[/cyan]")
    console.print(f"  Name: {info.get('name', name)}")
    console.print(f"  Port: {info.get('port', port)}")
    console.print(f"  Device: {info.get('device', device)}")
    console.print(f"  Workers: {info.get('nodes', 1)}")
    if models := info.get("models", models):
        console.print(f"  Models: {', '.join(models)}")

    console.print("\n[dim]Logs:[/dim]")

    try:
        # Stream logs
        async for log in node.stream_logs():
            console.print(log, end="")
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping node...[/yellow]")
        await node.stop()
        console.print("[green]✓[/green] Node stopped")


@cluster.command()
@click.option("--name", "-n", default="hanzo-local", help="Node name")
@click.pass_context
async def stop(ctx, name: str):
    """Stop local AI node."""
    try:
        from hanzo_cluster import HanzoCluster
    except ImportError:
        console.print("[red]Error:[/red] hanzo-cluster not installed")
        return

    node = HanzoCluster(name=name)

    console.print("[yellow]Stopping node...[/yellow]")
    try:
        await node.stop()
        console.print("[green]✓[/green] Node stopped")
    except Exception as e:
        console.print(f"[red]Failed to stop node: {e}[/red]")


@cluster.command()
@click.option("--name", "-n", default="hanzo-local", help="Node name")
@click.pass_context
async def status(ctx, name: str):
    """Show node status."""
    try:
        from hanzo_cluster import HanzoCluster
    except ImportError:
        console.print("[red]Error:[/red] hanzo-cluster not installed")
        return

    node = HanzoCluster(name=name)

    try:
        status = await node.status()

        if status.get("running"):
            console.print("[green]✓[/green] Node is running")

            # Show node info
            console.print("\n[cyan]Node Information:[/cyan]")
            console.print(f"  Name: {status.get('name', name)}")
            console.print(f"  Workers: {status.get('nodes', 0)}")
            console.print(f"  Status: {status.get('state', 'unknown')}")

            # Show models
            if models := status.get("models", []):
                console.print("\n[cyan]Available Models:[/cyan]")
                for model in models:
                    console.print(f"  • {model}")

            # Show worker details
            if workers := status.get("node_details", []):
                console.print("\n[cyan]Workers:[/cyan]")
                for worker in workers:
                    console.print(
                        f"  • {worker.get('name', 'unknown')} ({worker.get('state', 'unknown')})"
                    )
                    if device := worker.get("device"):
                        console.print(f"    Device: {device}")
        else:
            console.print("[yellow]![/yellow] Node is not running")
            console.print("Start with: hanzo node start")

    except Exception as e:
        console.print(f"[red]Error checking status: {e}[/red]")


@cluster.command()
@click.option("--name", "-n", default="hanzo-local", help="Node name")
@click.pass_context
async def models(ctx, name: str):
    """List available models."""
    try:
        from hanzo_cluster import HanzoCluster
    except ImportError:
        console.print("[red]Error:[/red] hanzo-cluster not installed")
        return

    node = HanzoCluster(name=name)

    try:
        models = await node.list_models()

        if models:
            table = Table(title="Available Models")
            table.add_column("Model ID", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("Worker", style="blue")

            for model in models:
                table.add_row(
                    model.get("id", "unknown"),
                    model.get("type", "model"),
                    model.get("status", "unknown"),
                    model.get("node", "local"),
                )

            console.print(table)
        else:
            console.print("[yellow]No models loaded[/yellow]")
            console.print("Load models with: hanzo node load <model>")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cluster.command()
@click.argument("model")
@click.option("--name", "-n", default="hanzo-local", help="Node name")
@click.option("--worker", help="Target worker (default: auto-select)")
@click.pass_context
async def load(ctx, model: str, name: str, worker: str = None):
    """Load a model into the node."""
    try:
        from hanzo_cluster import HanzoCluster
    except ImportError:
        console.print("[red]Error:[/red] hanzo-cluster not installed")
        return

    node = HanzoCluster(name=name)

    with console.status(f"Loading model '{model}'..."):
        try:
            result = await node.load_model(model, node=worker)
            console.print(f"[green]✓[/green] Loaded model: {model}")
            if worker_name := result.get("node"):
                console.print(f"  Worker: {worker_name}")
        except Exception as e:
            console.print(f"[red]Failed to load model: {e}[/red]")


@cluster.command()
@click.argument("model")
@click.option("--name", "-n", default="hanzo-local", help="Node name")
@click.pass_context
async def unload(ctx, model: str, name: str):
    """Unload a model from the node."""
    try:
        from hanzo_cluster import HanzoCluster
    except ImportError:
        console.print("[red]Error:[/red] hanzo-cluster not installed")
        return

    node = HanzoCluster(name=name)

    if click.confirm(f"Unload model '{model}'?"):
        with console.status(f"Unloading model '{model}'..."):
            try:
                await node.unload_model(model)
                console.print(f"[green]✓[/green] Unloaded model: {model}")
            except Exception as e:
                console.print(f"[red]Failed to unload model: {e}[/red]")


@cluster.group(name="worker")
def worker_group():
    """Manage node workers."""
    pass


@worker_group.command(name="start")
@click.option("--name", "-n", default="worker-1", help="Worker name")
@click.option("--node", "-nd", default="hanzo-local", help="Node to join")
@click.option(
    "--device",
    type=click.Choice(["cpu", "gpu", "auto"]),
    default="auto",
    help="Device to use",
)
@click.option(
    "--port", "-p", type=int, help="Worker port (auto-assigned if not specified)"
)
@click.option("--blockchain", is_flag=True, help="Enable blockchain features")
@click.option("--network", is_flag=True, help="Enable network discovery")
@click.pass_context
async def worker_start(
    ctx,
    name: str,
    node: str,
    device: str,
    port: int,
    blockchain: bool,
    network: bool,
):
    """Start this machine as a worker in the node."""
    try:
        from hanzo_cluster import HanzoNode

        if blockchain or network:
            from hanzo_network import HanzoNetwork
    except ImportError:
        console.print("[red]Error:[/red] Required packages not installed")
        console.print("Install with: pip install hanzo[cluster,network]")
        return

    worker = HanzoNode(name=name, device=device, port=port)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Starting worker '{name}'...", total=None)

        try:
            # Start the worker
            await worker.start(cluster=node)

            # Enable blockchain/network features if requested
            if blockchain or network:
                network_mgr = HanzoNetwork(node=worker)
                if blockchain:
                    await network_mgr.enable_blockchain()
                if network:
                    await network_mgr.enable_discovery()

            progress.update(task, completed=True)
        except Exception as e:
            progress.stop()
            console.print(f"[red]Failed to start worker: {e}[/red]")
            return

    console.print(f"[green]✓[/green] Worker '{name}' started")
    console.print(f"  Node: {node}")
    console.print(f"  Device: {device}")
    if port:
        console.print(f"  Port: {port}")
    if blockchain:
        console.print("  [cyan]Blockchain enabled[/cyan]")
    if network:
        console.print("  [cyan]Network discovery enabled[/cyan]")

    console.print("\nPress Ctrl+C to stop\n")
    console.print("[dim]Logs:[/dim]")

    try:
        # Stream logs
        async for log in worker.stream_logs():
            console.print(log, end="")
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping worker...[/yellow]")
        await worker.stop()
        console.print("[green]✓[/green] Worker stopped")


@worker_group.command(name="stop")
@click.option("--name", "-n", help="Worker name")
@click.option("--all", is_flag=True, help="Stop all workers")
@click.pass_context
async def worker_stop(ctx, name: str, all: bool):
    """Stop a worker."""
    try:
        from hanzo_cluster import HanzoNode
    except ImportError:
        console.print("[red]Error:[/red] hanzo-cluster not installed")
        return

    if all:
        if click.confirm("Stop all workers?"):
            console.print("[yellow]Stopping all workers...[/yellow]")
            try:
                await HanzoNode.stop_all()
                console.print("[green]✓[/green] All workers stopped")
            except Exception as e:
                console.print(f"[red]Failed to stop workers: {e}[/red]")
    elif name:
        worker = HanzoNode(name=name)
        console.print(f"[yellow]Stopping worker '{name}'...[/yellow]")
        try:
            await worker.stop()
            console.print(f"[green]✓[/green] Worker stopped")
        except Exception as e:
            console.print(f"[red]Failed to stop worker: {e}[/red]")
    else:
        console.print("[red]Error:[/red] Specify --name or --all")


@worker_group.command(name="list")
@click.option("--node", "-nd", help="Filter by node")
@click.pass_context
async def worker_list(ctx, node: str):
    """List all workers."""
    try:
        from hanzo_cluster import HanzoNode
    except ImportError:
        console.print("[red]Error:[/red] hanzo-cluster not installed")
        return

    try:
        workers = await HanzoNode.list_nodes(cluster=node)

        if workers:
            table = Table(title="Node Workers")
            table.add_column("Name", style="cyan")
            table.add_column("Node", style="green")
            table.add_column("Device", style="yellow")
            table.add_column("Status", style="blue")
            table.add_column("Models", style="magenta")

            for worker in workers:
                table.add_row(
                    worker.get("name", "unknown"),
                    worker.get("cluster", "unknown"),
                    worker.get("device", "unknown"),
                    worker.get("status", "unknown"),
                    str(len(worker.get("models", []))),
                )

            console.print(table)
        else:
            console.print("[yellow]No workers found[/yellow]")
            console.print("Start a worker with: hanzo node worker start")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@worker_group.command(name="info")
@click.argument("name")
@click.pass_context
async def worker_info(ctx, name: str):
    """Show detailed worker information."""
    try:
        from hanzo_cluster import HanzoNode
    except ImportError:
        console.print("[red]Error:[/red] hanzo-cluster not installed")
        return

    worker = HanzoNode(name=name)

    try:
        info = await worker.info()

        console.print(f"[cyan]Worker: {name}[/cyan]")
        console.print(f"  Node: {info.get('cluster', 'unknown')}")
        console.print(f"  Status: {info.get('status', 'unknown')}")
        console.print(f"  Device: {info.get('device', 'unknown')}")

        if uptime := info.get("uptime"):
            console.print(f"  Uptime: {uptime}")

        if resources := info.get("resources"):
            console.print("\n[cyan]Resources:[/cyan]")
            console.print(f"  CPU: {resources.get('cpu_percent', 'N/A')}%")
            console.print(
                f"  Memory: {resources.get('memory_used', 'N/A')} / {resources.get('memory_total', 'N/A')}"
            )
            if gpu := resources.get("gpu"):
                console.print(
                    f"  GPU: {gpu.get('name', 'N/A')} ({gpu.get('memory_used', 'N/A')} / {gpu.get('memory_total', 'N/A')})"
                )

        if models := info.get("models"):
            console.print("\n[cyan]Loaded Models:[/cyan]")
            for model in models:
                console.print(f"  • {model}")

        if network := info.get("network"):
            console.print("\n[cyan]Network:[/cyan]")
            console.print(
                f"  Blockchain: {'enabled' if network.get('blockchain') else 'disabled'}"
            )
            console.print(
                f"  Discovery: {'enabled' if network.get('discovery') else 'disabled'}"
            )
            if peers := network.get("peers"):
                console.print(f"  Peers: {len(peers)}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")