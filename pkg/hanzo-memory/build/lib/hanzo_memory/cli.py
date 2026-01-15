"""CLI entry point for Hanzo Memory Service."""

import click
from rich.console import Console

from .config import settings
from .server import run as run_server

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="hanzo-memory")
def cli() -> None:
    """Hanzo Memory Service - AI memory and knowledge management."""
    pass


@cli.command()
@click.option("--host", default="0.0.0.0", help="Server host")
@click.option("--port", default=4000, type=int, help="Server port")
def server(host: str, port: int) -> None:
    """Run the FastAPI server."""
    console.print(f"[green]Starting Hanzo Memory Service on {host}:{port}[/green]")
    settings.host = host
    settings.port = port
    run_server()


@cli.command()
def info() -> None:
    """Show service information."""
    console.print("[bold]Hanzo Memory Service[/bold]")
    console.print("Version: 0.1.0")
    console.print(f"Database: {settings.infinity_db_path}")
    console.print(f"Embedding Model: {settings.embedding_model}")
    console.print(f"LLM Model: {settings.llm_model}")
    console.print(f"Auth Disabled: {settings.disable_auth}")


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
