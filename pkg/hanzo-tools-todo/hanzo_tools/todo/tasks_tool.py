"""Unified todo tool."""

import uuid
from typing import (
    Any,
    Dict,
    List,
    Unpack,
    Optional,
    Annotated,
    TypedDict,
    final,
    override,
)
from datetime import datetime

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import auto_timeout
from hanzo_tools.todo.base import TodoStorage, TodoBaseTool

# Default session ID for the unified todo tool
DEFAULT_SESSION_ID = "default-session"

# Parameter types
Action = Annotated[
    str,
    Field(
        description="Action to perform: list (default), add, update, remove, clear",
        default="list",
    ),
]

Content = Annotated[
    Optional[str],
    Field(
        description="Todo content for add/update",
        default=None,
    ),
]

TodoId = Annotated[
    Optional[str],
    Field(
        description="Todo ID for update/remove",
        default=None,
    ),
]

Status = Annotated[
    Optional[str],
    Field(
        description="Status: pending, in_progress, completed",
        default="pending",
    ),
]

Priority = Annotated[
    Optional[str],
    Field(
        description="Priority: high, medium, low",
        default="medium",
    ),
]

Filter = Annotated[
    Optional[str],
    Field(
        description="Filter todos by status for list action",
        default=None,
    ),
]


class TodoParams(TypedDict, total=False):
    """Parameters for todo tool."""

    action: str
    content: Optional[str]
    id: Optional[str]
    status: Optional[str]
    priority: Optional[str]
    filter: Optional[str]


@final
class TasksTool(TodoBaseTool):
    """Unified todo management tool."""

    name = "tasks"

    def read_todos(self) -> list[Dict[str, Any]]:
        """Read todos from storage using default session."""
        return TodoStorage.get_todos(DEFAULT_SESSION_ID)

    def write_todos(self, todos: list[Dict[str, Any]]) -> None:
        """Write todos to storage using default session."""
        TodoStorage.set_todos(DEFAULT_SESSION_ID, todos)

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Manage todos. Actions: list (default), add, update, remove, clear.

Usage:
todo
todo "Fix the bug in authentication"
todo --action update --id abc123 --status completed
todo --action remove --id abc123
todo --filter in_progress
"""

    @override
    @auto_timeout("todo")
    async def call(
        self,
        ctx: MCPContext,
        **params: Unpack[TodoParams],
    ) -> str:
        """Execute todo operation."""
        tool_ctx = self.create_tool_context(ctx)

        # Extract action
        action = params.get("action", "list")

        # Route to appropriate handler
        if action == "list":
            return await self._handle_list(params.get("filter"), tool_ctx)
        elif action == "add":
            return await self._handle_add(params, tool_ctx)
        elif action == "update":
            return await self._handle_update(params, tool_ctx)
        elif action in ("remove", "delete"):
            return await self._handle_remove(params.get("id"), tool_ctx)
        elif action == "clear":
            return await self._handle_clear(params.get("filter"), tool_ctx)
        elif action == "stats":
            return await self._handle_stats(tool_ctx)
        elif action == "search":
            return await self._handle_search(params, tool_ctx)
        elif action == "batch":
            return await self._handle_batch(params, tool_ctx)
        elif action == "archive":
            return await self._handle_archive(params.get("id"), tool_ctx)
        elif action == "move":
            return await self._handle_move(params, tool_ctx)
        elif action == "prioritize":
            return await self._handle_prioritize(params, tool_ctx)
        elif action == "assign":
            return await self._handle_assign(params, tool_ctx)
        elif action == "subtasks":
            return await self._handle_subtasks(params, tool_ctx)
        elif action == "notes":
            return await self._handle_notes(params, tool_ctx)
        elif action == "export":
            return await self._handle_export(params, tool_ctx)
        elif action == "import":
            return await self._handle_import(params, tool_ctx)
        else:
            return f"Error: Unknown action '{action}'. Valid actions: list, add, update, remove, delete, clear, stats, search, batch, archive, move, prioritize, assign, subtasks, notes, export, import"

    async def _handle_list(self, filter_status: Optional[str], tool_ctx) -> str:
        """List todos."""
        todos = self.read_todos()

        if not todos:
            return "No todos found. Use 'todo \"Your task here\"' to add one."

        # Apply filter if specified
        if filter_status:
            todos = [t for t in todos if t.get("status") == filter_status]
            if not todos:
                return f"No todos with status '{filter_status}'"

        # Group by status
        by_status = {}
        for todo in todos:
            status = todo.get("status", "pending")
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(todo)

        # Format output
        output = ["=== Todo List ==="]

        # Show in order: in_progress, pending, completed
        for status in ["in_progress", "pending", "completed"]:
            if status in by_status:
                output.append(f"\n{status.replace('_', ' ').title()}:")
                for todo in by_status[status]:
                    priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                        todo.get("priority", "medium"), "⚪"
                    )
                    output.append(
                        f"{priority_icon} [{todo['id'][:8]}] {todo['content']}"
                    )

        # Summary
        output.append(
            f"\nTotal: {len(todos)} | In Progress: {len(by_status.get('in_progress', []))} | Pending: {len(by_status.get('pending', []))} | Completed: {len(by_status.get('completed', []))}"
        )

        return "\n".join(output)

    async def _handle_add(self, params: Dict[str, Any], tool_ctx) -> str:
        """Add new todo."""
        content = params.get("content")
        if not content:
            return "Error: content is required for add action"

        todos = self.read_todos()

        new_todo = {
            "id": str(uuid.uuid4()),
            "content": content,
            "status": params.get("status", "pending"),
            "priority": params.get("priority", "medium"),
            "created_at": datetime.now().isoformat(),
        }

        todos.append(new_todo)
        self.write_todos(todos)

        await tool_ctx.info(f"Added todo: {content}")
        return f"Added todo [{new_todo['id'][:8]}]: {content}"

    async def _handle_update(self, params: Dict[str, Any], tool_ctx) -> str:
        """Update existing todo."""
        todo_id = params.get("id")
        if not todo_id:
            return "Error: id is required for update action"

        todos = self.read_todos()

        # Find todo (support partial ID match)
        todo_found = None
        for todo in todos:
            if todo["id"].startswith(todo_id):
                todo_found = todo
                break

        if not todo_found:
            return f"Error: Todo with ID '{todo_id}' not found"

        # Update fields
        if params.get("content"):
            todo_found["content"] = params["content"]
        if params.get("status"):
            todo_found["status"] = params["status"]
        if params.get("priority"):
            todo_found["priority"] = params["priority"]

        todo_found["updated_at"] = datetime.now().isoformat()

        self.write_todos(todos)

        await tool_ctx.info(f"Updated todo: {todo_found['content']}")
        return f"Updated todo [{todo_found['id'][:8]}]: {todo_found['content']} (status: {todo_found['status']})"

    async def _handle_remove(self, todo_id: Optional[str], tool_ctx) -> str:
        """Remove todo."""
        if not todo_id:
            return "Error: id is required for remove action"

        todos = self.read_todos()

        # Find and remove (support partial ID match)
        removed = None
        for i, todo in enumerate(todos):
            if todo["id"].startswith(todo_id):
                removed = todos.pop(i)
                break

        if not removed:
            return f"Error: Todo with ID '{todo_id}' not found"

        self.write_todos(todos)

        await tool_ctx.info(f"Removed todo: {removed['content']}")
        return f"Removed todo [{removed['id'][:8]}]: {removed['content']}"

    async def _handle_stats(self, tool_ctx) -> str:
        """Get todo statistics."""
        todos = self.read_todos()
        if not todos:
            return "No todos found."

        by_status = {}
        by_priority = {}
        for todo in todos:
            s = todo.get("status", "pending")
            p = todo.get("priority", "medium")
            by_status[s] = by_status.get(s, 0) + 1
            by_priority[p] = by_priority.get(p, 0) + 1

        lines = [f"Total: {len(todos)}"]
        lines.append("By status:")
        for s in ["in_progress", "pending", "completed"]:
            if s in by_status:
                lines.append(f"  {s}: {by_status[s]}")
        lines.append("By priority:")
        for p in ["high", "medium", "low"]:
            if p in by_priority:
                lines.append(f"  {p}: {by_priority[p]}")
        return "\n".join(lines)

    async def _handle_search(self, params: Dict[str, Any], tool_ctx) -> str:
        """Search todos by content."""
        query = params.get("content") or params.get("query") or ""
        if not query:
            return "Error: search query required (use content or query param)"
        todos = self.read_todos()
        query_lower = query.lower()
        matches = [t for t in todos if query_lower in t.get("content", "").lower()]
        if not matches:
            return f"No todos matching '{query}'"
        lines = [f"Found {len(matches)} matching todo(s):"]
        for t in matches:
            lines.append(f"  [{t['id'][:8]}] {t['content']} ({t.get('status', 'pending')})")
        return "\n".join(lines)

    async def _handle_batch(self, params: Dict[str, Any], tool_ctx) -> str:
        """Batch update todos by status."""
        from_status = params.get("filter") or params.get("from_status")
        to_status = params.get("status") or params.get("to_status")
        if not from_status or not to_status:
            return "Error: batch requires filter/from_status and status/to_status"
        todos = self.read_todos()
        count = 0
        for t in todos:
            if t.get("status") == from_status:
                t["status"] = to_status
                t["updated_at"] = datetime.now().isoformat()
                count += 1
        self.write_todos(todos)
        return f"Batch updated {count} todo(s) from '{from_status}' to '{to_status}'"

    async def _handle_archive(self, todo_id: Optional[str], tool_ctx) -> str:
        """Archive completed todos or a specific todo."""
        todos = self.read_todos()
        if todo_id:
            for t in todos:
                if t["id"].startswith(todo_id):
                    t["status"] = "archived"
                    t["updated_at"] = datetime.now().isoformat()
                    self.write_todos(todos)
                    return f"Archived todo [{t['id'][:8]}]"
            return f"Error: Todo '{todo_id}' not found"
        # Archive all completed
        count = 0
        for t in todos:
            if t.get("status") == "completed":
                t["status"] = "archived"
                t["updated_at"] = datetime.now().isoformat()
                count += 1
        self.write_todos(todos)
        return f"Archived {count} completed todo(s)"

    async def _handle_move(self, params: Dict[str, Any], tool_ctx) -> str:
        """Move a todo to a different position."""
        todo_id = params.get("id")
        position = params.get("position")
        if not todo_id:
            return "Error: id required for move"
        todos = self.read_todos()
        idx = None
        for i, t in enumerate(todos):
            if t["id"].startswith(todo_id):
                idx = i
                break
        if idx is None:
            return f"Error: Todo '{todo_id}' not found"
        item = todos.pop(idx)
        try:
            pos = int(position) if position is not None else 0
        except (ValueError, TypeError):
            pos = 0
        pos = max(0, min(pos, len(todos)))
        todos.insert(pos, item)
        self.write_todos(todos)
        return f"Moved todo [{item['id'][:8]}] to position {pos}"

    async def _handle_prioritize(self, params: Dict[str, Any], tool_ctx) -> str:
        """Change todo priority."""
        todo_id = params.get("id")
        priority = params.get("priority")
        if not todo_id or not priority:
            return "Error: id and priority required"
        todos = self.read_todos()
        for t in todos:
            if t["id"].startswith(todo_id):
                t["priority"] = priority
                t["updated_at"] = datetime.now().isoformat()
                self.write_todos(todos)
                return f"Set priority of [{t['id'][:8]}] to '{priority}'"
        return f"Error: Todo '{todo_id}' not found"

    async def _handle_assign(self, params: Dict[str, Any], tool_ctx) -> str:
        """Assign a todo to someone."""
        todo_id = params.get("id")
        assignee = params.get("assignee") or params.get("content")
        if not todo_id:
            return "Error: id required for assign"
        todos = self.read_todos()
        for t in todos:
            if t["id"].startswith(todo_id):
                t["assignee"] = assignee or ""
                t["updated_at"] = datetime.now().isoformat()
                self.write_todos(todos)
                return f"Assigned [{t['id'][:8]}] to '{assignee or 'unassigned'}'"
        return f"Error: Todo '{todo_id}' not found"

    async def _handle_subtasks(self, params: Dict[str, Any], tool_ctx) -> str:
        """Manage subtasks of a todo."""
        todo_id = params.get("id")
        content = params.get("content")
        if not todo_id:
            return "Error: id required for subtasks"
        todos = self.read_todos()
        for t in todos:
            if t["id"].startswith(todo_id):
                if "subtasks" not in t:
                    t["subtasks"] = []
                if content:
                    t["subtasks"].append({
                        "id": str(uuid.uuid4()),
                        "content": content,
                        "status": "pending",
                        "created_at": datetime.now().isoformat(),
                    })
                    self.write_todos(todos)
                    return f"Added subtask to [{t['id'][:8]}]: {content}"
                else:
                    if not t["subtasks"]:
                        return f"No subtasks for [{t['id'][:8]}]"
                    lines = [f"Subtasks for [{t['id'][:8]}]:"]
                    for st in t["subtasks"]:
                        lines.append(f"  [{st['id'][:8]}] {st['content']} ({st.get('status', 'pending')})")
                    return "\n".join(lines)
        return f"Error: Todo '{todo_id}' not found"

    async def _handle_notes(self, params: Dict[str, Any], tool_ctx) -> str:
        """Add or view notes on a todo."""
        todo_id = params.get("id")
        content = params.get("content")
        if not todo_id:
            return "Error: id required for notes"
        todos = self.read_todos()
        for t in todos:
            if t["id"].startswith(todo_id):
                if "notes" not in t:
                    t["notes"] = []
                if content:
                    t["notes"].append({
                        "text": content,
                        "created_at": datetime.now().isoformat(),
                    })
                    self.write_todos(todos)
                    return f"Added note to [{t['id'][:8]}]"
                else:
                    if not t["notes"]:
                        return f"No notes for [{t['id'][:8]}]"
                    lines = [f"Notes for [{t['id'][:8]}]:"]
                    for n in t["notes"]:
                        lines.append(f"  [{n.get('created_at', '?')}] {n['text']}")
                    return "\n".join(lines)
        return f"Error: Todo '{todo_id}' not found"

    async def _handle_export(self, params: Dict[str, Any], tool_ctx) -> str:
        """Export todos as JSON."""
        import json
        todos = self.read_todos()
        fmt = params.get("format") or "json"
        if fmt == "json":
            return json.dumps({"todos": todos}, indent=2, default=str)
        elif fmt == "markdown":
            lines = ["# Todos"]
            for t in todos:
                status_icon = {"completed": "x", "in_progress": "~", "pending": " "}.get(t.get("status", "pending"), " ")
                lines.append(f"- [{status_icon}] {t['content']}")
            return "\n".join(lines)
        return json.dumps({"todos": todos}, indent=2, default=str)

    async def _handle_import(self, params: Dict[str, Any], tool_ctx) -> str:
        """Import todos from JSON."""
        import json
        content = params.get("content")
        if not content:
            return "Error: content (JSON) required for import"
        try:
            data = json.loads(content)
            items = data if isinstance(data, list) else data.get("todos", data.get("items", []))
            todos = self.read_todos()
            count = 0
            for item in items:
                if isinstance(item, dict) and "content" in item:
                    if "id" not in item:
                        item["id"] = str(uuid.uuid4())
                    if "status" not in item:
                        item["status"] = "pending"
                    if "priority" not in item:
                        item["priority"] = "medium"
                    item["created_at"] = datetime.now().isoformat()
                    todos.append(item)
                    count += 1
            self.write_todos(todos)
            return f"Imported {count} todo(s)"
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON: {e}"

    async def _handle_clear(self, filter_status: Optional[str], tool_ctx) -> str:
        """Clear todos."""
        todos = self.read_todos()

        if filter_status:
            # Clear only todos with specific status
            original_count = len(todos)
            todos = [t for t in todos if t.get("status") != filter_status]
            removed_count = original_count - len(todos)

            if removed_count == 0:
                return f"No todos with status '{filter_status}' to clear"

            self.write_todos(todos)
            return f"Cleared {removed_count} todo(s) with status '{filter_status}'"
        else:
            # Clear all
            if not todos:
                return "No todos to clear"

            count = len(todos)
            self.write_todos([])
            return f"Cleared all {count} todo(s)"

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register this tool with the MCP server."""
        tool_self = self  # Create a reference to self for use in the closure

        @mcp_server.tool(name=self.name, description=self.description)
        async def todo(
            action: Action = "list",
            content: Content = None,
            id: TodoId = None,
            status: Status = None,
            priority: Priority = None,
            filter: Filter = None,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_self.call(
                ctx,
                action=action,
                content=content,
                id=id,
                status=status,
                priority=priority,
                filter=filter,
            )
