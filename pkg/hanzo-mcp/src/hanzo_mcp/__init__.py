"""
Hanzo MCP - Model Context Protocol for Python

This package provides a Python implementation of MCP tools with automatic
fallback to Rust-based tools when available for better performance.

Usage:
    from hanzo_mcp import McpServer, Tool, execute_tool
    
    # Start MCP server
    server = McpServer()
    await server.serve()
    
    # Execute a tool directly
    result = await execute_tool('read_file', {'path': 'example.txt'})
"""

from .bridge import McpBridge, RustBridge, PythonBridge
from .server import McpServer
from .tools import Tool, ToolRegistry, execute_tool
from .types import ToolResult, ToolError, ToolInfo

__version__ = "1.0.0"

__all__ = [
    "McpBridge",
    "RustBridge", 
    "PythonBridge",
    "McpServer",
    "Tool",
    "ToolRegistry",
    "execute_tool",
    "ToolResult",
    "ToolError",
    "ToolInfo",
]