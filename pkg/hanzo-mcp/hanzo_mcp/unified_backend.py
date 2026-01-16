#!/usr/bin/env python3
"""
Hanzo Unified MCP Backend
========================

Core backend service that powers all MCP interfaces (VS Code, browser, CLI, MCP server).
Implements the 6 universal tools: edit, fmt, test, build, lint, guard.

Features:
- Unified session logging to ~/.hanzo/sessions/<id>
- Codebase intelligence with SQLite vector storage
- LSP integration for semantic operations
- Workspace-aware operations with go.work support
- Cross-language tool execution
"""

import asyncio
import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Literal
from dataclasses import dataclass, asdict
import subprocess

from pydantic import BaseModel, Field


# Core Types
@dataclass
class ToolResult:
    """Standard result format for all tools"""
    ok: bool
    root: str
    language_used: Union[str, List[str]]
    backend_used: Union[str, List[str]]
    scope_resolved: Union[str, List[str]]
    touched_files: List[str]
    stdout: str
    stderr: str
    exit_code: int
    errors: List[str]
    execution_time: float
    session_id: str


class TargetSpec(BaseModel):
    """Target specification for tool operations"""
    target: str = Field(..., description="file:<path>, dir:<path>, pkg:<spec>, ws, or changed")
    language: str = Field(default="auto", description="Language override")
    backend: str = Field(default="auto", description="Backend override") 
    root: Optional[str] = Field(default=None, description="Workspace root override")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    dry_run: bool = Field(default=False, description="Preview mode")


class WorkspaceDetector:
    """Intelligent workspace detection with go.work support"""
    
    @staticmethod
    def detect(target_path: str) -> Dict[str, Any]:
        """Detect workspace root and configuration"""
        path = Path(target_path).absolute()
        
        # Walk up to find workspace markers
        for current in [path] + list(path.parents):
            # Check for various workspace indicators
            if (current / "go.work").exists():
                return {
                    "root": str(current),
                    "type": "go_workspace",
                    "config": current / "go.work",
                    "language": "go"
                }
            elif (current / "package.json").exists():
                return {
                    "root": str(current), 
                    "type": "node_workspace",
                    "config": current / "package.json",
                    "language": "ts"
                }
            elif (current / "pyproject.toml").exists():
                return {
                    "root": str(current),
                    "type": "python_workspace", 
                    "config": current / "pyproject.toml",
                    "language": "py"
                }
            elif (current / "Cargo.toml").exists():
                return {
                    "root": str(current),
                    "type": "rust_workspace",
                    "config": current / "Cargo.toml", 
                    "language": "rs"
                }
            elif (current / ".git").exists():
                return {
                    "root": str(current),
                    "type": "git_repository",
                    "config": current / ".git",
                    "language": "auto"
                }
        
        # Default to current directory
        return {
            "root": str(path.parent if path.is_file() else path),
            "type": "directory",
            "config": None,
            "language": "auto"
        }


class SessionManager:
    """Manages logging and session tracking"""
    
    def __init__(self):
        self.hanzo_dir = Path.home() / ".hanzo"
        self.sessions_dir = self.hanzo_dir / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.current_session = str(uuid.uuid4())
        self.session_file = self.sessions_dir / f"{self.current_session}.jsonl"
    
    def log_tool_execution(self, tool_name: str, args: Dict, result: ToolResult):
        """Log tool execution to JSONL"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": self.current_session,
            "tool": tool_name,
            "args": args,
            "result": asdict(result),
            "user": os.getenv("USER", "unknown"),
            "cwd": os.getcwd()
        }
        
        with open(self.session_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """Get recent session activity"""
        sessions = []
        for session_file in sorted(self.sessions_dir.glob("*.jsonl"), reverse=True)[:limit]:
            with open(session_file) as f:
                session_data = [json.loads(line) for line in f]
                if session_data:
                    sessions.append({
                        "session_id": session_file.stem,
                        "start_time": session_data[0]["timestamp"],
                        "tool_count": len(session_data),
                        "tools_used": list(set(entry["tool"] for entry in session_data))
                    })
        return sessions


class CodebaseIndexer:
    """SQLite-based codebase intelligence"""
    
    def __init__(self, hanzo_dir: Path):
        self.db_path = hanzo_dir / "codebase.db"
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with vector storage"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY,
                    path TEXT UNIQUE NOT NULL,
                    content_hash TEXT NOT NULL,
                    language TEXT,
                    size INTEGER,
                    modified_time REAL,
                    indexed_time REAL DEFAULT (julianday('now'))
                );
                
                CREATE TABLE IF NOT EXISTS symbols (
                    id INTEGER PRIMARY KEY,
                    file_id INTEGER REFERENCES files(id),
                    name TEXT NOT NULL,
                    kind TEXT NOT NULL, -- function, class, variable, etc
                    line_start INTEGER,
                    line_end INTEGER,
                    definition TEXT,
                    UNIQUE(file_id, name, line_start)
                );
                
                CREATE TABLE IF NOT EXISTS imports (
                    id INTEGER PRIMARY KEY,
                    file_id INTEGER REFERENCES files(id),
                    import_path TEXT NOT NULL,
                    alias TEXT,
                    line_number INTEGER
                );
                
                CREATE TABLE IF NOT EXISTS dependencies (
                    id INTEGER PRIMARY KEY,
                    from_file_id INTEGER REFERENCES files(id),
                    to_file_id INTEGER REFERENCES files(id),
                    relationship TEXT NOT NULL, -- imports, calls, extends, etc
                    UNIQUE(from_file_id, to_file_id, relationship)
                );
                
                CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);
                CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);
                CREATE INDEX IF NOT EXISTS idx_imports_path ON imports(import_path);
            """)
    
    def index_file(self, file_path: str, content: str, language: str):
        """Index a single file for intelligent search"""
        import hashlib
        
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        file_size = len(content.encode())
        modified_time = os.path.getmtime(file_path)
        
        with sqlite3.connect(self.db_path) as conn:
            # Insert or update file record
            conn.execute("""
                INSERT OR REPLACE INTO files (path, content_hash, language, size, modified_time)
                VALUES (?, ?, ?, ?, ?)
            """, (file_path, content_hash, language, file_size, modified_time))
            
            file_id = conn.lastrowid
            
            # TODO: Extract symbols, imports, and dependencies based on language
            # This would use language-specific parsers or LSP
            
    def search_symbols(self, query: str, language: Optional[str] = None) -> List[Dict]:
        """Search for symbols across codebase"""
        with sqlite3.connect(self.db_path) as conn:
            sql = """
                SELECT f.path, s.name, s.kind, s.line_start, s.definition
                FROM symbols s
                JOIN files f ON s.file_id = f.id
                WHERE s.name LIKE ?
            """
            params = [f"%{query}%"]
            
            if language:
                sql += " AND f.language = ?"
                params.append(language)
            
            cursor = conn.execute(sql, params)
            return [
                {
                    "path": row[0],
                    "name": row[1], 
                    "kind": row[2],
                    "line": row[3],
                    "definition": row[4]
                }
                for row in cursor.fetchall()
            ]


class LSPBridge:
    """Unified LSP client for cross-language operations"""
    
    LSP_SERVERS = {
        "go": "gopls",
        "ts": "typescript-language-server",
        "py": "pyright",
        "rs": "rust-analyzer", 
        "cc": "clangd",
        "sol": "solidity-language-server"
    }
    
    def __init__(self):
        self.active_servers = {}
    
    async def start_server(self, language: str, workspace_root: str):
        """Start LSP server for language"""
        # Implementation would start LSP server process
        # and handle communication via JSON-RPC
        pass
    
    async def rename_symbol(self, file_path: str, line: int, character: int, new_name: str):
        """Perform LSP rename operation"""
        # Implementation would send LSP rename request
        pass
    
    async def code_actions(self, file_path: str, line_start: int, line_end: int):
        """Get available code actions"""
        # Implementation would send LSP codeAction request
        pass


class UnifiedBackend:
    """Main backend service implementing the 6 universal tools"""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.indexer = CodebaseIndexer(self.session_manager.hanzo_dir)
        self.lsp_bridge = LSPBridge()
        self.logger = logging.getLogger(__name__)
    
    def resolve_target(self, target_spec: TargetSpec) -> Dict[str, Any]:
        """Resolve target specification to concrete file/directory list"""
        target = target_spec.target
        
        if target.startswith("file:"):
            path = target[5:]
            workspace = WorkspaceDetector.detect(path)
            return {
                "type": "file",
                "paths": [path],
                "workspace": workspace
            }
        
        elif target.startswith("dir:"):
            path = target[4:]
            workspace = WorkspaceDetector.detect(path)
            # Recursively find relevant files
            files = []
            for ext in [".py", ".go", ".ts", ".js", ".rs", ".c", ".cpp", ".sol"]:
                files.extend(Path(path).rglob(f"*{ext}"))
            return {
                "type": "directory", 
                "paths": [str(f) for f in files],
                "workspace": workspace
            }
        
        elif target.startswith("pkg:"):
            pkg_spec = target[4:]
            workspace = WorkspaceDetector.detect(".")
            # Language-specific package resolution
            if workspace["language"] == "go":
                return self._resolve_go_package(pkg_spec, workspace)
            elif workspace["language"] == "ts":
                return self._resolve_ts_package(pkg_spec, workspace)
            # etc.
        
        elif target == "ws":
            workspace = WorkspaceDetector.detect(".")
            # Return all files in workspace
            root = Path(workspace["root"])
            files = []
            for ext in [".py", ".go", ".ts", ".js", ".rs", ".c", ".cpp", ".sol"]:
                files.extend(root.rglob(f"*{ext}"))
            return {
                "type": "workspace",
                "paths": [str(f) for f in files],
                "workspace": workspace
            }
        
        elif target == "changed":
            # Git diff against HEAD
            try:
                result = subprocess.run(
                    ["git", "diff", "--name-only", "HEAD"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                changed_files = result.stdout.strip().split("\n") if result.stdout.strip() else []
                workspace = WorkspaceDetector.detect(".")
                return {
                    "type": "changed",
                    "paths": changed_files,
                    "workspace": workspace
                }
            except subprocess.CalledProcessError:
                return {
                    "type": "changed", 
                    "paths": [],
                    "workspace": WorkspaceDetector.detect("."),
                    "error": "Not a git repository or git not available"
                }
    
    def _resolve_go_package(self, pkg_spec: str, workspace: Dict) -> Dict:
        """Resolve Go package specification"""
        # Implementation for Go package resolution
        # Handle ./..., ./cli/..., specific packages
        pass
    
    def _resolve_ts_package(self, pkg_spec: str, workspace: Dict) -> Dict:
        """Resolve TypeScript/Node package specification"""
        # Implementation for TS package resolution
        pass

    async def edit(self, target: TargetSpec, op: str, **kwargs) -> ToolResult:
        """Edit tool: semantic refactors via LSP"""
        start_time = datetime.utcnow().timestamp()
        
        try:
            resolved = self.resolve_target(target)
            workspace = resolved["workspace"]
            
            result = ToolResult(
                ok=True,
                root=workspace["root"],
                language_used=workspace["language"],
                backend_used="lsp",
                scope_resolved=resolved["paths"],
                touched_files=[],
                stdout="",
                stderr="",
                exit_code=0,
                errors=[],
                execution_time=0,
                session_id=self.session_manager.current_session
            )
            
            if op == "rename":
                # LSP rename operation
                file_path = kwargs.get("file")
                pos = kwargs.get("pos", {})
                new_name = kwargs.get("new_name")
                
                if target.dry_run:
                    result.stdout = f"Would rename symbol at {file_path}:{pos} to {new_name}"
                else:
                    # Actual LSP rename
                    await self.lsp_bridge.rename_symbol(
                        file_path, pos.get("line", 0), pos.get("character", 0), new_name
                    )
                    result.touched_files = [file_path]
            
            elif op == "code_action":
                # LSP code actions
                file_path = kwargs.get("file")
                range_spec = kwargs.get("range", {})
                only = kwargs.get("only", [])
                
                actions = await self.lsp_bridge.code_actions(
                    file_path, 
                    range_spec.get("start", {}).get("line", 0),
                    range_spec.get("end", {}).get("line", 0)
                )
                result.stdout = f"Available actions: {actions}"
            
            elif op == "organize_imports":
                # Organize imports for all files in scope
                for file_path in resolved["paths"]:
                    if not target.dry_run:
                        # Implement import organization
                        pass
                    result.touched_files.append(file_path)
            
            result.execution_time = datetime.utcnow().timestamp() - start_time
            return result
            
        except Exception as e:
            result = ToolResult(
                ok=False,
                root=workspace.get("root", "."),
                language_used="unknown",
                backend_used="lsp",
                scope_resolved=[],
                touched_files=[],
                stdout="",
                stderr=str(e),
                exit_code=1,
                errors=[str(e)],
                execution_time=datetime.utcnow().timestamp() - start_time,
                session_id=self.session_manager.current_session
            )
            return result

    async def fmt(self, target: TargetSpec, **kwargs) -> ToolResult:
        """Format tool: formatting + import normalization"""
        start_time = datetime.utcnow().timestamp()
        
        try:
            resolved = self.resolve_target(target)
            workspace = resolved["workspace"]
            language = workspace["language"]
            
            # Select formatter based on language
            formatters = {
                "go": "goimports",
                "py": "ruff format",
                "ts": "prettier",
                "rs": "cargo fmt",
                "cc": "clang-format",
                "sol": "prettier"
            }
            
            formatter = formatters.get(language, "cat")
            backend_used = formatter.split()[0]
            
            result = ToolResult(
                ok=True,
                root=workspace["root"],
                language_used=language,
                backend_used=backend_used,
                scope_resolved=resolved["paths"],
                touched_files=[],
                stdout="",
                stderr="",
                exit_code=0,
                errors=[],
                execution_time=0,
                session_id=self.session_manager.current_session
            )
            
            if not target.dry_run:
                for file_path in resolved["paths"]:
                    # Run formatter on each file
                    if language == "go":
                        cmd = ["goimports", "-w"]
                        local_prefix = kwargs.get("opts", {}).get("local_prefix")
                        if local_prefix:
                            cmd.extend(["-local", local_prefix])
                        cmd.append(file_path)
                        
                        proc_result = subprocess.run(cmd, capture_output=True, text=True)
                        if proc_result.returncode == 0:
                            result.touched_files.append(file_path)
                        else:
                            result.errors.append(f"Failed to format {file_path}: {proc_result.stderr}")
                    
                    # Add other language formatting logic
            
            result.execution_time = datetime.utcnow().timestamp() - start_time
            result.ok = len(result.errors) == 0
            return result
            
        except Exception as e:
            return ToolResult(
                ok=False,
                root=".",
                language_used="unknown", 
                backend_used="unknown",
                scope_resolved=[],
                touched_files=[],
                stdout="",
                stderr=str(e),
                exit_code=1,
                errors=[str(e)],
                execution_time=datetime.utcnow().timestamp() - start_time,
                session_id=self.session_manager.current_session
            )

    async def test(self, target: TargetSpec, **kwargs) -> ToolResult:
        """Test tool: run tests narrowly by default"""
        # Implementation for test execution
        pass

    async def build(self, target: TargetSpec, **kwargs) -> ToolResult:
        """Build tool: compile/build artifacts"""
        # Implementation for build execution
        pass

    async def lint(self, target: TargetSpec, **kwargs) -> ToolResult:
        """Lint tool: lint/typecheck in one place"""
        # Implementation for linting
        pass

    async def guard(self, target: TargetSpec, rules: List[Dict], **kwargs) -> ToolResult:
        """Guard tool: repo invariants"""
        # Implementation for guard rules
        pass


# Global backend instance
backend = UnifiedBackend()


if __name__ == "__main__":
    # CLI interface for testing
    import sys
    import asyncio
    
    async def main():
        if len(sys.argv) < 2:
            print("Usage: python unified_backend.py <tool> <target> [args...]")
            sys.exit(1)
        
        tool_name = sys.argv[1]
        target_spec = TargetSpec(target=sys.argv[2])
        
        if tool_name == "fmt":
            result = await backend.fmt(target_spec)
        elif tool_name == "edit":
            result = await backend.edit(target_spec, op="organize_imports")
        # Add other tools
        
        print(json.dumps(asdict(result), indent=2))
    
    asyncio.run(main())