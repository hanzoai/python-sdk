"""Unified agent tool - run any agent by name.

Single tool that dispatches to installed CLI agents (claude, codex, gemini, grok)
and orchestrates multi-agent workflows.
"""

from typing import Optional, List, Dict, Any, Literal, final, override, Annotated

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, auto_timeout, create_tool_context


Action = Annotated[
    Literal[
        "run",          # Run a specific agent
        "list",         # List available agents
        "status",       # Check agent status
    ],
    Field(description="Agent action to perform"),
]


@final
class UnifiedAgentTool(BaseTool):
    """Unified agent tool for running CLI agents.

    Dispatches to: claude, codex, gemini, grok or custom agents.
    """

    name = "agent"

    # Available agent configurations
    AGENTS = {
        "claude": {
            "command": "claude",
            "description": "Anthropic Claude Code CLI",
            "check": ["claude", "--version"],
        },
        "codex": {
            "command": "codex",
            "description": "OpenAI Codex CLI",
            "check": ["codex", "--version"],
        },
        "gemini": {
            "command": "gemini",
            "description": "Google Gemini CLI",
            "check": ["gemini", "--version"],
        },
        "grok": {
            "command": "grok",
            "description": "xAI Grok CLI",
            "check": ["grok", "--version"],
        },
    }

    @property
    @override
    def description(self) -> str:
        return """Run AI agents by name.

Actions:
- run: Execute an agent with a prompt
- list: List available agents
- status: Check if an agent is available

Agents: claude, codex, gemini, grok

Examples:
  agent run --name claude --prompt "Explain this code"
  agent run --name codex --prompt "Write a function" --cwd /path/to/project
  agent list
  agent status --name claude
"""

    @override
    @auto_timeout("agent")
    async def call(
        self,
        ctx: MCPContext,
        action: str = "list",
        name: Optional[str] = None,
        prompt: Optional[str] = None,
        cwd: Optional[str] = None,
        args: Optional[List[str]] = None,
        timeout: int = 300,
        **kwargs,
    ) -> str:
        """Execute agent operation."""
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        if action == "list":
            return self._list_agents()
        elif action == "status":
            return await self._check_status(name)
        elif action == "run":
            return await self._run_agent(name, prompt, cwd, args, timeout)
        else:
            return f"Unknown action: {action}. Use: run, list, status"

    def _list_agents(self) -> str:
        """List available agents."""
        lines = ["Available agents:"]
        for name, config in self.AGENTS.items():
            lines.append(f"  • {name}: {config['description']}")
        lines.append("")
        lines.append("Usage: agent run --name <agent> --prompt 'your prompt'")
        return "\n".join(lines)

    async def _check_status(self, name: Optional[str]) -> str:
        """Check if an agent is available."""
        import asyncio

        if not name:
            # Check all agents
            results = []
            for agent_name, config in self.AGENTS.items():
                available = await self._is_available(config["check"])
                status = "✓ available" if available else "✗ not found"
                results.append(f"  {agent_name}: {status}")
            return "Agent status:\n" + "\n".join(results)

        if name not in self.AGENTS:
            return f"Unknown agent: {name}. Available: {', '.join(self.AGENTS.keys())}"

        config = self.AGENTS[name]
        available = await self._is_available(config["check"])
        if available:
            return f"✓ {name} is available"
        return f"✗ {name} is not installed or not in PATH"

    async def _is_available(self, check_cmd: List[str]) -> bool:
        """Check if a command is available."""
        import asyncio

        try:
            proc = await asyncio.create_subprocess_exec(
                *check_cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.wait_for(proc.wait(), timeout=5)
            return proc.returncode == 0
        except Exception:
            return False

    async def _run_agent(
        self,
        name: Optional[str],
        prompt: Optional[str],
        cwd: Optional[str],
        args: Optional[List[str]],
        timeout: int,
    ) -> str:
        """Run an agent with a prompt."""
        import asyncio
        import os

        if not name:
            return "Error: name required for run action"
        if not prompt:
            return "Error: prompt required for run action"

        if name not in self.AGENTS:
            return f"Unknown agent: {name}. Available: {', '.join(self.AGENTS.keys())}"

        config = self.AGENTS[name]
        command = config["command"]

        # Build command
        cmd_args = [command, prompt]
        if args:
            cmd_args.extend(args)

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd or os.getcwd(),
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout,
                )

                output = stdout.decode("utf-8", errors="replace")
                if proc.returncode != 0:
                    err = stderr.decode("utf-8", errors="replace")
                    return f"Agent {name} failed (exit {proc.returncode}):\n{output}\n{err}"

                return f"[{name}] {output}"

            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return f"Agent {name} timed out after {timeout}s"

        except FileNotFoundError:
            return f"Agent {name} not found. Install it or check PATH."
        except Exception as e:
            return f"Error running {name}: {e}"

    def register(self, mcp_server: FastMCP) -> None:
        """Register with MCP server."""
        tool_instance = self

        @mcp_server.tool()
        async def agent(
            action: Action = "list",
            name: Annotated[Optional[str], Field(description="Agent name: claude, codex, gemini, grok")] = None,
            prompt: Annotated[Optional[str], Field(description="Prompt for the agent")] = None,
            cwd: Annotated[Optional[str], Field(description="Working directory")] = None,
            args: Annotated[Optional[List[str]], Field(description="Additional arguments")] = None,
            timeout: Annotated[int, Field(description="Timeout in seconds")] = 300,
            ctx: MCPContext = None,
        ) -> str:
            """Run AI agents: claude, codex, gemini, grok."""
            return await tool_instance.call(
                ctx,
                action=action,
                name=name,
                prompt=prompt,
                cwd=cwd,
                args=args,
                timeout=timeout,
            )
