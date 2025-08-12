"""MCP server entry point for hanzo/mcp command."""

import sys

import click


def main():
    """Start the Hanzo MCP server."""
    try:
        from hanzo_mcp.server import main as mcp_main

        mcp_main()
    except ImportError:
        click.echo(
            "Error: hanzo-mcp is not installed. Please run: pip install hanzo[mcp] or pip install hanzo[all]",
            err=True,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
