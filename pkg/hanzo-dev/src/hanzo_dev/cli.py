"""CLI entry point for Hanzo REPL."""

import asyncio

import click

from .ipython_repl import main as ipython_main
from .repl import HanzoREPL


@click.command()
@click.option(
    "--mode",
    default="ipython",
    type=click.Choice(["basic", "ipython", "tui"]),
    help="REPL mode to use",
)
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--model", help="LLM model to use")
@click.option(
    "--config",
    "config_home",
    default=None,
    help="Path to config home (default: ~/.hanzo)",
)
def main(mode, debug, model, config_home):
    """Hanzo REPL - Interactive testing environment."""
    import os

    if config_home:
        os.environ["HANZO_CONFIG_HOME"] = config_home

    if mode == "tui":
        from .textual_repl import main as tui_main
        tui_main()
    elif mode == "ipython":
        # Use IPython-based REPL (recommended)
        ipython_main()
    else:
        # Use basic REPL
        config = {"debug": debug, "model": model}
        repl = HanzoREPL(config)
        asyncio.run(repl.run())


if __name__ == "__main__":
    main()
