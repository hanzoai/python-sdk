"""Tool executor for running MCP tools based on LLM responses."""

import json
import logging
from typing import Any, Dict, List, Optional

from hanzo_mcp.server import HanzoMCPServer
from hanzoai.mcp import MCPClient, MCPClientError
from hanzoai.protocols import (
    PermissionMode,
    PermissionOutcome,
    PermissionPolicy,
    PermissionPrompter,
    PermissionRequest,
    TokenUsage,
    UsageTracker,
)
from rich.console import Console
from rich.panel import Panel

logger = logging.getLogger(__name__)


class _DefaultPrompter:
    """Prompter that allows everything (bypass mode)."""

    def decide(self, request: PermissionRequest) -> PermissionOutcome:
        return PermissionOutcome.allow()


class ToolExecutor:
    """Execute MCP tools based on LLM requests."""

    def __init__(
        self,
        mcp_server: HanzoMCPServer,
        backend,
        permission_policy: Optional[PermissionPolicy] = None,
        prompter: Optional[PermissionPrompter] = None,
    ):
        self.mcp_server = mcp_server
        self.backend = backend  # Can be LLMClient or BackendManager
        self.console = Console()
        self.conversation_history = []
        self.max_iterations = 10  # Prevent infinite loops
        self.permission_policy = permission_policy or PermissionPolicy(
            default_mode=PermissionMode.Allow,
        )
        self.prompter = prompter or _DefaultPrompter()
        self.usage_tracker = UsageTracker()
        self._mcp_clients: dict[str, MCPClient] = {}
        self._mcp_tools: dict[str, dict[str, Any]] = {}  # server_name -> {tool_name: schema}

    # -- MCP client management ------------------------------------------------

    async def register_mcp_server(
        self,
        server_name: str,
        command: list[str],
        env: dict[str, str] | None = None,
    ) -> int:
        """Connect to an MCP server subprocess via stdio and register its tools.

        Returns the number of tools discovered.
        """
        client = MCPClient(server_command=command, env=env)
        try:
            await client.connect()
        except MCPClientError as exc:
            logger.warning("Failed to connect to MCP server %s: %s", server_name, exc)
            return 0

        tools = await client.list_tools()
        self._mcp_clients[server_name] = client
        self._mcp_tools[server_name] = {t["name"]: t for t in tools}
        return len(tools)

    async def disconnect_mcp_servers(self) -> None:
        """Disconnect all registered MCP server clients."""
        for client in self._mcp_clients.values():
            try:
                await client.disconnect()
            except Exception:
                pass
        self._mcp_clients.clear()
        self._mcp_tools.clear()

    # -- Context management ----------------------------------------------------

    def get_context(self) -> List[Dict[str, str]]:
        """Get current conversation context."""
        return self.conversation_history.copy()

    def reset_context(self):
        """Reset conversation context."""
        self.conversation_history = []

    def _format_tools_for_llm(self) -> List[Dict[str, Any]]:
        """Format MCP tools for LLM consumption (local + remote MCP servers)."""
        tools = []

        for tool_name, tool in self.mcp_server.tools.items():
            # Convert MCP tool to OpenAI function format
            tool_spec = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool.description,
                    "parameters": tool.get_schema(),
                },
            }
            tools.append(tool_spec)

        # Append tools from external MCP servers
        for server_name, server_tools in self._mcp_tools.items():
            for tname, tschema in server_tools.items():
                canonical = f"mcp__{server_name}__{tname}"
                tool_spec = {
                    "type": "function",
                    "function": {
                        "name": canonical,
                        "description": tschema.get("description", ""),
                        "parameters": tschema.get("inputSchema", {}),
                    },
                }
                tools.append(tool_spec)

        return tools

    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a single tool after checking permissions."""
        input_str = json.dumps(arguments)

        # Check permission policy before execution
        outcome = self.permission_policy.authorize(
            tool_name, input_str, self.prompter,
        )
        if not outcome.allowed:
            msg = f"Tool '{tool_name}' denied: {outcome.reason}"
            self.console.print(Panel(f"[bold red]{msg}[/bold red]", border_style="red"))
            raise PermissionError(msg)

        # Route to external MCP server if tool name matches mcp__server__tool
        if tool_name.startswith("mcp__"):
            return await self._execute_mcp_tool(tool_name, arguments)

        if tool_name not in self.mcp_server.tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        tool = self.mcp_server.tools[tool_name]

        # Display tool execution
        self.console.print(
            Panel(
                f"[bold cyan]Executing:[/bold cyan] {tool_name}\n"
                f"[dim]Arguments:[/dim] {json.dumps(arguments, indent=2)}",
                border_style="blue",
            )
        )

        # Execute tool
        try:
            result = await tool.execute(**arguments)

            # Display result
            if isinstance(result, str) and len(result) > 500:
                # Truncate long results
                display_result = result[:500] + "... (truncated)"
            else:
                display_result = result

            self.console.print(
                Panel(
                    f"[bold green]Result:[/bold green]\n{display_result}",
                    border_style="green",
                )
            )

            return result

        except Exception as e:
            self.console.print(
                Panel(f"[bold red]Error:[/bold red] {str(e)}", border_style="red")
            )
            raise

    async def _execute_mcp_tool(
        self, canonical_name: str, arguments: Dict[str, Any]
    ) -> Any:
        """Execute a tool on an external MCP server via its client."""
        # Parse mcp__server__tool
        parts = canonical_name.split("__", 2)
        if len(parts) != 3:
            raise ValueError(f"Invalid MCP tool name: {canonical_name}")
        _, server_name, tool_name = parts

        client = self._mcp_clients.get(server_name)
        if client is None:
            raise ValueError(f"No MCP client for server: {server_name}")

        self.console.print(
            Panel(
                f"[bold cyan]MCP Call:[/bold cyan] {server_name}/{tool_name}\n"
                f"[dim]Arguments:[/dim] {json.dumps(arguments, indent=2)}",
                border_style="blue",
            )
        )

        try:
            result = await client.call_tool(tool_name, arguments)
            content = result.get("content", [])
            text_parts = [c.get("text", "") for c in content if c.get("type") == "text"]
            output = "\n".join(text_parts) if text_parts else json.dumps(result)

            display = output[:500] + "... (truncated)" if len(output) > 500 else output
            self.console.print(
                Panel(f"[bold green]Result:[/bold green]\n{display}", border_style="green")
            )
            return output
        except MCPClientError as e:
            self.console.print(
                Panel(f"[bold red]MCP Error:[/bold red] {e}", border_style="red")
            )
            raise

    async def execute_with_tools(self, user_message: str) -> str:
        """Execute a user message with MCP tool support."""
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_message})

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
            *self.conversation_history,
        ]

        iterations = 0
        final_response = ""

        while iterations < self.max_iterations:
            iterations += 1

            # Call backend with tools
            if hasattr(self.backend, "chat"):
                # Direct backend (BackendManager)
                response_text = await self.backend.chat(
                    messages[-1]["content"],  # Just the last user message
                    tools=tools,
                )
                # Create a response object that matches expected format
                from types import SimpleNamespace

                response = SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(
                                content=response_text, tool_calls=None
                            )
                        )
                    ]
                )
            else:
                # Legacy LLMClient
                response = await self.backend.chat(
                    messages=messages, tools=tools, tool_choice="auto"
                )

            # Extract response
            message = response.choices[0].message

            # Check if LLM wants to use tools
            if hasattr(message, "tool_calls") and message.tool_calls:
                # Add assistant message with tool calls
                messages.append(
                    {
                        "role": "assistant",
                        "content": message.content or "",
                        "tool_calls": message.tool_calls,
                    }
                )

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
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": (
                                    json.dumps(result)
                                    if not isinstance(result, str)
                                    else result
                                ),
                            }
                        )

                    except Exception as e:
                        # Add error to messages
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": f"Error: {str(e)}",
                            }
                        )

                # Continue conversation
                continue

            # No tool calls, we have the final response
            final_response = message.content

            # Add to history
            self.conversation_history.append(
                {"role": "assistant", "content": final_response}
            )

            # Track token usage estimate (char_count / 4 heuristic)
            est_input = len(str(messages)) // 4
            est_output = len(final_response) // 4 if final_response else 0
            self.usage_tracker.record(
                TokenUsage(input_tokens=est_input, output_tokens=est_output)
            )

            break

        if iterations >= self.max_iterations:
            final_response = "Maximum iterations reached. Please try a simpler request."

        return final_response
