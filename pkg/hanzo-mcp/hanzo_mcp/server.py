"""MCP server implementing Hanzo capabilities.

IMPORTANT: This module uses lazy imports to ensure fast startup.
Heavy imports happen only when the server is actually created, not at module load time.
"""

from __future__ import annotations

import os
import atexit
import signal
import logging
import secrets
import warnings
import threading
from typing import TYPE_CHECKING, Literal, cast, final

# Type-only imports - don't execute at runtime
if TYPE_CHECKING:
    from mcp.server import FastMCP
    from hanzo_tools.shell.session_storage import SessionStorage

    from hanzo_mcp.server_enhanced import EnhancedFastMCP
    from hanzo_mcp.tools.common.permissions import PermissionManager

# Suppress litellm deprecation warnings about event loop
warnings.filterwarnings("ignore", message="There is no current event loop", category=DeprecationWarning)

# Cached imports - lazy loaded on first use
_FastMCP = None
_EnhancedFastMCP = None
_PermissionManager = None
_SessionStorage = None
_register_all_tools = None
_register_all_prompts = None


def _get_fast_mcp():
    """Get FastMCP class lazily."""
    global _FastMCP
    if _FastMCP is None:
        try:
            from fastmcp import FastMCP

            _FastMCP = FastMCP
        except ImportError:
            try:
                from mcp.server import FastMCP

                _FastMCP = FastMCP
            except ImportError:
                from mcp import FastMCP

                _FastMCP = FastMCP
    return _FastMCP


def _get_enhanced_fast_mcp():
    """Get EnhancedFastMCP class lazily."""
    global _EnhancedFastMCP
    if _EnhancedFastMCP is None:
        from hanzo_mcp.server_enhanced import EnhancedFastMCP

        _EnhancedFastMCP = EnhancedFastMCP
    return _EnhancedFastMCP


def _get_permission_manager():
    """Get PermissionManager class lazily."""
    global _PermissionManager
    if _PermissionManager is None:
        from hanzo_mcp.tools.common.permissions import PermissionManager

        _PermissionManager = PermissionManager
    return _PermissionManager


def _get_session_storage():
    """Get SessionStorage class lazily."""
    global _SessionStorage
    if _SessionStorage is None:
        from hanzo_tools.shell.session_storage import SessionStorage

        _SessionStorage = SessionStorage
    return _SessionStorage


def _get_register_all_tools():
    """Get register_all_tools function lazily."""
    global _register_all_tools
    if _register_all_tools is None:
        from hanzo_mcp.tools import register_all_tools

        _register_all_tools = register_all_tools
    return _register_all_tools


def _get_register_all_prompts():
    """Get register_all_prompts function lazily."""
    global _register_all_prompts
    if _register_all_prompts is None:
        from hanzo_mcp.prompts import register_all_prompts

        _register_all_prompts = register_all_prompts
    return _register_all_prompts


@final
class HanzoMCPServer:
    """MCP server implementing Hanzo capabilities."""

    def __init__(
        self,
        name: str = "hanzo",
        allowed_paths: list[str] | None = None,
        project_paths: list[str] | None = None,
        project_dir: str | None = None,
        mcp_instance: FastMCP | None = None,
        agent_model: str | None = None,
        agent_max_tokens: int | None = None,
        agent_api_key: str | None = None,
        agent_base_url: str | None = None,
        agent_max_iterations: int = 10,
        agent_max_tool_uses: int = 30,
        enable_agent_tool: bool = False,
        command_timeout: float = 120.0,
        disable_write_tools: bool = False,
        disable_search_tools: bool = False,
        host: str = "127.0.0.1",
        port: int = 8888,
        enabled_tools: dict[str, bool] | None = None,
        disabled_tools: list[str] | None = None,
        auth_token: str | None = None,
    ):
        """Initialize the Hanzo AI server.

        Args:
            name: The name of the server
            allowed_paths: list of paths that the server is allowed to access
            project_paths: list of project paths to generate prompts for
            project_dir: single project directory (added to allowed_paths and project_paths)
            mcp_instance: Optional FastMCP instance for testing
            agent_model: Optional model name for agent tool in LiteLLM format
            agent_max_tokens: Optional maximum tokens for agent responses
            agent_api_key: Optional API key for the LLM provider
            agent_base_url: Optional base URL for the LLM provider API endpoint
            agent_max_iterations: Maximum number of iterations for agent (default: 10)
            agent_max_tool_uses: Maximum number of total tool uses for agent (default: 30)
            enable_agent_tool: Whether to enable the agent tool (default: False)
            command_timeout: Default timeout for command execution in seconds (default: 120.0)
            disable_write_tools: Whether to disable write tools (default: False)
            disable_search_tools: Whether to disable search tools (default: False)
            host: Host for SSE server (default: 127.0.0.1)
            port: Port for SSE server (default: 3000)
            enabled_tools: Dictionary of individual tool enable states (default: None)
            disabled_tools: List of tool names to disable (default: None)
        """
        # Use enhanced server for automatic context normalization
        EnhancedFastMCP = _get_enhanced_fast_mcp()
        self.mcp = mcp_instance if mcp_instance is not None else EnhancedFastMCP(name)

        # Initialize authentication token
        self.auth_token = auth_token or os.environ.get("HANZO_MCP_TOKEN")
        if not self.auth_token:
            # Generate a secure random token if none provided
            self.auth_token = secrets.token_urlsafe(32)
            logger = logging.getLogger(__name__)
            logger.warning(f"No auth token provided. Generated token: {self.auth_token}")
            logger.warning("Set HANZO_MCP_TOKEN environment variable for persistent auth")

        # Initialize permissions and command executor
        PermissionManager = _get_permission_manager()
        self.permission_manager = PermissionManager()

        # Handle project_dir parameter
        if project_dir:
            if allowed_paths is None:
                allowed_paths = []
            if project_dir not in allowed_paths:
                allowed_paths.append(project_dir)
            if project_paths is None:
                project_paths = []
            if project_dir not in project_paths:
                project_paths.append(project_dir)

        # Add allowed paths
        if allowed_paths:
            for path in allowed_paths:
                self.permission_manager.add_allowed_path(path)

        # Store paths and options
        self.project_paths = project_paths
        self.project_dir = project_dir
        self.disable_write_tools = disable_write_tools
        self.disable_search_tools = disable_search_tools
        self.host = host
        self.port = port
        self.enabled_tools = enabled_tools or {}
        self.disabled_tools = disabled_tools or []

        # Store agent options
        self.agent_model = agent_model
        self.agent_max_tokens = agent_max_tokens
        self.agent_api_key = agent_api_key
        self.agent_base_url = agent_base_url
        self.agent_max_iterations = agent_max_iterations
        self.agent_max_tool_uses = agent_max_tool_uses
        self.enable_agent_tool = enable_agent_tool
        self.command_timeout = command_timeout

        # Initialize cleanup tracking with thread-safe lock
        self._cleanup_thread: threading.Thread | None = None
        self._shutdown_event = threading.Event()
        self._cleanup_registered = False
        self._cleanup_lock = threading.Lock()

        # Apply disabled_tools to enabled_tools
        final_enabled_tools = self.enabled_tools.copy()
        for tool_name in self.disabled_tools:
            final_enabled_tools[tool_name] = False

        # Store the final processed tool configuration
        self.enabled_tools = final_enabled_tools

        # Register all tools (lazy import)
        register_all_tools = _get_register_all_tools()
        register_all_tools(
            mcp_server=self.mcp,
            permission_manager=self.permission_manager,
            agent_model=self.agent_model,
            agent_max_tokens=self.agent_max_tokens,
            agent_api_key=self.agent_api_key,
            agent_base_url=self.agent_base_url,
            agent_max_iterations=self.agent_max_iterations,
            agent_max_tool_uses=self.agent_max_tool_uses,
            enable_agent_tool=self.enable_agent_tool,
            disable_write_tools=self.disable_write_tools,
            disable_search_tools=self.disable_search_tools,
            enabled_tools=final_enabled_tools,
        )

        register_all_prompts = _get_register_all_prompts()
        register_all_prompts(mcp_server=self.mcp, projects=self.project_paths)

    def _setup_cleanup_handlers(self) -> None:
        """Set up signal handlers and background cleanup thread."""
        # Use lock to prevent race condition in concurrent calls
        with self._cleanup_lock:
            if self._cleanup_registered:
                return

            # Mark as registered first to prevent re-entry
            self._cleanup_registered = True

            # Register cleanup on normal exit
            atexit.register(self._cleanup_sessions)

            # Register signal handlers for graceful shutdown
            def signal_handler(signum, frame):
                import sys

                # Only log if not stdio transport
                if hasattr(self, "_transport") and self._transport != "stdio":
                    logger = logging.getLogger(__name__)
                    logger.info("\nShutting down gracefully...")
                self._cleanup_sessions()
                self._shutdown_event.set()
                sys.exit(0)

            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)

            # Start background cleanup thread for periodic cleanup
            self._cleanup_thread = threading.Thread(target=self._background_cleanup, daemon=True)
            self._cleanup_thread.start()

    def _background_cleanup(self) -> None:
        """Background thread for periodic session cleanup."""
        SessionStorage = _get_session_storage()
        while not self._shutdown_event.is_set():
            try:
                # Clean up expired sessions every 2 minutes
                # Using shorter TTL of 5 minutes (300 seconds)
                SessionStorage.cleanup_expired_sessions(max_age_seconds=300)

                # Wait for 2 minutes or until shutdown
                self._shutdown_event.wait(timeout=120)
            except Exception:
                # Ignore cleanup errors and continue
                pass

    def _cleanup_sessions(self) -> None:
        """Clean up all active sessions."""
        try:
            SessionStorage = _get_session_storage()
            cleared_count = SessionStorage.clear_all_sessions()
            if cleared_count > 0:
                # Only log if not stdio transport
                if hasattr(self, "_transport") and self._transport != "stdio":
                    logger = logging.getLogger(__name__)
                    logger.info(f"Cleaned up {cleared_count} tmux sessions on shutdown")
        except Exception:
            # Ignore cleanup errors during shutdown
            pass

    def run(self, transport: str = "stdio", allowed_paths: list[str] | None = None):
        """Run the MCP server.

        Args:
            transport: The transport to use (stdio or sse)
            allowed_paths: list of paths that the server is allowed to access
        """
        # Store transport for later use
        self._transport = transport

        # Add allowed paths if provided
        allowed_paths_list = allowed_paths or []
        for path in allowed_paths_list:
            self.permission_manager.add_allowed_path(path)

        # Show compute nodes only in non-stdio mode (to avoid corrupting protocol)
        if transport != "stdio" and not os.environ.get("HANZO_QUIET"):
            try:
                from hanzo_mcp.compute_nodes import ComputeNodeDetector

                detector = ComputeNodeDetector()
                summary = detector.get_node_summary()
                logger = logging.getLogger(__name__)
                logger.info(f"🖥️  {summary}")
            except Exception:
                # Silently ignore if compute node detection fails
                pass

        # Set up cleanup handlers before running
        self._setup_cleanup_handlers()

        # Run the server
        transport_type = cast(Literal["stdio", "sse"], transport)
        self.mcp.run(transport=transport_type)


def create_server(
    name: str = "hanzo-mcp",
    allowed_paths: list[str] | None = None,
    enable_all_tools: bool = False,
    **kwargs,
) -> HanzoMCPServer:
    """Create a Hanzo MCP server instance.

    Args:
        name: Server name
        allowed_paths: List of allowed file paths
        enable_all_tools: Enable all tools including agent tools
        **kwargs: Additional server configuration

    Returns:
        HanzoMCPServer instance
    """
    if enable_all_tools:
        kwargs["enable_agent_tool"] = True

    return HanzoMCPServer(name=name, allowed_paths=allowed_paths, **kwargs)


def main():
    """Main entry point for the server."""
    from hanzo_mcp.cli import main as cli_main

    cli_main()
