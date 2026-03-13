"""
hanzo-zap - Zero-copy Agent Protocol SDK for Python

1000x faster than MCP/JSON-RPC through binary wire protocol.

Example:
    >>> from hanzo_zap import ZapClient
    >>> async with ZapClient.connect("zap://localhost:9999") as client:
    ...     tools = await client.list_tools()
    ...     result = await client.call_tool("read_file", {"path": "README.md"})
"""

from .types import (
    ApprovalPolicy,
    SandboxPolicy,
    MessageType,
    Tool,
    ToolCall,
    ToolResult,
    ServerInfo,
    ClientInfo,
)
from .client import ZapClient
from .server import ZapServer

__version__ = "0.6.1"
__all__ = [
    "ZapClient",
    "ZapServer",
    "ApprovalPolicy",
    "SandboxPolicy",
    "MessageType",
    "Tool",
    "ToolCall",
    "ToolResult",
    "ServerInfo",
    "ClientInfo",
]
