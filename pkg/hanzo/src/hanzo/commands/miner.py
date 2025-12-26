"""Mining commands for distributed AI compute."""

import click
from rich.table import Table
from rich.progress import Progress, TextColumn, SpinnerColumn

from ..utils.output import console


@click.group(name="miner")
def miner_group():
    """Manage Hanzo AI mining (contribute compute)."""
    pass


@miner_group.command()
@click.option("--name", "-n", help="Miner name (auto-generated if not provided)")
@click.option("--wallet", "-w", help="Wallet address for rewards")
@click.option("--models", "-m", multiple=True, help="Models to support")
@click.option(
    "--device",
    type=click.Choice(["cpu", "gpu", "auto"]),
    default="auto",
    help="Device to use",
)
@click.option("--network", default="mainnet", help="Network to join")
@click.option("--min-stake", type=float, help="Minimum stake requirement")
@click.pass_context
async def start(
    ctx,
    name: str,
    wallet: str,
    models: tuple,
    device: str,
    network: str,
    min_stake: float,
):
    """Start mining (contribute compute to network)."""
    try:
        from hanzo_miner import HanzoMiner
    except ImportError:
        console.print("[red]Error:[/red] hanzo-miner not installed")
        console.print("Install with: pip install hanzo[miner]")
        return

    # Check wallet
    if not wallet:
        console.print("[yellow]Warning:[/yellow] No wallet address provided")
        console.print("You won't earn rewards without a wallet")
        if not click.confirm("Continue without wallet?"):
            return

    miner = HanzoMiner(
        name=name, wallet=wallet, device=device, network=network, min_stake=min_stake
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Starting miner...", total=None)

        try:
            # Start miner
            await miner.start(models=list(models) if models else None)
            progress.update(task, completed=True)
        except Exception as e:
            progress.stop()
            console.print(f"[red]Failed to start miner: {e}[/red]")
            return

    console.print(f"[green]✓[/green] Miner started")
    console.print(f"  Name: {miner.name}")
    console.print(f"  Network: {network}")
    console.print(f"  Device: {device}")
    if wallet:
        console.print(f"  Wallet: {wallet[:8]}...{wallet[-4:]}")

    # Show initial stats
    stats = await miner.get_stats()
    if stats:
        console.print("\n[cyan]Initial Stats:[/cyan]")
        console.print(f"  Jobs completed: {stats.get('jobs_completed', 0)}")
        console.print(f"  Tokens earned: {stats.get('tokens_earned', 0)}")
        console.print(f"  Uptime: {stats.get('uptime', '0s')}")

    console.print("\nPress Ctrl+C to stop mining\n")
    console.print("[dim]Logs:[/dim]")

    try:
        # Stream logs and stats
        async for event in miner.stream_events():
            if event["type"] == "log":
                console.print(event["message"], end="")
            elif event["type"] == "job":
                console.print(
                    f"[green]Job completed:[/green] {event['job_id']} (+{event['tokens']} tokens)"
                )
            elif event["type"] == "error":
                console.print(f"[red]Error:[/red] {event['message']}")
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping miner...[/yellow]")
        await miner.stop()

        # Show final stats
        final_stats = await miner.get_stats()
        if final_stats:
            console.print("\n[cyan]Session Summary:[/cyan]")
            console.print(f"  Jobs completed: {final_stats.get('jobs_completed', 0)}")
            console.print(f"  Tokens earned: {final_stats.get('tokens_earned', 0)}")
            console.print(
                f"  Average job time: {final_stats.get('avg_job_time', 'N/A')}"
            )

        console.print("[green]✓[/green] Miner stopped")


@miner_group.command()
@click.option("--name", "-n", help="Miner name")
@click.pass_context
async def stop(ctx, name: str):
    """Stop mining."""
    try:
        from hanzo_miner import HanzoMiner
    except ImportError:
        console.print("[red]Error:[/red] hanzo-miner not installed")
        return

    if name:
        miner = HanzoMiner.get_by_name(name)
        if miner:
            console.print(f"[yellow]Stopping miner '{name}'...[/yellow]")
            await miner.stop()
            console.print(f"[green]✓[/green] Miner stopped")
        else:
            console.print(f"[red]Miner not found: {name}[/red]")
    else:
        # Stop all miners
        miners = HanzoMiner.get_all()
        if miners:
            if click.confirm(f"Stop all {len(miners)} miners?"):
                for miner in miners:
                    await miner.stop()
                console.print(f"[green]✓[/green] Stopped {len(miners)} miners")
        else:
            console.print("[yellow]No miners running[/yellow]")


@miner_group.command()
@click.option("--name", "-n", help="Miner name")
@click.option("--detailed", "-d", is_flag=True, help="Show detailed stats")
@click.pass_context
async def status(ctx, name: str, detailed: bool):
    """Show mining status."""
    try:
        from hanzo_miner import HanzoMiner
    except ImportError:
        console.print("[red]Error:[/red] hanzo-miner not installed")
        return

    if name:
        # Show specific miner
        miner = HanzoMiner.get_by_name(name)
        if not miner:
            console.print(f"[red]Miner not found: {name}[/red]")
            return

        miners = [miner]
    else:
        # Show all miners
        miners = HanzoMiner.get_all()

    if not miners:
        console.print("[yellow]No miners running[/yellow]")
        console.print("Start mining with: hanzo miner start")
        return

    # Create table
    table = Table(title="Active Miners")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Device", style="yellow")
    table.add_column("Jobs", style="blue")
    table.add_column("Tokens", style="magenta")
    table.add_column("Uptime", style="white")

    for miner in miners:
        stats = await miner.get_stats()
        table.add_row(
            miner.name,
            stats.get("status", "unknown"),
            stats.get("device", "unknown"),
            str(stats.get("jobs_completed", 0)),
            f"{stats.get('tokens_earned', 0):.2f}",
            stats.get("uptime", "0s"),
        )

    console.print(table)

    if detailed and len(miners) == 1:
        # Show detailed stats for single miner
        miner = miners[0]
        stats = await miner.get_stats()

        console.print("\n[cyan]Detailed Statistics:[/cyan]")
        console.print(f"  Network: {stats.get('network', 'unknown')}")
        console.print(f"  Wallet: {stats.get('wallet', 'Not set')}")
        console.print(f"  Models: {', '.join(stats.get('models', []))}")
        console.print(
            f"  Memory: {stats.get('memory_used', 0)} / {stats.get('memory_total', 0)} MB"
        )
        console.print(f"  CPU: {stats.get('cpu_percent', 0)}%")

        if gpu := stats.get("gpu"):
            console.print(
                f"  GPU: {gpu['name']} ({gpu['memory_used']} / {gpu['memory_total']} MB)"
            )

        console.print(f"\n[cyan]Performance:[/cyan]")
        console.print(f"  Average job time: {stats.get('avg_job_time', 'N/A')}")
        console.print(f"  Success rate: {stats.get('success_rate', 0)}%")
        console.print(f"  Tokens/hour: {stats.get('tokens_per_hour', 0):.2f}")


@miner_group.command()
@click.option("--network", default="mainnet", help="Network to check")
@click.pass_context
async def leaderboard(ctx, network: str):
    """Show mining leaderboard."""
    try:
        from hanzo_miner import get_leaderboard
    except ImportError:
        console.print("[red]Error:[/red] hanzo-miner not installed")
        return

    with console.status("Loading leaderboard..."):
        try:
            leaders = await get_leaderboard(network=network)
        except Exception as e:
            console.print(f"[red]Failed to load leaderboard: {e}[/red]")
            return

    if not leaders:
        console.print("[yellow]No data available[/yellow]")
        return

    table = Table(title=f"Mining Leaderboard - {network}")
    table.add_column("Rank", style="cyan")
    table.add_column("Miner", style="green")
    table.add_column("Jobs", style="yellow")
    table.add_column("Tokens", style="magenta")
    table.add_column("Success Rate", style="blue")

    for i, leader in enumerate(leaders[:20], 1):
        table.add_row(
            str(i),
            leader["name"],
            str(leader["jobs"]),
            f"{leader['tokens']:.2f}",
            f"{leader['success_rate']}%",
        )

    console.print(table)


@miner_group.command()
@click.option("--wallet", "-w", required=True, help="Wallet address")
@click.option("--network", default="mainnet", help="Network")
@click.pass_context
async def earnings(ctx, wallet: str, network: str):
    """Check mining earnings."""
    try:
        from hanzo_miner import check_earnings
    except ImportError:
        console.print("[red]Error:[/red] hanzo-miner not installed")
        return

    with console.status("Checking earnings..."):
        try:
            data = await check_earnings(wallet=wallet, network=network)
        except Exception as e:
            console.print(f"[red]Failed to check earnings: {e}[/red]")
            return

    console.print(f"[cyan]Earnings for {wallet[:8]}...{wallet[-4:]}[/cyan]")
    console.print(f"  Network: {network}")
    console.print(f"  Total earned: {data.get('total_earned', 0):.2f} tokens")
    console.print(f"  Available: {data.get('available', 0):.2f} tokens")
    console.print(f"  Pending: {data.get('pending', 0):.2f} tokens")

    if history := data.get("recent_jobs"):
        console.print("\n[cyan]Recent Jobs:[/cyan]")
        for job in history[:5]:
            console.print(
                f"  • {job['timestamp']}: +{job['tokens']} tokens ({job['model']})"
            )


@miner_group.command()
@click.argument("amount", type=float)
@click.option("--wallet", "-w", required=True, help="Wallet address")
@click.option("--to", required=True, help="Destination address")
@click.option("--network", default="mainnet", help="Network")
@click.pass_context
async def withdraw(ctx, amount: float, wallet: str, to: str, network: str):
    """Withdraw mining earnings."""
    try:
        from hanzo_miner import withdraw_earnings
    except ImportError:
        console.print("[red]Error:[/red] hanzo-miner not installed")
        return

    # Confirm withdrawal
    console.print(f"[yellow]Withdrawal Request:[/yellow]")
    console.print(f"  Amount: {amount} tokens")
    console.print(f"  From: {wallet[:8]}...{wallet[-4:]}")
    console.print(f"  To: {to[:8]}...{to[-4:]}")
    console.print(f"  Network: {network}")

    if not click.confirm("Proceed with withdrawal?"):
        return

    with console.status("Processing withdrawal..."):
        try:
            result = await withdraw_earnings(
                wallet=wallet, amount=amount, destination=to, network=network
            )

            console.print(f"[green]✓[/green] Withdrawal successful")
            console.print(f"  Transaction: {result['tx_hash']}")
            console.print(f"  Amount: {result['amount']} tokens")
            console.print(f"  Fee: {result['fee']} tokens")

        except Exception as e:
            console.print(f"[red]Withdrawal failed: {e}[/red]")
