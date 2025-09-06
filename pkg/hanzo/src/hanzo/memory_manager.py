"""
Memory management system for Hanzo Dev.
Provides persistent context and memory like Claude Desktop.
"""

import os
import json
import hashlib
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import asdict, dataclass


@dataclass
class MemoryItem:
    """A single memory item."""

    id: str
    content: str
    type: str  # 'context', 'instruction', 'fact', 'code'
    created_at: str
    tags: List[str]
    priority: int = 0  # Higher priority items are kept longer

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "MemoryItem":
        return cls(**data)


class MemoryManager:
    """Manages persistent memory and context for AI conversations."""

    def __init__(self, workspace_dir: str = None):
        """Initialize memory manager."""
        if workspace_dir:
            self.memory_dir = Path(workspace_dir) / ".hanzo" / "memory"
        else:
            self.memory_dir = Path.home() / ".hanzo" / "memory"

        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.memory_dir / "context.json"
        self.session_file = self.memory_dir / "session.json"

        self.memories: List[MemoryItem] = []
        self.session_context: Dict[str, Any] = {}

        self.load_memories()
        self.load_session()

    def load_memories(self):
        """Load persistent memories from disk."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r") as f:
                    data = json.load(f)
                    self.memories = [
                        MemoryItem.from_dict(item) for item in data.get("memories", [])
                    ]
            except Exception as e:
                print(f"Error loading memories: {e}")
                self.memories = []
        else:
            # Initialize with default memories
            self._init_default_memories()

    def _init_default_memories(self):
        """Initialize with helpful default memories."""
        defaults = [
            MemoryItem(
                id=self._generate_id("system"),
                content="I am Hanzo Dev, an AI coding assistant with multiple orchestrator modes.",
                type="instruction",
                created_at=datetime.now().isoformat(),
                tags=["system", "identity"],
                priority=10,
            ),
            MemoryItem(
                id=self._generate_id("capabilities"),
                content="I can read/write files, search code, run commands, and use various AI models.",
                type="fact",
                created_at=datetime.now().isoformat(),
                tags=["system", "capabilities"],
                priority=9,
            ),
            MemoryItem(
                id=self._generate_id("help"),
                content="Use /help for commands, #memory for context management, or just chat naturally.",
                type="instruction",
                created_at=datetime.now().isoformat(),
                tags=["system", "usage"],
                priority=8,
            ),
        ]
        self.memories = defaults
        self.save_memories()

    def save_memories(self):
        """Save memories to disk."""
        try:
            data = {
                "memories": [m.to_dict() for m in self.memories],
                "updated_at": datetime.now().isoformat(),
            }
            with open(self.memory_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving memories: {e}")

    def load_session(self):
        """Load current session context."""
        if self.session_file.exists():
            try:
                with open(self.session_file, "r") as f:
                    self.session_context = json.load(f)
            except Exception:
                self.session_context = {}
        else:
            self.session_context = {
                "started_at": datetime.now().isoformat(),
                "messages": [],
                "current_task": None,
                "preferences": {},
            }

    def save_session(self):
        """Save session context."""
        try:
            with open(self.session_file, "w") as f:
                json.dump(self.session_context, f, indent=2)
        except Exception as e:
            print(f"Error saving session: {e}")

    def add_memory(
        self,
        content: str,
        type: str = "context",
        tags: List[str] = None,
        priority: int = 0,
    ) -> str:
        """Add a new memory item."""
        memory_id = self._generate_id(content)

        # Check if similar memory exists
        for mem in self.memories:
            if mem.content == content:
                return mem.id  # Don't duplicate

        memory = MemoryItem(
            id=memory_id,
            content=content,
            type=type,
            created_at=datetime.now().isoformat(),
            tags=tags or [],
            priority=priority,
        )

        self.memories.append(memory)
        self.save_memories()

        return memory_id

    def remove_memory(self, memory_id: str) -> bool:
        """Remove a memory by ID."""
        for i, mem in enumerate(self.memories):
            if mem.id == memory_id:
                del self.memories[i]
                self.save_memories()
                return True
        return False

    def clear_memories(self, keep_system: bool = True):
        """Clear all memories, optionally keeping system memories."""
        if keep_system:
            self.memories = [m for m in self.memories if "system" in m.tags]
        else:
            self.memories = []
        self.save_memories()

    def get_memories(
        self, type: str = None, tags: List[str] = None
    ) -> List[MemoryItem]:
        """Get memories filtered by type or tags."""
        result = self.memories

        if type:
            result = [m for m in result if m.type == type]

        if tags:
            result = [m for m in result if any(tag in m.tags for tag in tags)]

        # Sort by priority and creation date
        result.sort(key=lambda m: (-m.priority, m.created_at), reverse=True)

        return result

    def get_context_string(self, max_tokens: int = 2000) -> str:
        """Get a formatted context string for AI prompts."""
        # Sort memories by priority
        sorted_memories = sorted(self.memories, key=lambda m: -m.priority)

        context_parts = []
        token_count = 0

        for memory in sorted_memories:
            # Rough token estimation (4 chars = 1 token)
            memory_tokens = len(memory.content) // 4

            if token_count + memory_tokens > max_tokens:
                break

            if memory.type == "instruction":
                context_parts.append(f"INSTRUCTION: {memory.content}")
            elif memory.type == "fact":
                context_parts.append(f"FACT: {memory.content}")
            elif memory.type == "code":
                context_parts.append(f"CODE CONTEXT:\n{memory.content}")
            else:
                context_parts.append(memory.content)

            token_count += memory_tokens

        return "\n\n".join(context_parts)

    def add_message(self, role: str, content: str):
        """Add a message to session history."""
        self.session_context["messages"].append(
            {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
        )

        # Keep only last 50 messages
        if len(self.session_context["messages"]) > 50:
            self.session_context["messages"] = self.session_context["messages"][-50:]

        self.save_session()

    def get_recent_messages(self, count: int = 10) -> List[Dict]:
        """Get recent messages from session."""
        return self.session_context["messages"][-count:]

    def set_preference(self, key: str, value: Any):
        """Set a user preference."""
        self.session_context["preferences"][key] = value
        self.save_session()

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        return self.session_context["preferences"].get(key, default)

    def _generate_id(self, content: str) -> str:
        """Generate a unique ID for a memory item."""
        hash_input = f"{content}{datetime.now().isoformat()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:8]

    def summarize_for_ai(self) -> str:
        """Create a summary suitable for AI context."""
        summary = []

        # Add system memories
        system_memories = self.get_memories(tags=["system"])
        if system_memories:
            summary.append("SYSTEM CONTEXT:")
            for mem in system_memories[:3]:  # Top 3 system memories
                summary.append(f"- {mem.content}")

        # Add recent instructions
        instructions = self.get_memories(type="instruction")
        if instructions:
            summary.append("\nINSTRUCTIONS:")
            for mem in instructions[:3]:  # Top 3 instructions
                summary.append(f"- {mem.content}")

        # Add important facts
        facts = self.get_memories(type="fact")
        if facts:
            summary.append("\nKEY FACTS:")
            for mem in facts[:5]:  # Top 5 facts
                summary.append(f"- {mem.content}")

        # Add current task if set
        if self.session_context.get("current_task"):
            summary.append(f"\nCURRENT TASK: {self.session_context['current_task']}")

        return "\n".join(summary)

    def export_memories(self, file_path: str):
        """Export memories to a file."""
        data = {
            "memories": [m.to_dict() for m in self.memories],
            "session": self.session_context,
            "exported_at": datetime.now().isoformat(),
        }

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def import_memories(self, file_path: str):
        """Import memories from a file."""
        with open(file_path, "r") as f:
            data = json.load(f)

        # Merge memories (avoid duplicates)
        existing_ids = {m.id for m in self.memories}

        for mem_data in data.get("memories", []):
            if mem_data["id"] not in existing_ids:
                self.memories.append(MemoryItem.from_dict(mem_data))

        # Merge session preferences
        if "session" in data and "preferences" in data["session"]:
            self.session_context["preferences"].update(data["session"]["preferences"])

        self.save_memories()
        self.save_session()


def handle_memory_command(command: str, memory_manager: MemoryManager, console) -> bool:
    """
    Handle #memory commands.
    Returns True if command was handled, False otherwise.
    """
    from rich.panel import Panel
    from rich.table import Table

    parts = command.strip().split(maxsplit=2)

    if len(parts) == 1 or parts[1] == "show":
        # Show current memories
        memories = memory_manager.get_memories()

        if not memories:
            console.print("[yellow]No memories stored.[/yellow]")
            return True

        table = Table(
            title="Current Memories", show_header=True, header_style="bold magenta"
        )
        table.add_column("ID", style="cyan", width=10)
        table.add_column("Type", width=12)
        table.add_column("Content", width=50)
        table.add_column("Priority", width=8)

        for mem in memories[:10]:  # Show top 10
            content = mem.content[:47] + "..." if len(mem.content) > 50 else mem.content
            table.add_row(mem.id, mem.type, content, str(mem.priority))

        console.print(table)

        if len(memories) > 10:
            console.print(f"[dim]... and {len(memories) - 10} more[/dim]")

        return True

    elif parts[1] == "add":
        if len(parts) < 3:
            console.print("[red]Usage: #memory add <content>[/red]")
            return True

        content = parts[2]
        memory_id = memory_manager.add_memory(content, type="context")
        console.print(f"[green]Added memory: {memory_id}[/green]")
        return True

    elif parts[1] == "remove":
        if len(parts) < 3:
            console.print("[red]Usage: #memory remove <id>[/red]")
            return True

        memory_id = parts[2]
        if memory_manager.remove_memory(memory_id):
            console.print(f"[green]Removed memory: {memory_id}[/green]")
        else:
            console.print(f"[red]Memory not found: {memory_id}[/red]")
        return True

    elif parts[1] == "clear":
        memory_manager.clear_memories(keep_system=True)
        console.print("[green]Cleared all non-system memories.[/green]")
        return True

    elif parts[1] == "save":
        memory_manager.save_memories()
        memory_manager.save_session()
        console.print("[green]Memories saved.[/green]")
        return True

    elif parts[1] == "export":
        if len(parts) < 3:
            file_path = "hanzo_memories.json"
        else:
            file_path = parts[2]

        memory_manager.export_memories(file_path)
        console.print(f"[green]Exported memories to {file_path}[/green]")
        return True

    elif parts[1] == "import":
        if len(parts) < 3:
            console.print("[red]Usage: #memory import <file_path>[/red]")
            return True

        file_path = parts[2]
        try:
            memory_manager.import_memories(file_path)
            console.print(f"[green]Imported memories from {file_path}[/green]")
        except Exception as e:
            console.print(f"[red]Error importing: {e}[/red]")
        return True

    elif parts[1] == "context":
        # Show AI context
        context = memory_manager.summarize_for_ai()
        console.print(
            Panel(
                context,
                title="[bold cyan]AI Context[/bold cyan]",
                title_align="left",
                border_style="dim cyan",
            )
        )
        return True

    elif parts[1] == "help":
        help_text = """Memory Commands:
#memory [show]      - Show current memories
#memory add <text>  - Add new memory
#memory remove <id> - Remove memory by ID
#memory clear       - Clear all memories (keep system)
#memory save        - Save memories to disk
#memory export [file] - Export memories to file
#memory import <file> - Import memories from file
#memory context     - Show AI context summary
#memory help        - Show this help"""

        console.print(
            Panel(
                help_text,
                title="[bold cyan]Memory Help[/bold cyan]",
                title_align="left",
                border_style="dim cyan",
            )
        )
        return True

    return False
