"""Unified agent tool - lightweight agent spawning.

Single tool that dispatches to installed CLI agents and supports:
- claude: Claude Code CLI (default when running in Claude Code)
- codex: OpenAI Codex CLI
- gemini: Google Gemini CLI
- grok: xAI Grok CLI
- qwen: Alibaba Qwen CLI
- vibe: Vibe coding agent
- code: Hanzo Code agent
- dev: Hanzo Dev agent (default)

Key features:
- Auto-detects Claude Code environment and uses same auth
- Shares hanzo-mcp config with spawned agents
- Lightweight - no heavy dependencies
"""

import os
import json
import asyncio
from typing import List, Literal, Optional, Annotated, final, override
from pathlib import Path

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import BaseTool, auto_timeout, create_tool_context

Action = Annotated[
    Literal[
        "run",  # Run a specific agent
        "list",  # List available agents
        "status",  # Check agent status
        "config",  # Show/set agent config
    ],
    Field(description="Agent action to perform"),
]


def detect_claude_code_env() -> dict:
    """Detect if running inside Claude Code and get auth info.

    Returns dict with:
        running_in_claude: bool
        session_id: Optional[str]
        auth_token: Optional[str]
        api_key: Optional[str]
    """
    result = {
        "running_in_claude": False,
        "session_id": None,
        "auth_token": None,
        "api_key": None,
    }

    # Check Claude Code environment markers
    if os.environ.get("CLAUDE_CODE") or os.environ.get("CLAUDE_SESSION_ID"):
        result["running_in_claude"] = True
        result["session_id"] = os.environ.get("CLAUDE_SESSION_ID")

    # Check for Claude auth
    if os.environ.get("ANTHROPIC_API_KEY"):
        result["api_key"] = os.environ.get("ANTHROPIC_API_KEY")

    # Check Claude Desktop config for OAuth tokens
    claude_config_path = Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
    if claude_config_path.exists():
        try:
            with open(claude_config_path) as f:
                config = json.load(f)
                if "mcpServers" in config and "hanzo-mcp" in config["mcpServers"]:
                    result["running_in_claude"] = True
        except Exception:
            pass

    return result


def get_mcp_config() -> dict:
    """Get current hanzo-mcp config to share with spawned agents."""
    config = {}

    # Get relevant environment variables
    mcp_env_vars = [
        "HANZO_MCP_MODE",
        "HANZO_MCP_ALLOWED_PATHS",
        "HANZO_MCP_ENABLED_TOOLS",
        "HANZO_MCP_PERSONA",
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
    ]

    for var in mcp_env_vars:
        if os.environ.get(var):
            config[var] = os.environ.get(var)

    return config


@final
class UnifiedAgentTool(BaseTool):
    """Unified agent tool for running CLI agents.

    Lightweight agent spawning that:
    - Auto-detects Claude Code environment
    - Shares hanzo-mcp config with child agents
    - Supports multiple agent backends
    """

    name = "agent"

    # Available agent configurations
    AGENTS = {
        "claude": {
            "command": "claude",
            "args": ["-p"],  # Use -p for print mode (non-interactive)
            "description": "Anthropic Claude Code CLI (recommended when in Claude)",
            "check": ["claude", "--version"],
            "env_key": "ANTHROPIC_API_KEY",
            "priority": 1,  # Highest priority when in Claude env
        },
        "codex": {
            "command": "codex",
            "args": [],
            "description": "OpenAI Codex CLI",
            "check": ["codex", "--version"],
            "env_key": "OPENAI_API_KEY",
            "priority": 2,
        },
        "gemini": {
            "command": "gemini",
            "args": [],
            "description": "Google Gemini CLI",
            "check": ["gemini", "--version"],
            "env_key": "GOOGLE_API_KEY",
            "priority": 3,
        },
        "grok": {
            "command": "grok",
            "args": [],
            "description": "xAI Grok CLI",
            "check": ["grok", "--version"],
            "env_key": "XAI_API_KEY",
            "priority": 4,
        },
        "qwen": {
            "command": "qwen",
            "args": [],
            "description": "Alibaba Qwen CLI",
            "check": ["qwen", "--version"],
            "env_key": "DASHSCOPE_API_KEY",
            "priority": 5,
        },
        "vibe": {
            "command": "vibe",
            "args": [],
            "description": "Vibe coding agent",
            "check": ["vibe", "--version"],
            "priority": 6,
        },
        "code": {
            "command": "hanzo-code",
            "args": [],
            "description": "Hanzo Code agent",
            "check": ["hanzo-code", "--version"],
            "priority": 7,
        },
        "dev": {
            "command": "hanzo-dev",
            "args": [],
            "description": "Hanzo Dev agent (full development assistant)",
            "check": ["hanzo-dev", "--version"],
            "priority": 8,
        },
    }

    def __init__(self):
        super().__init__()
        self._claude_env = detect_claude_code_env()
        self._mcp_config = get_mcp_config()

    @property
    @override
    def description(self) -> str:
        default_agent = self._get_default_agent()
        return f"""Run AI agents by name. Lightweight agent spawning.

Actions:
- run: Execute an agent with a prompt (default: {default_agent})
- list: List available agents
- status: Check agent availability
- config: Show/set agent configuration

Agents: claude, codex, gemini, grok, qwen, vibe, code, dev

Examples:
  agent run --prompt "Explain this code"  # Uses default agent
  agent run --name claude --prompt "Review this PR"
  agent run --name dev --prompt "Fix the build" --cwd /project
  agent list
  agent status

{"⚡ Running in Claude Code - claude agent uses same auth" if self._claude_env["running_in_claude"] else ""}
"""

    def _get_default_agent(self) -> str:
        """Get the default agent based on environment."""
        # If running in Claude Code, prefer claude
        if self._claude_env.get("running_in_claude"):
            return "claude"

        # Otherwise check which agents are configured
        for name, config in sorted(self.AGENTS.items(), key=lambda x: x[1].get("priority", 99)):
            env_key = config.get("env_key")
            if env_key and os.environ.get(env_key):
                return name

        # Default fallback
        return "dev"

    @override
    @auto_timeout("agent")
    async def call(
        self,
        ctx: MCPContext,
        action: str = "run",
        name: Optional[str] = None,
        prompt: Optional[str] = None,
        cwd: Optional[str] = None,
        args: Optional[List[str]] = None,
        timeout: int = 300,
        share_config: bool = True,
        **kwargs,
    ) -> str:
        """Execute agent operation."""
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        if action == "list":
            return self._list_agents()
        elif action == "status":
            return await self._check_status(name)
        elif action == "config":
            return self._show_config()
        elif action == "run":
            # Use default agent if not specified
            agent_name = name or self._get_default_agent()
            return await self._run_agent(agent_name, prompt, cwd, args, timeout, share_config)
        else:
            return f"Unknown action: {action}. Use: run, list, status, config"

    def _list_agents(self) -> str:
        """List available agents."""
        default = self._get_default_agent()
        lines = ["Available agents:"]

        for name, config in sorted(self.AGENTS.items(), key=lambda x: x[1].get("priority", 99)):
            marker = " (default)" if name == default else ""
            lines.append(f"  • {name}: {config['description']}{marker}")

        lines.append("")
        lines.append("Usage: agent run --prompt 'your prompt'")
        lines.append(f"       agent run --name <agent> --prompt 'prompt'")

        if self._claude_env.get("running_in_claude"):
            lines.append("")
            lines.append("⚡ Running in Claude Code - using same authentication")

        return "\n".join(lines)

    def _show_config(self) -> str:
        """Show current agent configuration."""
        lines = ["Agent Configuration:"]
        lines.append(f"  Default agent: {self._get_default_agent()}")
        lines.append(f"  Running in Claude: {self._claude_env.get('running_in_claude', False)}")

        if self._claude_env.get("session_id"):
            lines.append(f"  Claude session: {self._claude_env['session_id'][:8]}...")

        lines.append("")
        lines.append("MCP Config (shared with spawned agents):")
        for key, value in self._mcp_config.items():
            # Mask sensitive values
            if "KEY" in key or "TOKEN" in key:
                display = value[:8] + "..." if len(value) > 8 else "***"
            else:
                display = value
            lines.append(f"  {key}: {display}")

        return "\n".join(lines)

    async def _check_status(self, name: Optional[str]) -> str:
        """Check if agents are available."""
        if not name:
            # Check all agents
            results = []
            for agent_name, config in sorted(self.AGENTS.items(), key=lambda x: x[1].get("priority", 99)):
                available = await self._is_available(config["check"])

                # Check for API key
                env_key = config.get("env_key")
                has_key = bool(env_key and os.environ.get(env_key))

                if available:
                    key_status = "✓ key" if has_key else "○ no key"
                    status = f"✓ installed ({key_status})"
                else:
                    status = "✗ not found"

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
        name: str,
        prompt: Optional[str],
        cwd: Optional[str],
        args: Optional[List[str]],
        timeout: int,
        share_config: bool,
    ) -> str:
        """Run an agent with a prompt."""
        if not prompt:
            return "Error: prompt required for run action"

        if name not in self.AGENTS:
            return f"Unknown agent: {name}. Available: {', '.join(self.AGENTS.keys())}"

        config = self.AGENTS[name]
        command = config["command"]
        default_args = config.get("args", [])

        # Build command
        cmd_args = [command] + default_args + [prompt]
        if args:
            cmd_args.extend(args)

        # Build environment with shared MCP config
        env = os.environ.copy()
        if share_config:
            env.update(self._mcp_config)
            # Mark that this is a child agent
            env["HANZO_AGENT_PARENT"] = "true"
            env["HANZO_AGENT_NAME"] = name

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd or os.getcwd(),
                env=env,
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
            # Provide helpful installation instructions
            install_hints = {
                "claude": "npm install -g @anthropic-ai/claude-code",
                "codex": "npm install -g @openai/codex",
                "gemini": "pip install google-generativeai",
                "grok": "pip install xai-grok",
                "dev": "pip install hanzo-dev",
                "code": "pip install hanzo-code",
            }
            hint = install_hints.get(name, f"Install the {name} CLI")
            return f"Agent {name} not found.\n\nTo install: {hint}"
        except Exception as e:
            return f"Error running {name}: {e}"

    def register(self, mcp_server: FastMCP) -> None:
        """Register with MCP server."""
        tool_instance = self

        @mcp_server.tool()
        async def agent(
            action: Action = "run",
            name: Annotated[
                Optional[str], Field(description="Agent: claude, codex, gemini, grok, qwen, vibe, code, dev")
            ] = None,
            prompt: Annotated[Optional[str], Field(description="Prompt for the agent")] = None,
            cwd: Annotated[Optional[str], Field(description="Working directory")] = None,
            args: Annotated[Optional[List[str]], Field(description="Additional arguments")] = None,
            timeout: Annotated[int, Field(description="Timeout in seconds")] = 300,
            share_config: Annotated[bool, Field(description="Share hanzo-mcp config with agent")] = True,
            ctx: MCPContext = None,
        ) -> str:
            """Run AI agents: claude, codex, gemini, grok, qwen, vibe, code, dev.

            Lightweight agent spawning with shared MCP config.
            Auto-detects Claude Code environment for seamless auth.
            """
            return await tool_instance.call(
                ctx,
                action=action,
                name=name,
                prompt=prompt,
                cwd=cwd,
                args=args,
                timeout=timeout,
                share_config=share_config,
            )
