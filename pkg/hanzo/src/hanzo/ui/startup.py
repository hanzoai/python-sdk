"""
Hanzo startup UI and changelog integration.
"""

import os
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.columns import Columns
from rich.markdown import Markdown
from rich import box

console = Console()


class StartupUI:
    """Clean startup UI for Hanzo with changelog integration."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".hanzo"
        self.config_file = self.config_dir / "config.json"
        self.changelog_cache = self.config_dir / "changelog_cache.json"
        self.last_shown_file = self.config_dir / ".last_shown_version"
        self.current_version = self._get_current_version()
        
    def _get_current_version(self) -> str:
        """Get current Hanzo version."""
        try:
            from hanzo import __version__
            return __version__
        except:
            return "0.3.23"
    
    def _get_last_shown_version(self) -> Optional[str]:
        """Get the last version shown to user."""
        if self.last_shown_file.exists():
            return self.last_shown_file.read_text().strip()
        return None
    
    def _save_last_shown_version(self):
        """Save current version as last shown."""
        self.config_dir.mkdir(exist_ok=True)
        self.last_shown_file.write_text(self.current_version)
    
    def _fetch_changelog(self) -> List[Dict[str, Any]]:
        """Fetch latest changelog from GitHub."""
        try:
            # Check cache first
            if self.changelog_cache.exists():
                cache_data = json.loads(self.changelog_cache.read_text())
                cache_time = datetime.fromisoformat(cache_data["timestamp"])
                if datetime.now() - cache_time < timedelta(hours=6):
                    return cache_data["entries"]
            
            # Fetch from GitHub
            response = httpx.get(
                "https://api.github.com/repos/hanzoai/python-sdk/releases",
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=5
            )
            
            if response.status_code == 200:
                releases = response.json()[:5]  # Last 5 releases
                entries = []
                
                for release in releases:
                    entries.append({
                        "version": release["tag_name"],
                        "date": release["published_at"][:10],
                        "highlights": self._parse_highlights(release["body"])
                    })
                
                # Cache the results
                cache_data = {
                    "timestamp": datetime.now().isoformat(),
                    "entries": entries
                }
                self.changelog_cache.write_text(json.dumps(cache_data))
                return entries
                
        except Exception:
            pass
        
        # Fallback to static changelog
        return self._get_static_changelog()
    
    def _parse_highlights(self, body: str) -> List[str]:
        """Parse release highlights from markdown."""
        if not body:
            return []
        
        highlights = []
        lines = body.split("\n")
        
        for line in lines:
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                highlight = line[2:].strip()
                if len(highlight) > 80:
                    highlight = highlight[:77] + "..."
                highlights.append(highlight)
                if len(highlights) >= 3:
                    break
        
        return highlights
    
    def _get_static_changelog(self) -> List[Dict[str, Any]]:
        """Get static changelog for offline mode."""
        return [
            {
                "version": "v0.3.23",
                "date": "2024-09-06",
                "highlights": [
                    "✨ Added router management commands for LLM proxy control",
                    "🎯 Renamed cluster to node for better clarity", 
                    "📚 Comprehensive documentation for all packages"
                ]
            },
            {
                "version": "v0.3.22",
                "date": "2024-09-05",
                "highlights": [
                    "🚀 Improved MCP tool performance with batch operations",
                    "🔧 Fixed file permission handling in Windows",
                    "💾 Added memory persistence for conversations"
                ]
            }
        ]
    
    def _create_welcome_panel(self) -> Panel:
        """Create the welcome panel with branding."""
        # ASCII art logo
        logo = """
    ██╗  ██╗ █████╗ ███╗   ██╗███████╗ ██████╗ 
    ██║  ██║██╔══██╗████╗  ██║╚══███╔╝██╔═══██╗
    ███████║███████║██╔██╗ ██║  ███╔╝ ██║   ██║
    ██╔══██║██╔══██║██║╚██╗██║ ███╔╝  ██║   ██║
    ██║  ██║██║  ██║██║ ╚████║███████╗╚██████╔╝
    ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝ ╚═════╝ 
        """
        
        # Create welcome text
        welcome = Text()
        welcome.append("Welcome to ", style="white")
        welcome.append("Hanzo AI", style="bold cyan")
        welcome.append(" • ", style="dim")
        welcome.append(f"v{self.current_version}", style="green")
        
        # Add subtitle
        subtitle = Text("Your AI Infrastructure Platform", style="italic dim")
        
        # Combine elements
        content = Align.center(
            Text.from_ansi(logo) + "\n" + welcome + "\n" + subtitle
        )
        
        return Panel(
            content,
            box=box.DOUBLE,
            border_style="cyan",
            padding=(1, 2)
        )
    
    def _create_whats_new_panel(self) -> Optional[Panel]:
        """Create What's New panel with recent changes."""
        last_shown = self._get_last_shown_version()
        
        # Only show if there's new content
        if last_shown == self.current_version:
            return None
        
        changelog = self._fetch_changelog()
        if not changelog:
            return None
        
        # Build content
        content = Text()
        content.append("🎉 What's New\n\n", style="bold yellow")
        
        for entry in changelog[:2]:  # Show last 2 versions
            content.append(f"  {entry['version']}", style="bold cyan")
            content.append(f"  ({entry['date']})\n", style="dim")
            
            for highlight in entry['highlights'][:2]:
                content.append(f"    • {highlight}\n", style="white")
            
            content.append("\n")
        
        return Panel(
            content,
            title="[yellow]Recent Updates[/yellow]",
            box=box.ROUNDED,
            border_style="yellow",
            padding=(0, 1)
        )
    
    def _create_quick_start_panel(self) -> Panel:
        """Create quick start tips panel."""
        tips = [
            ("chat", "Start interactive AI chat"),
            ("node start", "Run local AI node"),
            ("router start", "Start LLM proxy"),
            ("repl", "Interactive Python + AI"),
            ("help", "Show all commands")
        ]
        
        # Create table
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="dim")
        
        for cmd, desc in tips:
            table.add_row(f"hanzo {cmd}", desc)
        
        return Panel(
            table,
            title="[green]Quick Start[/green]",
            box=box.ROUNDED,
            border_style="green",
            padding=(0, 1)
        )
    
    def _create_status_panel(self) -> Panel:
        """Create status panel showing system state."""
        items = []
        
        # Check router status
        try:
            response = httpx.get("http://localhost:4000/health", timeout=1)
            router_status = "🟢 Running" if response.status_code == 200 else "🔴 Offline"
        except:
            router_status = "⚫ Offline"
        
        # Check node status  
        try:
            response = httpx.get("http://localhost:8000/health", timeout=1)
            node_status = "🟢 Running" if response.status_code == 200 else "🔴 Offline"
        except:
            node_status = "⚫ Offline"
        
        # Check API key
        api_key = os.getenv("HANZO_API_KEY")
        api_status = "🟢 Configured" if api_key else "🟡 Not Set"
        
        # Build status text
        status = Text()
        status.append("Router: ", style="bold")
        status.append(f"{router_status}  ", style="white")
        status.append("Node: ", style="bold")
        status.append(f"{node_status}  ", style="white")
        status.append("API: ", style="bold")
        status.append(api_status, style="white")
        
        return Panel(
            Align.center(status),
            box=box.ROUNDED,
            border_style="blue",
            padding=(0, 1)
        )
    
    def _check_for_updates(self) -> Optional[str]:
        """Check if updates are available."""
        try:
            response = httpx.get(
                "https://pypi.org/pypi/hanzo/json",
                timeout=3
            )
            if response.status_code == 200:
                data = response.json()
                latest = data["info"]["version"]
                if latest != self.current_version:
                    return latest
        except:
            pass
        return None
    
    def show(self, minimal: bool = False):
        """Display the startup UI."""
        console.clear()
        
        if minimal:
            # Minimal mode - just show compact welcome
            console.print(
                Panel(
                    f"[bold cyan]Hanzo AI[/bold cyan] • v{self.current_version} • [dim]Type [cyan]hanzo help[/cyan] for commands[/dim]",
                    box=box.ROUNDED,
                    padding=(0, 1)
                )
            )
            return
        
        # Full startup UI
        panels = []
        
        # Welcome panel
        welcome = self._create_welcome_panel()
        console.print(welcome)
        
        # What's New (if applicable)
        whats_new = self._create_whats_new_panel()
        if whats_new:
            console.print(whats_new)
            self._save_last_shown_version()
        
        # Quick start and status in columns
        quick_start = self._create_quick_start_panel()
        status = self._create_status_panel()
        
        console.print(Columns([quick_start, status], equal=True, expand=True))
        
        # Check for updates
        latest = self._check_for_updates()
        if latest:
            console.print(
                Panel(
                    f"[yellow]📦 Update available:[/yellow] v{latest} → Run [cyan]pip install --upgrade hanzo[/cyan]",
                    box=box.ROUNDED,
                    border_style="yellow",
                    padding=(0, 1)
                )
            )
        
        # Footer
        console.print(
            Align.center(
                Text("Get started with ", style="dim") + 
                Text("hanzo chat", style="bold cyan") +
                Text(" or view docs at ", style="dim") +
                Text("docs.hanzo.ai", style="blue underline")
            )
        )
        console.print()


def show_startup(minimal: bool = False):
    """Show the startup UI."""
    ui = StartupUI()
    ui.show(minimal=minimal)


if __name__ == "__main__":
    show_startup()