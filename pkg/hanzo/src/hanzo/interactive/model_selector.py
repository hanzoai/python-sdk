"""Quick model selector with arrow key navigation."""

from typing import List, Optional, Tuple
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import Label
from rich.console import Console


class QuickModelSelector:
    """Quick model selector with arrow navigation."""
    
    def __init__(self, models: List[Tuple[str, str]], tools: List[Tuple[str, str]], current: str):
        self.models = models
        self.tools = tools
        self.current = current
        self.all_items = tools + models  # Tools first, then models
        self.selected_index = 0
        
        # Find current selection
        for i, (item_id, _) in enumerate(self.all_items):
            if item_id == current:
                self.selected_index = i
                break
    
    def get_display_lines(self) -> List[str]:
        """Get display lines for the selector."""
        lines = []
        
        if self.tools:
            lines.append("AI Coding Assistants:")
            for i, (tool_id, tool_name) in enumerate(self.tools):
                marker = "→ " if i == self.selected_index else "  "
                lines.append(f"{marker}{tool_name}")
        
        if self.models:
            if self.tools:
                lines.append("")  # Empty line
            lines.append("Language Models:")
            
            tool_count = len(self.tools)
            for i, (model_id, model_name) in enumerate(self.models):
                actual_idx = tool_count + i
                marker = "→ " if actual_idx == self.selected_index else "  "
                lines.append(f"{marker}{model_name}")
        
        return lines
    
    def move_up(self):
        """Move selection up."""
        if self.selected_index > 0:
            self.selected_index -= 1
    
    def move_down(self):
        """Move selection down."""
        if self.selected_index < len(self.all_items) - 1:
            self.selected_index += 1
    
    def get_selected(self) -> Tuple[str, str]:
        """Get the selected item."""
        if 0 <= self.selected_index < len(self.all_items):
            return self.all_items[self.selected_index]
        return None, None
    
    async def run(self) -> Optional[str]:
        """Run the selector and return selected model/tool ID."""
        kb = KeyBindings()
        
        @kb.add('up')
        def _(event):
            self.move_up()
            event.app.invalidate()
        
        @kb.add('down')
        def _(event):
            self.move_down()
            event.app.invalidate()
        
        @kb.add('enter')
        def _(event):
            event.app.exit(result=self.get_selected()[0])
        
        @kb.add('c-c')
        @kb.add('escape')
        def _(event):
            event.app.exit(result=None)
        
        def get_text():
            lines = self.get_display_lines()
            lines.append("")
            lines.append("↑/↓: Navigate  Enter: Select  Esc: Cancel")
            return "\n".join(lines)
        
        layout = Layout(
            Window(
                FormattedTextControl(get_text),
                wrap_lines=False
            )
        )
        
        app = Application(
            layout=layout,
            key_bindings=kb,
            full_screen=False,
            mouse_support=True
        )
        
        return await app.run_async()


class BackgroundTaskManager:
    """Manage background tasks."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.tasks = {}  # task_id -> process
        self.next_id = 1
    
    def add_task(self, name: str, process):
        """Add a background task."""
        task_id = f"task_{self.next_id}"
        self.next_id += 1
        self.tasks[task_id] = {
            "name": name,
            "process": process,
            "started": True
        }
        return task_id
    
    def list_tasks(self):
        """List all background tasks."""
        if not self.tasks:
            self.console.print("[dim]No background tasks running[/dim]")
            return
        
        self.console.print("[bold]Background Tasks:[/bold]")
        for task_id, task in self.tasks.items():
            status = "🟢 Running" if task["process"].poll() is None else "🔴 Stopped"
            self.console.print(f"  {task_id}: {task['name']} - {status}")
    
    def kill_task(self, task_id: str):
        """Kill a background task."""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if task["process"].poll() is None:
                task["process"].terminate()
                self.console.print(f"[yellow]Terminated {task_id}: {task['name']}[/yellow]")
            else:
                self.console.print(f"[dim]Task {task_id} already stopped[/dim]")
            del self.tasks[task_id]
        else:
            self.console.print(f"[red]Task {task_id} not found[/red]")
    
    def kill_all(self):
        """Kill all background tasks."""
        if not self.tasks:
            self.console.print("[dim]No tasks to kill[/dim]")
            return
        
        for task_id in list(self.tasks.keys()):
            self.kill_task(task_id)
        
        self.console.print("[green]All tasks terminated[/green]")