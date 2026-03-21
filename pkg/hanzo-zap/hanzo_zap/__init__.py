"""
hanzo-zap - Zero-copy Agent Protocol SDK for Python

1000x faster than MCP/JSON-RPC through binary wire protocol.
Includes PlaygroundClient for the Hanzo Playground control plane.

Example:
    >>> from hanzo_zap import ZapClient
    >>> async with ZapClient.connect("zap://localhost:9999") as client:
    ...     tools = await client.list_tools()
    ...     result = await client.call_tool("read_file", {"path": "README.md"})
"""

from .types import (
    AgentEvent,
    AgentInfo,
    ApprovalPolicy,
    ClientInfo,
    CommitInfo,
    EventMsg,
    FileChange,
    MessageType,
    RealtimeAudioFrame,
    SandboxPolicy,
    ServerInfo,
    Submission,
    Tool,
    ToolCall,
    ToolResult,
)
from .client import ZapClient
from .server import ZapServer
from .playground import PlaygroundClient

__version__ = "0.7.0"
__all__ = [
    # Wire protocol
    "ZapClient",
    "ZapServer",
    # Playground
    "PlaygroundClient",
    # Core types
    "ApprovalPolicy",
    "ClientInfo",
    "MessageType",
    "SandboxPolicy",
    "ServerInfo",
    "Tool",
    "ToolCall",
    "ToolResult",
    # Playground types
    "AgentEvent",
    "AgentInfo",
    "CommitInfo",
    "EventMsg",
    "FileChange",
    "RealtimeAudioFrame",
    "Submission",
]
