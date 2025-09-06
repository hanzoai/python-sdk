"""Router command for starting Hanzo router proxy."""

import os
import sys
import subprocess
from typing import Optional
from pathlib import Path

import click

from ..utils.output import console


@click.group(name="router")
def router_group():
    """Manage Hanzo router (LLM proxy)."""
    pass


@router_group.command(name="start")
@click.option("--port", "-p", default=4000, help="Port to run router on")
@click.option("--config", "-c", help="Config file path")
@click.option("--detach", "-d", is_flag=True, help="Run in background")
@click.pass_context
def start_router(ctx, port: int, config: Optional[str], detach: bool):
    """Start the Hanzo router proxy server."""
    # Find router directory
    router_paths = [
        Path.home() / "work" / "hanzo" / "router",
        Path.home() / "hanzo" / "router",
        Path.cwd().parent / "router",
    ]
    
    router_dir = None
    for path in router_paths:
        if path.exists() and (path / "litellm" / "proxy" / "proxy_server.py").exists():
            router_dir = path
            break
    
    if not router_dir:
        console.print("[red]Error:[/red] Hanzo router not found")
        console.print("\nPlease clone the router:")
        console.print("  git clone https://github.com/hanzoai/router.git ~/work/hanzo/router")
        return
    
    console.print(f"[green]✓[/green] Found router at {router_dir}")
    
    # Prepare environment
    env = os.environ.copy()
    env["PYTHONPATH"] = str(router_dir) + ":" + env.get("PYTHONPATH", "")
    
    # Build command
    cmd = [
        sys.executable,
        "-m", "litellm.proxy.proxy_server",
        "--port", str(port),
    ]
    
    if config:
        # Use provided config
        config_path = Path(config)
        if not config_path.exists():
            console.print(f"[red]Error:[/red] Config file not found: {config}")
            return
        cmd.extend(["--config", str(config_path)])
    else:
        # Check for default config
        default_config = router_dir / "config.yaml"
        if default_config.exists():
            cmd.extend(["--config", str(default_config)])
            console.print(f"[dim]Using config: {default_config}[/dim]")
    
    console.print(f"\n[bold cyan]Starting Hanzo Router on port {port}[/bold cyan]")
    console.print(f"API endpoint: http://localhost:{port}/v1")
    console.print("\nPress Ctrl+C to stop\n")
    
    try:
        # Change to router directory and run
        os.chdir(router_dir)
        
        if detach:
            # Run in background
            process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            console.print(f"[green]✓[/green] Router started in background (PID: {process.pid})")
            console.print(f"Check status: curl http://localhost:{port}/health")
        else:
            # Run in foreground
            subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        console.print("\n[yellow]Router stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]Error starting router: {e}[/red]")


@router_group.command(name="stop")
@click.option("--port", "-p", default=4000, help="Port router is running on")
def stop_router(port: int):
    """Stop the router."""
    import signal

    import psutil
    
    found = False
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and 'proxy_server' in ' '.join(cmdline) and str(port) in ' '.join(cmdline):
                console.print(f"[yellow]Stopping router (PID: {proc.info['pid']})[/yellow]")
                proc.send_signal(signal.SIGTERM)
                proc.wait(timeout=5)
                found = True
                console.print("[green]✓[/green] Router stopped")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            continue
    
    if not found:
        console.print(f"[yellow]No router found on port {port}[/yellow]")


@router_group.command(name="status")
@click.option("--port", "-p", default=4000, help="Port to check")
def router_status(port: int):
    """Check router status."""
    import httpx
    
    try:
        response = httpx.get(f"http://localhost:{port}/health", timeout=2.0)
        if response.status_code == 200:
            console.print(f"[green]✓[/green] Router is running on port {port}")
            
            # Try to get models
            try:
                models_response = httpx.get(f"http://localhost:{port}/models", timeout=2.0)
                if models_response.status_code == 200:
                    data = models_response.json()
                    if "data" in data:
                        console.print(f"Available models: {len(data['data'])}")
            except Exception:
                pass
        else:
            console.print(f"[yellow]Router responding but unhealthy (status: {response.status_code})[/yellow]")
    except httpx.ConnectError:
        console.print(f"[red]Router not running on port {port}[/red]")
        console.print("\nStart with: hanzo router start")
    except Exception as e:
        console.print(f"[red]Error checking router: {e}[/red]")