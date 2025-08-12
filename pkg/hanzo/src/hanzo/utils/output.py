"""Output utilities for Hanzo CLI."""

from typing import Any, Callable
from functools import wraps

from rich.theme import Theme
from rich.console import Console

# Custom theme
hanzo_theme = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "red",
        "success": "green",
        "dim": "dim white",
        "highlight": "bold cyan",
    }
)

# Global console instance
console = Console(theme=hanzo_theme)


def handle_errors(func: Callable) -> Callable:
    """Decorator to handle errors in CLI commands."""

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted[/yellow]")
        except Exception as e:
            console.print(f"[error]Error: {e}[/error]")
            if console.is_debug:
                console.print_exception()

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted[/yellow]")
        except Exception as e:
            console.print(f"[error]Error: {e}[/error]")
            if console.is_debug:
                console.print_exception()

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


def print_json(data: Any, indent: int = 2):
    """Print JSON data with syntax highlighting."""
    console.print_json(data=data, indent=indent)


def print_table(data: list[dict], title: str = None):
    """Print data as a table."""
    if not data:
        console.print("[dim]No data[/dim]")
        return

    from rich.table import Table

    table = Table(title=title)

    # Add columns from first row
    for key in data[0].keys():
        table.add_column(key.replace("_", " ").title())

    # Add rows
    for row in data:
        table.add_row(*[str(v) for v in row.values()])

    console.print(table)


def confirm(message: str, default: bool = False) -> bool:
    """Ask for confirmation."""
    from rich.prompt import Confirm

    return Confirm.ask(message, default=default)


def prompt(message: str, default: str = None, password: bool = False) -> str:
    """Prompt for input."""
    from rich.prompt import Prompt

    return Prompt.ask(message, default=default, password=password)


def progress(description: str):
    """Context manager for progress indicator."""
    return console.status(description)


# Export common methods
print = console.print
print_exception = console.print_exception
rule = console.rule
clear = console.clear


# Import asyncio for the decorator
import asyncio
