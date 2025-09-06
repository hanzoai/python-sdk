"""MCP server entry point for hanzo/mcp command."""

import sys

import click


def main():
    """Start the Hanzo MCP server.

    This wrapper defers to hanzo_mcp.cli:main so that the CLI can parse
    transport flags and configure logging BEFORE importing any heavy modules,
    preventing stdio protocol corruption.
    """
    try:
        from hanzo_mcp.cli import main as cli_main

        cli_main()
    except ImportError:
        click.echo(
            "Error: hanzo-mcp is not installed. Please run: pip install hanzo[mcp] or pip install hanzo[all]",
            err=True,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
