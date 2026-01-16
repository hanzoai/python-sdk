"""Language Server Protocol (LSP) tool for code intelligence.

This tool provides on-demand LSP configuration and installation for various
programming languages. It automatically installs language servers as needed
and provides code intelligence features like go-to-definition, find references,
rename symbol, and diagnostics.
"""

import os
import json
import atexit
import shutil
import asyncio
import logging
import tempfile
import uuid
from urllib.parse import unquote, urlparse
from typing import Any, Dict, List, Optional
from pathlib import Path
from dataclasses import field, dataclass

from hanzo_tools.core import BaseTool, MCPResourceDocument

# LSP server configurations
LSP_SERVERS = {
    "go": {
        "name": "gopls",
        "install_cmd": ["go", "install", "golang.org/x/tools/gopls@latest"],
        "check_cmd": ["gopls", "version"],
        "start_cmd": ["gopls", "serve", "-mode=stdio"],
        "root_markers": ["go.work", "go.mod", "go.sum"],
        "file_extensions": [".go"],
        "capabilities": ["definition", "references", "rename", "diagnostics", "hover", "completion"],
        "env": {"GOWORK": "auto"},
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
    - code_action: Run LSP code actions
    - organize_imports: Organize imports for a file
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
        path = Path(file_path).resolve()
        if language == "go":
            try:
                return str(self._find_go_workspace_root(path))
            except FileNotFoundError:
                return str(path.parent)
        markers = LSP_SERVERS[language]["root_markers"]
        for parent in path.parents:
            for marker in markers:
                if (parent / marker).is_file():
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
                env = os.environ.copy()
                env.update(config.get("env", {}))
                process = await asyncio.create_subprocess_exec(
                    *config["start_cmd"],
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=root_uri,
                    env=env,
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
        root_uri = Path(server.root_uri).resolve().as_uri()
        init_params = {
            "processId": os.getpid(),
            "rootUri": root_uri,
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
            "workspaceFolders": [{"uri": root_uri, "name": Path(server.root_uri).name}],
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

    async def _send_request(
        self, server: LSPServer, request: Dict[str, Any], timeout: float = 30.0
    ) -> Optional[Dict[str, Any]]:
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

    async def run(
        self,
        action: str,
        file: str,
        line: Optional[int] = None,
        character: Optional[int] = None,
        new_name: Optional[str] = None,
        apply_edits: bool = False,
        **kwargs,
    ) -> MCPResourceDocument:
        """Execute LSP action."""
        valid_actions = [
            "definition",
            "references",
            "rename",
            "diagnostics",
            "hover",
            "completion",
            "code_action",
            "organize_imports",
            "status",
        ]
        if action not in valid_actions:
            return MCPResourceDocument(data={"error": f"Invalid action. Must be one of: {', '.join(valid_actions)}"})

        language = self._get_language_from_file(file)
        if not language:
            return MCPResourceDocument(
                data={"error": f"Unsupported file type: {file}", "supported_languages": list(LSP_SERVERS.keys())}
            )

        capabilities = LSP_SERVERS[language]["capabilities"]
        if action not in capabilities and action not in ["status", "organize_imports", "code_action"]:
            return MCPResourceDocument(
                data={"error": f"Action '{action}' not supported for {language}", "supported_actions": capabilities}
            )

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

        root_uri = self._find_project_root(file, language)
        server = await self._ensure_lsp_running(language, root_uri)
        if not server:
            return MCPResourceDocument(
                data={
                    "error": f"Failed to start LSP server for {language}",
                    "install_command": " ".join(LSP_SERVERS[language]["install_cmd"]),
                }
            )

        result = await self._execute_lsp_action(
            server,
            action,
            file,
            line,
            character,
            new_name,
            apply_edits,
            range_spec=kwargs.get("range"),
            only=kwargs.get("only"),
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
            apply_edits: bool = False,
            only: Optional[List[str]] = None,
            range: Optional[Dict[str, Dict[str, int]]] = None,
        ) -> str:
            return await self.call(
                action=action,
                file=file,
                line=line,
                character=character,
                new_name=new_name,
                apply_edits=apply_edits,
                only=only,
                range=range,
            )

    def _path_to_uri(self, path: str) -> str:
        return Path(path).resolve().as_uri()

    def _uri_to_path(self, uri: str) -> str:
        if uri.startswith("file://"):
            parsed = urlparse(uri)
            path = unquote(parsed.path)
            if path.startswith("/") and len(path) >= 3 and path[2] == ":" and path[1].isalpha():
                path = path[1:]
            return path
        return uri

    def _find_go_workspace_root(self, start: Path) -> Path:
        p = start.resolve()
        if p.is_file():
            p = p.parent
        for d in (p, *p.parents):
            work = d / "go.work"
            if work.is_file():
                return d
        for d in (p, *p.parents):
            mod = d / "go.mod"
            if mod.is_file():
                return d
        raise FileNotFoundError(f"no go.work or go.mod found above {start}")

    def _is_within_root(self, path: str, root_dir: str) -> bool:
        try:
            Path(path).resolve().relative_to(Path(root_dir).resolve())
            return True
        except Exception:
            return False

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
        params = {"textDocument": {"uri": self._path_to_uri(abs_path), "languageId": language_id, "version": 1, "text": content}}
        return await self._send_notification(server, "textDocument/didOpen", params)

    def _parse_location(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LSP Location into a readable format."""
        uri = location.get("uri", "")
        file_path = self._uri_to_path(uri)
        range_info = location.get("range", {})
        start = range_info.get("start", {})
        end = range_info.get("end", {})
        return {
            "file": file_path,
            "start": {"line": start.get("line", 0) + 1, "character": start.get("character", 0)},
            "end": {"line": end.get("line", 0) + 1, "character": end.get("character", 0)},
        }

    def _utf16_index_to_py_index(self, text: str, utf16_index: int) -> int:
        if utf16_index <= 0:
            return 0
        units = 0
        for idx, ch in enumerate(text):
            units += 2 if ord(ch) > 0xFFFF else 1
            if units >= utf16_index:
                return idx + 1
        return len(text)

    def _utf16_len(self, text: str) -> int:
        units = 0
        for ch in text:
            units += 2 if ord(ch) > 0xFFFF else 1
        return units

    def _lsp_position_to_offset(self, lines: List[str], line: int, character: int) -> int:
        if line < 0:
            return 0
        if line >= len(lines):
            return sum(len(l) for l in lines)
        offset = sum(len(l) for l in lines[:line])
        line_text = lines[line]
        return offset + self._utf16_index_to_py_index(line_text, character)

    def _file_range_for_code_action(self, file_path: str) -> Dict[str, Dict[str, int]]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 0}}
        if not content:
            return {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 0}}
        lines = content.splitlines()
        last_line_index = len(lines) - 1
        end_char = self._utf16_len(lines[last_line_index])
        return {"start": {"line": 0, "character": 0}, "end": {"line": last_line_index, "character": end_char}}

    def _apply_text_edits(self, file_path: str, edits: List[Dict[str, Any]]) -> None:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        content = self._render_text_edits(content, edits)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _render_text_edits(self, content: str, edits: List[Dict[str, Any]]) -> str:
        lines = content.splitlines(keepends=True)
        normalized = []
        for edit in edits:
            range_info = edit.get("range", {})
            start = range_info.get("start", {})
            end = range_info.get("end", {})
            start_offset = self._lsp_position_to_offset(
                lines, start.get("line", 0), start.get("character", 0)
            )
            end_offset = self._lsp_position_to_offset(
                lines, end.get("line", 0), end.get("character", 0)
            )
            normalized.append(
                (
                    start.get("line", 0),
                    start.get("character", 0),
                    start_offset,
                    end_offset,
                    edit.get("newText", ""),
                )
            )
        normalized.sort(key=lambda item: (item[0], item[1]), reverse=True)
        for _, _, start_offset, end_offset, new_text in normalized:
            content = content[:start_offset] + new_text + content[end_offset:]
        return content

    def _workspace_edit_files(self, edit: Dict[str, Any]) -> List[str]:
        files: List[str] = []
        if "documentChanges" in edit:
            for change in edit["documentChanges"]:
                if "kind" in change:
                    if change.get("kind") == "rename":
                        files.append(self._uri_to_path(change.get("oldUri", "")))
                        files.append(self._uri_to_path(change.get("newUri", "")))
                    elif change.get("kind") in ["create", "delete"]:
                        files.append(self._uri_to_path(change.get("uri", "")))
                elif "textDocument" in change:
                    files.append(self._uri_to_path(change["textDocument"]["uri"]))
        elif "changes" in edit:
            for uri in edit["changes"].keys():
                files.append(self._uri_to_path(uri))
        return sorted({f for f in files if f})

    def _apply_workspace_edit(self, edit: Dict[str, Any], root_dir: str) -> tuple[list[str], list[str]]:
        applied: list[str] = []
        errors: list[str] = []
        root_dir = str(Path(root_dir).resolve())

        changes = edit.get("documentChanges")
        if changes is None:
            changes = [{"textDocument": {"uri": uri}, "edits": edits} for uri, edits in edit.get("changes", {}).items()]

        if not changes:
            return applied, errors

        backup_dir = Path(tempfile.mkdtemp(prefix="hanzo-lsp-", dir=root_dir))
        backups: Dict[str, str] = {}
        mtimes: Dict[str, float] = {}
        created: set[str] = set()

        def backup_path(path: str) -> str:
            rel = os.path.relpath(path, root_dir)
            dst = backup_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            return str(dst)

        try:
            # Preflight: collect backups
            for change in changes:
                if "kind" in change:
                    kind = change.get("kind")
                    if kind == "rename":
                        old_path = self._uri_to_path(change.get("oldUri", ""))
                        new_path = self._uri_to_path(change.get("newUri", ""))
                        if not self._is_within_root(old_path, root_dir) or not self._is_within_root(
                            new_path, root_dir
                        ):
                            raise RuntimeError(f"rename outside workspace root: {old_path} -> {new_path}")
                        if os.path.exists(old_path) and old_path not in backups:
                            backups[old_path] = backup_path(old_path)
                            shutil.copy2(old_path, backups[old_path])
                            mtimes[old_path] = os.path.getmtime(old_path)
                        if os.path.exists(new_path) and new_path not in backups:
                            backups[new_path] = backup_path(new_path)
                            shutil.copy2(new_path, backups[new_path])
                            mtimes[new_path] = os.path.getmtime(new_path)
                    elif kind == "create":
                        file_path = self._uri_to_path(change.get("uri", ""))
                        if not self._is_within_root(file_path, root_dir):
                            raise RuntimeError(f"create outside workspace root: {file_path}")
                        if os.path.exists(file_path) and file_path not in backups:
                            backups[file_path] = backup_path(file_path)
                            shutil.copy2(file_path, backups[file_path])
                            mtimes[file_path] = os.path.getmtime(file_path)
                    elif kind == "delete":
                        file_path = self._uri_to_path(change.get("uri", ""))
                        if not self._is_within_root(file_path, root_dir):
                            raise RuntimeError(f"delete outside workspace root: {file_path}")
                        if os.path.exists(file_path) and file_path not in backups:
                            backups[file_path] = backup_path(file_path)
                            shutil.copy2(file_path, backups[file_path])
                            mtimes[file_path] = os.path.getmtime(file_path)
                elif "textDocument" in change and "edits" in change:
                    file_path = self._uri_to_path(change["textDocument"]["uri"])
                    if not self._is_within_root(file_path, root_dir):
                        raise RuntimeError(f"edit outside workspace root: {file_path}")
                    if os.path.exists(file_path) and file_path not in backups:
                        backups[file_path] = backup_path(file_path)
                        shutil.copy2(file_path, backups[file_path])
                        mtimes[file_path] = os.path.getmtime(file_path)

            # Apply changes in order
            for change in changes:
                if "kind" in change:
                    kind = change.get("kind")
                    if kind == "rename":
                        old_path = self._uri_to_path(change.get("oldUri", ""))
                        new_path = self._uri_to_path(change.get("newUri", ""))
                        options = change.get("options", {})
                        if os.path.exists(new_path):
                            if options.get("ignoreIfExists"):
                                continue
                            if not options.get("overwrite"):
                                raise RuntimeError(f"rename target exists: {new_path}")
                        Path(new_path).parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(old_path, new_path)
                        applied.append(new_path)
                        continue
                    if kind == "create":
                        file_path = self._uri_to_path(change.get("uri", ""))
                        options = change.get("options", {})
                        if os.path.exists(file_path):
                            if options.get("ignoreIfExists"):
                                continue
                            if not options.get("overwrite"):
                                raise RuntimeError(f"create target exists: {file_path}")
                        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(change.get("content", ""))
                        created.add(file_path)
                        applied.append(file_path)
                        continue
                    if kind == "delete":
                        file_path = self._uri_to_path(change.get("uri", ""))
                        options = change.get("options", {})
                        if not os.path.exists(file_path):
                            if options.get("ignoreIfNotExists"):
                                continue
                            raise RuntimeError(f"delete target missing: {file_path}")
                        if os.path.isdir(file_path):
                            if not options.get("recursive"):
                                raise RuntimeError(f"delete target is directory: {file_path}")
                            shutil.rmtree(file_path)
                        else:
                            os.unlink(file_path)
                        applied.append(file_path)
                        continue
                    raise RuntimeError(f"unsupported documentChange: {kind}")

                if "textDocument" in change and "edits" in change:
                    file_path = self._uri_to_path(change["textDocument"]["uri"])
                    if file_path in mtimes and os.path.exists(file_path):
                        if os.path.getmtime(file_path) != mtimes[file_path]:
                            raise RuntimeError(f"conflict detected for {file_path}")
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    updated = self._render_text_edits(content, change["edits"])
                    temp_path = f"{file_path}.hanzo_tmp_{uuid.uuid4().hex}"
                    with open(temp_path, "w", encoding="utf-8") as f:
                        f.write(updated)
                    os.replace(temp_path, file_path)
                    applied.append(file_path)
                else:
                    raise RuntimeError(f"unsupported documentChange: {change.get('kind', 'unknown')}")

        except Exception as exc:
            errors.append(str(exc))
            # Rollback
            for path, backup in backups.items():
                try:
                    Path(path).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup, path)
                except Exception:
                    pass
            for path in created:
                if path not in backups:
                    try:
                        if os.path.isdir(path):
                            shutil.rmtree(path)
                        else:
                            os.unlink(path)
                    except Exception:
                        pass
            applied = []
        finally:
            shutil.rmtree(backup_dir, ignore_errors=True)

        return applied, errors

    async def _execute_lsp_action(
        self,
        server: LSPServer,
        action: str,
        file: str,
        line: Optional[int],
        character: Optional[int],
        new_name: Optional[str],
        apply_edits: bool,
        range_spec: Optional[Dict[str, Any]] = None,
        only: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Execute specific LSP action."""
        abs_path = str(Path(file).resolve())
        uri = self._path_to_uri(abs_path)
        await self._open_document(server, file)
        position = {"line": (line - 1) if line else 0, "character": character if character else 0}

        if action == "definition":
            request = {
                "jsonrpc": "2.0",
                "id": server.next_id(),
                "method": "textDocument/definition",
                "params": {"textDocument": {"uri": uri}, "position": position},
            }
            response = await self._send_request(server, request)
            if response and "result" in response:
                result = response["result"]
                if result is None:
                    return {"action": "definition", "file": file, "result": None, "message": "No definition found"}
                if isinstance(result, list):
                    return {
                        "action": "definition",
                        "file": file,
                        "definitions": [self._parse_location(loc) for loc in result],
                    }
                elif isinstance(result, dict):
                    return {"action": "definition", "file": file, "definition": self._parse_location(result)}
            return {"action": "definition", "file": file, "error": response.get("error") if response else "No response"}

        elif action == "references":
            request = {
                "jsonrpc": "2.0",
                "id": server.next_id(),
                "method": "textDocument/references",
                "params": {"textDocument": {"uri": uri}, "position": position, "context": {"includeDeclaration": True}},
            }
            response = await self._send_request(server, request)
            if response and "result" in response:
                result = response["result"]
                refs = [self._parse_location(loc) for loc in result] if isinstance(result, list) else []
                return {"action": "references", "file": file, "references": refs, "count": len(refs)}
            return {"action": "references", "file": file, "error": response.get("error") if response else "No response"}

        elif action == "rename":
            if not new_name:
                return {"action": "rename", "error": "new_name is required for rename action"}
            request = {
                "jsonrpc": "2.0",
                "id": server.next_id(),
                "method": "textDocument/rename",
                "params": {"textDocument": {"uri": uri}, "position": position, "newName": new_name},
            }
            response = await self._send_request(server, request)
            if response and "result" in response:
                result = response["result"]
                if result is None:
                    return {"action": "rename", "file": file, "error": "Rename not possible at this location"}
                changes = {}
                if "changes" in result:
                    for file_uri, edits in result["changes"].items():
                        file_path = self._uri_to_path(file_uri)
                        changes[file_path] = [
                            {
                                "range": self._parse_location({"uri": file_uri, "range": edit["range"]}),
                                "newText": edit["newText"],
                            }
                            for edit in edits
                        ]
                applied = []
                apply_errors: List[str] = []
                touched_files = self._workspace_edit_files(result)
                if apply_edits:
                    applied, apply_errors = self._apply_workspace_edit(result, server.root_uri)
                payload: Dict[str, Any] = {
                    "action": "rename",
                    "file": file,
                    "new_name": new_name,
                    "changes": changes,
                    "files_affected": len(changes),
                    "touched_files": touched_files,
                }
                if apply_edits:
                    payload["applied_files"] = applied
                    if apply_errors:
                        payload["apply_errors"] = apply_errors
                return payload
            return {"action": "rename", "file": file, "error": response.get("error") if response else "No response"}

        elif action == "hover":
            request = {
                "jsonrpc": "2.0",
                "id": server.next_id(),
                "method": "textDocument/hover",
                "params": {"textDocument": {"uri": uri}, "position": position},
            }
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
                return {
                    "action": "hover",
                    "file": file,
                    "position": {"line": line, "character": character},
                    "contents": hover_text,
                }
            return {"action": "hover", "file": file, "error": response.get("error") if response else "No response"}

        elif action == "completion":
            request = {
                "jsonrpc": "2.0",
                "id": server.next_id(),
                "method": "textDocument/completion",
                "params": {"textDocument": {"uri": uri}, "position": position},
            }
            response = await self._send_request(server, request, timeout=10.0)
            if response and "result" in response:
                result = response["result"]
                if result is None:
                    return {"action": "completion", "file": file, "completions": [], "count": 0}
                items = result if isinstance(result, list) else result.get("items", [])
                completions = [
                    {"label": item.get("label", ""), "kind": item.get("kind", 0), "detail": item.get("detail", "")}
                    for item in items[:50]
                ]
                return {
                    "action": "completion",
                    "file": file,
                    "position": {"line": line, "character": character},
                    "completions": completions,
                    "count": len(completions),
                }
            return {"action": "completion", "file": file, "error": response.get("error") if response else "No response"}

        elif action == "code_action":
            action_range = range_spec or self._file_range_for_code_action(abs_path)
            context: Dict[str, Any] = {}
            if only:
                context["only"] = only
            request = {
                "jsonrpc": "2.0",
                "id": server.next_id(),
                "method": "textDocument/codeAction",
                "params": {
                    "textDocument": {"uri": uri},
                    "range": action_range,
                    "context": context,
                },
            }
            response = await self._send_request(server, request)
            if response and "result" in response:
                actions = response["result"] or []
                edits_applied: list[str] = []
                apply_errors: list[str] = []
                touched_files: list[str] = []
                commands: list[Dict[str, Any]] = []
                edits_seen = 0
                for action_item in actions:
                    if "edit" in action_item:
                        edits_seen += 1
                        touched_files.extend(self._workspace_edit_files(action_item["edit"]))
                        if apply_edits:
                            applied, errors = self._apply_workspace_edit(action_item["edit"], server.root_uri)
                            edits_applied.extend(applied)
                            apply_errors.extend(errors)
                    if "command" in action_item:
                        commands.append(action_item["command"])
                payload: Dict[str, Any] = {
                    "action": "code_action",
                    "file": file,
                    "edits_found": edits_seen,
                    "touched_files": sorted(set(touched_files)),
                    "commands": commands,
                }
                if apply_edits:
                    payload["applied_files"] = edits_applied
                    if apply_errors:
                        payload["apply_errors"] = apply_errors
                return payload
            return {
                "action": "code_action",
                "file": file,
                "error": response.get("error") if response else "No response",
            }

        elif action == "organize_imports":
            file_range = self._file_range_for_code_action(abs_path)
            request = {
                "jsonrpc": "2.0",
                "id": server.next_id(),
                "method": "textDocument/codeAction",
                "params": {
                    "textDocument": {"uri": uri},
                    "range": file_range,
                    "context": {"only": ["source.organizeImports"]},
                },
            }
            response = await self._send_request(server, request)
            if response and "result" in response:
                actions = response["result"] or []
                edits_applied: list[str] = []
                apply_errors: list[str] = []
                edits_seen = 0
                touched_files: list[str] = []
                for action_item in actions:
                    kind = action_item.get("kind")
                    if kind and kind != "source.organizeImports":
                        continue
                    if "edit" in action_item:
                        edits_seen += 1
                        touched_files.extend(self._workspace_edit_files(action_item["edit"]))
                        if apply_edits:
                            applied, errors = self._apply_workspace_edit(action_item["edit"], server.root_uri)
                            edits_applied.extend(applied)
                            apply_errors.extend(errors)
                payload: Dict[str, Any] = {
                    "action": "organize_imports",
                    "file": file,
                    "edits_found": edits_seen,
                    "touched_files": sorted(set(touched_files)),
                }
                if apply_edits:
                    payload["applied_files"] = edits_applied
                    if apply_errors:
                        payload["apply_errors"] = apply_errors
                return payload
            return {
                "action": "organize_imports",
                "file": file,
                "error": response.get("error") if response else "No response",
            }

        elif action == "diagnostics":
            return {
                "action": "diagnostics",
                "file": file,
                "note": "Diagnostics are push-based; use language-specific tools (go vet, pylint, etc.) for on-demand checking",
            }

        return {"error": f"Unknown action: {action}"}

    async def cleanup(self):
        """Clean up LSP servers."""
        async with _GLOBAL_LOCK:
            for server in list(_GLOBAL_SERVERS.values()):
                if server.process and server.process.returncode is None:
                    try:
                        server.process.terminate()
                        await asyncio.wait_for(server.process.wait(), timeout=5.0)
                    except Exception:
                        pass
            _GLOBAL_SERVERS.clear()


def create_lsp_tool():
    """Factory function to create LSP tool."""
    return LSPTool()
