"""Native todo management for Hanzo REPL."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from enum import Enum

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.prompt import Prompt, Confirm


class TodoPriority(Enum):
    """Todo priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TodoStatus(Enum):
    """Todo status."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class Todo:
    """Single todo item."""
    
    def __init__(
        self,
        title: str,
        description: str = "",
        priority: TodoPriority = TodoPriority.MEDIUM,
        status: TodoStatus = TodoStatus.TODO,
        tags: List[str] = None,
        due_date: Optional[str] = None,
        id: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        completed_at: Optional[str] = None
    ):
        self.id = id or str(uuid.uuid4())[:8]
        self.title = title
        self.description = description
        self.priority = priority
        self.status = status
        self.tags = tags or []
        self.due_date = due_date
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
        self.completed_at = completed_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "tags": self.tags,
            "due_date": self.due_date,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Todo":
        """Create from dictionary."""
        return cls(
            id=data.get("id"),
            title=data["title"],
            description=data.get("description", ""),
            priority=TodoPriority(data.get("priority", "medium")),
            status=TodoStatus(data.get("status", "todo")),
            tags=data.get("tags", []),
            due_date=data.get("due_date"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            completed_at=data.get("completed_at")
        )


class TodoManager:
    """Manage todos with persistent storage."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.config_dir = Path.home() / ".hanzo"
        self.todos_file = self.config_dir / "todos.json"
        self.todos: List[Todo] = []
        self.load_todos()
    
    def load_todos(self):
        """Load todos from file."""
        if self.todos_file.exists():
            try:
                data = json.loads(self.todos_file.read_text())
                self.todos = [Todo.from_dict(t) for t in data.get("todos", [])]
            except Exception as e:
                self.console.print(f"[red]Error loading todos: {e}[/red]")
                self.todos = []
        else:
            self.todos = []
    
    def save_todos(self):
        """Save todos to file."""
        self.config_dir.mkdir(exist_ok=True)
        data = {
            "todos": [t.to_dict() for t in self.todos],
            "last_updated": datetime.now().isoformat()
        }
        self.todos_file.write_text(json.dumps(data, indent=2))
    
    def add_todo(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        tags: List[str] = None,
        due_date: Optional[str] = None
    ) -> Todo:
        """Add a new todo."""
        try:
            priority_enum = TodoPriority(priority.lower())
        except ValueError:
            priority_enum = TodoPriority.MEDIUM
        
        todo = Todo(
            title=title,
            description=description,
            priority=priority_enum,
            tags=tags or [],
            due_date=due_date
        )
        
        self.todos.append(todo)
        self.save_todos()
        
        return todo
    
    def update_todo(self, todo_id: str, **kwargs) -> Optional[Todo]:
        """Update a todo."""
        todo = self.get_todo(todo_id)
        if not todo:
            return None
        
        # Update fields
        if "title" in kwargs:
            todo.title = kwargs["title"]
        if "description" in kwargs:
            todo.description = kwargs["description"]
        if "priority" in kwargs:
            try:
                todo.priority = TodoPriority(kwargs["priority"].lower())
            except ValueError:
                pass
        if "status" in kwargs:
            try:
                new_status = TodoStatus(kwargs["status"].lower())
                todo.status = new_status
                
                # Update completed timestamp
                if new_status == TodoStatus.DONE:
                    todo.completed_at = datetime.now().isoformat()
                elif todo.status == TodoStatus.DONE and new_status != TodoStatus.DONE:
                    todo.completed_at = None
            except ValueError:
                pass
        if "tags" in kwargs:
            todo.tags = kwargs["tags"]
        if "due_date" in kwargs:
            todo.due_date = kwargs["due_date"]
        
        todo.updated_at = datetime.now().isoformat()
        self.save_todos()
        
        return todo
    
    def delete_todo(self, todo_id: str) -> bool:
        """Delete a todo."""
        todo = self.get_todo(todo_id)
        if todo:
            self.todos.remove(todo)
            self.save_todos()
            return True
        return False
    
    def get_todo(self, todo_id: str) -> Optional[Todo]:
        """Get a todo by ID."""
        for todo in self.todos:
            if todo.id == todo_id:
                return todo
        return None
    
    def list_todos(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        tag: Optional[str] = None
    ) -> List[Todo]:
        """List todos with optional filters."""
        filtered = self.todos
        
        # Filter by status
        if status:
            try:
                status_enum = TodoStatus(status.lower())
                filtered = [t for t in filtered if t.status == status_enum]
            except ValueError:
                pass
        
        # Filter by priority
        if priority:
            try:
                priority_enum = TodoPriority(priority.lower())
                filtered = [t for t in filtered if t.priority == priority_enum]
            except ValueError:
                pass
        
        # Filter by tag
        if tag:
            filtered = [t for t in filtered if tag in t.tags]
        
        # Sort by priority and status
        priority_order = {
            TodoPriority.URGENT: 0,
            TodoPriority.HIGH: 1,
            TodoPriority.MEDIUM: 2,
            TodoPriority.LOW: 3
        }
        
        status_order = {
            TodoStatus.IN_PROGRESS: 0,
            TodoStatus.TODO: 1,
            TodoStatus.DONE: 2,
            TodoStatus.CANCELLED: 3
        }
        
        filtered.sort(key=lambda t: (
            status_order.get(t.status, 999),
            priority_order.get(t.priority, 999),
            t.created_at
        ))
        
        return filtered
    
    def display_todos(
        self,
        todos: Optional[List[Todo]] = None,
        title: str = "Todos"
    ):
        """Display todos in a nice table."""
        if todos is None:
            todos = self.list_todos()
        
        if not todos:
            self.console.print("[yellow]No todos found[/yellow]")
            return
        
        # Create table
        table = Table(title=title, box=box.ROUNDED)
        table.add_column("ID", style="cyan", width=8)
        table.add_column("Status", width=12)
        table.add_column("Priority", width=8)
        table.add_column("Title", style="white")
        table.add_column("Tags", style="dim")
        table.add_column("Due", style="yellow")
        
        for todo in todos:
            # Status emoji
            status_display = {
                TodoStatus.TODO: "⭕ Todo",
                TodoStatus.IN_PROGRESS: "🔄 In Progress",
                TodoStatus.DONE: "✅ Done",
                TodoStatus.CANCELLED: "❌ Cancelled"
            }.get(todo.status, todo.status.value)
            
            # Priority color
            priority_color = {
                TodoPriority.URGENT: "red bold",
                TodoPriority.HIGH: "red",
                TodoPriority.MEDIUM: "yellow",
                TodoPriority.LOW: "green"
            }.get(todo.priority, "white")
            
            priority_display = f"[{priority_color}]{todo.priority.value.upper()}[/{priority_color}]"
            
            # Tags
            tags_display = ", ".join(todo.tags) if todo.tags else "-"
            
            # Due date
            due_display = todo.due_date if todo.due_date else "-"
            
            table.add_row(
                todo.id,
                status_display,
                priority_display,
                todo.title,
                tags_display,
                due_display
            )
        
        self.console.print(table)
        
        # Summary
        total = len(todos)
        done = len([t for t in todos if t.status == TodoStatus.DONE])
        in_progress = len([t for t in todos if t.status == TodoStatus.IN_PROGRESS])
        todo_count = len([t for t in todos if t.status == TodoStatus.TODO])
        
        summary = f"Total: {total} | Todo: {todo_count} | In Progress: {in_progress} | Done: {done}"
        self.console.print(f"\n[dim]{summary}[/dim]")
    
    def display_todo_detail(self, todo: Todo):
        """Display detailed view of a todo."""
        # Status color
        status_color = {
            TodoStatus.TODO: "yellow",
            TodoStatus.IN_PROGRESS: "cyan",
            TodoStatus.DONE: "green",
            TodoStatus.CANCELLED: "red"
        }.get(todo.status, "white")
        
        # Priority color
        priority_color = {
            TodoPriority.URGENT: "red bold",
            TodoPriority.HIGH: "red",
            TodoPriority.MEDIUM: "yellow",
            TodoPriority.LOW: "green"
        }.get(todo.priority, "white")
        
        # Build content
        content = f"""
[bold]{todo.title}[/bold]

[dim]ID:[/dim] {todo.id}
[dim]Status:[/dim] [{status_color}]{todo.status.value.replace('_', ' ').title()}[/{status_color}]
[dim]Priority:[/dim] [{priority_color}]{todo.priority.value.upper()}[/{priority_color}]
[dim]Tags:[/dim] {', '.join(todo.tags) if todo.tags else 'None'}
[dim]Due Date:[/dim] {todo.due_date if todo.due_date else 'Not set'}

[dim]Description:[/dim]
{todo.description if todo.description else 'No description'}

[dim]Created:[/dim] {todo.created_at}
[dim]Updated:[/dim] {todo.updated_at}
[dim]Completed:[/dim] {todo.completed_at if todo.completed_at else 'Not completed'}
"""
        
        panel = Panel(content.strip(), title=f"Todo: {todo.title}", box=box.ROUNDED)
        self.console.print(panel)
    
    def quick_add(self, text: str) -> Todo:
        """Quick add todo from text.
        
        Format: title #tag1 #tag2 !priority @due_date
        """
        import re
        
        # Extract tags (words starting with #)
        tags = re.findall(r'#(\w+)', text)
        text = re.sub(r'#\w+', '', text)
        
        # Extract priority (word after !)
        priority_match = re.search(r'!(\w+)', text)
        priority = priority_match.group(1) if priority_match else "medium"
        text = re.sub(r'!\w+', '', text)
        
        # Extract due date (text after @)
        due_match = re.search(r'@([^\s]+)', text)
        due_date = due_match.group(1) if due_match else None
        text = re.sub(r'@[^\s]+', '', text)
        
        # Clean up title
        title = text.strip()
        
        if not title:
            raise ValueError("Todo title cannot be empty")
        
        return self.add_todo(
            title=title,
            priority=priority,
            tags=tags,
            due_date=due_date
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get todo statistics."""
        total = len(self.todos)
        
        # Status counts
        status_counts = {}
        for status in TodoStatus:
            count = len([t for t in self.todos if t.status == status])
            status_counts[status.value] = count
        
        # Priority counts
        priority_counts = {}
        for priority in TodoPriority:
            count = len([t for t in self.todos if t.priority == priority])
            priority_counts[priority.value] = count
        
        # Tags
        all_tags = set()
        for todo in self.todos:
            all_tags.update(todo.tags)
        
        # Completion rate
        done = status_counts.get("done", 0)
        completion_rate = (done / total * 100) if total > 0 else 0
        
        return {
            "total": total,
            "status": status_counts,
            "priority": priority_counts,
            "tags": list(all_tags),
            "completion_rate": completion_rate
        }
    
    def display_statistics(self):
        """Display todo statistics."""
        stats = self.get_statistics()
        
        # Create stats panel
        content = f"""
[bold cyan]Todo Statistics[/bold cyan]

[bold]Total Todos:[/bold] {stats['total']}
[bold]Completion Rate:[/bold] {stats['completion_rate']:.1f}%

[bold]By Status:[/bold]
  ⭕ Todo: {stats['status'].get('todo', 0)}
  🔄 In Progress: {stats['status'].get('in_progress', 0)}
  ✅ Done: {stats['status'].get('done', 0)}
  ❌ Cancelled: {stats['status'].get('cancelled', 0)}

[bold]By Priority:[/bold]
  🔴 Urgent: {stats['priority'].get('urgent', 0)}
  🟠 High: {stats['priority'].get('high', 0)}
  🟡 Medium: {stats['priority'].get('medium', 0)}
  🟢 Low: {stats['priority'].get('low', 0)}

[bold]Tags:[/bold] {', '.join(stats['tags']) if stats['tags'] else 'None'}
"""
        
        panel = Panel(content.strip(), title="📊 Statistics", box=box.ROUNDED)
        self.console.print(panel)