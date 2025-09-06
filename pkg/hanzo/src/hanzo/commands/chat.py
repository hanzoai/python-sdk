"""Chat command for interactive AI conversations."""

import asyncio
import os
from typing import Optional

import click
import httpx
from rich.markdown import Markdown
from rich.panel import Panel
from rich import box

from ..utils.output import console


@click.command(name="chat")
@click.option("--model", "-m", default="llama-3.2-3b", help="Model to use")
@click.option("--local/--cloud", default=True, help="Use local or cloud model")
@click.option("--once", is_flag=True, help="Single question mode")
@click.option("--system", "-s", help="System prompt")
@click.option(
    "--repl", is_flag=True, help="Start full REPL interface (like Claude Code)"
)
@click.option("--ipython", is_flag=True, help="Use IPython REPL interface")
@click.option("--tui", is_flag=True, help="Use beautiful TUI interface")
@click.argument("prompt", nargs=-1)
@click.pass_context
def chat_command(
    ctx,
    model: str,
    local: bool,
    once: bool,
    system: Optional[str],
    repl: bool,
    ipython: bool,
    tui: bool,
    prompt: tuple,
):
    """Interactive AI chat."""
    # Check if REPL mode requested
    if repl or ipython or tui:
        try:
            import os
            import sys

            # Set up environment
            if model:
                os.environ["HANZO_DEFAULT_MODEL"] = model
            if local:
                os.environ["HANZO_USE_LOCAL"] = "true"
            if system:
                os.environ["HANZO_SYSTEM_PROMPT"] = system

            if ipython:
                from hanzo_repl.ipython_repl import main

                sys.exit(main())
            elif tui:
                from hanzo_repl.textual_repl import main

                sys.exit(main())
            else:
                from hanzo_repl.cli import main

                sys.exit(main())
        except ImportError:
            console.print("[red]Error:[/red] hanzo-repl not installed")
            console.print("Install with: pip install hanzo[repl]")
            console.print("\nAlternatively:")
            console.print("  pip install hanzo-repl")
            return

    prompt_text = " ".join(prompt) if prompt else None

    if once or prompt_text:
        # Single question mode
        asyncio.run(ask_once(ctx, prompt_text or "Hello", model, local, system))
    else:
        # Interactive chat
        asyncio.run(interactive_chat(ctx, model, local, system))


async def ask_once(
    ctx, prompt: str, model: str, local: bool, system: Optional[str] = None
):
    """Ask a single question."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        if local:
            # Try router first, then fall back to local node
            base_urls = [
                "http://localhost:4000",  # Hanzo router default port
                "http://localhost:8000",  # Local node port
            ]
            
            base_url = None
            for url in base_urls:
                try:
                    async with httpx.AsyncClient() as client:
                        await client.get(f"{url}/health", timeout=1.0)
                        base_url = url
                        break
                except (httpx.ConnectError, httpx.TimeoutException):
                    continue
            
            if not base_url:
                console.print(
                    "[yellow]No local AI server running.[/yellow]\n"
                    "Start one of:\n"
                    "  • Hanzo router: hanzo router start\n"
                    "  • Local node: hanzo serve"
                )
                return

            # Make request to local node
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/v1/chat/completions",
                    json={"model": model, "messages": messages, "stream": False},
                )
                response.raise_for_status()
                result = response.json()
                content = result["choices"][0]["message"]["content"]
        else:
            # Use cloud API
            try:
                # Try different import paths
                try:
                    from hanzoai import completion
                except ImportError:
                    try:
                        from pkg.hanzoai import completion
                    except ImportError:
                        # Fallback to using litellm directly
                        import litellm
                        def completion(**kwargs):
                            import os
                            api_key = os.getenv("HANZO_API_KEY")
                            if api_key:
                                kwargs["api_key"] = api_key
                            kwargs["api_base"] = "https://api.hanzo.ai/v1"
                            return litellm.completion(**kwargs)

                result = completion(
                    model=f"anthropic/{model}" if "claude" in model else model,
                    messages=messages,
                )
                content = result.choices[0].message.content
            except ImportError as e:
                console.print(f"[red]Error:[/red] Missing dependencies: {e}")
                console.print("Install with: pip install litellm")
                return

        # Display response
        if ctx.obj.get("json"):
            console.print_json(data={"response": content})
        else:
            console.print(Markdown(content))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


async def interactive_chat(ctx, model: str, local: bool, system: Optional[str]):
    """Run interactive chat session."""
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory

    console.print(
        f"[cyan]Chat session started[/cyan] (model: {model}, mode: {'local' if local else 'cloud'})"
    )
    console.print("Type 'exit' or Ctrl+D to quit\n")

    session = PromptSession(history=FileHistory(".hanzo_chat_history"))
    messages = []

    if system:
        messages.append({"role": "system", "content": system})

    while True:
        try:
            # Get user input
            user_input = await session.prompt_async("You: ")

            if user_input.lower() in ["exit", "quit"]:
                break

            # Add to messages
            messages.append({"role": "user", "content": user_input})

            # Get response
            console.print("AI: ", end="")
            with console.status(""):
                if local:
                    # Use local node
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            "http://localhost:8000/v1/chat/completions",
                            json={
                                "model": model,
                                "messages": messages,
                                "stream": False,
                            },
                        )
                        response.raise_for_status()
                        result = response.json()
                        content = result["choices"][0]["message"]["content"]
                else:
                    # Use cloud API
                    try:
                        from hanzoai import completion
                    except ImportError:
                        try:
                            from pkg.hanzoai import completion
                        except ImportError:
                            # Fallback to using litellm directly
                            import litellm
                            def completion(**kwargs):
                                import os
                                api_key = os.getenv("HANZO_API_KEY")
                                if api_key:
                                    kwargs["api_key"] = api_key
                                kwargs["api_base"] = "https://api.hanzo.ai/v1"
                                return litellm.completion(**kwargs)

                    result = completion(
                        model=f"anthropic/{model}" if "claude" in model else model,
                        messages=messages,
                    )
                    content = result.choices[0].message.content

            # Display and save response
            console.print(Markdown(content))
            messages.append({"role": "assistant", "content": content})
            console.print()

        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]\n")
