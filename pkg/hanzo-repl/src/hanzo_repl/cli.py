"""CLI entry point for Hanzo REPL."""

import click
import asyncio
from .repl import HanzoREPL
from .ipython_repl import main as ipython_main


@click.command()
@click.option('--mode', default='ipython', type=click.Choice(['basic', 'ipython']), 
              help='REPL mode to use')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--model', help='LLM model to use')
def main(mode, debug, model):
    """Hanzo REPL - Interactive testing environment."""
    
    if mode == 'ipython':
        # Use IPython-based REPL (recommended)
        ipython_main()
    else:
        # Use basic REPL
        config = {
            'debug': debug,
            'model': model
        }
        repl = HanzoREPL(config)
        asyncio.run(repl.run())


if __name__ == "__main__":
    main()