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
async def dispatch(ctx, prompt: str, agents: int, model: str, mode: str, consensus: bool, timeout: int):
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


@network_group.command()
@click.option("--json", is_flag=True, help="Output as JSON")
@click.pass_context
def topology(ctx, json: bool):
    """Show local device topology and GPU information."""
    try:
        from hanzo_network.topology.topology import Topology
        from hanzo_network.topology.device_capabilities import device_capabilities
    except ImportError:
        console.print("[red]Error:[/red] hanzo-network not installed")
        console.print("Install with: pip install hanzo[network]")
        return

    # Get device capabilities
    caps = device_capabilities()

    if json:
        import json as json_lib

        console.print(json_lib.dumps(caps.to_dict(), indent=2))
        return

    # Display in nice table format
    console.print("\n[cyan]Device Topology[/cyan]")
    console.print("=" * 60)

    table = Table(title="Local Device Information")
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    table.add_row("Model", caps.model)
    table.add_row("Chip/GPU", caps.chip)
    table.add_row("Memory", f"{caps.memory:,} MB")
    table.add_row("FP32 Performance", f"{caps.flops.fp32:.2f} TFLOPS")
    table.add_row("FP16 Performance", f"{caps.flops.fp16:.2f} TFLOPS")
    table.add_row("INT8 Performance", f"{caps.flops.int8:.2f} TFLOPS")

    console.print(table)
    console.print()

    # Show GPU availability
    gpu_available = caps.flops.fp32 > 0 and (
        "GPU" in caps.chip.upper()
        or "NVIDIA" in caps.chip.upper()
        or "AMD" in caps.chip.upper()
        or "APPLE M" in caps.chip.upper()  # Apple Silicon has integrated GPU
    )

    if gpu_available:
        console.print("[green]✓[/green] GPU/Accelerator detected and available for AI workloads")
        if "APPLE M" in caps.chip.upper():
            console.print("  [dim]Apple Silicon Neural Engine available for on-device AI[/dim]")
    else:
        console.print("[yellow]⚠[/yellow] No GPU detected - using CPU only")
        console.print("  To enable GPU support:")
        console.print("  - NVIDIA: Install CUDA and nvidia-smi")
        console.print("  - AMD: Install ROCm and rocm-smi")
    console.print()

    # Show QR code for easy device connection
    console.print("[bold cyan]Connect Other Devices:[/bold cyan]")
    try:
        import json as json_lib
        import socket

        import qrcode

        # Get local IP - try multiple methods
        local_ip = "localhost"
        try:
            # Method 1: Connect to external address to find local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            try:
                # Method 2: Use hostname
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
            except Exception:
                # Method 3: Default to localhost
                local_ip = "127.0.0.1"

        # Generate connection data
        connection_data = json_lib.dumps(
            {
                "node_id": f"{caps.model.lower().replace(' ', '-')}",
                "model": caps.model,
                "chip": caps.chip,
                "memory": caps.memory,
                "flops": {
                    "fp32": caps.flops.fp32,
                    "fp16": caps.flops.fp16,
                    "int8": caps.flops.int8,
                },
                "host": local_ip,
                "port": 8080,  # Default port for device connection
            }
        )

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=1,
        )
        qr.add_data(connection_data)
        qr.make(fit=True)

        console.print(f"[dim]Scan this QR code from another device to connect:[/dim]")
        qr.print_ascii(invert=True)
        console.print(f"\n[dim]Or run on other device:[/dim]")
        console.print(f"  [cyan]hanzo network join '{connection_data}'[/cyan]")
        console.print(f"\n[dim]Device IP:[/dim] {local_ip}")
    except Exception as e:
        console.print(f"[dim]QR code generation failed: {e}[/dim]")

    console.print()


@network_group.command(name="topology-add")
@click.argument("node_id")
@click.option("--model", "-m", required=True, help="Device model name")
@click.option("--chip", "-c", required=True, help="Chip/GPU name")
@click.option("--memory", type=int, required=True, help="Memory in MB")
@click.option("--fp32", type=float, default=0, help="FP32 TFLOPS")
@click.option("--fp16", type=float, default=0, help="FP16 TFLOPS")
@click.option("--int8", type=float, default=0, help="INT8 TFLOPS")
@click.option("--host", help="Host/IP address for remote access")
@click.option("--port", type=int, help="Port for remote access")
@click.option("--qr", is_flag=True, help="Generate QR code for easy device joining")
@click.pass_context
def topology_add(
    ctx,
    node_id: str,
    model: str,
    chip: str,
    memory: int,
    fp32: float,
    fp16: float,
    int8: float,
    host: str,
    port: int,
    qr: bool,
):
    """Add a GPU/device node to the network topology."""
    try:
        import os
        import json as json_lib

        from hanzo_network.topology.topology import Topology
        from hanzo_network.topology.device_capabilities import (
            DeviceFlops,
            DeviceCapabilities,
        )
    except ImportError:
        console.print("[red]Error:[/red] hanzo-network not installed")
        console.print("Install with: pip install hanzo[network]")
        return

    # Create device capabilities
    caps = DeviceCapabilities(
        model=model,
        chip=chip,
        memory=memory,
        flops=DeviceFlops(fp32=fp32, fp16=fp16, int8=int8),
    )

    # Load or create topology
    topology_file = os.path.expanduser("~/.hanzo/topology.json")
    os.makedirs(os.path.dirname(topology_file), exist_ok=True)

    topo = Topology()
    if os.path.exists(topology_file):
        with open(topology_file, "r") as f:
            data = json_lib.load(f)
            # Reconstruct topology from JSON
            for nid, ncaps in data.get("nodes", {}).items():
                topo.update_node(nid, DeviceCapabilities.model_validate(ncaps))

    # Add new node
    topo.update_node(node_id, caps)

    # Save topology
    with open(topology_file, "w") as f:
        json_lib.dump(topo.to_json(), f, indent=2)

    console.print(f"[green]✓[/green] Added node '{node_id}' to topology")
    console.print(f"  Model: {model}")
    console.print(f"  Chip: {chip}")
    console.print(f"  Memory: {memory:,} MB")
    console.print(f"  Performance: {fp32:.2f} TFLOPS (FP32)")
    console.print(f"\nTopology saved to: {topology_file}")

    # Generate QR code if requested
    if qr or (host and port):
        try:
            import qrcode
        except ImportError:
            console.print("\n[yellow]QR code generation requires qrcode library[/yellow]")
            console.print("Install with: pip install qrcode[pil]")
            return

        # Create connection info
        connection_info = {
            "node_id": node_id,
            "model": model,
            "chip": chip,
            "memory": memory,
            "flops": {"fp32": fp32, "fp16": fp16, "int8": int8},
        }

        if host:
            connection_info["host"] = host
        if port:
            connection_info["port"] = port

        # Generate QR code data
        qr_data = json_lib.dumps(connection_info)

        # Create QR code
        qr_obj = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr_obj.add_data(qr_data)
        qr_obj.make(fit=True)

        # Print QR code to terminal
        console.print("\n[cyan]QR Code for Device Join:[/cyan]")
        qr_obj.print_ascii(invert=True)

        # Also print connection command
        console.print("\n[cyan]Connection Info:[/cyan]")
        if host and port:
            console.print(f"  Host: {host}:{port}")
        console.print(f"\nScan QR code or run:")
        console.print(f"  hanzo network join '{qr_data}'")
        console.print()


@network_group.command(name="join")
@click.argument("connection_data")
@click.pass_context
def join_network(ctx, connection_data: str):
    """Join a GPU node to the network using QR code data or connection info."""
    try:
        import os
        import json as json_lib

        from hanzo_network.topology.topology import Topology
        from hanzo_network.topology.device_capabilities import (
            DeviceFlops,
            DeviceCapabilities,
        )
    except ImportError:
        console.print("[red]Error:[/red] hanzo-network not installed")
        console.print("Install with: pip install hanzo[network]")
        return

    try:
        # Parse connection data
        conn_info = json_lib.loads(connection_data)
    except json_lib.JSONDecodeError:
        console.print("[red]Error:[/red] Invalid connection data")
        console.print("Expected JSON format from QR code")
        return

    # Extract node information
    node_id = conn_info.get("node_id")
    model = conn_info.get("model")
    chip = conn_info.get("chip")
    memory = conn_info.get("memory")
    flops_data = conn_info.get("flops", {})
    host = conn_info.get("host")
    port = conn_info.get("port")

    if not all([node_id, model, chip, memory]):
        console.print("[red]Error:[/red] Missing required node information")
        return

    # Create device capabilities
    caps = DeviceCapabilities(
        model=model,
        chip=chip,
        memory=memory,
        flops=DeviceFlops(
            fp32=flops_data.get("fp32", 0),
            fp16=flops_data.get("fp16", 0),
            int8=flops_data.get("int8", 0),
        ),
    )

    # Load or create topology
    topology_file = os.path.expanduser("~/.hanzo/topology.json")
    os.makedirs(os.path.dirname(topology_file), exist_ok=True)

    topo = Topology()
    if os.path.exists(topology_file):
        with open(topology_file, "r") as f:
            data = json_lib.load(f)
            for nid, ncaps in data.get("nodes", {}).items():
                topo.update_node(nid, DeviceCapabilities.model_validate(ncaps))

    # Add new node
    topo.update_node(node_id, caps)

    # Save topology
    with open(topology_file, "w") as f:
        json_lib.dump(topo.to_json(), f, indent=2)

    console.print(f"[green]✓[/green] Joined node '{node_id}' to network")
    console.print(f"  Model: {model}")
    console.print(f"  Chip: {chip}")
    if host and port:
        console.print(f"  Location: {host}:{port}")
    console.print(f"  Performance: {flops_data.get('fp32', 0):.2f} TFLOPS (FP32)")
    console.print(f"\nTopology updated: {topology_file}")


@network_group.command(name="models")
@click.option("--endpoint", help="Gateway endpoint (default: gateway.hanzo.ai)")
@click.pass_context
def models(ctx, endpoint: str):
    """List models available on gateway.hanzo.ai."""
    import httpx

    if not endpoint:
        from hanzo.orchestrator_config import get_default_router_endpoint

        endpoint = get_default_router_endpoint()

    console.print(f"\n[cyan]Models Available on {endpoint}[/cyan]")
    console.print("=" * 60)

    try:
        # Try to fetch models from gateway
        response = httpx.get(f"{endpoint}/v1/models", timeout=5.0)

        if response.status_code == 200:
            data = response.json()
            all_models = data.get("data", [])

            # Filter out embedding models - only show LLMs
            embedding_keywords = ["embedding", "voyage", "embed", "text-embedding"]
            models_list = [
                model
                for model in all_models
                if not any(keyword in model.get("id", "").lower() for keyword in embedding_keywords)
            ]

            if models_list:
                # Create table
                table = Table(title=f"Gateway LLMs (Chat Models)")
                table.add_column("#", style="dim")
                table.add_column("Model ID", style="cyan")
                table.add_column("Tier", style="yellow")
                table.add_column("Provider", style="green")

                for i, model in enumerate(models_list, 1):
                    model_id = model.get("id", "unknown")

                    # All gateway models are FREE! 🎉
                    tier = "Free"

                    # Determine provider
                    if "gpt" in model_id or "openai" in model_id:
                        provider = "OpenAI"
                    elif "claude" in model_id or "anthropic" in model_id:
                        provider = "Anthropic"
                    elif "gemini" in model_id or "google" in model_id:
                        provider = "Google"
                    elif "llama" in model_id:
                        provider = "Meta"
                    elif "mistral" in model_id or "mixtral" in model_id:
                        provider = "Mistral"
                    elif "qwen" in model_id or "alibaba" in model_id:
                        provider = "Alibaba"
                    elif "deepseek" in model_id:
                        provider = "DeepSeek"
                    else:
                        provider = model.get("owned_by", "Various")

                    table.add_row(str(i), model_id, tier, provider)

                console.print(table)
                console.print(f"\n[dim]Total LLMs: {len(models_list)} (embedding models filtered out)[/dim]")
            else:
                console.print("[yellow]No models available on gateway[/yellow]")
        else:
            # Show static list of known models
            console.print("[yellow]Could not fetch live models, showing known models:[/yellow]\n")
            _show_static_models()
    except Exception as e:
        console.print(f"[yellow]Error fetching models: {e}[/yellow]\n")
        _show_static_models()

    console.print("\n[dim]To use a model:[/dim]")
    console.print("  [cyan]hanzo dev --model llama3-8b-instruct[/cyan]")
    console.print("\n[dim cyan]Free tier:[/dim cyan] [green]Most models available without login![/green]")
    console.print(
        "[dim cyan]Premium models:[/dim cyan] [yellow]gpt-4, claude-3-opus, o1-preview[/yellow] - [cyan]hanzo auth login[/cyan]"
    )
    console.print()


def _show_static_models():
    """Show static list of known gateway models."""
    table = Table(title="Known Gateway Models")
    table.add_column("#", style="dim")
    table.add_column("Model ID", style="cyan")
    table.add_column("Tier", style="yellow")
    table.add_column("Provider", style="green")

    models = [
        # Free tier
        ("gpt-4o-mini", "Free", "OpenAI"),
        ("gpt-3.5-turbo", "Free", "OpenAI"),
        ("llama-3.1-8b", "Free", "Meta"),
        ("llama-3.2-3b", "Free", "Meta"),
        # Premium (requires login)
        ("gpt-4o", "Premium", "OpenAI"),
        ("gpt-4-turbo", "Premium", "OpenAI"),
        ("claude-3-5-sonnet", "Premium", "Anthropic"),
        ("claude-3-opus", "Premium", "Anthropic"),
        ("claude-3-sonnet", "Premium", "Anthropic"),
        ("claude-3-haiku", "Premium", "Anthropic"),
        ("gemini-pro", "Premium", "Google"),
        ("llama-3.1-70b", "Premium", "Meta"),
        ("mixtral-8x7b", "Premium", "Mistral"),
        ("qwen-2.5-72b", "Premium", "Alibaba"),
    ]

    for i, (model_id, tier, provider) in enumerate(models, 1):
        table.add_row(str(i), model_id, tier, provider)

    console.print(table)


@network_group.command(name="topology-list")
@click.option("--json", is_flag=True, help="Output as JSON")
@click.pass_context
def topology_list(ctx, json: bool):
    """List all nodes in the network topology."""
    try:
        import os
        import json as json_lib

        from hanzo_network.topology.topology import Topology
        from hanzo_network.topology.device_capabilities import DeviceCapabilities
    except ImportError:
        console.print("[red]Error:[/red] hanzo-network not installed")
        console.print("Install with: pip install hanzo[network]")
        return

    topology_file = os.path.expanduser("~/.hanzo/topology.json")

    if not os.path.exists(topology_file):
        console.print("[yellow]No topology file found[/yellow]")
        console.print(f"Create one by adding nodes with: hanzo network topology-add")
        return

    # Load topology
    with open(topology_file, "r") as f:
        data = json_lib.load(f)

    if json:
        console.print(json_lib.dumps(data, indent=2))
        return

    nodes = data.get("nodes", {})
    if not nodes:
        console.print("[yellow]No nodes in topology[/yellow]")
        return

    # Display nodes table
    table = Table(title="Network Topology Nodes")
    table.add_column("Node ID", style="cyan", no_wrap=True)
    table.add_column("Model", style="green")
    table.add_column("Chip/GPU", style="yellow")
    table.add_column("Memory", style="blue")
    table.add_column("FP32", style="magenta")

    for node_id, caps in nodes.items():
        table.add_row(
            node_id,
            caps.get("model", "Unknown"),
            caps.get("chip", "Unknown"),
            f"{caps.get('memory', 0):,} MB",
            f"{caps.get('flops', {}).get('fp32', 0):.2f} TF",
        )

    console.print("\n")
    console.print(table)
    console.print(f"\nTopology file: {topology_file}")
    console.print()
