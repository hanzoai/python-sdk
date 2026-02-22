"""
Unified REPL Tool with Multi-Language Jupyter Kernel Support.

Provides persistent interactive sessions for code evaluation across languages.
Uses Jupyter kernels as backend for consistent cross-language experience.
"""

from __future__ import annotations

import uuid
import asyncio
from typing import Any
from datetime import datetime
from dataclasses import field, dataclass

# Jupyter client imports
try:
    from jupyter_client import KernelManager as JupyterKernelManager
    from jupyter_client.asynchronous import AsyncKernelClient

    JUPYTER_AVAILABLE = True
except ImportError:
    JUPYTER_AVAILABLE = False
    JupyterKernelManager = None
    AsyncKernelClient = None

from hanzo_tools.core import BaseTool

# Language to kernel mapping
LANGUAGE_KERNELS: dict[str, str] = {
    # Python variants
    "python": "python3",
    "python3": "python3",
    "py": "python3",
    "ipython": "python3",
    # JavaScript/TypeScript
    "javascript": "tslab",
    "js": "tslab",
    "typescript": "tslab",
    "ts": "tslab",
    "node": "tslab",
    # Shell
    "bash": "bash",
    "sh": "bash",
    "shell": "bash",
    "zsh": "bash",
    # Other languages (require kernel installation)
    "ruby": "ruby",
    "go": "gophernotes",
    "rust": "evcxr",
    "julia": "julia-1.10",
    "r": "ir",
}


@dataclass
class ExecutionResult:
    """Result of code execution."""

    success: bool
    output: str
    error: str | None = None
    execution_count: int = 0
    data: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0


@dataclass
class KernelSession:
    """Represents an active kernel session."""

    id: str
    language: str
    kernel_name: str
    manager: Any  # JupyterKernelManager
    client: Any  # AsyncKernelClient
    created_at: datetime = field(default_factory=datetime.now)
    execution_count: int = 0
    history: list[tuple[str, ExecutionResult]] = field(default_factory=list)


class KernelManager:
    """Manages multiple Jupyter kernel sessions."""

    _instance: KernelManager | None = None

    def __init__(self) -> None:
        self.sessions: dict[str, KernelSession] = {}
        self.default_session: str | None = None
        self._lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> KernelManager:
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def start_kernel(
        self,
        language: str = "python",
        session_id: str | None = None,
    ) -> KernelSession:
        """Start a new kernel session."""
        if not JUPYTER_AVAILABLE:
            raise RuntimeError(
                "jupyter-client not installed. Install with: pip install hanzo-tools-repl[full]"
            )

        kernel_name = LANGUAGE_KERNELS.get(language.lower(), language)
        session_id = session_id or f"{language}_{uuid.uuid4().hex[:8]}"

        async with self._lock:
            if session_id in self.sessions:
                return self.sessions[session_id]

            # Create kernel manager
            km = JupyterKernelManager(kernel_name=kernel_name)
            km.start_kernel()

            # Get async client
            client = km.client()
            client.start_channels()

            # Wait for kernel ready
            await asyncio.sleep(0.5)

            session = KernelSession(
                id=session_id,
                language=language,
                kernel_name=kernel_name,
                manager=km,
                client=client,
            )

            self.sessions[session_id] = session

            if self.default_session is None:
                self.default_session = session_id

            return session

    async def execute(
        self,
        code: str,
        session_id: str | None = None,
        timeout: float = 30.0,
    ) -> ExecutionResult:
        """Execute code in a kernel session."""
        session_id = session_id or self.default_session

        if not session_id or session_id not in self.sessions:
            # Auto-start default Python kernel
            session = await self.start_kernel("python")
            session_id = session.id

        session = self.sessions[session_id]
        start_time = datetime.now()

        try:
            # Execute code
            msg_id = session.client.execute(code)

            output_parts: list[str] = []
            error_output: str | None = None
            data: dict[str, Any] = {}

            # Collect results
            while True:
                try:
                    msg = await asyncio.wait_for(
                        asyncio.to_thread(
                            session.client.get_iopub_msg, timeout=timeout
                        ),
                        timeout=timeout,
                    )
                except asyncio.TimeoutError:
                    break

                msg_type = msg.get("msg_type", "")
                content = msg.get("content", {})

                if msg_type == "stream":
                    output_parts.append(content.get("text", ""))

                elif msg_type == "execute_result":
                    data = content.get("data", {})
                    if "text/plain" in data:
                        output_parts.append(data["text/plain"])

                elif msg_type == "display_data":
                    data.update(content.get("data", {}))
                    if "text/plain" in data:
                        output_parts.append(data["text/plain"])

                elif msg_type == "error":
                    error_output = "\n".join(content.get("traceback", []))

                elif msg_type == "status":
                    if content.get("execution_state") == "idle":
                        break

            duration = (datetime.now() - start_time).total_seconds() * 1000
            session.execution_count += 1

            result = ExecutionResult(
                success=error_output is None,
                output="".join(output_parts),
                error=error_output,
                execution_count=session.execution_count,
                data=data,
                duration_ms=duration,
            )

            # Add to history
            session.history.append((code, result))

            return result

        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
            )

    async def stop_kernel(self, session_id: str | None = None) -> bool:
        """Stop a kernel session."""
        session_id = session_id or self.default_session

        if not session_id or session_id not in self.sessions:
            return False

        async with self._lock:
            session = self.sessions.pop(session_id)
            session.client.stop_channels()
            session.manager.shutdown_kernel()

            if self.default_session == session_id:
                self.default_session = next(iter(self.sessions), None)

            return True

    async def stop_all(self) -> int:
        """Stop all kernel sessions."""
        count = len(self.sessions)
        for session_id in list(self.sessions.keys()):
            await self.stop_kernel(session_id)
        return count

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all active sessions."""
        return [
            {
                "id": s.id,
                "language": s.language,
                "kernel": s.kernel_name,
                "created": s.created_at.isoformat(),
                "executions": s.execution_count,
                "is_default": s.id == self.default_session,
            }
            for s in self.sessions.values()
        ]

    def get_history(
        self,
        session_id: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get execution history for a session."""
        session_id = session_id or self.default_session

        if not session_id or session_id not in self.sessions:
            return []

        session = self.sessions[session_id]
        history = session.history[-limit:]

        return [
            {
                "index": i + 1,
                "code": code,
                "success": result.success,
                "output": result.output[:500] if result.output else None,
                "error": result.error[:200] if result.error else None,
            }
            for i, (code, result) in enumerate(history)
        ]

    @staticmethod
    def list_available_kernels() -> list[dict[str, str]]:
        """List available Jupyter kernels."""
        if not JUPYTER_AVAILABLE:
            return []

        try:
            from jupyter_client.kernelspec import find_kernel_specs

            specs = find_kernel_specs()
            return [{"name": name, "path": path} for name, path in specs.items()]
        except Exception:
            return []


class ReplTool(BaseTool):
    """
    Multi-language REPL with Jupyter kernel backend.

    Provides interactive code evaluation for agents across languages:
    - Python, Node.js/TypeScript, Bash, and any Jupyter kernel

    Actions:
    - start: Start a new kernel session
    - eval: Execute code in a session
    - stop: Stop a kernel session
    - list: List active sessions
    - history: Get execution history
    - kernels: List available kernels

    Examples:
        repl(action="start", language="python")
        repl(action="eval", code="x = 1 + 1; print(x)")
        repl(action="eval", code="console.log('hello')", language="node")
        repl(action="history", limit=10)
        repl(action="stop")
    """

    name = "repl"

    @property
    def description(self) -> str:
        return """Multi-language REPL with persistent Jupyter kernel sessions.

ACTIONS:
- start: Start kernel (language: python|node|typescript|bash|ruby|go|rust)
- eval: Execute code (code: string, language?: string, session?: string)
- stop: Stop kernel (session?: string)
- list: List active sessions
- history: Get execution history (session?: string, limit?: int)
- kernels: List available Jupyter kernels

LANGUAGES: python, node/javascript/typescript, bash/shell, ruby, go, rust

EXAMPLES:
  repl(action="start", language="python")
  repl(action="eval", code="print('hello')")
  repl(action="eval", code="const x = [1,2,3].map(n => n*2)", language="node")
  repl(action="history")
  repl(action="stop")"""

    def __init__(self) -> None:
        super().__init__()
        self.manager = KernelManager.get_instance()

    async def call(
        self,
        action: str = "eval",
        code: str | None = None,
        language: str = "python",
        session: str | None = None,
        limit: int = 20,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> str:
        """Execute REPL action."""

        action = action.lower()

        if action == "start":
            return await self._start(language, session)

        elif action in ("eval", "execute", "run"):
            if not code:
                return "Error: code parameter required for eval action"
            return await self._eval(code, language, session, timeout)

        elif action == "stop":
            return await self._stop(session)

        elif action == "list":
            return self._list()

        elif action == "history":
            return self._history(session, limit)

        elif action == "kernels":
            return self._kernels()

        else:
            return f"Unknown action: {action}. Use: start, eval, stop, list, history, kernels"

    async def _start(self, language: str, session_id: str | None) -> str:
        """Start a new kernel session."""
        try:
            session = await self.manager.start_kernel(language, session_id)
            return f"""Kernel started:
  Session: {session.id}
  Language: {session.language}
  Kernel: {session.kernel_name}

Use repl(action="eval", code="...") to execute code."""
        except Exception as e:
            return f"Error starting kernel: {e}"

    async def _eval(
        self,
        code: str,
        language: str,
        session_id: str | None,
        timeout: float,
    ) -> str:
        """Execute code in a session."""
        # Auto-start kernel if needed
        if not self.manager.sessions:
            await self.manager.start_kernel(language)
        elif session_id is None and language != "python":
            # Start language-specific kernel if not exists
            lang_sessions = [
                s
                for s in self.manager.sessions.values()
                if s.language.lower() == language.lower()
            ]
            if not lang_sessions:
                await self.manager.start_kernel(language)

        result = await self.manager.execute(code, session_id, timeout)

        if result.success:
            output = result.output or "(no output)"
            return f"""[{result.execution_count}] {output}"""
        else:
            return f"""[{result.execution_count}] Error:
{result.error}"""

    async def _stop(self, session_id: str | None) -> str:
        """Stop a kernel session."""
        if session_id == "all":
            count = await self.manager.stop_all()
            return f"Stopped {count} kernel(s)"

        success = await self.manager.stop_kernel(session_id)
        if success:
            return f"Kernel stopped: {session_id or 'default'}"
        return "No active kernel to stop"

    def _list(self) -> str:
        """List active sessions."""
        sessions = self.manager.list_sessions()
        if not sessions:
            return "No active REPL sessions"

        lines = ["Active REPL sessions:"]
        for s in sessions:
            default = " (default)" if s["is_default"] else ""
            lines.append(
                f"  {s['id']}: {s['language']} ({s['kernel']}) - {s['executions']} executions{default}"
            )
        return "\n".join(lines)

    def _history(self, session_id: str | None, limit: int) -> str:
        """Get execution history."""
        history = self.manager.get_history(session_id, limit)
        if not history:
            return "No execution history"

        lines = ["Execution history:"]
        for h in history:
            status = "OK" if h["success"] else "ERR"
            code_preview = h["code"][:50].replace("\n", "\\n")
            if len(h["code"]) > 50:
                code_preview += "..."
            lines.append(f"  [{h['index']}] {status}: {code_preview}")
        return "\n".join(lines)

    def _kernels(self) -> str:
        """List available kernels."""
        kernels = self.manager.list_available_kernels()
        if not kernels:
            return "No Jupyter kernels found. Install with: pip install ipykernel"

        lines = ["Available Jupyter kernels:"]
        for k in kernels:
            lines.append(f"  {k['name']}")

        lines.append("\nSupported language aliases:")
        for lang, kernel in sorted(set((v, k) for k, v in LANGUAGE_KERNELS.items())):
            aliases = [k for k, v in LANGUAGE_KERNELS.items() if v == lang]
            lines.append(f"  {lang}: {', '.join(aliases)}")

        return "\n".join(lines)
