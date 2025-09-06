"""
Streaming response handler for Hanzo Dev.
Provides real-time feedback as AI generates responses.
"""

import time
import asyncio
from typing import Callable, Optional, AsyncGenerator

from rich.live import Live
from rich.panel import Panel
from rich.console import Console
from rich.markdown import Markdown


class StreamingHandler:
    """Handles streaming responses from AI models."""

    def __init__(self, console: Console = None):
        """Initialize streaming handler."""
        self.console = console or Console()
        self.current_response = ""
        self.is_streaming = False

    async def stream_openai(self, client, messages: list, model: str = "gpt-4") -> str:
        """Stream response from OpenAI API."""
        try:
            stream = await client.chat.completions.create(
                model=model, messages=messages, stream=True, max_tokens=1000
            )

            self.current_response = ""
            self.is_streaming = True

            with Live(
                Panel(
                    "",
                    title="[bold cyan]AI Response[/bold cyan]",
                    title_align="left",
                    border_style="dim cyan",
                ),
                console=self.console,
                refresh_per_second=10,
            ) as live:
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        self.current_response += chunk.choices[0].delta.content
                        live.update(
                            Panel(
                                Markdown(self.current_response),
                                title="[bold cyan]AI Response[/bold cyan]",
                                title_align="left",
                                border_style="dim cyan",
                                padding=(1, 2),
                            )
                        )

            self.is_streaming = False
            return self.current_response

        except Exception as e:
            self.console.print(f"[red]Streaming error: {e}[/red]")
            self.is_streaming = False
            return None

    async def stream_anthropic(
        self, client, messages: list, model: str = "claude-3-5-sonnet-20241022"
    ) -> str:
        """Stream response from Anthropic API."""
        try:
            self.current_response = ""
            self.is_streaming = True

            with Live(
                Panel(
                    "",
                    title="[bold cyan]AI Response[/bold cyan]",
                    title_align="left",
                    border_style="dim cyan",
                ),
                console=self.console,
                refresh_per_second=10,
            ) as live:
                async with client.messages.stream(
                    model=model, messages=messages, max_tokens=1000
                ) as stream:
                    async for text in stream.text_stream:
                        self.current_response += text
                        live.update(
                            Panel(
                                Markdown(self.current_response),
                                title="[bold cyan]AI Response[/bold cyan]",
                                title_align="left",
                                border_style="dim cyan",
                                padding=(1, 2),
                            )
                        )

            self.is_streaming = False
            return self.current_response

        except Exception as e:
            self.console.print(f"[red]Streaming error: {e}[/red]")
            self.is_streaming = False
            return None

    async def stream_ollama(self, message: str, model: str = "llama3.2") -> str:
        """Stream response from Ollama local model."""
        import httpx

        try:
            self.current_response = ""
            self.is_streaming = True

            with Live(
                Panel(
                    "",
                    title="[bold cyan]AI Response (Local)[/bold cyan]",
                    title_align="left",
                    border_style="dim cyan",
                ),
                console=self.console,
                refresh_per_second=10,
            ) as live:
                async with httpx.AsyncClient() as client:
                    async with client.stream(
                        "POST",
                        "http://localhost:11434/api/generate",
                        json={"model": model, "prompt": message, "stream": True},
                        timeout=60.0,
                    ) as response:
                        async for line in response.aiter_lines():
                            if line:
                                import json

                                data = json.loads(line)
                                if "response" in data:
                                    self.current_response += data["response"]
                                    live.update(
                                        Panel(
                                            Markdown(self.current_response),
                                            title="[bold cyan]AI Response (Local)[/bold cyan]",
                                            title_align="left",
                                            border_style="dim cyan",
                                            padding=(1, 2),
                                        )
                                    )
                                if data.get("done", False):
                                    break

            self.is_streaming = False
            return self.current_response

        except Exception as e:
            self.console.print(f"[red]Ollama streaming error: {e}[/red]")
            self.is_streaming = False
            return None

    async def simulate_streaming(self, text: str, delay: float = 0.02) -> str:
        """Simulate streaming for non-streaming APIs."""
        self.current_response = ""
        self.is_streaming = True

        words = text.split()

        with Live(
            Panel(
                "",
                title="[bold cyan]AI Response[/bold cyan]",
                title_align="left",
                border_style="dim cyan",
            ),
            console=self.console,
            refresh_per_second=20,
        ) as live:
            for i, word in enumerate(words):
                self.current_response += word
                if i < len(words) - 1:
                    self.current_response += " "

                live.update(
                    Panel(
                        Markdown(self.current_response),
                        title="[bold cyan]AI Response[/bold cyan]",
                        title_align="left",
                        border_style="dim cyan",
                        padding=(1, 2),
                    )
                )
                await asyncio.sleep(delay)

        self.is_streaming = False
        return self.current_response

    def stop_streaming(self):
        """Stop current streaming operation."""
        self.is_streaming = False
        if self.current_response:
            self.console.print(f"\n[yellow]Streaming interrupted[/yellow]")


class TypewriterEffect:
    """Provides typewriter effect for text output."""

    def __init__(self, console: Console = None):
        self.console = console or Console()

    async def type_text(self, text: str, speed: float = 0.03):
        """Type text with typewriter effect."""
        for char in text:
            self.console.print(char, end="")
            await asyncio.sleep(speed)
        self.console.print()  # New line at end

    async def type_code(self, code: str, language: str = "python", speed: float = 0.01):
        """Type code with syntax highlighting."""
        from rich.syntax import Syntax

        # Build up code progressively
        current_code = ""
        lines = code.split("\n")

        with Live(console=self.console, refresh_per_second=30) as live:
            for line in lines:
                for char in line:
                    current_code += char
                    syntax = Syntax(
                        current_code, language, theme="monokai", line_numbers=True
                    )
                    live.update(syntax)
                    await asyncio.sleep(speed)
                current_code += "\n"
                syntax = Syntax(
                    current_code, language, theme="monokai", line_numbers=True
                )
                live.update(syntax)


async def stream_with_fallback(message: str, console: Console = None) -> Optional[str]:
    """
    Stream response with automatic fallback to available options.
    """
    import os

    handler = StreamingHandler(console)

    # Try OpenAI streaming
    if os.getenv("OPENAI_API_KEY"):
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI()
            return await handler.stream_openai(
                client, [{"role": "user", "content": message}]
            )
        except Exception as e:
            if console:
                console.print(f"[yellow]OpenAI streaming failed: {e}[/yellow]")

    # Try Anthropic streaming
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic()
            return await handler.stream_anthropic(
                client, [{"role": "user", "content": message}]
            )
        except Exception as e:
            if console:
                console.print(f"[yellow]Anthropic streaming failed: {e}[/yellow]")

    # Try Ollama streaming
    try:
        return await handler.stream_ollama(message)
    except Exception:
        pass

    # Fallback to non-streaming with simulated effect
    if console:
        console.print("[yellow]Falling back to non-streaming mode[/yellow]")

    # Get response from fallback handler
    from .fallback_handler import smart_chat

    response = await smart_chat(message, console)

    if response:
        # Simulate streaming
        return await handler.simulate_streaming(response)

    return None
