"""
IDE Integration Tool for VS Code, JetBrains, and LSP-compatible editors.

Architecture:
- VS Code: Connect via Hanzo extension (WebSocket on port 9225)
- JetBrains: Connect via Gateway protocol
- Neovim: Connect via RPC socket
- Generic: Connect via LSP

VS Code Extension API surfaces used:
- vscode.window: Active editor, terminals, notifications
- vscode.workspace: Files, folders, configuration
- vscode.commands: Execute any VS Code command
- vscode.languages: Diagnostics, completion, hover

The Hanzo VS Code extension acts as a bridge, exposing these APIs
via WebSocket for external AI agent control.
"""

from __future__ import annotations

import asyncio
import json
import uuid
import logging
from dataclasses import dataclass, field
from typing import Any
from enum import Enum

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

from hanzo_tools.core import BaseTool

logger = logging.getLogger(__name__)


class IdeType(str, Enum):
    """Supported IDE types."""
    VSCODE = "vscode"
    JETBRAINS = "jetbrains"
    NEOVIM = "neovim"
    CURSOR = "cursor"
    WINDSURF = "windsurf"
    GENERIC = "generic"


@dataclass
class IdeConnection:
    """Connection state for an IDE."""
    ide_type: IdeType
    endpoint: str
    websocket: Any = None
    connected: bool = False
    workspace_path: str | None = None
    active_file: str | None = None
    pending_requests: dict[str, asyncio.Future] = field(default_factory=dict)

    async def connect(self) -> bool:
        """Establish connection to IDE."""
        if not WEBSOCKETS_AVAILABLE:
            logger.warning("websockets not available")
            return False

        try:
            self.websocket = await websockets.connect(
                self.endpoint,
                ping_interval=30,
                ping_timeout=10,
            )
            self.connected = True

            # Start message receiver
            asyncio.create_task(self._receive_loop())

            return True
        except Exception as e:
            logger.debug(f"Failed to connect to {self.ide_type}: {e}")
            return False

    async def disconnect(self) -> None:
        """Close connection."""
        if self.websocket:
            await self.websocket.close()
        self.connected = False

    async def send(self, action: str, **params: Any) -> dict[str, Any]:
        """Send request and wait for response."""
        if not self.connected or not self.websocket:
            return {"error": "Not connected to IDE"}

        request_id = str(uuid.uuid4())

        message = {
            "id": request_id,
            "action": action,
            "params": params,
        }

        future: asyncio.Future[dict] = asyncio.get_event_loop().create_future()
        self.pending_requests[request_id] = future

        try:
            await self.websocket.send(json.dumps(message))
            result = await asyncio.wait_for(future, timeout=30.0)
            return result
        except asyncio.TimeoutError:
            return {"error": "Request timed out"}
        finally:
            self.pending_requests.pop(request_id, None)

    async def _receive_loop(self) -> None:
        """Receive messages from IDE."""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                request_id = data.get("id")

                if request_id and request_id in self.pending_requests:
                    self.pending_requests[request_id].set_result(data)
                else:
                    # Event notification
                    await self._handle_event(data)
        except Exception as e:
            logger.debug(f"Receive loop error: {e}")
            self.connected = False

    async def _handle_event(self, data: dict) -> None:
        """Handle event notification from IDE."""
        event_type = data.get("event")
        if event_type == "activeEditorChanged":
            self.active_file = data.get("path")
        elif event_type == "workspaceChanged":
            self.workspace_path = data.get("path")


class IdeManager:
    """Manages IDE connections."""

    _instance: IdeManager | None = None

    def __init__(self) -> None:
        self.connections: dict[IdeType, IdeConnection] = {}
        self.default_ide: IdeType | None = None

    @classmethod
    def get_instance(cls) -> IdeManager:
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def connect(self, ide_type: IdeType = IdeType.VSCODE) -> IdeConnection:
        """Connect to an IDE."""
        if ide_type in self.connections and self.connections[ide_type].connected:
            return self.connections[ide_type]

        # Default endpoints for each IDE type
        endpoints = {
            IdeType.VSCODE: "ws://localhost:9225",
            IdeType.CURSOR: "ws://localhost:9226",
            IdeType.WINDSURF: "ws://localhost:9227",
            IdeType.JETBRAINS: "ws://localhost:63342/api/hanzo",
            IdeType.NEOVIM: "ws://localhost:9228",
        }

        endpoint = endpoints.get(ide_type, endpoints[IdeType.VSCODE])

        conn = IdeConnection(ide_type=ide_type, endpoint=endpoint)
        if await conn.connect():
            self.connections[ide_type] = conn
            if self.default_ide is None:
                self.default_ide = ide_type
            return conn

        return conn

    async def auto_connect(self) -> IdeConnection | None:
        """Auto-detect and connect to available IDE."""
        for ide_type in [IdeType.VSCODE, IdeType.CURSOR, IdeType.WINDSURF]:
            conn = await self.connect(ide_type)
            if conn.connected:
                return conn
        return None

    def get_connection(self, ide_type: IdeType | None = None) -> IdeConnection | None:
        """Get existing connection."""
        ide_type = ide_type or self.default_ide
        if ide_type:
            return self.connections.get(ide_type)
        return None


class IdeTool(BaseTool):
    """
    IDE integration tool for controlling VS Code, JetBrains, and other editors.

    Connects to the Hanzo IDE extension (VS Code, Cursor, Windsurf) via WebSocket.
    Provides full control over editor operations for AI agents.

    Actions:
    - connect: Connect to IDE (auto-detects VS Code, Cursor, Windsurf)
    - status: Check connection status
    - open: Open file in editor
    - close: Close file
    - save: Save current file
    - files: List open files
    - select: Set selection in editor
    - insert: Insert text at position
    - replace: Replace text in range
    - get_text: Get text from file/selection
    - go_to_definition: Navigate to symbol definition
    - find_references: Find all references to symbol
    - rename: Rename symbol across workspace
    - format: Format document
    - diagnostics: Get errors and warnings
    - quick_fix: Apply quick fix
    - command: Execute VS Code command
    - terminal: Create/send to terminal
    - search: Search in workspace
    """

    name = "ide"

    @property
    def description(self) -> str:
        return """IDE control for VS Code, Cursor, Windsurf, and JetBrains.

ACTIONS:
- connect: Connect to IDE (ide?: vscode|cursor|windsurf|jetbrains)
- status: Check connection status
- open: Open file (path: string, line?: int)
- close: Close file (path?: string)
- save: Save file (path?: string)
- files: List open files
- select: Set selection (line: int, column: int, end_line?: int, end_column?: int)
- insert: Insert text (text: string, line: int, column?: int)
- replace: Replace text (text: string, line: int, column: int, end_line: int, end_column: int)
- get_text: Get text (line?: int, end_line?: int)
- go_to_definition: Go to definition (line: int, column: int)
- find_references: Find references (line: int, column: int)
- rename: Rename symbol (new_name: string, line: int, column: int)
- format: Format document
- diagnostics: Get diagnostics (severity?: error|warning|info)
- quick_fix: Apply quick fix (line: int, column: int, index?: int)
- command: Execute command (command: string, args?: list)
- terminal: Terminal (command?: string, name?: string)
- search: Search workspace (query: string, include?: string, exclude?: string)

EXAMPLES:
  ide(action="connect")
  ide(action="open", path="/src/main.py", line=42)
  ide(action="insert", text="# TODO: fix this", line=10)
  ide(action="rename", new_name="better_name", line=15, column=8)
  ide(action="terminal", command="npm test")
  ide(action="command", command="workbench.action.toggleSidebarVisibility")"""

    def __init__(self) -> None:
        super().__init__()
        self.manager = IdeManager.get_instance()

    async def call(
        self,
        action: str = "status",
        ide: str | None = None,
        path: str | None = None,
        line: int | None = None,
        column: int | None = None,
        end_line: int | None = None,
        end_column: int | None = None,
        text: str | None = None,
        new_name: str | None = None,
        command: str | None = None,
        args: list[Any] | None = None,
        query: str | None = None,
        include: str | None = None,
        exclude: str | None = None,
        name: str | None = None,
        severity: str | None = None,
        index: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Execute IDE action."""

        action = action.lower()

        # Connection management
        if action == "connect":
            return await self._connect(ide)
        elif action == "status":
            return self._status()

        # Get connection
        ide_type = IdeType(ide) if ide else None
        conn = self.manager.get_connection(ide_type)

        if not conn or not conn.connected:
            # Try auto-connect
            conn = await self.manager.auto_connect()
            if not conn or not conn.connected:
                return "Not connected to IDE. Use ide(action='connect') first or install Hanzo IDE extension."

        # File operations
        if action == "open":
            if not path:
                return "Error: path required for open action"
            result = await conn.send("openFile", path=path, line=line)
            return self._format_result(result, f"Opened {path}")

        elif action == "close":
            result = await conn.send("closeFile", path=path)
            return self._format_result(result, "File closed")

        elif action == "save":
            result = await conn.send("saveFile", path=path)
            return self._format_result(result, "File saved")

        elif action == "files":
            result = await conn.send("listOpenFiles")
            return self._format_result(result)

        # Editor operations
        elif action == "select":
            if line is None:
                return "Error: line required for select action"
            result = await conn.send(
                "setSelection",
                line=line,
                column=column or 0,
                endLine=end_line,
                endColumn=end_column,
            )
            return self._format_result(result, "Selection set")

        elif action == "insert":
            if text is None or line is None:
                return "Error: text and line required for insert action"
            result = await conn.send(
                "insertText",
                text=text,
                line=line,
                column=column or 0,
            )
            return self._format_result(result, "Text inserted")

        elif action == "replace":
            if text is None:
                return "Error: text required for replace action"
            result = await conn.send(
                "replaceText",
                text=text,
                line=line,
                column=column,
                endLine=end_line,
                endColumn=end_column,
            )
            return self._format_result(result, "Text replaced")

        elif action in ("get_text", "text"):
            result = await conn.send(
                "getText",
                line=line,
                endLine=end_line,
            )
            return self._format_result(result)

        # Navigation
        elif action in ("go_to_definition", "definition"):
            if line is None or column is None:
                return "Error: line and column required"
            result = await conn.send(
                "goToDefinition",
                line=line,
                column=column,
            )
            return self._format_result(result)

        elif action in ("find_references", "references"):
            if line is None or column is None:
                return "Error: line and column required"
            result = await conn.send(
                "findReferences",
                line=line,
                column=column,
            )
            return self._format_result(result)

        # Refactoring
        elif action == "rename":
            if new_name is None or line is None or column is None:
                return "Error: new_name, line, and column required"
            result = await conn.send(
                "rename",
                newName=new_name,
                line=line,
                column=column,
            )
            return self._format_result(result, f"Renamed to {new_name}")

        elif action == "format":
            result = await conn.send("formatDocument")
            return self._format_result(result, "Document formatted")

        # Diagnostics
        elif action == "diagnostics":
            result = await conn.send("getDiagnostics", severity=severity)
            return self._format_result(result)

        elif action == "quick_fix":
            if line is None or column is None:
                return "Error: line and column required"
            result = await conn.send(
                "applyQuickFix",
                line=line,
                column=column,
                index=index or 0,
            )
            return self._format_result(result, "Quick fix applied")

        # Commands
        elif action == "command":
            if not command:
                return "Error: command required"
            result = await conn.send(
                "executeCommand",
                command=command,
                args=args or [],
            )
            return self._format_result(result)

        # Terminal
        elif action == "terminal":
            if command:
                result = await conn.send(
                    "sendToTerminal",
                    command=command,
                    name=name,
                )
            else:
                result = await conn.send(
                    "createTerminal",
                    name=name,
                )
            return self._format_result(result)

        # Search
        elif action == "search":
            if not query:
                return "Error: query required"
            result = await conn.send(
                "searchWorkspace",
                query=query,
                include=include,
                exclude=exclude,
            )
            return self._format_result(result)

        else:
            return f"Unknown action: {action}"

    async def _connect(self, ide: str | None) -> str:
        """Connect to IDE."""
        ide_type = IdeType(ide) if ide else None

        if ide_type:
            conn = await self.manager.connect(ide_type)
        else:
            conn = await self.manager.auto_connect()

        if conn and conn.connected:
            return f"Connected to {conn.ide_type.value}"
        return "Failed to connect. Ensure Hanzo IDE extension is installed and running."

    def _status(self) -> str:
        """Get connection status."""
        if not self.manager.connections:
            return "No IDE connections"

        lines = ["IDE Connections:"]
        for ide_type, conn in self.manager.connections.items():
            status = "connected" if conn.connected else "disconnected"
            default = " (default)" if ide_type == self.manager.default_ide else ""
            lines.append(f"  {ide_type.value}: {status}{default}")
            if conn.workspace_path:
                lines.append(f"    Workspace: {conn.workspace_path}")
            if conn.active_file:
                lines.append(f"    Active: {conn.active_file}")

        return "\n".join(lines)

    def _format_result(self, result: dict, success_msg: str | None = None) -> str:
        """Format result from IDE."""
        if "error" in result:
            return f"Error: {result['error']}"

        if success_msg and result.get("success", True):
            return success_msg

        # Format result data
        data = result.get("data") or result.get("result")
        if data:
            if isinstance(data, str):
                return data
            return json.dumps(data, indent=2)

        return str(result)
