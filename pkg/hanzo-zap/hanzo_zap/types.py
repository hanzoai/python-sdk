"""
ZAP type definitions matching the Rust implementation.
"""

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any


class ApprovalPolicy(str, Enum):
    """Approval policy for tool execution (from hanzo-protocol)."""

    UNLESS_TRUSTED = "unless-trusted"  # Only auto-approve known-safe reads
    ON_FAILURE = "on-failure"  # Auto-approve, escalate on failure
    ON_REQUEST = "on-request"  # Model decides (default)
    NEVER = "never"  # Never ask


@dataclass
class SandboxPolicy:
    """Sandbox policy for tool execution (from hanzo-protocol)."""

    mode: str  # "danger-full-access", "read-only", "workspace-write"
    writable_roots: list[str] = field(default_factory=list)
    network_access: bool = False
    allow_git_writes: bool = False

    @classmethod
    def danger_full_access(cls) -> "SandboxPolicy":
        return cls(mode="danger-full-access")

    @classmethod
    def read_only(cls) -> "SandboxPolicy":
        return cls(mode="read-only")

    @classmethod
    def workspace_write(
        cls,
        writable_roots: list[str] | None = None,
        network_access: bool = False,
        allow_git_writes: bool = False,
    ) -> "SandboxPolicy":
        return cls(
            mode="workspace-write",
            writable_roots=writable_roots or [],
            network_access=network_access,
            allow_git_writes=allow_git_writes,
        )


class MessageType(IntEnum):
    """Wire protocol message types."""

    # Handshake
    INIT = 0x01
    INIT_ACK = 0x02

    # Tools
    LIST_TOOLS = 0x10
    LIST_TOOLS_RESPONSE = 0x11
    CALL_TOOL = 0x12
    CALL_TOOL_RESPONSE = 0x13

    # Resources
    LIST_RESOURCES = 0x20
    LIST_RESOURCES_RESPONSE = 0x21
    READ_RESOURCE = 0x22
    READ_RESOURCE_RESPONSE = 0x23

    # Prompts
    LIST_PROMPTS = 0x30
    LIST_PROMPTS_RESPONSE = 0x31
    GET_PROMPT = 0x32
    GET_PROMPT_RESPONSE = 0x33

    # Control
    PING = 0xF0
    PONG = 0xF1
    ERROR = 0xFF


@dataclass
class Tool:
    """Tool definition."""

    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCall:
    """Tool call request."""

    id: str
    name: str
    args: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] | None = None


@dataclass
class ToolResult:
    """Tool execution result."""

    id: str
    content: Any = None
    error: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class ServerInfo:
    """Server capabilities and info."""

    name: str
    version: str
    capabilities: dict[str, bool] = field(
        default_factory=lambda: {"tools": True, "resources": False, "prompts": False}
    )


@dataclass
class ClientInfo:
    """Client info sent during handshake."""

    name: str
    version: str


@dataclass
class Resource:
    """Resource definition."""

    uri: str
    name: str
    description: str | None = None
    mime_type: str | None = None


@dataclass
class Prompt:
    """Prompt definition."""

    name: str
    description: str | None = None
    arguments: list[dict[str, Any]] | None = None
