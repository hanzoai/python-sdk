"""Enhanced tool system with MCP (Model Context Protocol) support."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol

from .exceptions import AgentsException
from .logger import logger
from .run_context import RunContextWrapper
from .tool import FunctionTool, Tool, function_tool


class MCPServer(Protocol):
    """Protocol for MCP server implementations."""
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server."""
        ...
        
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server."""
        ...


@dataclass
class MCPTool(Tool):
    """A tool that delegates to an MCP server."""
    
    name: str
    """Tool name as exposed by MCP server."""
    
    description: str
    """Tool description."""
    
    parameters_schema: Dict[str, Any]
    """JSON schema for parameters."""
    
    server: MCPServer
    """The MCP server instance."""
    
    async def execute(self, arguments: Dict[str, Any]) -> Any:
        """Execute the tool via MCP server."""
        return await self.server.call_tool(self.name, arguments)


class MCPToolAdapter:
    """Adapts MCP tools to work with the agent framework."""
    
    def __init__(self, server: MCPServer):
        """Initialize adapter with MCP server.
        
        Args:
            server: MCP server instance
        """
        self.server = server
        self._tools_cache: List[Tool] | None = None
        
    async def get_tools(self) -> List[Tool]:
        """Get all tools from the MCP server as agent tools."""
        if self._tools_cache is not None:
            return self._tools_cache
            
        mcp_tools = await self.server.list_tools()
        tools = []
        
        for tool_def in mcp_tools:
            # Create FunctionTool wrapper
            tool = self._create_tool_wrapper(tool_def)
            tools.append(tool)
            
        self._tools_cache = tools
        return tools
        
    def _create_tool_wrapper(self, tool_def: Dict[str, Any]) -> FunctionTool:
        """Create a FunctionTool wrapper for an MCP tool."""
        name = tool_def["name"]
        description = tool_def.get("description", "")
        parameters = tool_def.get("inputSchema", {})
        
        async def tool_function(ctx: RunContextWrapper[Any], **kwargs) -> str:
            # Call MCP server
            result = await self.server.call_tool(name, kwargs)
            
            # Convert result to string
            if isinstance(result, str):
                return result
            return json.dumps(result)
            
        # Create function tool
        return FunctionTool(
            name=name,
            description=description,
            params_json_schema=parameters,
            on_invoke_tool=lambda ctx, args: tool_function(ctx, **json.loads(args)),
        )
        
    async def refresh_tools(self) -> None:
        """Refresh the tools cache."""
        self._tools_cache = None


class CompositeTool(Tool):
    """A tool that combines multiple sub-tools."""
    
    def __init__(
        self,
        name: str,
        description: str,
        tools: List[Tool],
        orchestrator: Callable[[str, List[Tool]], Tool] | None = None,
    ):
        """Initialize composite tool.
        
        Args:
            name: Tool name
            description: Tool description
            tools: List of sub-tools
            orchestrator: Optional function to select which tool to use
        """
        self.name = name
        self.description = description
        self.tools = tools
        self.orchestrator = orchestrator or self._default_orchestrator
        
    def _default_orchestrator(self, input: str, tools: List[Tool]) -> Tool:
        """Default orchestrator - just uses the first tool."""
        if not tools:
            raise AgentsException("No tools available")
        return tools[0]
        
    async def execute(self, ctx: RunContextWrapper[Any], input: str) -> str:
        """Execute the composite tool."""
        # Select tool to use
        selected_tool = self.orchestrator(input, self.tools)
        
        # Execute selected tool
        if isinstance(selected_tool, FunctionTool):
            return await selected_tool.on_invoke_tool(ctx, input)
        else:
            raise AgentsException(f"Cannot execute tool type: {type(selected_tool)}")


class ToolRegistry:
    """Registry for managing tools across the system."""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._categories: Dict[str, List[str]] = {}
        self._mcp_adapters: List[MCPToolAdapter] = []
        
    def register(self, tool: Tool, category: str = "general") -> None:
        """Register a tool.
        
        Args:
            tool: Tool to register
            category: Tool category
        """
        if tool.name in self._tools:
            raise AgentsException(f"Tool '{tool.name}' already registered")
            
        self._tools[tool.name] = tool
        
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(tool.name)
        
        logger.debug(f"Registered tool '{tool.name}' in category '{category}'")
        
    def unregister(self, name: str) -> None:
        """Unregister a tool."""
        if name not in self._tools:
            return
            
        del self._tools[name]
        
        # Remove from categories
        for category, tools in self._categories.items():
            if name in tools:
                tools.remove(name)
                
    def get(self, name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(name)
        
    def list(self, category: str | None = None) -> List[Tool]:
        """List tools, optionally filtered by category."""
        if category:
            tool_names = self._categories.get(category, [])
            return [self._tools[name] for name in tool_names if name in self._tools]
        return list(self._tools.values())
        
    def categories(self) -> List[str]:
        """List all categories."""
        return list(self._categories.keys())
        
    async def add_mcp_server(self, server: MCPServer) -> None:
        """Add an MCP server to the registry.
        
        Args:
            server: MCP server to add
        """
        adapter = MCPToolAdapter(server)
        self._mcp_adapters.append(adapter)
        
        # Load tools from server
        tools = await adapter.get_tools()
        for tool in tools:
            self.register(tool, category="mcp")
            
    async def refresh_mcp_tools(self) -> None:
        """Refresh tools from all MCP servers."""
        # Remove existing MCP tools
        mcp_tools = self._categories.get("mcp", [])
        for tool_name in mcp_tools:
            self.unregister(tool_name)
            
        # Reload from all adapters
        for adapter in self._mcp_adapters:
            await adapter.refresh_tools()
            tools = await adapter.get_tools()
            for tool in tools:
                self.register(tool, category="mcp")


# Global tool registry
_global_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return _global_registry


def register_tool(tool: Tool, category: str = "general") -> None:
    """Register a tool in the global registry."""
    _global_registry.register(tool, category)


def tool_from_function(
    func: Callable,
    name: str | None = None,
    description: str | None = None,
    category: str = "general",
) -> FunctionTool:
    """Create and register a tool from a function.
    
    Args:
        func: Function to wrap
        name: Tool name (defaults to function name)
        description: Tool description
        category: Tool category
        
    Returns:
        The created tool
    """
    tool = function_tool(
        func=func,
        name_override=name,
        description_override=description,
    )
    
    register_tool(tool, category)
    return tool


class ToolChain:
    """Chain multiple tools together."""
    
    def __init__(self, tools: List[Tool]):
        """Initialize tool chain.
        
        Args:
            tools: Tools to chain in order
        """
        self.tools = tools
        
    async def execute(
        self,
        ctx: RunContextWrapper[Any],
        input: Any,
    ) -> Any:
        """Execute the tool chain.
        
        Args:
            ctx: Execution context
            input: Initial input
            
        Returns:
            Final output after all tools
        """
        current_input = input
        
        for tool in self.tools:
            if isinstance(tool, FunctionTool):
                # Convert input to JSON string for function tools
                json_input = json.dumps(current_input) if not isinstance(current_input, str) else current_input
                output = await tool.on_invoke_tool(ctx, json_input)
                
                # Try to parse output as JSON
                try:
                    current_input = json.loads(output)
                except json.JSONDecodeError:
                    current_input = output
            else:
                # For other tool types, pass through
                current_input = str(current_input)
                
        return current_input
        
    def __add__(self, other: Tool | ToolChain) -> ToolChain:
        """Add another tool or chain."""
        if isinstance(other, ToolChain):
            return ToolChain(self.tools + other.tools)
        else:
            return ToolChain(self.tools + [other])


@dataclass
class ToolMetrics:
    """Metrics for tool execution."""
    
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_duration: float = 0.0
    last_error: str | None = None
    last_call_time: float | None = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls
        
    @property
    def average_duration(self) -> float:
        """Calculate average duration."""
        if self.successful_calls == 0:
            return 0.0
        return self.total_duration / self.successful_calls


class MonitoredTool(Tool):
    """Wrapper that adds monitoring to any tool."""
    
    def __init__(self, tool: Tool):
        """Initialize monitored tool.
        
        Args:
            tool: Tool to monitor
        """
        self.tool = tool
        self.metrics = ToolMetrics()
        
    @property
    def name(self) -> str:
        """Get tool name."""
        return self.tool.name
        
    async def execute(self, ctx: RunContextWrapper[Any], input: str) -> str:
        """Execute with monitoring."""
        import time
        
        start_time = time.time()
        self.metrics.total_calls += 1
        self.metrics.last_call_time = start_time
        
        try:
            if isinstance(self.tool, FunctionTool):
                result = await self.tool.on_invoke_tool(ctx, input)
            else:
                raise AgentsException(f"Cannot monitor tool type: {type(self.tool)}")
                
            # Success
            self.metrics.successful_calls += 1
            self.metrics.total_duration += time.time() - start_time
            
            return result
            
        except Exception as e:
            # Failure
            self.metrics.failed_calls += 1
            self.metrics.last_error = str(e)
            raise