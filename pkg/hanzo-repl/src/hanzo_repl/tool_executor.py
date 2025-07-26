"""Tool executor for running MCP tools based on LLM responses."""

import json
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel

from hanzo_mcp.server import HanzoMCPServer
from .llm_client import LLMClient


class ToolExecutor:
    """Execute MCP tools based on LLM requests."""
    
    def __init__(self, mcp_server: HanzoMCPServer, backend):
        self.mcp_server = mcp_server
        self.backend = backend  # Can be LLMClient or BackendManager
        self.console = Console()
        self.conversation_history = []
        self.max_iterations = 10  # Prevent infinite loops
        
    def get_context(self) -> List[Dict[str, str]]:
        """Get current conversation context."""
        return self.conversation_history.copy()
    
    def reset_context(self):
        """Reset conversation context."""
        self.conversation_history = []
    
    def _format_tools_for_llm(self) -> List[Dict[str, Any]]:
        """Format MCP tools for LLM consumption."""
        tools = []
        
        for tool_name, tool in self.mcp_server.tools.items():
            # Convert MCP tool to OpenAI function format
            tool_spec = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool.description,
                    "parameters": tool.get_schema()
                }
            }
            tools.append(tool_spec)
        
        return tools
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a single MCP tool."""
        if tool_name not in self.mcp_server.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        tool = self.mcp_server.tools[tool_name]
        
        # Display tool execution
        self.console.print(Panel(
            f"[bold cyan]Executing:[/bold cyan] {tool_name}\n"
            f"[dim]Arguments:[/dim] {json.dumps(arguments, indent=2)}",
            border_style="blue"
        ))
        
        # Execute tool
        try:
            result = await tool.execute(**arguments)
            
            # Display result
            if isinstance(result, str) and len(result) > 500:
                # Truncate long results
                display_result = result[:500] + "... (truncated)"
            else:
                display_result = result
            
            self.console.print(Panel(
                f"[bold green]Result:[/bold green]\n{display_result}",
                border_style="green"
            ))
            
            return result
            
        except Exception as e:
            self.console.print(Panel(
                f"[bold red]Error:[/bold red] {str(e)}",
                border_style="red"
            ))
            raise
    
    async def execute_with_tools(self, user_message: str) -> str:
        """Execute a user message with MCP tool support."""
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Get available tools
        tools = self._format_tools_for_llm()
        
        # System prompt
        system_prompt = """You are a helpful AI assistant with access to various tools via the Model Context Protocol (MCP).
You can use these tools to help users with file operations, code execution, searching, and more.

When using tools:
1. Be precise with tool arguments
2. Use tools when they would be helpful
3. Explain what you're doing
4. Handle errors gracefully
5. Provide clear, helpful responses

Available tool categories:
- File operations (read, write, edit, search)
- Shell commands (run_command)
- Code analysis (grep, search)
- Database operations (SQL queries)
- And more...
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            *self.conversation_history
        ]
        
        iterations = 0
        final_response = ""
        
        while iterations < self.max_iterations:
            iterations += 1
            
            # Call backend with tools
            if hasattr(self.backend, 'chat'):
                # Direct backend (BackendManager)
                response_text = await self.backend.chat(
                    messages[-1]["content"],  # Just the last user message
                    tools=tools
                )
                # Create a response object that matches expected format
                from types import SimpleNamespace
                response = SimpleNamespace(
                    choices=[SimpleNamespace(
                        message=SimpleNamespace(
                            content=response_text,
                            tool_calls=None
                        )
                    )]
                )
            else:
                # Legacy LLMClient
                response = await self.backend.chat(
                    messages=messages,
                    tools=tools,
                    tool_choice="auto"
                )
            
            # Extract response
            message = response.choices[0].message
            
            # Check if LLM wants to use tools
            if hasattr(message, 'tool_calls') and message.tool_calls:
                # Add assistant message with tool calls
                messages.append({
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": message.tool_calls
                })
                
                # Execute each tool call
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        arguments = {}
                    
                    try:
                        # Execute tool
                        result = await self._execute_tool(tool_name, arguments)
                        
                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result) if not isinstance(result, str) else result
                        })
                        
                    except Exception as e:
                        # Add error to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": f"Error: {str(e)}"
                        })
                
                # Continue conversation
                continue
            
            else:
                # No tool calls, we have the final response
                final_response = message.content
                
                # Add to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_response
                })
                
                break
        
        if iterations >= self.max_iterations:
            final_response = "Maximum iterations reached. Please try a simpler request."
        
        return final_response