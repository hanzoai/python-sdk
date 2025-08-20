#!/usr/bin/env python3
"""Test the fallback handler."""

import asyncio
import sys
from pathlib import Path
from rich.console import Console

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "pkg" / "hanzo" / "src"))

from hanzo.fallback_handler import FallbackHandler, smart_chat

async def test_fallback():
    """Test the fallback handler."""
    console = Console()
    
    console.print("\n[bold cyan]Testing Fallback Handler[/bold cyan]\n")
    
    # Create handler and check status
    handler = FallbackHandler()
    handler.print_status(console)
    
    # Test smart chat
    console.print("\n[bold]Testing smart chat with automatic fallback:[/bold]")
    
    test_message = "What is 2 + 2? Reply with just the number."
    console.print(f"\nMessage: [cyan]{test_message}[/cyan]")
    
    response = await smart_chat(test_message, console)
    
    if response:
        console.print(f"\n[green]Success! AI responded:[/green]")
        console.print(f"[bold]{response}[/bold]")
    else:
        console.print("\n[red]Failed to get response from any AI option[/red]")
        console.print("\n[yellow]Setup suggestions:[/yellow]")
        console.print(handler.suggest_setup())
    
    return response is not None

if __name__ == "__main__":
    success = asyncio.run(test_fallback())
    sys.exit(0 if success else 1)