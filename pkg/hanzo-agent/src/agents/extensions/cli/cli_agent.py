"""CLI-based agent implementation for external tools."""

import os
import json
import asyncio
import tempfile
from typing import Any, Dict, List, Optional

from hanzo_agents.core.agent import Agent, ToolCall, InferenceResult
from hanzo_agents.core.state import State
from hanzo_agents.core.history import History


class CLIAgent(Agent):
    """Agent that uses external CLI tools.

    Supports tools like:
    - claude (Claude Code)
    - openai (Codex)
    - gemini (Google Gemini)
    - grok (xAI Grok)
    - cursor
    - aider
    - etc.
    """

    cli_command: str  # Base command to run
    cli_args: List[str] = []  # Default arguments

    def __init__(
        self,
        cli_command: Optional[str] = None,
        cli_args: Optional[List[str]] = None,
        working_dir: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        **kwargs,
    ):
        """Initialize CLI agent.

        Args:
            cli_command: Override default CLI command
            cli_args: Override default arguments
            working_dir: Working directory for CLI
            env: Environment variables
        """
        super().__init__(**kwargs)

        if cli_command:
            self.cli_command = cli_command
        if cli_args is not None:
            self.cli_args = cli_args

        self.working_dir = working_dir or os.getcwd()
        self.env = os.environ.copy()
        if env:
            self.env.update(env)

    async def run(
        self, state: State, history: History, network: "Network"
    ) -> InferenceResult:
        """Execute CLI tool with current context."""
        # Build prompt from history
        prompt = self._build_prompt(state, history)

        # Execute CLI
        result = await self._execute_cli(prompt)

        # Parse response
        return self._parse_response(result)

    def _build_prompt(self, state: State, history: History) -> str:
        """Build prompt from state and history."""
        # Include state context
        prompt_parts = [
            f"Current state: {json.dumps(state.to_dict(), indent=2)}",
            "",
            "Conversation history:",
        ]

        # Add recent history
        for entry in history[-10:]:  # Last 10 entries
            if entry.role == "user":
                prompt_parts.append(f"User: {entry.content}")
            elif entry.role == "assistant" and entry.agent:
                prompt_parts.append(f"{entry.agent}: {entry.content}")

        # Add current task
        prompt_parts.extend(
            ["", f"As {self.name}, {self.description}", "What should we do next?"]
        )

        return "\n".join(prompt_parts)

    async def _execute_cli(self, prompt: str) -> Dict[str, Any]:
        """Execute the CLI tool."""
        # Write prompt to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(prompt)
            prompt_file = f.name

        try:
            # Build command
            cmd = [self.cli_command] + self.cli_args

            # Some tools accept prompt via stdin, others via file
            if any(arg in ["-", "--stdin"] for arg in self.cli_args):
                # Use stdin
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=self.working_dir,
                    env=self.env,
                )
                stdout, stderr = await process.communicate(prompt.encode())
            else:
                # Use file argument
                cmd.append(prompt_file)
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=self.working_dir,
                    env=self.env,
                )
                stdout, stderr = await process.communicate()

            return {
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
                "returncode": process.returncode,
            }

        finally:
            # Clean up temp file
            try:
                os.unlink(prompt_file)
            except Exception:
                pass

    def _parse_response(self, result: Dict[str, Any]) -> InferenceResult:
        """Parse CLI output into inference result."""
        if result["returncode"] != 0:
            # Handle error
            return InferenceResult(
                agent=self.name,
                content=f"Error: {result['stderr']}",
                metadata={"cli_error": True},
            )

        # Parse stdout for response
        output = result["stdout"]

        # Try to detect tool calls in output
        tool_calls = self._extract_tool_calls(output)

        return InferenceResult(
            agent=self.name,
            content=output,
            tool_calls=tool_calls,
            metadata={"cli_output": True},
        )

    def _extract_tool_calls(self, output: str) -> List[ToolCall]:
        """Extract tool calls from CLI output.

        Look for patterns like:
        - TOOL: tool_name(arg1="value1", arg2="value2")
        - @tool tool_name {"arg1": "value1"}
        """
        tool_calls = []

        # Simple pattern matching (extend as needed)
        lines = output.split("\n")
        for line in lines:
            if line.startswith("TOOL:") or line.startswith("@tool"):
                # Parse tool call
                # This is simplified - real implementation would be more robust
                parts = line.split(None, 2)
                if len(parts) >= 3:
                    tool_name = parts[1]
                    try:
                        # Try to parse as JSON
                        args_str = parts[2]
                        if args_str.startswith("{"):
                            arguments = json.loads(args_str)
                        else:
                            # Simple key=value parsing
                            arguments = {}
                            # ... parse key=value pairs

                        tool_calls.append(ToolCall(tool=tool_name, arguments=arguments))
                    except Exception:
                        pass

        return tool_calls


# Concrete CLI agent implementations


class ClaudeCodeAgent(CLIAgent):
    """Claude Code CLI agent."""

    name = "claude_code"
    description = "Claude Code AI assistant"
    cli_command = "claude"
    cli_args = ["--no-interactive"]
    model = "model://anthropic/claude-3-5-sonnet-20241022"


class OpenAICodexAgent(CLIAgent):
    """OpenAI Codex/ChatGPT CLI agent."""

    name = "openai_codex"
    description = "OpenAI GPT code assistant"
    cli_command = "openai"
    cli_args = ["chat", "--model", "gpt-4"]


class GeminiAgent(CLIAgent):
    """Google Gemini CLI agent."""

    name = "gemini"
    description = "Google Gemini AI assistant"
    cli_command = "gemini"
    cli_args = ["--format", "json"]


class GrokAgent(CLIAgent):
    """xAI Grok CLI agent."""

    name = "grok"
    description = "xAI Grok assistant"
    cli_command = "grok"
    cli_args = ["--mode", "code"]


class CursorAgent(CLIAgent):
    """Cursor AI editor agent."""

    name = "cursor"
    description = "Cursor AI-powered editor"
    cli_command = "cursor"
    cli_args = ["--headless"]


class AiderAgent(CLIAgent):
    """Aider coding assistant agent."""

    name = "aider"
    description = "Aider AI pair programmer"
    cli_command = "aider"
    cli_args = ["--no-pretty", "--yes"]
