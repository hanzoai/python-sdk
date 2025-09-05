"""Clarification tool for agents to request information from main loop."""

from typing import Any, Dict, List, Optional, override

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.common.base import BaseTool


class ClarificationTool(BaseTool):
    """Tool for agents to request clarification from the main loop."""

    name = "request_clarification"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Request clarification from the main loop (not the human user).

Use this when you encounter:
- Ambiguous instructions that could be interpreted multiple ways
- Missing context needed to complete the task
- Multiple valid options where you need guidance
- Operations that need confirmation before proceeding
- Need for additional information not provided

Parameters:
- type: Type of clarification (AMBIGUOUS_INSTRUCTION, MISSING_CONTEXT, MULTIPLE_OPTIONS, CONFIRMATION_NEEDED, ADDITIONAL_INFO)
- question: Clear, specific question to ask
- context: Relevant context (e.g., file_path, current_operation, etc.)
- options: Optional list of possible choices (for MULTIPLE_OPTIONS type)

You can only use this ONCE per task, so make it count!

Example:
request_clarification(
    type="MISSING_CONTEXT",
    question="What is the correct import path for the common package?",
    context={"file_path": "/path/to/file.go", "undefined_symbol": "common"},
    options=["github.com/luxfi/node/common", "github.com/project/common"]
)"""

    async def call(
        self,
        ctx: MCPContext,
        type: str,
        question: str,
        context: Dict[str, Any],
        options: Optional[List[str]] = None,
    ) -> str:
        """This is a placeholder - actual implementation happens in AgentTool."""
        # This tool is handled specially in the agent execution
        return f"Clarification request: {question}"

    def register(self, server: FastMCP) -> None:
        """Register the tool with the MCP server."""
        tool_self = self

        @server.tool(name=self.name, description=self.description)
        async def request_clarification(
            ctx: MCPContext,
            type: str,
            question: str,
            context: Dict[str, Any],
            options: Optional[List[str]] = None,
        ) -> str:
            return await tool_self.call(ctx, type, question, context, options)
