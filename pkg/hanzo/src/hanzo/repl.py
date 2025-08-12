"""REPL and AI chat entry points for Hanzo."""

import sys

import click


def ai_chat():
    """Start AI chat interface (hanzo/ai or hanzo/chat)."""
    try:
        # Use hanzo-router instead of litellm for AI routing
        from hanzo_repl.cli import main as repl_main

        # Pass AI chat mode
        sys.argv = [sys.argv[0], "--mode", "ai"]
        repl_main()
    except ImportError:
        click.echo(
            "Error: hanzo-repl or hanzo-router is not installed. Please run: pip install hanzo[ai] or pip install hanzo[all]",
            err=True,
        )
        sys.exit(1)


def repl_main():
    """Start the Hanzo REPL interface (hanzo/repl)."""
    try:
        from hanzo_repl.cli import main as repl_cli_main

        repl_cli_main()
    except ImportError:
        click.echo(
            "Error: hanzo-repl is not installed. Please run: pip install hanzo[all]",
            err=True,
        )
        sys.exit(1)


if __name__ == "__main__":
    import os

    if os.path.basename(sys.argv[0]) in ["ai", "chat"]:
        ai_chat()
    else:
        repl_main()
