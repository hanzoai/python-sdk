"""
Intelligent fallback handler for Hanzo Dev.
Automatically tries available AI options when primary fails.
"""

import os
import shutil
import subprocess
from typing import Any, Dict, Optional
from pathlib import Path


class FallbackHandler:
    """Handles automatic fallback to available AI options."""

    def __init__(self):
        self.available_options = self._detect_available_options()
        self.fallback_order = self._determine_fallback_order()

    def _detect_available_options(self) -> Dict[str, bool]:
        """Detect which AI options are available."""
        options = {
            "openai_api": bool(os.getenv("OPENAI_API_KEY")),
            "anthropic_api": bool(os.getenv("ANTHROPIC_API_KEY")),
            "google_api": bool(
                os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            ),
            "openai_cli": shutil.which("openai") is not None,
            "claude_cli": shutil.which("claude") is not None,
            "gemini_cli": shutil.which("gemini") is not None,
            "ollama": self._check_ollama(),
            "hanzo_ide": Path.home().joinpath("work/hanzo/ide").exists(),
            "free_apis": True,  # Always available (Codestral, StarCoder)
        }
        return options

    def _check_ollama(self) -> bool:
        """Check if Ollama is running and has models."""
        try:
            import httpx

            with httpx.Client(timeout=2.0) as client:
                response = client.get("http://localhost:11434/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return len(data.get("models", [])) > 0
        except Exception:
            pass
        return False

    def _determine_fallback_order(self) -> list:
        """Determine the order of fallback options based on availability."""
        order = []

        # Priority 1: API keys (fastest, most reliable)
        if self.available_options["openai_api"]:
            order.append(("openai_api", "gpt-4"))
        if self.available_options["anthropic_api"]:
            order.append(("anthropic_api", "claude-3-5-sonnet"))
        if self.available_options["google_api"]:
            order.append(("google_api", "gemini-pro"))

        # Priority 2: CLI tools (no API key needed)
        if self.available_options["openai_cli"]:
            order.append(("openai_cli", "codex"))
        if self.available_options["claude_cli"]:
            order.append(("claude_cli", "claude-desktop"))
        if self.available_options["gemini_cli"]:
            order.append(("gemini_cli", "gemini"))

        # Priority 3: Local models (free, but requires setup)
        if self.available_options["ollama"]:
            order.append(("ollama", "local:llama3.2"))
        if self.available_options["hanzo_ide"]:
            order.append(("hanzo_ide", "hanzo-ide"))

        # Priority 4: Free cloud APIs (rate limited)
        if self.available_options["free_apis"]:
            order.append(("free_api", "codestral-free"))
            order.append(("free_api", "starcoder2"))

        return order

    def get_best_option(self) -> Optional[tuple]:
        """Get the best available AI option."""
        if self.fallback_order:
            return self.fallback_order[0]
        return None

    def get_next_option(self, failed_option: str) -> Optional[tuple]:
        """Get the next fallback option after one fails."""
        for i, (option_type, model) in enumerate(self.fallback_order):
            if model == failed_option and i + 1 < len(self.fallback_order):
                return self.fallback_order[i + 1]
        return None

    def suggest_setup(self) -> str:
        """Suggest setup instructions for unavailable options."""
        suggestions = []

        if not self.available_options["openai_api"]:
            suggestions.append("• Set OPENAI_API_KEY for GPT-4/GPT-5 access")

        if not self.available_options["anthropic_api"]:
            suggestions.append("• Set ANTHROPIC_API_KEY for Claude access")

        if not self.available_options["ollama"]:
            suggestions.append(
                "• Install Ollama: curl -fsSL https://ollama.com/install.sh | sh"
            )
            suggestions.append("  Then run: ollama pull llama3.2")

        if not self.available_options["openai_cli"]:
            suggestions.append("• Install OpenAI CLI: pip install openai-cli")

        if not self.available_options["claude_cli"]:
            suggestions.append(
                "• Install Claude Desktop from https://claude.ai/download"
            )

        return (
            "\n".join(suggestions) if suggestions else "All AI options are available!"
        )

    def print_status(self, console):
        """Print the current status of available AI options."""
        from rich.table import Table

        table = Table(
            title="Available AI Options", show_header=True, header_style="bold magenta"
        )
        table.add_column("Option", style="cyan", width=20)
        table.add_column("Status", width=10)
        table.add_column("Model", width=20)

        status_map = {
            "openai_api": ("OpenAI API", "gpt-4"),
            "anthropic_api": ("Anthropic API", "claude-3-5"),
            "google_api": ("Google API", "gemini-pro"),
            "openai_cli": ("OpenAI CLI", "codex"),
            "claude_cli": ("Claude Desktop", "claude"),
            "gemini_cli": ("Gemini CLI", "gemini"),
            "ollama": ("Ollama Local", "llama3.2"),
            "hanzo_ide": ("Hanzo IDE", "hanzo-dev"),
            "free_apis": ("Free APIs", "codestral/starcoder"),
        }

        for key, available in self.available_options.items():
            if key in status_map:
                name, model = status_map[key]
                status = "✅" if available else "❌"
                table.add_row(name, status, model if available else "Not available")

        console.print(table)

        if self.fallback_order:
            console.print(
                f"\n[green]Primary option: {self.fallback_order[0][1]}[/green]"
            )
            if len(self.fallback_order) > 1:
                fallbacks = ", ".join([opt[1] for opt in self.fallback_order[1:]])
                console.print(f"[yellow]Fallback options: {fallbacks}[/yellow]")
        else:
            console.print("\n[red]No AI options available![/red]")
            console.print("\n[yellow]Setup suggestions:[/yellow]")
            console.print(self.suggest_setup())


async def smart_chat(message: str, console=None) -> Optional[str]:
    """
    Smart chat that automatically tries available AI options.
    Returns the AI response or None if all options fail.
    """
    from .rate_limiter import smart_limiter

    handler = FallbackHandler()

    if console:
        console.print("\n[dim]Detecting available AI options...[/dim]")

    best_option = handler.get_best_option()
    if not best_option:
        if console:
            handler.print_status(console)
        return None

    option_type, model = best_option

    # Try the primary option with rate limiting
    try:
        if option_type == "openai_api":

            async def call_openai():
                from openai import AsyncOpenAI

                client = AsyncOpenAI()
                response = await client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": message}],
                    max_tokens=500,
                )
                return response.choices[0].message.content

            return await smart_limiter.execute_with_limit("openai", call_openai)

        elif option_type == "anthropic_api":
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic()
            response = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                messages=[{"role": "user", "content": message}],
                max_tokens=500,
            )
            return response.content[0].text

        elif option_type == "openai_cli":
            # Use OpenAI CLI
            result = subprocess.run(
                [
                    "openai",
                    "api",
                    "chat.completions.create",
                    "-m",
                    "gpt-4",
                    "-g",
                    message,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return result.stdout.strip()

        elif option_type == "ollama":
            # Use Ollama
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={"model": "llama3.2", "prompt": message, "stream": False},
                    timeout=30.0,
                )
                if response.status_code == 200:
                    return response.json().get("response", "")

        elif option_type == "free_api":
            # Try free Codestral API
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://codestral.mistral.ai/v1/fim/completions",
                    headers={"Content-Type": "application/json"},
                    json={"prompt": message, "suffix": "", "max_tokens": 500},
                    timeout=30.0,
                )
                if response.status_code == 200:
                    return response.json().get("choices", [{}])[0].get("text", "")

    except Exception as e:
        if console:
            console.print(f"[yellow]Primary option {model} failed: {e}[/yellow]")
            console.print("[dim]Trying fallback...[/dim]")

        # Try next fallback
        next_option = handler.get_next_option(model)
        if next_option:
            # Recursively try the next option
            handler.fallback_order.remove(best_option)
            return await smart_chat(message, console)

    return None
