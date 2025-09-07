"""Language Server Protocol (LSP) tool for code intelligence.

This tool provides on-demand LSP configuration and installation for various
programming languages. It automatically installs language servers as needed
and provides code intelligence features like go-to-definition, find references,
rename symbol, and diagnostics.
"""

import os
import json
import shutil
import asyncio
import logging
from typing import Any, Dict, Optional
from pathlib import Path
from dataclasses import dataclass

from hanzo_mcp.types import MCPResourceDocument
from hanzo_mcp.tools.common.base import BaseTool

# LSP server configurations
LSP_SERVERS = {
    "go": {
        "name": "gopls",
        "install_cmd": ["go", "install", "golang.org/x/tools/gopls@latest"],
        "check_cmd": ["gopls", "version"],
        "start_cmd": ["gopls", "serve"],
        "root_markers": ["go.mod", "go.sum"],
        "file_extensions": [".go"],
        "capabilities": [
            "definition",
            "references",
            "rename",
            "diagnostics",
            "hover",
            "completion",
        ],
    },
    "python": {
        "name": "pylsp",
        "install_cmd": ["pip", "install", "python-lsp-server[all]"],
        "check_cmd": ["pylsp", "--version"],
        "start_cmd": ["pylsp"],
        "root_markers": ["pyproject.toml", "setup.py", "requirements.txt"],
        "file_extensions": [".py"],
        "capabilities": [
            "definition",
            "references",
            "rename",
            "diagnostics",
            "hover",
            "completion",
        ],
    },
    "typescript": {
        "name": "typescript-language-server",
        "install_cmd": [
            "npm",
            "install",
            "-g",
            "typescript",
            "typescript-language-server",
        ],
        "check_cmd": ["typescript-language-server", "--version"],
        "start_cmd": ["typescript-language-server", "--stdio"],
        "root_markers": ["tsconfig.json", "package.json"],
        "file_extensions": [".ts", ".tsx", ".js", ".jsx"],
        "capabilities": [
            "definition",
            "references",
            "rename",
            "diagnostics",
            "hover",
            "completion",
        ],
    },
    "rust": {
        "name": "rust-analyzer",
        "install_cmd": ["rustup", "component", "add", "rust-analyzer"],
        "check_cmd": ["rust-analyzer", "--version"],
        "start_cmd": ["rust-analyzer"],
        "root_markers": ["Cargo.toml"],
        "file_extensions": [".rs"],
        "capabilities": [
            "definition",
            "references",
            "rename",
            "diagnostics",
            "hover",
            "completion",
            "inlay_hints",
        ],
    },
    "java": {
        "name": "jdtls",
        "install_cmd": ["brew", "install", "jdtls"],  # Or manual download
        "check_cmd": ["jdtls", "--version"],
        "start_cmd": ["jdtls"],
        "root_markers": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "file_extensions": [".java"],
        "capabilities": [
            "definition",
            "references",
            "rename",
            "diagnostics",
            "hover",
            "completion",
        ],
    },
    "cpp": {
        "name": "clangd",
        "install_cmd": ["brew", "install", "llvm"],  # Or apt-get install clangd
        "check_cmd": ["clangd", "--version"],
        "start_cmd": ["clangd"],
        "root_markers": ["compile_commands.json", "CMakeLists.txt"],
        "file_extensions": [".cpp", ".cc", ".cxx", ".c", ".h", ".hpp"],
        "capabilities": [
            "definition",
            "references",
            "rename",
            "diagnostics",
            "hover",
            "completion",
        ],
    },
    "ruby": {
        "name": "solargraph",
        "install_cmd": ["gem", "install", "solargraph"],
        "check_cmd": ["solargraph", "--version"],
        "start_cmd": ["solargraph", "stdio"],
        "root_markers": ["Gemfile", ".solargraph.yml"],
        "file_extensions": [".rb"],
        "capabilities": [
            "definition",
            "references",
            "diagnostics",
            "hover",
            "completion",
        ],
    },
    "lua": {
        "name": "lua-language-server",
        "install_cmd": ["brew", "install", "lua-language-server"],
        "check_cmd": ["lua-language-server", "--version"],
        "start_cmd": ["lua-language-server"],
        "root_markers": [".luarc.json"],
        "file_extensions": [".lua"],
        "capabilities": [
            "definition",
            "references",
            "rename",
            "diagnostics",
            "hover",
            "completion",
        ],
    },
}


@dataclass
class LSPServer:
    """Represents an LSP server instance."""

    language: str
    process: Optional[asyncio.subprocess.Process]
    config: Dict[str, Any]
    root_uri: str
    initialized: bool = False


class LSPTool(BaseTool):
    """Language Server Protocol tool for code intelligence.

    This tool automatically configures and manages LSP servers for various
    programming languages. It installs language servers on-demand and provides
    code intelligence features.

    Features:
    - Auto-installation of language servers
    - Go-to-definition
    - Find references
    - Rename symbol
    - Get diagnostics
    - Hover information
    - Code completion

    Example usage:

    1. Find definition of a Go function:
       lsp("definition", file="main.go", line=10, character=15)

    2. Find all references to a Python class:
       lsp("references", file="models.py", line=25, character=10)

    3. Rename a TypeScript variable:
       lsp("rename", file="app.ts", line=30, character=20, new_name="newVarName")

    4. Get diagnostics for a Rust file:
       lsp("diagnostics", file="lib.rs")

    The tool automatically detects the language based on file extension and
    installs the appropriate language server if not already available.
    """

    name = "lsp"
    description = """Language Server Protocol tool for code intelligence.
    
    Actions:
    - definition: Go to definition of symbol at position
    - references: Find all references to symbol
    - rename: Rename symbol across codebase
    - diagnostics: Get errors and warnings for file
    - hover: Get hover information at position
    - completion: Get code completions at position
    - status: Check LSP server status
    
    The tool automatically installs language servers as needed.
    Supported languages: Go, Python, TypeScript/JavaScript, Rust, Java, C/C++, Ruby, Lua
    """

    def __init__(self):
        super().__init__()
        self.servers: Dict[str, LSPServer] = {}
        self.logger = logging.getLogger(__name__)

    def _get_language_from_file(self, file_path: str) -> Optional[str]:
        """Detect language from file extension."""
        ext = Path(file_path).suffix.lower()

        for lang, config in LSP_SERVERS.items():
            if ext in config["file_extensions"]:
                return lang

        return None

    def _find_project_root(self, file_path: str, language: str) -> str:
        """Find project root based on language markers."""
        markers = LSP_SERVERS[language]["root_markers"]
        path = Path(file_path).resolve()

        for parent in path.parents:
            for marker in markers:
                if (parent / marker).exists():
                    return str(parent)

        return str(path.parent)

    async def _check_lsp_installed(self, language: str) -> bool:
        """Check if LSP server is installed."""
        config = LSP_SERVERS.get(language)
        if not config:
            return False

        try:
            result = await asyncio.create_subprocess_exec(
                *config["check_cmd"],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await result.communicate()
            return result.returncode == 0
        except (FileNotFoundError, OSError):
            return False

    async def _install_lsp(self, language: str) -> bool:
        """Install LSP server for language."""
        config = LSP_SERVERS.get(language)
        if not config:
            return False

        self.logger.info(f"Installing {config['name']} for {language}")

        try:
            # Check if installer is available
            installer = config["install_cmd"][0]
            if not shutil.which(installer):
                self.logger.error(f"Installer {installer} not found")
                return False

            # Run installation command
            result = await asyncio.create_subprocess_exec(
                *config["install_cmd"],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                self.logger.error(f"Installation failed: {stderr.decode()}")
                return False

            self.logger.info(f"Successfully installed {config['name']}")
            return True

        except Exception as e:
            self.logger.error(f"Installation error: {e}")
            return False

    async def _ensure_lsp_running(
        self, language: str, root_uri: str
    ) -> Optional[LSPServer]:
        """Ensure LSP server is running for language."""
        # Check if already running
        server_key = f"{language}:{root_uri}"
        if server_key in self.servers:
            server = self.servers[server_key]
            if server.process and server.process.returncode is None:
                return server

        # Check if installed
        if not await self._check_lsp_installed(language):
            # Try to install
            if not await self._install_lsp(language):
                return None

        # Start LSP server
        config = LSP_SERVERS[language]

        try:
            process = await asyncio.create_subprocess_exec(
                *config["start_cmd"],
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=root_uri,
            )

            server = LSPServer(
                language=language, process=process, config=config, root_uri=root_uri
            )

            # Initialize LSP
            await self._initialize_lsp(server)

            self.servers[server_key] = server
            return server

        except Exception as e:
            self.logger.error(f"Failed to start LSP: {e}")
            return None

    async def _initialize_lsp(self, server: LSPServer):
        """Send initialize request to LSP server."""
        # This is a simplified initialization
        # In a real implementation, you'd use the full LSP protocol
        init_params = {
            "processId": os.getpid(),
            "rootUri": f"file://{server.root_uri}",
            "capabilities": {
                "textDocument": {
                    "definition": {"dynamicRegistration": True},
                    "references": {"dynamicRegistration": True},
                    "rename": {"dynamicRegistration": True},
                }
            },
        }

        # Send initialize request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": init_params,
        }

        await self._send_request(server, request)
        server.initialized = True

    async def _send_request(
        self, server: LSPServer, request: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Send JSON-RPC request to LSP server."""
        if not server.process or server.process.returncode is not None:
            return None

        try:
            # Serialize request
            request_str = json.dumps(request)
            content_length = len(request_str.encode("utf-8"))

            # Send LSP message
            message = f"Content-Length: {content_length}\r\n\r\n{request_str}"
            server.process.stdin.write(message.encode("utf-8"))
            await server.process.stdin.drain()

            # Read response (simplified - real implementation needs proper parsing)
            # This is a placeholder - actual LSP requires parsing Content-Length headers
            response_data = await server.process.stdout.readline()

            if response_data:
                return json.loads(response_data.decode("utf-8"))

        except Exception as e:
            self.logger.error(f"LSP communication error: {e}")

        return None

    async def run(
        self,
        action: str,
        file: str,
        line: Optional[int] = None,
        character: Optional[int] = None,
        new_name: Optional[str] = None,
        **kwargs,
    ) -> MCPResourceDocument:
        """Execute LSP action.

        Args:
            action: LSP action (definition, references, rename, diagnostics, hover, completion, status)
            file: File path to analyze
            line: Line number (1-indexed)
            character: Character position in line (0-indexed)
            new_name: New name for rename action
        """

        # Validate action
        valid_actions = [
            "definition",
            "references",
            "rename",
            "diagnostics",
            "hover",
            "completion",
            "status",
        ]
        if action not in valid_actions:
            return MCPResourceDocument(
                data={
                    "error": f"Invalid action. Must be one of: {', '.join(valid_actions)}"
                }
            )

        # Get language from file
        language = self._get_language_from_file(file)
        if not language:
            return MCPResourceDocument(
                data={
                    "error": f"Unsupported file type: {file}",
                    "supported_languages": list(LSP_SERVERS.keys()),
                }
            )

        # Check LSP capabilities
        capabilities = LSP_SERVERS[language]["capabilities"]
        if action not in capabilities and action != "status":
            return MCPResourceDocument(
                data={
                    "error": f"Action '{action}' not supported for {language}",
                    "supported_actions": capabilities,
                }
            )

        # Status check
        if action == "status":
            installed = await self._check_lsp_installed(language)
            return MCPResourceDocument(
                data={
                    "language": language,
                    "lsp_server": LSP_SERVERS[language]["name"],
                    "installed": installed,
                    "capabilities": capabilities,
                }
            )

        # Find project root
        root_uri = self._find_project_root(file, language)

        # Ensure LSP is running
        server = await self._ensure_lsp_running(language, root_uri)
        if not server:
            return MCPResourceDocument(
                data={
                    "error": f"Failed to start LSP server for {language}",
                    "install_command": " ".join(LSP_SERVERS[language]["install_cmd"]),
                }
            )

        # Execute action
        result = await self._execute_lsp_action(
            server, action, file, line, character, new_name
        )

        return MCPResourceDocument(data=result)

    async def call(self, **kwargs) -> str:
        """Tool interface for MCP - converts result to JSON string."""
        result = await self.run(**kwargs)
        return result.to_json_string()

    def register(self, mcp_server) -> None:
        """Register tool with MCP server."""

        @mcp_server.tool(name=self.name, description=self.description)
        async def lsp_handler(
            action: str,
            file: str,
            line: Optional[int] = None,
            character: Optional[int] = None,
            new_name: Optional[str] = None,
        ) -> str:
            """Execute LSP action."""
            return await self.call(
                action=action,
                file=file,
                line=line,
                character=character,
                new_name=new_name,
            )

    async def _execute_lsp_action(
        self,
        server: LSPServer,
        action: str,
        file: str,
        line: Optional[int],
        character: Optional[int],
        new_name: Optional[str],
    ) -> Dict[str, Any]:
        """Execute specific LSP action."""

        # This is a simplified implementation
        # Real implementation would use proper LSP protocol

        if action == "definition":
            # textDocument/definition request
            return {
                "action": "definition",
                "file": file,
                "position": {"line": line, "character": character},
                "note": "LSP integration pending full implementation",
                "fallback": "Use mcp__lsp__find_definition tool for now",
            }

        elif action == "references":
            # textDocument/references request
            return {
                "action": "references",
                "file": file,
                "position": {"line": line, "character": character},
                "note": "LSP integration pending full implementation",
                "fallback": "Use mcp__lsp__find_references tool for now",
            }

        elif action == "rename":
            # textDocument/rename request
            return {
                "action": "rename",
                "file": file,
                "position": {"line": line, "character": character},
                "new_name": new_name,
                "note": "LSP integration pending full implementation",
                "fallback": "Use mcp__lsp__rename_symbol tool for now",
            }

        elif action == "diagnostics":
            # textDocument/diagnostic request
            return {
                "action": "diagnostics",
                "file": file,
                "note": "LSP integration pending full implementation",
                "fallback": "Use mcp__lsp__get_diagnostics tool for now",
            }

        elif action == "hover":
            # textDocument/hover request
            return {
                "action": "hover",
                "file": file,
                "position": {"line": line, "character": character},
                "note": "LSP integration pending full implementation",
            }

        elif action == "completion":
            # textDocument/completion request
            return {
                "action": "completion",
                "file": file,
                "position": {"line": line, "character": character},
                "note": "LSP integration pending full implementation",
            }

        return {"error": "Unknown action"}

    async def cleanup(self):
        """Clean up LSP servers."""
        for server in self.servers.values():
            if server.process and server.process.returncode is None:
                server.process.terminate()
                await server.process.wait()


# Tool registration
def create_lsp_tool():
    """Factory function to create LSP tool."""
    return LSPTool()
