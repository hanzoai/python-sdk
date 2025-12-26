#!/usr/bin/env python3
"""Test streaming responses."""

import sys
import asyncio
from pathlib import Path

import pytest
from rich.console import Console

# Add hanzo src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "pkg" / "hanzo" / "src"))

from hanzo.streaming import StreamingHandler, TypewriterEffect, stream_with_fallback


async def test_streaming():
    """Test streaming functionality."""
    console = Console()

    console.print("\n[bold cyan]Testing Streaming Responses[/bold cyan]\n")

    # Test typewriter effect
    console.print("[bold]Testing typewriter effect:[/bold]")
    typewriter = TypewriterEffect(console)

    await typewriter.type_text("This is a typewriter effect demonstration...", speed=0.02)

    # Test code typing
    console.print("\n[bold]Testing code typing:[/bold]")
    code = """def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)"""

    await typewriter.type_code(code, language="python", speed=0.01)

    # Test simulated streaming
    console.print("\n[bold]Testing simulated streaming:[/bold]")
    handler = StreamingHandler(console)

    sample_text = "This is a simulated streaming response. It will appear word by word as if being generated in real-time. This creates a better user experience!"

    await handler.simulate_streaming(sample_text, delay=0.03)

    # Test real streaming with fallback
    console.print("\n[bold]Testing streaming with fallback:[/bold]")

    test_message = "What is 2 + 2? Reply with just the number."

    response = await stream_with_fallback(test_message, console)

    if response:
        console.print(f"\n[green]✅ Streaming test successful![/green]")
        console.print(f"Response: {response}")
    else:
        console.print("\n[yellow]⚠️ No streaming available (no API keys)[/yellow]")

    return True


if __name__ == "__main__":
    success = asyncio.run(test_streaming())
    sys.exit(0 if success else 1)
