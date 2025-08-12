"""Network commands for agent networks."""

import click
from rich.table import Table
from rich.progress import Progress, TextColumn, SpinnerColumn

from ..utils.output import console


@click.group(name="network")
def network_group():
    """Manage agent networks."""
    pass


@network_group.command()
@click.argument("prompt")
@click.option("--agents", "-a", type=int, default=3, help="Number of agents")
@click.option("--model", "-m", help="Model to use")
@click.option(
    "--mode",
    type=click.Choice(["local", "distributed", "hybrid"]),
    default="hybrid",
    help="Execution mode",
)
@click.option("--consensus", is_flag=True, help="Require consensus")
@click.option("--timeout", "-t", type=int, default=300, help="Timeout in seconds")
@click.pass_context
async def dispatch(
    ctx, prompt: str, agents: int, model: str, mode: str, consensus: bool, timeout: int
):
    """Dispatch work to agent network."""
    try:
        from hanzo_network import NetworkDispatcher
    except ImportError:
        console.print("[red]Error:[/red] hanzo-network not installed")
        console.print("Install with: pip install hanzo[network]")
        return

    dispatcher = NetworkDispatcher(mode=mode)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Dispatching to network...", total=None)

        try:
            # Create job
            job = await dispatcher.create_job(
                prompt=prompt,
                num_agents=agents,
                model=model,
                consensus=consensus,
                timeout=timeout,
            )

            progress.update(task, description=f"Job {job['id']} - Finding agents...")

            # Execute job
            result = await dispatcher.execute_job(job)

            progress.update(task, completed=True)

        except Exception as e:
            progress.stop()
            console.print(f"[red]Dispatch failed: {e}[/red]")
            return

    # Show results
    console.print(f"\n[green]✓[/green] Job completed")
    console.print(f"  ID: {result['job_id']}")
    console.print(f"  Agents: {result['num_agents']}")
    console.print(f"  Duration: {result['duration']}s")

    if consensus:
        console.print(f"  Consensus: {result.get('consensus_reached', False)}")

    console.print("\n[cyan]Results:[/cyan]")

    if consensus and result.get("consensus_result"):
        console.print(result["consensus_result"])
    else:
        for i, agent_result in enumerate(result["agent_results"], 1):
            console.print(f"\n[yellow]Agent {i} ({agent_result['agent_id']}):[/yellow]")
            console.print(agent_result["result"])


@network_group.command()
@click.option(
    "--mode",
    type=click.Choice(["local", "distributed", "all"]),
    default="all",
    help="Network mode",
)
@click.pass_context
async def agents(ctx, mode: str):
    """List available agents in network."""
    try:
        from hanzo_network import get_network_agents
    except ImportError:
        console.print("[red]Error:[/red] hanzo-network not installed")
        return

    with console.status("Discovering agents..."):
        try:
            agents = await get_network_agents(mode=mode)
        except Exception as e:
            console.print(f"[red]Failed to discover agents: {e}[/red]")
            return

    if not agents:
        console.print("[yellow]No agents found[/yellow]")
        if mode == "local":
            console.print("Start local agents with: hanzo agent start")
        return

    # Group by type
    local_agents = [a for a in agents if a["type"] == "local"]
    network_agents = [a for a in agents if a["type"] == "network"]

    if local_agents:
        table = Table(title="Local Agents")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Model", style="yellow")
        table.add_column("Status", style="blue")
        table.add_column("Jobs", style="magenta")

        for agent in local_agents:
            table.add_row(
                agent["id"][:8],
                agent["name"],
                agent.get("model", "default"),
                agent["status"],
                str(agent.get("jobs_completed", 0)),
            )

        console.print(table)

    if network_agents:
        table = Table(title="Network Agents")
        table.add_column("ID", style="cyan")
        table.add_column("Location", style="green")
        table.add_column("Model", style="yellow")
        table.add_column("Latency", style="blue")
        table.add_column("Cost", style="magenta")

        for agent in network_agents:
            table.add_row(
                agent["id"][:8],
                agent.get("location", "unknown"),
                agent.get("model", "various"),
                f"{agent.get('latency', 0)}ms",
                f"${agent.get('cost_per_token', 0):.4f}",
            )

        console.print(table)


@network_group.command()
@click.option("--active", is_flag=True, help="Show only active jobs")
@click.option("--limit", "-n", type=int, default=10, help="Number of jobs to show")
@click.pass_context
async def jobs(ctx, active: bool, limit: int):
    """List network jobs."""
    try:
        from hanzo_network import get_network_jobs
    except ImportError:
        console.print("[red]Error:[/red] hanzo-network not installed")
        return

    with console.status("Loading jobs..."):
        try:
            jobs = await get_network_jobs(active_only=active, limit=limit)
        except Exception as e:
            console.print(f"[red]Failed to load jobs: {e}[/red]")
            return

    if not jobs:
        console.print("[yellow]No jobs found[/yellow]")
        return

    table = Table(title="Network Jobs")
    table.add_column("ID", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Agents", style="yellow")
    table.add_column("Created", style="blue")
    table.add_column("Duration", style="magenta")

    for job in jobs:
        table.add_row(
            job["id"][:8],
            job["status"],
            str(job["num_agents"]),
            job["created_at"],
            f"{job.get('duration', 0)}s" if job.get("duration") else "-",
        )

    console.print(table)


@network_group.command()
@click.argument("job_id")
@click.pass_context
async def job(ctx, job_id: str):
    """Show job details."""
    try:
        from hanzo_network import get_job_details
    except ImportError:
        console.print("[red]Error:[/red] hanzo-network not installed")
        return

    with console.status("Loading job details..."):
        try:
            job = await get_job_details(job_id)
        except Exception as e:
            console.print(f"[red]Failed to load job: {e}[/red]")
            return

    console.print(f"[cyan]Job {job_id}[/cyan]")
    console.print(f"  Status: {job['status']}")
    console.print(f"  Created: {job['created_at']}")
    console.print(f"  Agents: {job['num_agents']}")
    console.print(f"  Mode: {job['mode']}")

    if job["status"] == "completed":
        console.print(f"  Duration: {job['duration']}s")
        console.print(f"  Cost: ${job.get('total_cost', 0):.4f}")

    console.print(f"\n[cyan]Prompt:[/cyan]")
    console.print(job["prompt"])

    if job["status"] == "completed" and job.get("results"):
        console.print("\n[cyan]Results:[/cyan]")
        for i, result in enumerate(job["results"], 1):
            console.print(f"\n[yellow]Agent {i}:[/yellow]")
            console.print(result["content"])


@network_group.command()
@click.option("--name", "-n", default="default", help="Swarm name")
@click.option("--agents", "-a", type=int, default=5, help="Number of agents")
@click.option("--model", "-m", help="Model to use")
@click.pass_context
async def swarm(ctx, name: str, agents: int, model: str):
    """Start a local agent swarm."""
    try:
        from hanzo_network import LocalSwarm
    except ImportError:
        console.print("[red]Error:[/red] hanzo-network not installed")
        return

    swarm = LocalSwarm(name=name, size=agents, model=model)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Starting swarm...", total=None)

        try:
            await swarm.start()
            progress.update(task, completed=True)
        except Exception as e:
            progress.stop()
            console.print(f"[red]Failed to start swarm: {e}[/red]")
            return

    console.print(f"[green]✓[/green] Swarm '{name}' started with {agents} agents")
    console.print("Use 'hanzo network dispatch --mode local' to send work to swarm")
    console.print("\nPress Ctrl+C to stop swarm")

    try:
        # Keep swarm running
        await swarm.run_forever()
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping swarm...[/yellow]")
        await swarm.stop()
        console.print("[green]✓[/green] Swarm stopped")


@network_group.command()
@click.pass_context
async def stats(ctx):
    """Show network statistics."""
    try:
        from hanzo_network import get_network_stats
    except ImportError:
        console.print("[red]Error:[/red] hanzo-network not installed")
        return

    with console.status("Loading network stats..."):
        try:
            stats = await get_network_stats()
        except Exception as e:
            console.print(f"[red]Failed to load stats: {e}[/red]")
            return

    console.print("[cyan]Network Statistics[/cyan]")
    console.print(f"  Total agents: {stats['total_agents']}")
    console.print(f"  Active agents: {stats['active_agents']}")
    console.print(f"  Total jobs: {stats['total_jobs']}")
    console.print(f"  Active jobs: {stats['active_jobs']}")
    console.print(f"  Success rate: {stats['success_rate']}%")

    console.print(f"\n[cyan]Performance:[/cyan]")
    console.print(f"  Average latency: {stats['avg_latency']}ms")
    console.print(f"  Average job time: {stats['avg_job_time']}s")
    console.print(f"  Throughput: {stats['throughput']} jobs/min")

    console.print(f"\n[cyan]Economics:[/cyan]")
    console.print(f"  Total tokens: {stats['total_tokens']:,}")
    console.print(f"  Average cost: ${stats['avg_cost']:.4f}/job")
    console.print(f"  Total cost: ${stats['total_cost']:.2f}")


@network_group.command()
@click.option("--enable/--disable", default=True, help="Enable or disable discovery")
@click.pass_context
async def discovery(ctx, enable: bool):
    """Configure network discovery."""
    try:
        from hanzo_network import configure_discovery
    except ImportError:
        console.print("[red]Error:[/red] hanzo-network not installed")
        return

    try:
        await configure_discovery(enabled=enable)

        if enable:
            console.print("[green]✓[/green] Network discovery enabled")
            console.print("Your agents will be discoverable by the network")
        else:
            console.print("[green]✓[/green] Network discovery disabled")
            console.print("Your agents will only be accessible locally")

    except Exception as e:
        console.print(f"[red]Failed to configure discovery: {e}[/red]")
