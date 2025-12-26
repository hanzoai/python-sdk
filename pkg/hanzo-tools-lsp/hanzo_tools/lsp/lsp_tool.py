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
import atexit
from typing import Any, Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, field

from hanzo_tools.core import BaseTool, MCPResourceDocument

# LSP server configurations
LSP_SERVERS = {
    "go": {
        "name": "gopls",
        "install_cmd": ["go", "install", "golang.org/x/tools/gopls@latest"],
        "check_cmd": ["gopls", "version"],
        "start_cmd": ["gopls", "serve"],
        "root_markers": ["go.mod", "go.sum"],
        "file_extensions": [".go"],
        "capabilities": ["definition", "references", "rename", "diagnostics", "hover", "completion"],
    },
    "python": {
        "name": "pyright",
        "install_cmd": ["npm", "install", "-g", "pyright"],
        "check_cmd": ["pyright-langserver", "--version"],
        "start_cmd": ["pyright-langserver", "--stdio"],
        "root_markers": ["pyproject.toml", "setup.py", "requirements.txt", "pyrightconfig.json"],
        "file_extensions": [".py", ".pyi"],
        "capabilities": ["definition", "references", "rename", "diagnostics", "hover", "completion", "typeDefinition"],
    },
    "typescript": {
        "name": "typescript-language-server",
        "install_cmd": ["npm", "install", "-g", "typescript", "typescript-language-server"],
        "check_cmd": ["typescript-language-server", "--version"],
        "start_cmd": ["typescript-language-server", "--stdio"],
        "root_markers": ["tsconfig.json", "package.json"],
        "file_extensions": [".ts", ".tsx", ".js", ".jsx"],
        "capabilities": ["definition", "references", "rename", "diagnostics", "hover", "completion"],
    },
    "rust": {
        "name": "rust-analyzer",
        "install_cmd": ["rustup", "component", "add", "rust-analyzer"],
        "check_cmd": ["rust-analyzer", "--version"],
        "start_cmd": ["rust-analyzer"],
        "root_markers": ["Cargo.toml"],
        "file_extensions": [".rs"],
        "capabilities": ["definition", "references", "rename", "diagnostics", "hover", "completion", "inlay_hints"],
    },
    "java": {
        "name": "jdtls",
        "install_cmd": ["brew", "install", "jdtls"],
        "check_cmd": ["jdtls", "--version"],
        "start_cmd": ["jdtls"],
        "root_markers": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "file_extensions": [".java"],
        "capabilities": ["definition", "references", "rename", "diagnostics", "hover", "completion"],
    },
    "cpp": {
        "name": "clangd",
        "install_cmd": ["brew", "install", "llvm"],
        "check_cmd": ["clangd", "--version"],
        "start_cmd": ["clangd"],
        "root_markers": ["compile_commands.json", "CMakeLists.txt"],
        "file_extensions": [".cpp", ".cc", ".cxx", ".c", ".h", ".hpp"],
        "capabilities": ["definition", "references", "rename", "diagnostics", "hover", "completion"],
    },
    "ruby": {
        "name": "solargraph",
        "install_cmd": ["gem", "install", "solargraph"],
        "check_cmd": ["solargraph", "--version"],
        "start_cmd": ["solargraph", "stdio"],
        "root_markers": ["Gemfile", ".solargraph.yml"],
        "file_extensions": [".rb"],
        "capabilities": ["definition", "references", "diagnostics", "hover", "completion"],
    },
    "lua": {
        "name": "lua-language-server",
        "install_cmd": ["brew", "install", "lua-language-server"],
        "check_cmd": ["lua-language-server", "--version"],
        "start_cmd": ["lua-language-server"],
        "root_markers": [".luarc.json"],
        "file_extensions": [".lua"],
        "capabilities": ["definition", "references", "rename", "diagnostics", "hover", "completion"],
    },
}


# Global LSP server registry - singleton per language:root_uri
_GLOBAL_SERVERS: Dict[str, "LSPServer"] = {}
_GLOBAL_LOCK = asyncio.Lock()
_CLEANUP_REGISTERED = False

logger = logging.getLogger(__name__)


def _cleanup_all_servers():
    """Cleanup all LSP servers on process exit."""
    for server in _GLOBAL_SERVERS.values():
        if server.process and server.process.returncode is None:
            try:
                server.process.terminate()
            except Exception:
                pass
    _GLOBAL_SERVERS.clear()


@dataclass
class LSPServer:
    """Represents an LSP server instance."""

    language: str
    process: Optional[asyncio.subprocess.Process]
    config: Dict[str, Any]
    root_uri: str
    initialized: bool = False
    request_id: int = field(default=0)
    pending_responses: Dict[int, asyncio.Future] = field(default_factory=dict)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def next_id(self) -> int:
        """Get next request ID."""
        self.request_id += 1
        return self.request_id


class LSPTool(BaseTool):
    """Language Server Protocol tool for code intelligence."""

    name = "lsp"
    
    @property
    def description(self) -> str:
        return """Language Server Protocol tool for code intelligence.
    
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
        global _CLEANUP_REGISTERED
        if not _CLEANUP_REGISTERED:
            atexit.register(_cleanup_all_servers)
            _CLEANUP_REGISTERED = True

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
        logger.info(f"Installing {config['name']} for {language}")
        try:
            installer = config["install_cmd"][0]
            if not shutil.which(installer):
                logger.error(f"Installer {installer} not found")
                return False
            result = await asyncio.create_subprocess_exec(
                *config["install_cmd"],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()
            if result.returncode != 0:
                logger.error(f"Installation failed: {stderr.decode()}")
                return False
            logger.info(f"Successfully installed {config['name']}")
            return True
        except Exception as e:
            logger.error(f"Installation error: {e}")
            return False

    async def _ensure_lsp_running(self, language: str, root_uri: str) -> Optional[LSPServer]:
        """Ensure LSP server is running for language."""
        server_key = f"{language}:{root_uri}"
        if server_key in _GLOBAL_SERVERS:
            server = _GLOBAL_SERVERS[server_key]
            if server.process and server.process.returncode is None:
                return server

        async with _GLOBAL_LOCK:
            if server_key in _GLOBAL_SERVERS:
                server = _GLOBAL_SERVERS[server_key]
                if server.process and server.process.returncode is None:
                    return server
                del _GLOBAL_SERVERS[server_key]

            if not await self._check_lsp_installed(language):
                if not await self._install_lsp(language):
                    return None

            config = LSP_SERVERS[language]
            try:
                process = await asyncio.create_subprocess_exec(
                    *config["start_cmd"],
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=root_uri,
                )
                server = LSPServer(language=language, process=process, config=config, root_uri=root_uri)
                if not await self._initialize_lsp(server):
                    if server.process:
                        server.process.terminate()
                    return None
                _GLOBAL_SERVERS[server_key] = server
                logger.info(f"Started global LSP server: {config['name']} for {root_uri}")
                return server
            except Exception as e:
                logger.error(f"Failed to start LSP: {e}")
                return None

    async def _initialize_lsp(self, server: LSPServer) -> bool:
        """Send initialize request to LSP server."""
        init_params = {
            "processId": os.getpid(),
            "rootUri": f"file://{server.root_uri}",
            "rootPath": server.root_uri,
            "capabilities": {
                "workspace": {"workspaceFolders": True, "applyEdit": True},
                "textDocument": {
                    "synchronization": {"dynamicRegistration": True, "didSave": True},
                    "completion": {"completionItem": {"snippetSupport": True}},
                    "hover": {"contentFormat": ["markdown", "plaintext"]},
                    "definition": {"dynamicRegistration": True, "linkSupport": True},
                    "references": {"dynamicRegistration": True},
                    "rename": {"dynamicRegistration": True, "prepareSupport": True},
                },
            },
            "workspaceFolders": [{"uri": f"file://{server.root_uri}", "name": Path(server.root_uri).name}],
        }
        request = {"jsonrpc": "2.0", "id": server.next_id(), "method": "initialize", "params": init_params}
        response = await self._send_request(server, request, timeout=60.0)
        if not response or "error" in response:
            logger.error(f"Failed to initialize LSP: {response}")
            return False
        await self._send_notification(server, "initialized", {})
        server.initialized = True
        return True

    async def _read_lsp_message(self, server: LSPServer, timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """Read a single LSP message from server stdout."""
        if not server.process or not server.process.stdout:
            return None
        try:
            headers = {}
            while True:
                line = await asyncio.wait_for(server.process.stdout.readline(), timeout=timeout)
                if not line:
                    return None
                line_str = line.decode("utf-8").strip()
                if not line_str:
                    break
                if ":" in line_str:
                    key, value = line_str.split(":", 1)
                    headers[key.strip().lower()] = value.strip()
            content_length = int(headers.get("content-length", 0))
            if content_length == 0:
                return None
            content = await asyncio.wait_for(server.process.stdout.read(content_length), timeout=timeout)
            return json.loads(content.decode("utf-8"))
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error(f"Error reading LSP message: {e}")
            return None

    async def _send_request(self, server: LSPServer, request: Dict[str, Any], timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """Send JSON-RPC request to LSP server and wait for response."""
        if not server.process or server.process.returncode is not None or not server.process.stdin:
            return None
        import time
        async with server.lock:
            try:
                request_str = json.dumps(request)
                content = request_str.encode("utf-8")
                header = f"Content-Length: {len(content)}\r\n\r\n"
                server.process.stdin.write(header.encode("utf-8") + content)
                await server.process.stdin.drain()
                request_id = request.get("id")
                start_time = time.monotonic()
                deadline = start_time + timeout
                while time.monotonic() < deadline:
                    remaining = max(0.1, deadline - time.monotonic())
                    response = await self._read_lsp_message(server, timeout=remaining)
                    if response is None:
                        if server.process.returncode is not None:
                            return None
                        continue
                    if "id" in response and response["id"] == request_id:
                        return response
                return None
            except Exception as e:
                logger.error(f"LSP communication error: {e}")
                return None

    async def _send_notification(self, server: LSPServer, method: str, params: Dict[str, Any]) -> bool:
        """Send JSON-RPC notification (no response expected)."""
        if not server.process or server.process.returncode is not None or not server.process.stdin:
            return False
        try:
            notification = {"jsonrpc": "2.0", "method": method, "params": params}
            content = json.dumps(notification).encode("utf-8")
            header = f"Content-Length: {len(content)}\r\n\r\n"
            server.process.stdin.write(header.encode("utf-8") + content)
            await server.process.stdin.drain()
            return True
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False

    async def run(self, action: str, file: str, line: Optional[int] = None, character: Optional[int] = None, new_name: Optional[str] = None, **kwargs) -> MCPResourceDocument:
        """Execute LSP action."""
        valid_actions = ["definition", "references", "rename", "diagnostics", "hover", "completion", "status"]
        if action not in valid_actions:
            return MCPResourceDocument(data={"error": f"Invalid action. Must be one of: {', '.join(valid_actions)}"})

        language = self._get_language_from_file(file)
        if not language:
            return MCPResourceDocument(data={"error": f"Unsupported file type: {file}", "supported_languages": list(LSP_SERVERS.keys())})

        capabilities = LSP_SERVERS[language]["capabilities"]
        if action not in capabilities and action != "status":
            return MCPResourceDocument(data={"error": f"Action '{action}' not supported for {language}", "supported_actions": capabilities})

        if action == "status":
            installed = await self._check_lsp_installed(language)
            return MCPResourceDocument(data={"language": language, "lsp_server": LSP_SERVERS[language]["name"], "installed": installed, "capabilities": capabilities})

        root_uri = self._find_project_root(file, language)
        server = await self._ensure_lsp_running(language, root_uri)
        if not server:
            return MCPResourceDocument(data={"error": f"Failed to start LSP server for {language}", "install_command": " ".join(LSP_SERVERS[language]["install_cmd"])})

        result = await self._execute_lsp_action(server, action, file, line, character, new_name)
        return MCPResourceDocument(data=result)

    async def call(self, **kwargs) -> str:
        """Tool interface for MCP - converts result to JSON string."""
        result = await self.run(**kwargs)
        return result.to_json_string()

    def register(self, mcp_server) -> None:
        """Register tool with MCP server."""
        @mcp_server.tool(name=self.name, description=self.description)
        async def lsp_handler(action: str, file: str, line: Optional[int] = None, character: Optional[int] = None, new_name: Optional[str] = None) -> str:
            return await self.call(action=action, file=file, line=line, character=character, new_name=new_name)

    async def _open_document(self, server: LSPServer, file_path: str) -> bool:
        """Notify LSP server that a document is opened."""
        abs_path = str(Path(file_path).resolve())
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return False
        language_id = server.language
        if server.language == "typescript":
            ext = Path(file_path).suffix.lower()
            if ext in [".tsx", ".jsx"]:
                language_id = "typescriptreact" if "ts" in ext else "javascriptreact"
            elif ext in [".js", ".mjs", ".cjs"]:
                language_id = "javascript"
        params = {"textDocument": {"uri": f"file://{abs_path}", "languageId": language_id, "version": 1, "text": content}}
        return await self._send_notification(server, "textDocument/didOpen", params)

    def _parse_location(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LSP Location into a readable format."""
        uri = location.get("uri", "")
        file_path = uri.replace("file://", "") if uri.startswith("file://") else uri
        range_info = location.get("range", {})
        start = range_info.get("start", {})
        end = range_info.get("end", {})
        return {
            "file": file_path,
            "start": {"line": start.get("line", 0) + 1, "character": start.get("character", 0)},
            "end": {"line": end.get("line", 0) + 1, "character": end.get("character", 0)},
        }

    async def _execute_lsp_action(self, server: LSPServer, action: str, file: str, line: Optional[int], character: Optional[int], new_name: Optional[str]) -> Dict[str, Any]:
        """Execute specific LSP action."""
        abs_path = str(Path(file).resolve())
        uri = f"file://{abs_path}"
        await self._open_document(server, file)
        position = {"line": (line - 1) if line else 0, "character": character if character else 0}

        if action == "definition":
            request = {"jsonrpc": "2.0", "id": server.next_id(), "method": "textDocument/definition", "params": {"textDocument": {"uri": uri}, "position": position}}
            response = await self._send_request(server, request)
            if response and "result" in response:
                result = response["result"]
                if result is None:
                    return {"action": "definition", "file": file, "result": None, "message": "No definition found"}
                if isinstance(result, list):
                    return {"action": "definition", "file": file, "definitions": [self._parse_location(loc) for loc in result]}
                elif isinstance(result, dict):
                    return {"action": "definition", "file": file, "definition": self._parse_location(result)}
            return {"action": "definition", "file": file, "error": response.get("error") if response else "No response"}

        elif action == "references":
            request = {"jsonrpc": "2.0", "id": server.next_id(), "method": "textDocument/references", "params": {"textDocument": {"uri": uri}, "position": position, "context": {"includeDeclaration": True}}}
            response = await self._send_request(server, request)
            if response and "result" in response:
                result = response["result"]
                refs = [self._parse_location(loc) for loc in result] if isinstance(result, list) else []
                return {"action": "references", "file": file, "references": refs, "count": len(refs)}
            return {"action": "references", "file": file, "error": response.get("error") if response else "No response"}

        elif action == "rename":
            if not new_name:
                return {"action": "rename", "error": "new_name is required for rename action"}
            request = {"jsonrpc": "2.0", "id": server.next_id(), "method": "textDocument/rename", "params": {"textDocument": {"uri": uri}, "position": position, "newName": new_name}}
            response = await self._send_request(server, request)
            if response and "result" in response:
                result = response["result"]
                if result is None:
                    return {"action": "rename", "file": file, "error": "Rename not possible at this location"}
                changes = {}
                if "changes" in result:
                    for file_uri, edits in result["changes"].items():
                        file_path = file_uri.replace("file://", "")
                        changes[file_path] = [{"range": self._parse_location({"uri": file_uri, "range": edit["range"]}), "newText": edit["newText"]} for edit in edits]
                return {"action": "rename", "file": file, "new_name": new_name, "changes": changes, "files_affected": len(changes)}
            return {"action": "rename", "file": file, "error": response.get("error") if response else "No response"}

        elif action == "hover":
            request = {"jsonrpc": "2.0", "id": server.next_id(), "method": "textDocument/hover", "params": {"textDocument": {"uri": uri}, "position": position}}
            response = await self._send_request(server, request)
            if response and "result" in response:
                result = response["result"]
                if result is None:
                    return {"action": "hover", "file": file, "result": None, "message": "No hover info"}
                contents = result.get("contents", "")
                if isinstance(contents, dict):
                    hover_text = contents.get("value", str(contents))
                elif isinstance(contents, list):
                    hover_text = "\n".join(c.get("value", str(c)) if isinstance(c, dict) else str(c) for c in contents)
                else:
                    hover_text = str(contents)
                return {"action": "hover", "file": file, "position": {"line": line, "character": character}, "contents": hover_text}
            return {"action": "hover", "file": file, "error": response.get("error") if response else "No response"}

        elif action == "completion":
            request = {"jsonrpc": "2.0", "id": server.next_id(), "method": "textDocument/completion", "params": {"textDocument": {"uri": uri}, "position": position}}
            response = await self._send_request(server, request, timeout=10.0)
            if response and "result" in response:
                result = response["result"]
                if result is None:
                    return {"action": "completion", "file": file, "completions": [], "count": 0}
                items = result if isinstance(result, list) else result.get("items", [])
                completions = [{"label": item.get("label", ""), "kind": item.get("kind", 0), "detail": item.get("detail", "")} for item in items[:50]]
                return {"action": "completion", "file": file, "position": {"line": line, "character": character}, "completions": completions, "count": len(completions)}
            return {"action": "completion", "file": file, "error": response.get("error") if response else "No response"}

        elif action == "diagnostics":
            return {"action": "diagnostics", "file": file, "note": "Diagnostics are push-based; use language-specific tools (go vet, pylint, etc.) for on-demand checking"}

        return {"error": f"Unknown action: {action}"}

    async def cleanup(self):
        """Clean up LSP servers."""
        async with _GLOBAL_LOCK:
            for server in list(_GLOBAL_SERVERS.values()):
                if server.process and server.process.returncode is None:
                    try:
                        server.process.terminate()
                        await asyncio.wait_for(server.process.wait(), timeout=5.0)
                    except:
                        pass
            _GLOBAL_SERVERS.clear()


def create_lsp_tool():
    """Factory function to create LSP tool."""
    return LSPTool()
