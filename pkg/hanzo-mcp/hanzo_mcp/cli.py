"""Command-line interface for the Hanzo AI server.

This module intentionally defers heavy imports (like the server and its
dependencies) until after we determine the transport and configure logging.
This prevents any stdout/stderr noise from imports that would corrupt the
MCP stdio transport used by Claude Desktop and other MCP clients.
"""

import os
import sys
import json
import signal
import logging
import argparse
from typing import Any, cast
from pathlib import Path

# Configure uvloop early (before any async imports) for better performance
# This is a no-op on Windows or if uvloop is not installed
try:
    from hanzo_mcp.utils.event_loop import configure_event_loop

    configure_event_loop(quiet=True)
except ImportError:
    pass


# Import timeout parser (deferred to avoid early imports)
def _parse_timeout_arg(timeout_str: str) -> float:
    """Parse timeout argument with human-readable format support."""
    try:
        from hanzo_mcp.tools.common.timeout_parser import parse_timeout

        return parse_timeout(timeout_str)
    except ImportError:
        # Fallback if parser not available
        try:
            return float(timeout_str)
        except ValueError:
            raise ValueError(f"Invalid timeout format: '{timeout_str}'")


def main() -> None:
    """Run the CLI for the Hanzo AI server."""
    # Pre-parse arguments to check transport type early, BEFORE importing server
    early_parser = argparse.ArgumentParser(add_help=False)
    early_parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio")
    early_args, _ = early_parser.parse_known_args()

    # Configure logging VERY early based on transport
    suppress_stdout = False
    original_stdout = sys.stdout
    if early_args.transport == "stdio":
        # Set environment variable for server to detect stdio mode as early as possible
        os.environ["HANZO_MCP_TRANSPORT"] = "stdio"
        # Aggressively quiet common dependency loggers/warnings in stdio mode
        os.environ.setdefault("PYTHONWARNINGS", "ignore")
        os.environ.setdefault("LITELLM_LOG", "ERROR")
        os.environ.setdefault("LITELLM_LOGGING_LEVEL", "ERROR")
        os.environ.setdefault("FASTMCP_LOG_LEVEL", "ERROR")

        # Suppress FastMCP logging (if available) and all standard logging
        try:
            from fastmcp.utilities.logging import configure_logging  # type: ignore

            configure_logging(level="ERROR")
        except Exception:
            pass

        logging.basicConfig(
            level=logging.ERROR,  # Only show errors
            handlers=[],  # No handlers for stdio to prevent protocol corruption
        )

        # Redirect stderr to devnull for stdio transport to prevent any output
        # Store handles for proper cleanup to avoid resource leaks
        _stderr_devnull = open(os.devnull, "w")
        sys.stderr = _stderr_devnull

        # Suppress stdout during potentially noisy imports unless user requested help/version
        _stdout_devnull = None
        if not any(flag in sys.argv for flag in ("--version", "-h", "--help")):
            _stdout_devnull = open(os.devnull, "w")
            sys.stdout = _stdout_devnull
            suppress_stdout = True

    # Import the server only AFTER transport/logging have been configured to avoid import-time noise
    from hanzo_mcp.server import HanzoMCPServer

    # Avoid importing hanzo_mcp package just to get version (it can have side-effects).
    try:
        from importlib.metadata import version as _pkg_version  # py3.8+

        _version = _pkg_version("hanzo-mcp")
    except Exception:
        _version = "unknown"

    parser = argparse.ArgumentParser(description="MCP server implementing Hanzo AI capabilities")

    parser.add_argument("--version", action="version", version=f"hanzo-mcp {_version}")

    _ = parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport protocol to use (default: stdio)",
    )

    _ = parser.add_argument(
        "--name",
        default="hanzo-mcp",
        help="Name of the MCP server (default: hanzo-mcp)",
    )

    _ = parser.add_argument(
        "--allow-path",
        action="append",
        dest="allowed_paths",
        help="Add an allowed path (can be specified multiple times)",
    )

    _ = parser.add_argument(
        "--project",
        action="append",
        dest="project_paths",
        help="Add a project path for prompt generation (can be specified multiple times)",
    )

    _ = parser.add_argument(
        "--agent-model",
        dest="agent_model",
        help="Specify the model name in LiteLLM format (e.g., 'openai/gpt-4o', 'anthropic/claude-4-sonnet')",
    )

    _ = parser.add_argument(
        "--agent-max-tokens",
        dest="agent_max_tokens",
        type=int,
        help="Specify the maximum tokens for agent responses",
    )

    _ = parser.add_argument(
        "--agent-api-key",
        dest="agent_api_key",
        help="Specify the API key for the LLM provider (for development/testing only)",
    )

    _ = parser.add_argument(
        "--agent-base-url",
        dest="agent_base_url",
        help="Specify the base URL for the LLM provider API endpoint (e.g., 'http://localhost:1234/v1')",
    )

    _ = parser.add_argument(
        "--agent-max-iterations",
        dest="agent_max_iterations",
        type=int,
        default=10,
        help="Maximum number of iterations for agent (default: 10)",
    )

    _ = parser.add_argument(
        "--agent-max-tool-uses",
        dest="agent_max_tool_uses",
        type=int,
        default=30,
        help="Maximum number of total tool uses for agent (default: 30)",
    )

    _ = parser.add_argument(
        "--enable-agent-tool",
        dest="enable_agent_tool",
        action="store_true",
        default=False,
        help="Enable the agent tool (disabled by default)",
    )

    _ = parser.add_argument(
        "--command-timeout",
        dest="command_timeout",
        type=str,
        default="120s",
        help="Default timeout for command execution (default: 120s). Supports: 2min, 5m, 120s, 30sec, 1.5h",
    )

    _ = parser.add_argument(
        "--timeout",
        "-t",
        dest="tool_timeout",
        type=str,
        help="Default timeout for MCP tool operations (default: 2min). Supports: 2min, 5m, 120s, 30sec, 1.5h",
    )

    _ = parser.add_argument(
        "--search-timeout",
        dest="search_timeout",
        type=str,
        help="Timeout specifically for search operations. Supports: 2min, 5m, 120s, 30sec, 1.5h",
    )

    _ = parser.add_argument(
        "--find-timeout",
        dest="find_timeout",
        type=str,
        help="Timeout specifically for find operations. Supports: 2min, 5m, 120s, 30sec, 1.5h",
    )

    _ = parser.add_argument(
        "--ast-timeout",
        dest="ast_timeout",
        type=str,
        help="Timeout specifically for AST operations. Supports: 2min, 5m, 120s, 30sec, 1.5h",
    )

    _ = parser.add_argument(
        "--force-shell",
        dest="force_shell",
        choices=["bash", "zsh", "sh"],
        default=None,
        help="Force all shell tools (bash, zsh, shell) to use this shell (default: use requested shell)",
    )

    _ = parser.add_argument(
        "--disable-write-tools",
        dest="disable_write_tools",
        action="store_true",
        default=False,
        help="Disable write tools (edit, write, etc.)",
    )

    _ = parser.add_argument(
        "--disable-search-tools",
        dest="disable_search_tools",
        action="store_true",
        default=False,
        help="Disable search tools (grep, search_content, etc.)",
    )

    _ = parser.add_argument(
        "--host",
        dest="host",
        default="127.0.0.1",
        help="Host for SSE server (default: 127.0.0.1)",
    )

    _ = parser.add_argument(
        "--port",
        dest="port",
        type=int,
        default=8888,
        help="Port for SSE server (default: 8888)",
    )

    _ = parser.add_argument(
        "--log-level",
        dest="log_level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    _ = parser.add_argument(
        "--project-dir",
        dest="project_dir",
        help="Single project directory (alias for --project)",
    )

    _ = parser.add_argument(
        "--dev",
        action="store_true",
        help="Run in development mode with hot reload",
    )

    _ = parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as daemon process for multiple agent connections",
    )

    _ = parser.add_argument(
        "--socket-path",
        dest="socket_path",
        default="/tmp/hanzo-mcp.sock",
        help="Unix socket path for daemon mode (default: /tmp/hanzo-mcp.sock)",
    )

    _ = parser.add_argument(
        "--max-connections",
        dest="max_connections",
        type=int,
        default=100,
        help="Maximum number of concurrent connections in daemon mode (default: 100)",
    )

    _ = parser.add_argument(
        "--install",
        action="store_true",
        help="Install server configuration in Claude Desktop",
    )

    args = parser.parse_args()

    # Restore stdout after parsing, before any explicit output or server start
    if suppress_stdout:
        try:
            if _stdout_devnull is not None:
                _stdout_devnull.close()  # Close devnull handle properly
        except Exception:
            pass
        sys.stdout = original_stdout

    # Note: We intentionally keep stderr redirected to devnull for stdio transport
    # to prevent any library noise from corrupting the protocol

    # Parse timeout arguments with human-readable format support
    command_timeout = _parse_timeout_arg(str(args.command_timeout))

    # Set timeout environment variables from CLI args
    if hasattr(args, "tool_timeout") and args.tool_timeout:
        tool_timeout = _parse_timeout_arg(args.tool_timeout)
        os.environ["HANZO_MCP_TOOL_TIMEOUT"] = str(tool_timeout)

    if hasattr(args, "search_timeout") and args.search_timeout:
        search_timeout = _parse_timeout_arg(args.search_timeout)
        os.environ["HANZO_MCP_SEARCH_TIMEOUT"] = str(search_timeout)

    if hasattr(args, "find_timeout") and args.find_timeout:
        find_timeout = _parse_timeout_arg(args.find_timeout)
        os.environ["HANZO_MCP_FIND_TIMEOUT"] = str(find_timeout)

    if hasattr(args, "ast_timeout") and args.ast_timeout:
        ast_timeout = _parse_timeout_arg(args.ast_timeout)
        os.environ["HANZO_MCP_AST_TIMEOUT"] = str(ast_timeout)

    # Set force shell environment variable
    if hasattr(args, "force_shell") and args.force_shell:
        os.environ["HANZO_MCP_FORCE_SHELL"] = args.force_shell

    # Cast args attributes to appropriate types to avoid 'Any' warnings
    name: str = cast(str, args.name)
    install: bool = cast(bool, args.install)
    dev: bool = cast(bool, args.dev)
    daemon: bool = cast(bool, args.daemon)
    socket_path: str = cast(str, args.socket_path)
    max_connections: int = cast(int, args.max_connections)
    transport: str = cast(str, args.transport)
    agent_model: str | None = cast(str | None, args.agent_model)
    agent_max_tokens: int | None = cast(int | None, args.agent_max_tokens)
    agent_api_key: str | None = cast(str | None, args.agent_api_key)
    agent_base_url: str | None = cast(str | None, args.agent_base_url)
    agent_max_iterations: int = cast(int, args.agent_max_iterations)
    agent_max_tool_uses: int = cast(int, args.agent_max_tool_uses)
    enable_agent_tool: bool = cast(bool, args.enable_agent_tool)
    disable_write_tools: bool = cast(bool, args.disable_write_tools)
    disable_search_tools: bool = cast(bool, args.disable_search_tools)
    host: str = cast(str, args.host)
    port: int = cast(int, args.port)
    log_level: str = cast(str, args.log_level)
    project_dir: str | None = cast(str | None, args.project_dir)
    allowed_paths: list[str] = cast(list[str], args.allowed_paths) if args.allowed_paths else []
    project_paths: list[str] = cast(list[str], args.project_paths) if args.project_paths else []

    # Handle project_dir parameter (add to both allowed_paths and project_paths)
    if project_dir:
        if project_dir not in allowed_paths:
            allowed_paths.append(project_dir)
        if project_dir not in project_paths:
            project_paths.append(project_dir)

    if install:
        install_claude_desktop_config(name, allowed_paths, disable_write_tools, disable_search_tools, host, port)
        return

    # Get logger
    logger = logging.getLogger(__name__)

    # Set up signal handler to ensure clean exit
    def signal_handler(signum, frame):
        if transport != "stdio":
            logger.info("\nReceived interrupt signal, shutting down...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Configure logging based on transport (stdio already configured early)
    if transport != "stdio":
        # For SSE transport, logging is fine
        log_level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
        }
        logging.basicConfig(
            level=log_level_map.get(log_level, logging.INFO),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    # If no allowed paths are specified, use the home directory
    if not allowed_paths:
        allowed_paths = [os.path.expanduser("~")]

    # Set daemon mode environment variables
    if daemon:
        os.environ["HANZO_MCP_DAEMON"] = "true"
        os.environ["HANZO_MCP_SOCKET_PATH"] = socket_path
        os.environ["HANZO_MCP_MAX_CONNECTIONS"] = str(max_connections)

        if transport != "stdio":
            logger.info(f"Starting Hanzo MCP daemon on {socket_path}")
            logger.info(f"Max connections: {max_connections}")

        # Ensure only one daemon runs per socket
        try:
            import fcntl

            lock_file = f"{socket_path}.lock"
            with open(lock_file, "w") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (ImportError, IOError):
            # Fallback for systems without fcntl or if lock fails
            pass

    # Run in dev mode if requested
    if dev:
        from hanzo_mcp.dev_server import DevServer

        dev_server = DevServer(
            name=name,
            allowed_paths=allowed_paths,
            project_paths=project_paths,
            project_dir=project_dir,
            agent_model=agent_model,
            agent_max_tokens=agent_max_tokens,
            agent_api_key=agent_api_key,
            agent_base_url=agent_base_url,
            agent_max_iterations=agent_max_iterations,
            agent_max_tool_uses=agent_max_tool_uses,
            enable_agent_tool=enable_agent_tool,
            command_timeout=command_timeout,
            disable_write_tools=disable_write_tools,
            disable_search_tools=disable_search_tools,
            host=host,
            port=port,
        )
        dev_server.run(transport=transport)
        return

    # Run the server
    server = HanzoMCPServer(
        name=name,
        allowed_paths=allowed_paths,
        project_paths=project_paths,
        project_dir=project_dir,
        agent_model=agent_model,
        agent_max_tokens=agent_max_tokens,
        agent_api_key=agent_api_key,
        agent_base_url=agent_base_url,
        agent_max_iterations=agent_max_iterations,
        agent_max_tool_uses=agent_max_tool_uses,
        enable_agent_tool=enable_agent_tool,
        command_timeout=command_timeout,
        disable_write_tools=disable_write_tools,
        disable_search_tools=disable_search_tools,
        host=host,
        port=port,
    )

    try:
        # Transport will be automatically cast to Literal['stdio', 'sse'] by the server
        server.run(transport=transport)
    except KeyboardInterrupt:
        if transport != "stdio":
            logger.info("\nShutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


def install_claude_desktop_config(
    name: str = "hanzo-mcp",
    allowed_paths: list[str] | None = None,
    disable_write_tools: bool = False,
    disable_search_tools: bool = False,
    host: str = "127.0.0.1",
    port: int = 8888,
) -> None:
    """Install the server configuration in Claude Desktop.

    Args:
        name: The name to use for the server in the config
        allowed_paths: Optional list of paths to allow
        disable_write_tools: Whether to disable write tools
        disable_search_tools: Whether to disable search tools
        host: Host for SSE server
        port: Port for SSE server
    """
    # Find the Claude Desktop config directory
    home: Path = Path.home()

    if sys.platform == "darwin":  # macOS
        config_dir: Path = home / "Library" / "Application Support" / "Claude"
    elif sys.platform == "win32":  # Windows
        config_dir = Path(os.environ.get("APPDATA", "")) / "Claude"
    else:  # Linux and others
        config_dir = home / ".config" / "claude"

    config_file: Path = config_dir / "claude_desktop_config.json"

    # Create directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)

    # Get current script path
    script_path: Path = Path(sys.executable)

    # Create args array
    args: list[str] = ["-m", "hanzo_mcp.cli"]

    # Add allowed paths if specified
    if allowed_paths:
        for path in allowed_paths:
            args.extend(["--allow-path", path])
    else:
        # Allow home directory by default
        args.extend(["--allow-path", str(home)])

    # Add tool disable flags if specified
    if disable_write_tools:
        args.append("--disable-write-tools")

    if disable_search_tools:
        args.append("--disable-search-tools")

    # Create config object
    config: dict[str, Any] = {"mcpServers": {name: {"command": script_path.as_posix(), "args": args}}}

    # Check if the file already exists
    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                existing_config: dict[str, Any] = json.load(f)

            # Update the existing config
            if "mcpServers" not in existing_config:
                existing_config["mcpServers"] = {}

            existing_config["mcpServers"][name] = config["mcpServers"][name]
            config = existing_config
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error reading existing config: {e}")
            logger.info("Creating new config file.")

    # Write the config file
    with open(config_file, mode="w") as f:
        json.dump(config, f, indent=2)

    logger = logging.getLogger(__name__)
    logger.info(f"Successfully installed {name} in Claude Desktop configuration.")
    logger.info(f"Config file: {config_file}")

    if allowed_paths:
        logger.info("\nAllowed paths:")
        for path in allowed_paths:
            logger.info(f"- {path}")
    else:
        logger.info(f"\nDefault allowed path: {home}")

    logger.info("\nYou can modify allowed paths in the config file directly.")
    logger.info("Restart Claude Desktop for changes to take effect.")


if __name__ == "__main__":
    main()
