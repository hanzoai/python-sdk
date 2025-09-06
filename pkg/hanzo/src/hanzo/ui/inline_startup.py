"""
Inline startup notifications for Hanzo commands.
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()


class InlineStartup:
    """Lightweight inline startup notifications."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".hanzo"
        self.last_shown_file = self.config_dir / ".last_inline_shown"
        self.show_interval = timedelta(hours=24)  # Show once per day
        
    def should_show(self) -> bool:
        """Check if we should show inline startup."""
        # Check environment variable
        if os.environ.get("HANZO_NO_STARTUP") == "1":
            return False
            
        # Check last shown time
        if self.last_shown_file.exists():
            try:
                last_shown = datetime.fromisoformat(
                    self.last_shown_file.read_text().strip()
                )
                if datetime.now() - last_shown < self.show_interval:
                    return False
            except:
                pass
                
        return True
    
    def mark_shown(self):
        """Mark inline startup as shown."""
        self.config_dir.mkdir(exist_ok=True)
        self.last_shown_file.write_text(datetime.now().isoformat())
    
    def show_mini(self, command: str = None):
        """Show mini inline startup."""
        if not self.should_show():
            return
            
        # Build message
        message = Text()
        message.append("✨ ", style="yellow")
        message.append("Hanzo AI ", style="bold cyan")
        message.append("v0.3.23", style="green")
        
        # Add what's new teaser
        message.append(" • ", style="dim")
        message.append("What's new: ", style="dim")
        message.append("Router management, improved docs", style="yellow dim")
        
        # Show panel
        console.print(
            Panel(
                message,
                box=box.MINIMAL,
                border_style="cyan",
                padding=(0, 1)
            )
        )
        
        self.mark_shown()
    
    def show_command_hint(self, command: str):
        """Show command-specific hints."""
        hints = {
            "chat": "💡 Tip: Use --model to change AI model, --router for local proxy",
            "node": "💡 Tip: Run 'hanzo node start' to enable local AI inference",
            "router": "💡 Tip: Router provides unified access to 100+ LLM providers",
            "repl": "💡 Tip: REPL combines Python with AI assistance",
            "agent": "💡 Tip: Agents can work in parallel with 'hanzo agent swarm'"
        }
        
        hint = hints.get(command)
        if hint and os.environ.get("HANZO_SHOW_HINTS") != "0":
            console.print(f"[dim]{hint}[/dim]")
    
    def show_status_bar(self):
        """Show a compact status bar."""
        items = []
        
        # Check router
        try:
            import httpx
            response = httpx.get("http://localhost:4000/health", timeout=0.5)
            if response.status_code == 200:
                items.append("[green]Router ✓[/green]")
        except:
            pass
            
        # Check node
        try:
            import httpx
            response = httpx.get("http://localhost:8000/health", timeout=0.5)
            if response.status_code == 200:
                items.append("[green]Node ✓[/green]")
        except:
            pass
            
        # Check API key
        if os.environ.get("HANZO_API_KEY"):
            items.append("[green]API ✓[/green]")
        else:
            items.append("[yellow]API ⚠[/yellow]")
            
        if items:
            status = " • ".join(items)
            console.print(f"[dim]Status: {status}[/dim]")


def show_inline_startup(command: str = None):
    """Show inline startup notification."""
    startup = InlineStartup()
    startup.show_mini(command)
    if command:
        startup.show_command_hint(command)


def show_status():
    """Show compact status bar."""
    startup = InlineStartup()
    startup.show_status_bar()