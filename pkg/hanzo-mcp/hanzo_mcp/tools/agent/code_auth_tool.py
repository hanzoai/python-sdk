"""Claude Code authentication tool.

This tool manages API keys and accounts for Claude Code and other AI coding tools.
"""

from typing import Unpack, Optional, TypedDict, final, override

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.common.base import BaseTool
from hanzo_mcp.tools.common.context import create_tool_context
from hanzo_mcp.tools.agent.code_auth import CodeAuthManager


class CodeAuthParams(TypedDict, total=False):
    """Parameters for code auth tool."""

    action: str
    account: Optional[str]
    provider: Optional[str]
    api_key: Optional[str]
    model: Optional[str]
    description: Optional[str]
    agent_id: Optional[str]
    parent_account: Optional[str]


@final
class CodeAuthTool(BaseTool):
    """Tool for managing Claude Code authentication and API keys."""

    @property
    @override
    def name(self) -> str:
        """Get the tool name."""
        return "code_auth"

    @property
    @override
    def description(self) -> str:
        """Get the tool description."""
        return """Manage Claude Code and AI provider authentication.

Actions:
- status: Show current login status
- list: List all accounts
- create: Create a new account
- login: Login to an account
- logout: Logout current account
- switch: Switch between accounts
- agent: Create/get agent account

Examples:
code_auth status
code_auth list
code_auth create --account work --provider claude
code_auth login --account work
code_auth logout
code_auth switch --account personal
code_auth agent --agent_id swarm_1 --parent_account work

Providers: claude, openai, azure, deepseek, google, groq"""

    def __init__(self):
        """Initialize the code auth tool."""
        self.auth_manager = CodeAuthManager()

    @override
    async def call(
        self,
        ctx: MCPContext,
        **params: Unpack[CodeAuthParams],
    ) -> str:
        """Execute the code auth tool.

        Args:
            ctx: MCP context
            **params: Tool parameters

        Returns:
            Result message
        """
        tool_ctx = create_tool_context(ctx)
        await tool_ctx.set_tool_info(self.name)

        action = params.get("action", "status")

        if action == "status":
            current = self.auth_manager.get_active_account()
            if current:
                info = self.auth_manager.get_account_info(current)
                if info:
                    return f"Logged in as: {current} ({info['provider']})"
            return "Not logged in"

        elif action == "list":
            accounts = self.auth_manager.list_accounts()
            if not accounts:
                return "No accounts configured"

            current = self.auth_manager.get_active_account()
            lines = ["Configured accounts:"]
            for account in accounts:
                info = self.auth_manager.get_account_info(account)
                marker = " (active)" if account == current else ""
                lines.append(f"  - {account}: {info['provider']}{marker}")
            return "\n".join(lines)

        elif action == "create":
            account = params.get("account")
            if not account:
                return "Error: account name required"

            provider = params.get("provider", "claude")
            api_key = params.get("api_key")
            model = params.get("model")
            description = params.get("description")

            success, msg = self.auth_manager.create_account(
                account, provider, api_key, model, description
            )
            return msg

        elif action == "login":
            account = params.get("account", "default")
            success, msg = self.auth_manager.login(account)
            return msg

        elif action == "logout":
            success, msg = self.auth_manager.logout()
            return msg

        elif action == "switch":
            account = params.get("account")
            if not account:
                return "Error: account name required"

            success, msg = self.auth_manager.switch_account(account)
            return msg

        elif action == "agent":
            agent_id = params.get("agent_id")
            if not agent_id:
                return "Error: agent_id required"

            provider = params.get("provider", "claude")
            parent_account = params.get("parent_account")

            # Try to create agent account
            success, result = self.auth_manager.create_agent_account(
                agent_id, provider, parent_account
            )

            if success:
                # Get credentials
                creds = self.auth_manager.get_agent_credentials(agent_id)
                if creds:
                    return f"Agent account ready: {result} ({creds.provider})"
                else:
                    return f"Agent account created but no credentials: {result}"
            else:
                return f"Failed to create agent account: {result}"

        else:
            return f"Unknown action: {action}. Use: status, list, create, login, logout, switch, agent"

    @override
    def register(self, mcp_server: FastMCP) -> None:
        """Register this tool with the MCP server."""
        tool_self = self

        @mcp_server.tool(name=self.name, description=self.description)
        async def code_auth(
            ctx: MCPContext,
            action: str = "status",
            account: Optional[str] = None,
            provider: Optional[str] = None,
            api_key: Optional[str] = None,
            model: Optional[str] = None,
            description: Optional[str] = None,
            agent_id: Optional[str] = None,
            parent_account: Optional[str] = None,
        ) -> str:
            return await tool_self.call(
                ctx,
                action=action,
                account=account,
                provider=provider,
                api_key=api_key,
                model=model,
                description=description,
                agent_id=agent_id,
                parent_account=parent_account,
            )
