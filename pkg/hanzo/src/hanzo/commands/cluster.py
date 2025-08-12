"""Cluster management commands."""

from typing import List, Optional

import click
from rich.table import Table
from rich.progress import Progress, TextColumn, SpinnerColumn

from ..utils.output import console


@click.group(name="cluster")
def cluster_group():
    """Manage local AI cluster."""
    pass


@cluster_group.command()
@click.option("--name", "-n", default="hanzo-local", help="Cluster name")
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
    """Start local AI cluster."""
    await start_cluster(ctx, name, port, list(models) if models else None, device)


async def start_cluster(
    ctx, name: str, port: int, models: Optional[List[str]] = None, device: str = "auto"
):
    """Start a local cluster via hanzo-cluster."""
    try:
        from hanzo_cluster import HanzoCluster
    except ImportError:
        console.print("[red]Error:[/red] hanzo-cluster not installed")
        console.print("Install with: pip install hanzo[cluster]")
        return

    cluster = HanzoCluster(name=name, port=port, device=device)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Starting cluster...", total=None)

        try:
            await cluster.start(models=models)
            progress.update(task, completed=True)
        except Exception as e:
            progress.stop()
            console.print(f"[red]Failed to start cluster: {e}[/red]")
            return

    console.print(f"[green]✓[/green] Cluster started at http://localhost:{port}")
    console.print("Press Ctrl+C to stop\n")

    # Show cluster info
    info = await cluster.info()
    console.print("[cyan]Cluster Information:[/cyan]")
    console.print(f"  Name: {info.get('name', name)}")
    console.print(f"  Port: {info.get('port', port)}")
    console.print(f"  Device: {info.get('device', device)}")
    console.print(f"  Nodes: {info.get('nodes', 1)}")
    if models := info.get("models", models):
        console.print(f"  Models: {', '.join(models)}")

    console.print("\n[dim]Logs:[/dim]")

    try:
        # Stream logs
        async for log in cluster.stream_logs():
            console.print(log, end="")
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping cluster...[/yellow]")
        await cluster.stop()
        console.print("[green]✓[/green] Cluster stopped")


@cluster_group.command()
@click.option("--name", "-n", default="hanzo-local", help="Cluster name")
@click.pass_context
async def stop(ctx, name: str):
    """Stop local AI cluster."""
    try:
        from hanzo_cluster import HanzoCluster
    except ImportError:
        console.print("[red]Error:[/red] hanzo-cluster not installed")
        return

    cluster = HanzoCluster(name=name)

    console.print("[yellow]Stopping cluster...[/yellow]")
    try:
        await cluster.stop()
        console.print("[green]✓[/green] Cluster stopped")
    except Exception as e:
        console.print(f"[red]Failed to stop cluster: {e}[/red]")


@cluster_group.command()
@click.option("--name", "-n", default="hanzo-local", help="Cluster name")
@click.pass_context
async def status(ctx, name: str):
    """Show cluster status."""
    try:
        from hanzo_cluster import HanzoCluster
    except ImportError:
        console.print("[red]Error:[/red] hanzo-cluster not installed")
        return

    cluster = HanzoCluster(name=name)

    try:
        status = await cluster.status()

        if status.get("running"):
            console.print("[green]✓[/green] Cluster is running")

            # Show cluster info
            console.print("\n[cyan]Cluster Information:[/cyan]")
            console.print(f"  Name: {status.get('name', name)}")
            console.print(f"  Nodes: {status.get('nodes', 0)}")
            console.print(f"  Status: {status.get('state', 'unknown')}")

            # Show models
            if models := status.get("models", []):
                console.print("\n[cyan]Available Models:[/cyan]")
                for model in models:
                    console.print(f"  • {model}")

            # Show nodes
            if nodes := status.get("node_details", []):
                console.print("\n[cyan]Nodes:[/cyan]")
                for node in nodes:
                    console.print(
                        f"  • {node.get('name', 'unknown')} ({node.get('state', 'unknown')})"
                    )
                    if device := node.get("device"):
                        console.print(f"    Device: {device}")
        else:
            console.print("[yellow]![/yellow] Cluster is not running")
            console.print("Start with: hanzo cluster start")

    except Exception as e:
        console.print(f"[red]Error checking status: {e}[/red]")


@cluster_group.command()
@click.option("--name", "-n", default="hanzo-local", help="Cluster name")
@click.pass_context
async def models(ctx, name: str):
    """List available models."""
    try:
        from hanzo_cluster import HanzoCluster
    except ImportError:
        console.print("[red]Error:[/red] hanzo-cluster not installed")
        return

    cluster = HanzoCluster(name=name)

    try:
        models = await cluster.list_models()

        if models:
            table = Table(title="Available Models")
            table.add_column("Model ID", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("Node", style="blue")

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
            console.print("Load models with: hanzo cluster load <model>")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@cluster_group.command()
@click.argument("model")
@click.option("--name", "-n", default="hanzo-local", help="Cluster name")
@click.option("--node", help="Target node (default: auto-select)")
@click.pass_context
async def load(ctx, model: str, name: str, node: str = None):
    """Load a model into the cluster."""
    try:
        from hanzo_cluster import HanzoCluster
    except ImportError:
        console.print("[red]Error:[/red] hanzo-cluster not installed")
        return

    cluster = HanzoCluster(name=name)

    with console.status(f"Loading model '{model}'..."):
        try:
            result = await cluster.load_model(model, node=node)
            console.print(f"[green]✓[/green] Loaded model: {model}")
            if node_name := result.get("node"):
                console.print(f"  Node: {node_name}")
        except Exception as e:
            console.print(f"[red]Failed to load model: {e}[/red]")


@cluster_group.command()
@click.argument("model")
@click.option("--name", "-n", default="hanzo-local", help="Cluster name")
@click.pass_context
async def unload(ctx, model: str, name: str):
    """Unload a model from the cluster."""
    try:
        from hanzo_cluster import HanzoCluster
    except ImportError:
        console.print("[red]Error:[/red] hanzo-cluster not installed")
        return

    cluster = HanzoCluster(name=name)

    if click.confirm(f"Unload model '{model}'?"):
        with console.status(f"Unloading model '{model}'..."):
            try:
                await cluster.unload_model(model)
                console.print(f"[green]✓[/green] Unloaded model: {model}")
            except Exception as e:
                console.print(f"[red]Failed to unload model: {e}[/red]")


@cluster_group.group(name="node")
def node_group():
    """Manage cluster nodes."""
    pass


@node_group.command(name="start")
@click.option("--name", "-n", default="node-1", help="Node name")
@click.option("--cluster", "-c", default="hanzo-local", help="Cluster to join")
@click.option(
    "--device",
    type=click.Choice(["cpu", "gpu", "auto"]),
    default="auto",
    help="Device to use",
)
@click.option(
    "--port", "-p", type=int, help="Node port (auto-assigned if not specified)"
)
@click.option("--blockchain", is_flag=True, help="Enable blockchain features")
@click.option("--network", is_flag=True, help="Enable network discovery")
@click.pass_context
async def node_start(
    ctx,
    name: str,
    cluster: str,
    device: str,
    port: int,
    blockchain: bool,
    network: bool,
):
    """Start this machine as a node in the cluster."""
    try:
        from hanzo_cluster import HanzoNode

        if blockchain or network:
            from hanzo_network import HanzoNetwork
    except ImportError:
        console.print("[red]Error:[/red] Required packages not installed")
        console.print("Install with: pip install hanzo[cluster,network]")
        return

    node = HanzoNode(name=name, device=device, port=port)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Starting node '{name}'...", total=None)

        try:
            # Start the node
            await node.start(cluster=cluster)

            # Enable blockchain/network features if requested
            if blockchain or network:
                network_mgr = HanzoNetwork(node=node)
                if blockchain:
                    await network_mgr.enable_blockchain()
                if network:
                    await network_mgr.enable_discovery()

            progress.update(task, completed=True)
        except Exception as e:
            progress.stop()
            console.print(f"[red]Failed to start node: {e}[/red]")
            return

    console.print(f"[green]✓[/green] Node '{name}' started")
    console.print(f"  Cluster: {cluster}")
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
        async for log in node.stream_logs():
            console.print(log, end="")
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping node...[/yellow]")
        await node.stop()
        console.print("[green]✓[/green] Node stopped")


@node_group.command(name="stop")
@click.option("--name", "-n", help="Node name")
@click.option("--all", is_flag=True, help="Stop all nodes")
@click.pass_context
async def node_stop(ctx, name: str, all: bool):
    """Stop a node."""
    try:
        from hanzo_cluster import HanzoNode
    except ImportError:
        console.print("[red]Error:[/red] hanzo-cluster not installed")
        return

    if all:
        if click.confirm("Stop all nodes?"):
            console.print("[yellow]Stopping all nodes...[/yellow]")
            try:
                await HanzoNode.stop_all()
                console.print("[green]✓[/green] All nodes stopped")
            except Exception as e:
                console.print(f"[red]Failed to stop nodes: {e}[/red]")
    elif name:
        node = HanzoNode(name=name)
        console.print(f"[yellow]Stopping node '{name}'...[/yellow]")
        try:
            await node.stop()
            console.print(f"[green]✓[/green] Node stopped")
        except Exception as e:
            console.print(f"[red]Failed to stop node: {e}[/red]")
    else:
        console.print("[red]Error:[/red] Specify --name or --all")


@node_group.command(name="list")
@click.option("--cluster", "-c", help="Filter by cluster")
@click.pass_context
async def node_list(ctx, cluster: str):
    """List all nodes."""
    try:
        from hanzo_cluster import HanzoNode
    except ImportError:
        console.print("[red]Error:[/red] hanzo-cluster not installed")
        return

    try:
        nodes = await HanzoNode.list_nodes(cluster=cluster)

        if nodes:
            table = Table(title="Cluster Nodes")
            table.add_column("Name", style="cyan")
            table.add_column("Cluster", style="green")
            table.add_column("Device", style="yellow")
            table.add_column("Status", style="blue")
            table.add_column("Models", style="magenta")

            for node in nodes:
                table.add_row(
                    node.get("name", "unknown"),
                    node.get("cluster", "unknown"),
                    node.get("device", "unknown"),
                    node.get("status", "unknown"),
                    str(len(node.get("models", []))),
                )

            console.print(table)
        else:
            console.print("[yellow]No nodes found[/yellow]")
            console.print("Start a node with: hanzo cluster node start")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@node_group.command(name="info")
@click.argument("name")
@click.pass_context
async def node_info(ctx, name: str):
    """Show detailed node information."""
    try:
        from hanzo_cluster import HanzoNode
    except ImportError:
        console.print("[red]Error:[/red] hanzo-cluster not installed")
        return

    node = HanzoNode(name=name)

    try:
        info = await node.info()

        console.print(f"[cyan]Node: {name}[/cyan]")
        console.print(f"  Cluster: {info.get('cluster', 'unknown')}")
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
