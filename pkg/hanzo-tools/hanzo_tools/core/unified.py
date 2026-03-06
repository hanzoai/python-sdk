"""Base tool class for HIP-0300 architecture.

Provides the foundation for orthogonal, composable tools following Unix philosophy:
- Permissive input, strict output
- Action routing with alias resolution
- Unified response envelope with ok/data/error/meta
- Built-in help and schema actions
- Typed error codes with Unix exit code semantics
- Paging/cursor support for large results
- Composable via stable identifiers (uri, hash, range, ref)

Design principles:
- Input parsing = permissive (accept many spellings/forms)
- Output + semantics = strict (one canonical shape)
- Aliases never appear in output; only canonical action names

Reference: HIP-0300 Unified MCP Tools Architecture
"""

import json
import hashlib
import inspect
from abc import abstractmethod
from typing import Any, Literal, TypeVar, Callable, ClassVar, get_type_hints
from dataclasses import field, dataclass
from collections.abc import Awaitable

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from .base import BaseTool as _BaseToolABC

# Error codes for structured error handling
ErrorCode = Literal[
    "UNKNOWN_ACTION",  # Action not found
    "INVALID_PARAMS",  # Invalid parameters
    "NOT_FOUND",  # Resource not found
    "CONFLICT",  # Precondition failed (e.g., base_hash mismatch)
    "PERMISSION_DENIED",  # Access denied
    "TIMEOUT",  # Operation timed out
    "INTERNAL_ERROR",  # Unexpected error
]


@dataclass
class Paging:
    """Pagination info for large results."""

    cursor: str | None = None
    more: bool = False
    total: int | None = None


@dataclass
class ToolError(Exception):
    """Structured error for tool operations."""

    code: ErrorCode
    message: str
    details: dict[str, Any] = field(default_factory=dict)


class ConflictError(ToolError):
    """Precondition failed (e.g., base_hash mismatch)."""

    def __init__(
        self, message: str, expected: str | None = None, actual: str | None = None
    ):
        details = {}
        if expected:
            details["expected"] = expected
        if actual:
            details["actual"] = actual
        super().__init__(code="CONFLICT", message=message, details=details)


class NotFoundError(ToolError):
    """Resource not found."""

    def __init__(self, message: str, uri: str | None = None):
        details = {"uri": uri} if uri else {}
        super().__init__(code="NOT_FOUND", message=message, details=details)


class InvalidParamsError(ToolError):
    """Invalid parameters."""

    def __init__(
        self, message: str, param: str | None = None, expected: str | None = None
    ):
        details = {}
        if param:
            details["param"] = param
        if expected:
            details["expected"] = expected
        super().__init__(code="INVALID_PARAMS", message=message, details=details)


@dataclass
class ActionHandler:
    """Metadata for a registered action handler."""

    name: str
    handler: Callable[..., Awaitable[Any]]
    description: str
    schema: dict[str, Any] | None = None
    examples: list[str] = field(default_factory=list)


class BaseTool(_BaseToolABC):
    """Base class for HIP-0300 unified tools with action routing.

    Design principles:
    - Permissive input, strict output
    - Action routing with alias resolution
    - Unified response envelope: {ok, data, error, meta}
    - Aliases never appear in output; only canonical action names

    Usage:
        class FsTool(BaseTool):
            name = "fs"
            description = "Filesystem operations"

            def __init__(self):
                super().__init__()
                self._register_actions()

            def _register_actions(self):
                @self.action("read", "Read file contents")
                async def read(ctx, uri: str, range: dict | None = None) -> dict:
                    content = await read_file(uri)
                    return {"text": content, "hash": hash_content(content)}

                @self.action("apply_patch", "Edit file with precondition")
                async def apply_patch(ctx, uri: str, patch: str, base_hash: str) -> dict:
                    if get_hash(uri) != base_hash:
                        raise ConflictError("base_hash mismatch", expected=base_hash)
                    # Apply patch...
                    return {"uri": uri, "hash": new_hash}
    """

    # Subclasses must define these
    name: ClassVar[str]

    # Version for meta envelope
    VERSION: ClassVar[str] = "0.12.0"

    def __init__(self):
        self._handlers: dict[str, ActionHandler] = {}
        self._register_builtin_actions()

    def _register_builtin_actions(self):
        """Register built-in help and schema actions."""

        @self.action("help", "List available actions with descriptions")
        async def help_action(ctx: MCPContext) -> dict:
            actions = {}
            for name, handler in self._handlers.items():
                if name not in ("help", "schema", "status"):
                    actions[name] = {
                        "description": handler.description,
                        "examples": handler.examples,
                    }
            return {"actions": actions, "tool": self.name}

        @self.action("schema", "Get JSON Schema for action parameters")
        async def schema_action(
            ctx: MCPContext, action_name: str | None = None
        ) -> dict:
            if action_name:
                handler = self._handlers.get(action_name)
                if not handler:
                    raise ToolError(
                        code="UNKNOWN_ACTION",
                        message=f"Unknown action: {action_name}",
                        details={"available": list(self._handlers.keys())},
                    )
                return {"action": action_name, "schema": handler.schema or {}}

            schemas = {}
            for name, handler in self._handlers.items():
                if name not in ("help", "schema", "status"):
                    schemas[name] = handler.schema or {}
            return {"schemas": schemas}

        @self.action("status", "Get tool status and version")
        async def status_action(ctx: MCPContext) -> dict:
            return {
                "tool": self.name,
                "version": self.VERSION,
                "enabled": True,
                "actions": list(self._handlers.keys()),
            }

    def action(
        self,
        name: str,
        description: str = "",
        schema: dict[str, Any] | None = None,
        examples: list[str] | None = None,
    ) -> Callable:
        """Decorator to register an action handler.

        Args:
            name: Action name (e.g., "read", "apply_patch")
            description: Human-readable description
            schema: Optional JSON Schema for parameters
            examples: Optional list of example usages

        Returns:
            Decorator function
        """

        def decorator(
            fn: Callable[..., Awaitable[Any]],
        ) -> Callable[..., Awaitable[Any]]:
            # Auto-generate schema from type hints if not provided
            auto_schema = schema
            if auto_schema is None:
                auto_schema = self._generate_schema(fn)

            self._handlers[name] = ActionHandler(
                name=name,
                handler=fn,
                description=description or fn.__doc__ or "",
                schema=auto_schema,
                examples=examples or [],
            )
            return fn

        return decorator

    def _generate_schema(self, fn: Callable) -> dict[str, Any]:
        """Generate JSON Schema from function signature and type hints."""
        try:
            hints = get_type_hints(fn)
        except Exception:
            hints = {}

        sig = inspect.signature(fn)
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "ctx"):
                continue

            param_schema: dict[str, Any] = {}
            hint = hints.get(param_name)

            if hint is str:
                param_schema["type"] = "string"
            elif hint is int:
                param_schema["type"] = "integer"
            elif hint is float:
                param_schema["type"] = "number"
            elif hint is bool:
                param_schema["type"] = "boolean"
            elif hint is dict or (
                hasattr(hint, "__origin__") and hint.__origin__ is dict
            ):
                param_schema["type"] = "object"
            elif hint is list or (
                hasattr(hint, "__origin__") and hint.__origin__ is list
            ):
                param_schema["type"] = "array"
            else:
                param_schema["type"] = "string"  # Default to string

            properties[param_name] = param_schema

            if param.default is inspect.Parameter.empty:
                required.append(param_name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    def _envelope(
        self,
        data: Any,
        action: str | None = None,
        paging: Paging | None = None,
        backend: str | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Wrap result in unified response envelope."""
        meta: dict[str, Any] = {
            "tool": self.name,
            "version": self.VERSION,
        }
        if action:
            meta["action"] = action
        if backend:
            meta["backend"] = backend
        if trace_id:
            meta["trace_id"] = trace_id

        if paging:
            meta["paging"] = {
                "cursor": paging.cursor,
                "more": paging.more,
            }
            if paging.total is not None:
                meta["paging"]["total"] = paging.total
        else:
            meta["paging"] = {"cursor": None, "more": False}

        return {
            "ok": True,
            "data": data,
            "error": None,
            "meta": meta,
        }

    def _error(
        self,
        code: ErrorCode,
        message: str,
        **details: Any,
    ) -> dict[str, Any]:
        """Create error response envelope."""
        error_dict: dict[str, Any] = {
            "code": code,
            "message": message,
        }
        if details:
            error_dict.update(details)

        return {
            "ok": False,
            "data": None,
            "error": error_dict,
            "meta": {"tool": self.name, "version": self.VERSION},
        }

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for MCP registration."""
        pass

    async def call(
        self, ctx: MCPContext, action: str = "help", **kwargs: Any
    ) -> dict[str, Any]:
        """Execute tool with action routing.

        Args:
            ctx: MCP context
            action: Action to execute (default: "help")
            **kwargs: Action parameters

        Returns:
            Unified response envelope
        """
        if action not in self._handlers:
            return self._error(
                "UNKNOWN_ACTION",
                f"Unknown action: {action}",
                available=list(self._handlers.keys()),
            )

        handler = self._handlers[action]

        try:
            result = await handler.handler(ctx, **kwargs)
            return self._envelope(result, action=action)
        except ToolError as e:
            return self._error(e.code, e.message, **e.details)
        except Exception as e:
            return self._error("INTERNAL_ERROR", str(e))

    def register(self, mcp_server: FastMCP) -> None:
        """Register this tool with the MCP server.

        Creates a single MCP tool with action parameter for routing.
        """
        tool_name = self.name
        tool_description = (
            f"{self.description}\n\nActions: {', '.join(self._handlers.keys())}"
        )

        @mcp_server.tool(name=tool_name, description=tool_description)
        async def handler(
            ctx: MCPContext,
            action: str = "help",
            **kwargs: Any,
        ) -> str:
            result = await self.call(ctx, action=action, **kwargs)
            return json.dumps(result, indent=2, default=str)


# Utility functions for composability


def content_hash(content: str | bytes, algorithm: str = "sha256") -> str:
    """Generate content hash for file identity."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    h = hashlib.new(algorithm)
    h.update(content)
    return f"{algorithm}:{h.hexdigest()}"


def file_uri(path: str) -> str:
    """Convert path to file:// URI."""
    from pathlib import Path

    abs_path = Path(path).resolve()
    return f"file://{abs_path}"


@dataclass
class Range:
    """Text range for composability.

    0-based line and column numbers.
    """

    start_line: int
    start_col: int = 0
    end_line: int | None = None
    end_col: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict format for serialization."""
        result = {
            "start": {"line": self.start_line, "col": self.start_col},
        }
        if self.end_line is not None:
            result["end"] = {
                "line": self.end_line,
                "col": self.end_col or 0,
            }
        return result

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Range":
        """Create Range from dict."""
        start = d.get("start", {})
        end = d.get("end")
        return cls(
            start_line=start.get("line", 0),
            start_col=start.get("col", 0),
            end_line=end.get("line") if end else None,
            end_col=end.get("col") if end else None,
        )
