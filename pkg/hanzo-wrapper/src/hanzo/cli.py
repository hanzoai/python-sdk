"""Main CLI entry point for Hanzo AI."""

import sys
import click
from importlib import import_module


def main():
    """Main entry point for hanzo command - delegates to hanzo-cli."""
    try:
        # Import and run hanzo_cli
        from hanzo_cli.cli import main as cli_main
        cli_main()
    except ImportError:
        click.echo("Error: hanzo-cli is not installed. Please run: pip install hanzo[all]", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()