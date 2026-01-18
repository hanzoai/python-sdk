#!/usr/bin/env python3
"""
Hanzo MCP - Exact 6-Tool Implementation
=======================================

Implements the precise specification for edit, fmt, test, build, lint, guard tools
with proper target resolution, workspace detection, and backend selection.
"""

import asyncio
import json
import os
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from hanzo_tools.lsp.lsp_tool import LSPTool
from pydantic import BaseModel, Field

try:
    from pydantic import ConfigDict
except ImportError:  # pragma: no cover - pydantic v1
    ConfigDict = None


class StrictModel(BaseModel):
    if ConfigDict is not None:
        model_config = ConfigDict(extra="forbid")
    else:

        class Config:
            extra = "forbid"


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
    violations: List[Dict[str, Any]] = field(default_factory=list)
    execution_time: float = 0.0


# Shared Input Schema
class TargetSpec(StrictModel):
    target: str = Field(
        ..., description="file:<path>, dir:<path>, pkg:<spec>, ws, or changed"
    )
    language: str = Field(default="auto", description="auto|go|ts|py|rs|cc|sol|schema")
    backend: str = Field(default="auto", description="Backend override")
    root: Optional[str] = Field(default=None, description="Workspace root override")
    env: Dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )
    dry_run: bool = Field(default=False, description="Preview mode")


# Tool-specific schemas
class EditArgs(StrictModel):
    op: Literal["rename", "code_action", "organize_imports", "apply_workspace_edit"]
    file: Optional[str] = None
    pos: Optional[Dict[str, int]] = None  # {line, character}
    range: Optional[Dict[str, Dict[str, int]]] = (
        None  # {start: {line, ch}, end: {line, ch}}
    )
    new_name: Optional[str] = None
    only: List[str] = Field(default_factory=list)  # LSP codeAction kinds
    apply: bool = True
    workspace_edit: Optional[Dict[str, Any]] = None


class FmtArgs(StrictModel):
    opts: Dict[str, Any] = Field(default_factory=dict)  # {local_prefix?: str}


class TestArgs(StrictModel):
    opts: Dict[str, Any] = Field(
        default_factory=dict
    )  # go: {run?, count?, race?}, ts: {filter?, watch?}, etc.


class BuildArgs(StrictModel):
    opts: Dict[str, Any] = Field(default_factory=dict)


class LintArgs(StrictModel):
    opts: Dict[str, Any] = Field(default_factory=dict)  # {fix?: bool}


class GuardRule(StrictModel):
    id: str
    type: Literal["regex", "import", "generated"]
    glob: str
    pattern: Optional[str] = None
    forbid_import_prefix: Optional[str] = None
    forbid_writes: Optional[bool] = None


class GuardArgs(StrictModel):
    rules: List[GuardRule]


class GuardViolation(StrictModel):
    file: str
    line: int
    column: int = 1
    import_path: Optional[str] = None
    symbol: Optional[str] = None
    message: Optional[str] = None
    rule_id: str
    text: str = ""


class WorkspaceDetector:
    """Intelligent workspace detection with go.work priority"""

    @staticmethod
    def detect(target_path: str, root_hint: Optional[str] = None) -> Dict[str, Any]:
        """Detect workspace root and configuration, preferring go.work"""
        path = Path(target_path).resolve()
        boundary: Optional[Path] = None
        if root_hint:
            boundary = Path(root_hint).resolve()
            if boundary.is_file():
                boundary = boundary.parent

        # If it's a file, start from parent directory
        if path.is_file():
            path = path.parent

        # Walk up to find workspace markers, prioritizing go.work
        parents = [path] + list(path.parents)
        if boundary is not None and boundary in parents:
            parents = parents[: parents.index(boundary) + 1]
        for current in parents:
            # Check for go.work first (highest priority)
            if (current / "go.work").is_file():
                return {
                    "root": str(current),
                    "type": "go_workspace",
                    "config": current / "go.work",
                    "language": "go",
                    "go_work_file": str(current / "go.work"),
                }

        # Then check other workspace types
        for current in parents:
            if (current / "go.mod").is_file():
                return {
                    "root": str(current),
                    "type": "go_module",
                    "config": current / "go.mod",
                    "language": "go",
                }
            elif (current / "package.json").is_file():
                with open(current / "package.json") as f:
                    pkg_data = json.load(f)
                    has_workspaces = "workspaces" in pkg_data
                return {
                    "root": str(current),
                    "type": "node_workspace" if has_workspaces else "node_project",
                    "config": current / "package.json",
                    "language": "ts",
                }
            elif (current / "pyproject.toml").is_file():
                return {
                    "root": str(current),
                    "type": "python_workspace",
                    "config": current / "pyproject.toml",
                    "language": "py",
                }
            elif (current / "Cargo.toml").is_file():
                return {
                    "root": str(current),
                    "type": "rust_workspace",
                    "config": current / "Cargo.toml",
                    "language": "rs",
                }
            elif (current / "CMakeLists.txt").is_file():
                return {
                    "root": str(current),
                    "type": "cmake_project",
                    "config": current / "CMakeLists.txt",
                    "language": "cc",
                }
            elif (current / "buf.yaml").is_file() or (current / "buf.yml").is_file():
                config_file = (
                    current / "buf.yaml"
                    if (current / "buf.yaml").is_file()
                    else current / "buf.yml"
                )
                return {
                    "root": str(current),
                    "type": "buf_workspace",
                    "config": config_file,
                    "language": "schema",
                }
            elif (current / ".git").exists():
                return {
                    "root": str(current),
                    "type": "git_repository",
                    "config": current / ".git",
                    "language": "auto",
                }

        # Default to current directory
        return {
            "root": str(path),
            "type": "directory",
            "config": None,
            "language": "auto",
        }


class TargetResolver:
    """Resolves target specifications to concrete file lists"""

    def __init__(self, workspace_detector: WorkspaceDetector):
        self.workspace_detector = workspace_detector

    def resolve(self, target_spec: TargetSpec) -> Dict[str, Any]:
        """Resolve target specification to concrete files/paths"""
        target = target_spec.target

        if target.startswith("file:"):
            return self._resolve_file(target[5:], target_spec)
        elif target.startswith("dir:"):
            return self._resolve_dir(target[4:], target_spec)
        elif target.startswith("pkg:"):
            return self._resolve_package(target[4:], target_spec)
        elif target == "ws":
            return self._resolve_workspace(target_spec)
        elif target == "changed":
            return self._resolve_changed(target_spec)
        else:
            raise ValueError(f"Unknown target format: {target}")

    def _resolve_file(self, file_path: str, target_spec: TargetSpec) -> Dict[str, Any]:
        """Resolve single file target"""
        path = Path(file_path).absolute()
        workspace = self.workspace_detector.detect(
            str(path), root_hint=target_spec.root
        )

        return {
            "type": "file",
            "paths": [str(path)],
            "workspace": workspace,
            "language": self._infer_language(path, workspace, target_spec.language),
        }

    def _resolve_dir(self, dir_path: str, target_spec: TargetSpec) -> Dict[str, Any]:
        """Resolve directory subtree target"""
        path = Path(dir_path).absolute()
        workspace = self.workspace_detector.detect(
            str(path), root_hint=target_spec.root
        )
        language = self._infer_language(path, workspace, target_spec.language)

        # Find relevant files based on language
        extensions = self._get_extensions_for_language(language)
        files = []

        for ext in extensions:
            files.extend(path.rglob(f"*{ext}"))

        return {
            "type": "directory",
            "paths": [str(f) for f in files],
            "workspace": workspace,
            "language": language,
        }

    def _resolve_package(
        self, pkg_spec: str, target_spec: TargetSpec
    ) -> Dict[str, Any]:
        """Resolve package specification"""
        workspace = self.workspace_detector.detect(
            target_spec.root or ".", root_hint=target_spec.root
        )
        language = (
            workspace["language"]
            if target_spec.language == "auto"
            else target_spec.language
        )

        if language == "go":
            return self._resolve_go_package(pkg_spec, workspace, target_spec)
        elif language == "ts":
            return self._resolve_ts_package(pkg_spec, workspace, target_spec)
        elif language == "py":
            return self._resolve_py_package(pkg_spec, workspace, target_spec)
        elif language == "rs":
            return self._resolve_rust_package(pkg_spec, workspace, target_spec)
        else:
            raise ValueError(
                f"Package resolution not supported for language: {language}"
            )

    def _resolve_workspace(self, target_spec: TargetSpec) -> Dict[str, Any]:
        """Resolve workspace root"""
        workspace = self.workspace_detector.detect(
            target_spec.root or ".", root_hint=target_spec.root
        )
        language = (
            workspace["language"]
            if target_spec.language == "auto"
            else target_spec.language
        )

        root = Path(workspace["root"])
        extensions = self._get_extensions_for_language(language)
        files = []

        for ext in extensions:
            files.extend(root.rglob(f"*{ext}"))

        return {
            "type": "workspace",
            "paths": [str(f) for f in files],
            "workspace": workspace,
            "language": language,
        }

    def _resolve_changed(self, target_spec: TargetSpec) -> Dict[str, Any]:
        """Resolve git changed files"""
        workspace = self.workspace_detector.detect(
            target_spec.root or ".", root_hint=target_spec.root
        )

        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                cwd=workspace["root"],
                capture_output=True,
                text=True,
                check=True,
            )
            changed_files = (
                result.stdout.strip().split("\n") if result.stdout.strip() else []
            )

            # Make paths absolute and filter existing files
            root_path = Path(workspace["root"])
            absolute_files = []
            for file in changed_files:
                abs_file = root_path / file
                if abs_file.exists():
                    absolute_files.append(str(abs_file))

            return {
                "type": "changed",
                "paths": absolute_files,
                "workspace": workspace,
                "language": "auto",  # Mixed files
            }
        except subprocess.CalledProcessError as e:
            return {
                "type": "changed",
                "paths": [],
                "workspace": workspace,
                "language": "auto",
                "error": f"Git command failed: {e}",
            }

    def _resolve_go_package(
        self, pkg_spec: str, workspace: Dict, target_spec: TargetSpec
    ) -> Dict[str, Any]:
        """Resolve Go package specification"""
        Path(workspace["root"])

        if pkg_spec == "./...":
            # All packages in workspace
            cmd = ["go", "list", "./..."]
        elif pkg_spec.endswith("/..."):
            # Package tree
            cmd = ["go", "list", pkg_spec]
        else:
            # Specific package
            cmd = ["go", "list", pkg_spec]

        try:
            env = os.environ.copy()
            env["GOWORK"] = "auto"  # Always use go.work if available

            result = subprocess.run(
                cmd,
                cwd=workspace["root"],
                capture_output=True,
                text=True,
                env=env,
                check=True,
            )

            packages = result.stdout.strip().split("\n")

            # Convert package names to file paths
            files = []
            for pkg in packages:
                if not pkg:
                    continue

                # Get package directory
                pkg_result = subprocess.run(
                    ["go", "list", "-f", "{{.Dir}}", pkg],
                    cwd=workspace["root"],
                    capture_output=True,
                    text=True,
                    env=env,
                    check=True,
                )

                pkg_dir = Path(pkg_result.stdout.strip())
                if pkg_dir.exists():
                    # Add all .go files in package
                    files.extend(pkg_dir.glob("*.go"))

            return {
                "type": "package",
                "paths": [str(f) for f in files],
                "workspace": workspace,
                "language": "go",
                "packages": packages,
            }

        except subprocess.CalledProcessError as e:
            return {
                "type": "package",
                "paths": [],
                "workspace": workspace,
                "language": "go",
                "error": f"Go list failed: {e}",
            }

    def _resolve_ts_package(
        self, pkg_spec: str, workspace: Dict, target_spec: TargetSpec
    ) -> Dict[str, Any]:
        """Resolve TypeScript/Node package specification"""
        # Handle npm/pnpm workspace filters
        if pkg_spec.startswith("--filter "):
            filter_name = pkg_spec[9:]
            # Use pnpm/npm workspace commands
            return {
                "type": "package",
                "paths": [],  # Would need to query workspace for actual files
                "workspace": workspace,
                "language": "ts",
                "filter": filter_name,
            }

        # Default to directory-based resolution
        return self._resolve_dir(pkg_spec, target_spec)

    def _resolve_py_package(
        self, pkg_spec: str, workspace: Dict, target_spec: TargetSpec
    ) -> Dict[str, Any]:
        """Resolve Python package specification"""
        # Could use importlib or package discovery here
        return self._resolve_dir(pkg_spec, target_spec)

    def _resolve_rust_package(
        self, pkg_spec: str, workspace: Dict, target_spec: TargetSpec
    ) -> Dict[str, Any]:
        """Resolve Rust package specification"""
        if pkg_spec.startswith("-p "):
            package_name = pkg_spec[3:]
            # Use cargo metadata to find package
            try:
                result = subprocess.run(
                    ["cargo", "metadata", "--format-version", "1"],
                    cwd=workspace["root"],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                metadata = json.loads(result.stdout)
                for pkg in metadata.get("packages", []):
                    if pkg["name"] == package_name:
                        manifest_path = Path(pkg["manifest_path"])
                        pkg_dir = manifest_path.parent
                        files = list(pkg_dir.rglob("*.rs"))

                        return {
                            "type": "package",
                            "paths": [str(f) for f in files],
                            "workspace": workspace,
                            "language": "rs",
                            "package": package_name,
                        }

            except subprocess.CalledProcessError:
                pass

        return self._resolve_dir(pkg_spec, target_spec)

    def _infer_language(self, path: Path, workspace: Dict, language_hint: str) -> str:
        """Infer language from file extension and workspace"""
        if language_hint != "auto":
            return language_hint

        # Use workspace language if available
        if workspace["language"] != "auto":
            return workspace["language"]

        # Infer from file extension
        if path.is_file():
            suffix = path.suffix
            extension_map = {
                ".go": "go",
                ".ts": "ts",
                ".tsx": "ts",
                ".js": "ts",
                ".jsx": "ts",
                ".py": "py",
                ".rs": "rs",
                ".c": "cc",
                ".cpp": "cc",
                ".cc": "cc",
                ".cxx": "cc",
                ".h": "cc",
                ".hpp": "cc",
                ".sol": "sol",
                ".proto": "schema",
            }
            return extension_map.get(suffix, "auto")

        return "auto"

    def _get_extensions_for_language(self, language: str) -> List[str]:
        """Get file extensions for language"""
        extension_map = {
            "go": [".go"],
            "ts": [".ts", ".tsx", ".js", ".jsx"],
            "py": [".py"],
            "rs": [".rs"],
            "cc": [".c", ".cpp", ".cc", ".cxx", ".h", ".hpp"],
            "sol": [".sol"],
            "schema": [".proto"],
            "auto": [
                ".go",
                ".ts",
                ".tsx",
                ".js",
                ".jsx",
                ".py",
                ".rs",
                ".c",
                ".cpp",
                ".cc",
                ".cxx",
                ".h",
                ".hpp",
                ".sol",
                ".proto",
            ],
        }
        return extension_map.get(
            language, [".go", ".ts", ".js", ".py", ".rs", ".c", ".cpp"]
        )


class BackendSelector:
    """Selects appropriate backend tools for each language/operation"""

    @staticmethod
    def select_backend(language: str, tool: str, backend_hint: str = "auto") -> str:
        """Select backend tool for language and operation"""
        if backend_hint != "auto":
            return backend_hint

        backend_map = {
            "go": {
                "fmt": "goimports",
                "test": "go",
                "build": "go",
                "lint": "golangci-lint",
                "edit": "gopls",
            },
            "ts": {
                "fmt": "prettier",
                "test": "npm",  # or pnpm/yarn
                "build": "tsc",
                "lint": "eslint",
                "edit": "typescript-language-server",
            },
            "py": {
                "fmt": "ruff",
                "test": "pytest",
                "build": "build",
                "lint": "ruff",
                "edit": "pyright",
            },
            "rs": {
                "fmt": "cargo",
                "test": "cargo",
                "build": "cargo",
                "lint": "cargo",
                "edit": "rust-analyzer",
            },
            "cc": {
                "fmt": "clang-format",
                "test": "ctest",
                "build": "cmake",
                "lint": "clang-tidy",
                "edit": "clangd",
            },
            "sol": {
                "fmt": "prettier",
                "test": "hardhat",
                "build": "forge",
                "lint": "slither",
                "edit": "solidity-language-server",
            },
            "schema": {
                "fmt": "buf",
                "test": "buf",
                "build": "buf",
                "lint": "buf",
                "edit": "buf",
            },
        }

        return backend_map.get(language, {}).get(tool, "unknown")


class LSPBridge:
    """LSP client for semantic operations"""

    def __init__(self):
        self.tool = LSPTool()

    async def rename_symbol(
        self,
        file_path: str,
        line: int,
        character: int,
        new_name: str,
        workspace_root: str,
        language: str,
        apply: bool,
    ) -> Dict[str, Any]:
        """Perform LSP rename operation, return result"""
        result = await self.tool.run(
            action="rename",
            file=file_path,
            line=line,
            character=character,
            new_name=new_name,
            apply_edits=apply,
        )
        return result.data

    async def code_actions(
        self,
        file_path: str,
        range_spec: Dict,
        only: List[str],
        workspace_root: str,
        language: str,
        apply: bool,
    ) -> Dict[str, Any]:
        """Get and apply code actions, return result"""
        result = await self.tool.run(
            action="code_action",
            file=file_path,
            line=range_spec.get("start", {}).get("line", 1),
            character=range_spec.get("start", {}).get("character", 0),
            only=only,
            range=range_spec,
            apply_edits=apply,
        )
        return result.data

    async def organize_imports(
        self,
        file_paths: List[str],
        workspace_root: str,
        language: str,
        apply: bool,
    ) -> Dict[str, Any]:
        """Organize imports for files, return result"""
        touched = []
        errors: List[str] = []
        for file_path in file_paths:
            result = await self.tool.run(
                action="organize_imports",
                file=file_path,
                apply_edits=apply,
            )
            data = result.data
            touched.extend(data.get("applied_files", data.get("touched_files", [])))
            if "apply_errors" in data:
                errors.extend(data["apply_errors"])
            if "error" in data:
                errors.append(str(data["error"]))
        return {"touched_files": sorted(set(touched)), "errors": errors}

    async def apply_workspace_edit(
        self, edit: Dict[str, Any], workspace_root: str
    ) -> Dict[str, Any]:
        """Apply a WorkspaceEdit directly."""
        applied, errors = self.tool._apply_workspace_edit(edit, workspace_root)
        return {"touched_files": applied, "errors": errors}


class HanzoTools:
    """Implementation of the 6 universal tools"""

    def __init__(self):
        self.workspace_detector = WorkspaceDetector()
        self.target_resolver = TargetResolver(self.workspace_detector)
        self.backend_selector = BackendSelector()
        self.lsp_bridge = LSPBridge()

    def _prepare_environment(
        self, workspace: Dict, target_spec: TargetSpec
    ) -> Dict[str, str]:
        """Prepare environment variables for tool execution"""
        env = os.environ.copy()

        # Always set GOWORK=auto for Go workspaces
        if workspace.get("type") == "go_workspace":
            env["GOWORK"] = "auto"

        # Add custom environment variables
        env.update(target_spec.env)

        return env

    async def edit(self, target_spec: TargetSpec, args: EditArgs) -> ToolResult:
        """Edit tool: semantic refactors via LSP"""
        start_time = datetime.utcnow()

        try:
            resolved = self.target_resolver.resolve(target_spec)
            workspace = resolved["workspace"]
            language = resolved["language"]

            backend = self.backend_selector.select_backend(
                language, "edit", target_spec.backend
            )

            touched_files = []
            stdout_parts = []
            stderr_parts = []
            errors: List[str] = []
            apply = args.apply and not target_spec.dry_run

            if args.op == "rename":
                if not args.file or not args.pos or not args.new_name:
                    raise ValueError("rename requires file, pos, and new_name")
                result = await self.lsp_bridge.rename_symbol(
                    args.file,
                    args.pos["line"],
                    args.pos["character"],
                    args.new_name,
                    workspace["root"],
                    language,
                    apply=apply,
                )
                if "error" in result:
                    raise RuntimeError(str(result["error"]))
                touched_files = result.get(
                    "applied_files", result.get("touched_files", [])
                )
                errors.extend(result.get("apply_errors", []))
                if apply:
                    stdout_parts.append(
                        f"Renamed symbol to '{args.new_name}' in {len(touched_files)} files"
                    )
                else:
                    stdout_parts.append(
                        f"Would rename symbol to '{args.new_name}' at {args.file}:{args.pos['line']}:{args.pos['character']}"
                    )

            elif args.op == "code_action":
                if not args.file:
                    raise ValueError("code_action requires file")
                result = await self.lsp_bridge.code_actions(
                    args.file,
                    args.range or {},
                    args.only,
                    workspace["root"],
                    language,
                    apply=apply,
                )
                if "error" in result:
                    raise RuntimeError(str(result["error"]))
                touched_files = result.get(
                    "applied_files", result.get("touched_files", [])
                )
                errors.extend(result.get("apply_errors", []))
                if apply:
                    stdout_parts.append(
                        f"Applied code actions to {len(touched_files)} files"
                    )
                else:
                    stdout_parts.append(f"Would apply code actions to {args.file}")

            elif args.op == "organize_imports":
                result = await self.lsp_bridge.organize_imports(
                    resolved["paths"], workspace["root"], language, apply=apply
                )
                touched_files = result.get("touched_files", [])
                errors.extend(result.get("errors", []))
                if apply:
                    stdout_parts.append(
                        f"Organized imports in {len(touched_files)} files"
                    )
                else:
                    stdout_parts.append(
                        f"Would organize imports in {len(resolved['paths'])} files"
                    )

            elif args.op == "apply_workspace_edit":
                if not args.workspace_edit:
                    raise ValueError("apply_workspace_edit requires workspace_edit")
                result = await self.lsp_bridge.apply_workspace_edit(
                    args.workspace_edit, workspace["root"]
                )
                touched_files = result.get("touched_files", [])
                errors.extend(result.get("errors", []))
                if apply:
                    stdout_parts.append(
                        f"Applied WorkspaceEdit to {len(touched_files)} files"
                    )
                else:
                    stdout_parts.append(
                        f"Would apply WorkspaceEdit to {len(touched_files)} files"
                    )

            return ToolResult(
                ok=len(errors) == 0,
                root=workspace["root"],
                language_used=language,
                backend_used=backend,
                scope_resolved=resolved["paths"],
                touched_files=touched_files,
                stdout="\n".join(stdout_parts),
                stderr="\n".join(stderr_parts),
                exit_code=0 if len(errors) == 0 else 1,
                errors=errors,
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
            )

        except Exception as e:
            return ToolResult(
                ok=False,
                root=workspace.get("root", "."),
                language_used="unknown",
                backend_used="unknown",
                scope_resolved=[],
                touched_files=[],
                stdout="",
                stderr=str(e),
                exit_code=1,
                errors=[str(e)],
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
            )

    async def fmt(self, target_spec: TargetSpec, args: FmtArgs) -> ToolResult:
        """Format tool: formatting + import normalization"""
        start_time = datetime.utcnow()

        try:
            resolved = self.target_resolver.resolve(target_spec)
            workspace = resolved["workspace"]
            language = resolved["language"]

            backend = self.backend_selector.select_backend(
                language, "fmt", target_spec.backend
            )
            env = self._prepare_environment(workspace, target_spec)

            touched_files = []
            stdout_parts = []
            stderr_parts = []

            for file_path in resolved["paths"]:
                if target_spec.dry_run:
                    stdout_parts.append(f"Would format: {file_path}")
                    continue

                if language == "go":
                    cmd = ["goimports", "-w"]
                    if "local_prefix" in args.opts:
                        cmd.extend(["-local", args.opts["local_prefix"]])
                    cmd.append(file_path)

                elif language == "ts":
                    cmd = ["prettier", "--write", file_path]

                elif language == "py":
                    cmd = ["ruff", "format", file_path]

                elif language == "rs":
                    # For Rust, format the whole package
                    cmd = ["cargo", "fmt"]

                elif language == "cc":
                    cmd = ["clang-format", "-i", file_path]

                elif language == "sol":
                    cmd = ["prettier", "--write", file_path]

                elif language == "schema":
                    cmd = ["buf", "format", "-w", file_path]

                else:
                    continue

                try:
                    result = subprocess.run(
                        cmd,
                        cwd=workspace["root"],
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )

                    if result.returncode == 0:
                        touched_files.append(file_path)
                        stdout_parts.append(f"Formatted: {file_path}")
                    else:
                        stderr_parts.append(
                            f"Failed to format {file_path}: {result.stderr}"
                        )

                except subprocess.TimeoutExpired:
                    stderr_parts.append(f"Timeout formatting {file_path}")
                except FileNotFoundError:
                    stderr_parts.append(f"Formatter not found for {language}: {cmd[0]}")

            return ToolResult(
                ok=len(stderr_parts) == 0,
                root=workspace["root"],
                language_used=language,
                backend_used=backend,
                scope_resolved=resolved["paths"],
                touched_files=touched_files,
                stdout="\n".join(stdout_parts),
                stderr="\n".join(stderr_parts),
                exit_code=0 if len(stderr_parts) == 0 else 1,
                errors=stderr_parts,
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
            )

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
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
            )

    async def test(self, target_spec: TargetSpec, args: TestArgs) -> ToolResult:
        """Test tool: run tests narrowly by default"""
        start_time = datetime.utcnow()

        try:
            resolved = self.target_resolver.resolve(target_spec)
            workspace = resolved["workspace"]
            language = resolved["language"]

            backend = self.backend_selector.select_backend(
                language, "test", target_spec.backend
            )
            env = self._prepare_environment(workspace, target_spec)

            # Build test command based on language and scope
            if language == "go":
                if resolved["type"] == "package":
                    # Test specific packages
                    packages = resolved.get("packages", ["./..."])
                    cmd = ["go", "test"] + packages
                else:
                    # Derive package from file
                    cmd = ["go", "test", "./..."]

                # Add Go-specific options
                if "run" in args.opts:
                    cmd.extend(["-run", args.opts["run"]])
                if "count" in args.opts:
                    cmd.extend(["-count", str(args.opts["count"])])
                if args.opts.get("race"):
                    cmd.append("-race")

            elif language == "ts":
                # Use npm/pnpm test script
                cmd = ["npm", "test"]
                if "filter" in args.opts:
                    cmd.append(f"--filter={args.opts['filter']}")
                if not args.opts.get("watch", True):
                    cmd.append("--no-watch")

            elif language == "py":
                cmd = ["pytest"]
                if resolved["type"] == "file":
                    # Test specific file
                    cmd.extend(resolved["paths"])

                if "k" in args.opts:
                    cmd.extend(["-k", args.opts["k"]])
                if "m" in args.opts:
                    cmd.extend(["-m", args.opts["m"]])

            elif language == "rs":
                cmd = ["cargo", "test"]
                if "p" in args.opts:
                    cmd.extend(["-p", args.opts["p"]])
                if "features" in args.opts:
                    cmd.extend(["--features", ",".join(args.opts["features"])])

            else:
                raise ValueError(f"Testing not supported for language: {language}")

            if target_spec.dry_run:
                return ToolResult(
                    ok=True,
                    root=workspace["root"],
                    language_used=language,
                    backend_used=backend,
                    scope_resolved=resolved["paths"],
                    touched_files=[],
                    stdout=f"Would run: {' '.join(cmd)}",
                    stderr="",
                    exit_code=0,
                    errors=[],
                    execution_time=(datetime.utcnow() - start_time).total_seconds(),
                )

            # Execute test command
            result = subprocess.run(
                cmd,
                cwd=workspace["root"],
                env=env,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout for tests
            )

            return ToolResult(
                ok=result.returncode == 0,
                root=workspace["root"],
                language_used=language,
                backend_used=backend,
                scope_resolved=resolved["paths"],
                touched_files=[],
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                errors=[result.stderr] if result.returncode != 0 else [],
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
            )

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
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
            )

    async def build(self, target_spec: TargetSpec, args: BuildArgs) -> ToolResult:
        """Build tool: compile/build artifacts narrowly by default"""
        start_time = datetime.utcnow()

        try:
            resolved = self.target_resolver.resolve(target_spec)
            workspace = resolved["workspace"]
            language = resolved["language"]

            backend = self.backend_selector.select_backend(
                language, "build", target_spec.backend
            )
            env = self._prepare_environment(workspace, target_spec)

            # Build command based on language
            if language == "go":
                if resolved["type"] == "package":
                    packages = resolved.get("packages", ["./..."])
                    cmd = ["go", "build"] + packages
                else:
                    cmd = ["go", "build", "./..."]

            elif language == "ts":
                cmd = ["tsc"]  # or npm run build

            elif language == "py":
                cmd = ["python", "-m", "build"]

            elif language == "rs":
                cmd = ["cargo", "build"]
                if args.opts.get("release"):
                    cmd.append("--release")

            elif language == "cc":
                cmd = ["cmake", "--build", "."]

            elif language == "sol":
                cmd = ["forge", "build"]  # or hardhat compile

            else:
                raise ValueError(f"Build not supported for language: {language}")

            if target_spec.dry_run:
                return ToolResult(
                    ok=True,
                    root=workspace["root"],
                    language_used=language,
                    backend_used=backend,
                    scope_resolved=resolved["paths"],
                    touched_files=[],
                    stdout=f"Would run: {' '.join(cmd)}",
                    stderr="",
                    exit_code=0,
                    errors=[],
                    execution_time=(datetime.utcnow() - start_time).total_seconds(),
                )

            result = subprocess.run(
                cmd,
                cwd=workspace["root"],
                env=env,
                capture_output=True,
                text=True,
                timeout=300,
            )

            return ToolResult(
                ok=result.returncode == 0,
                root=workspace["root"],
                language_used=language,
                backend_used=backend,
                scope_resolved=resolved["paths"],
                touched_files=[],  # Build typically doesn't modify source files
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                errors=[result.stderr] if result.returncode != 0 else [],
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
            )

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
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
            )

    async def lint(self, target_spec: TargetSpec, args: LintArgs) -> ToolResult:
        """Lint tool: lint/typecheck in one place"""
        start_time = datetime.utcnow()

        try:
            resolved = self.target_resolver.resolve(target_spec)
            workspace = resolved["workspace"]
            language = resolved["language"]

            backend = self.backend_selector.select_backend(
                language, "lint", target_spec.backend
            )
            env = self._prepare_environment(workspace, target_spec)

            # Build lint command based on language
            if language == "go":
                cmd = ["golangci-lint", "run"]
                if resolved["type"] == "file":
                    cmd.extend(resolved["paths"])
                elif resolved["type"] == "package":
                    cmd.append("./...")

            elif language == "ts":
                cmd = ["eslint"]
                if resolved["paths"]:
                    cmd.extend(resolved["paths"])
                else:
                    cmd.append(".")

                if args.opts.get("fix"):
                    cmd.append("--fix")

            elif language == "py":
                cmd = ["ruff", "check"]
                if resolved["paths"]:
                    cmd.extend(resolved["paths"])
                else:
                    cmd.append(".")

                if args.opts.get("fix"):
                    cmd.append("--fix")

            elif language == "rs":
                cmd = ["cargo", "clippy"]

            elif language == "cc":
                cmd = ["clang-tidy"] + resolved["paths"]

            elif language == "schema":
                cmd = ["buf", "lint"]

            else:
                raise ValueError(f"Lint not supported for language: {language}")

            if target_spec.dry_run:
                return ToolResult(
                    ok=True,
                    root=workspace["root"],
                    language_used=language,
                    backend_used=backend,
                    scope_resolved=resolved["paths"],
                    touched_files=[],
                    stdout=f"Would run: {' '.join(cmd)}",
                    stderr="",
                    exit_code=0,
                    errors=[],
                    execution_time=(datetime.utcnow() - start_time).total_seconds(),
                )

            result = subprocess.run(
                cmd,
                cwd=workspace["root"],
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
            )

            # Lint tools often return non-zero for warnings
            success = result.returncode == 0

            return ToolResult(
                ok=success,
                root=workspace["root"],
                language_used=language,
                backend_used=backend,
                scope_resolved=resolved["paths"],
                touched_files=[],  # Lint may fix files if --fix is used
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                errors=[result.stderr] if not success else [],
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
            )

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
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
            )

    async def guard(self, target_spec: TargetSpec, args: GuardArgs) -> ToolResult:
        """Guard tool: repo invariants (boundaries, forbidden imports/strings)"""
        start_time = datetime.utcnow()

        try:
            resolved = self.target_resolver.resolve(target_spec)
            workspace = resolved["workspace"]
            language = resolved["language"]

            violations = []

            for rule in args.rules:
                rule_violations = await self._check_guard_rule(
                    rule, resolved["paths"], workspace["root"], language
                )
                violations.extend(rule_violations)

            stdout_lines = []
            if violations:
                stdout_lines.append(f"Found {len(violations)} guard violations:")
                for v in violations:
                    location = f"{v.file}:{v.line}:{v.column}"
                    detail = v.import_path or v.text
                    stdout_lines.append(f"  {location} - {v.rule_id}: {detail}")
            else:
                stdout_lines.append("No guard violations found")

            return ToolResult(
                ok=len(violations) == 0,
                root=workspace["root"],
                language_used="auto",
                backend_used="guard",
                scope_resolved=resolved["paths"],
                touched_files=[],
                stdout="\n".join(stdout_lines),
                stderr="",
                exit_code=0 if len(violations) == 0 else 1,
                errors=[
                    f"{v.rule_id}: {v.file}:{v.line}:{v.column}" for v in violations
                ],
                violations=[v.model_dump() for v in violations],
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
            )

        except Exception as e:
            return ToolResult(
                ok=False,
                root=".",
                language_used="unknown",
                backend_used="guard",
                scope_resolved=[],
                touched_files=[],
                stdout="",
                stderr=str(e),
                exit_code=1,
                errors=[str(e)],
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
            )

    async def _check_guard_rule(
        self, rule: GuardRule, file_paths: List[str], workspace_root: str, language: str
    ) -> List[GuardViolation]:
        """Check a single guard rule against files"""
        violations = []

        # Match files against glob pattern
        import fnmatch

        matched_files = []

        for file_path in file_paths:
            rel_path = os.path.relpath(file_path, workspace_root)
            if fnmatch.fnmatch(rel_path, rule.glob):
                matched_files.append(file_path)

        if rule.type == "import" and rule.forbid_import_prefix:
            wants_go = language in ["go", "auto"] and any(
                p.endswith(".go") for p in matched_files
            )
            wants_ts = language in ["ts", "js", "auto"] and any(
                p.endswith((".ts", ".tsx", ".js", ".jsx")) for p in matched_files
            )
            go_index = (
                await self._go_package_index(workspace_root) if wants_go else None
            )
            ts_graph = (
                self._build_ts_dependency_graph(workspace_root) if wants_ts else None
            )
        else:
            go_index = None
            ts_graph = None

        for file_path in matched_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                if rule.type == "regex":
                    import re

                    pattern = re.compile(rule.pattern)
                    for line_num, line in enumerate(lines, 1):
                        if pattern.search(line):
                            violations.append(
                                GuardViolation(
                                    file=file_path,
                                    line=line_num,
                                    column=1,
                                    text=line.strip(),
                                    rule_id=rule.id,
                                )
                            )

                elif rule.type == "import":
                    if file_path.endswith(".go"):
                        for imp in self._scan_go_imports(file_path):
                            if imp["import_path"].startswith(rule.forbid_import_prefix):
                                violations.append(
                                    GuardViolation(
                                        file=file_path,
                                        line=imp["line"],
                                        column=imp["column"],
                                        import_path=imp["import_path"],
                                        rule_id=rule.id,
                                        message="forbidden direct import",
                                    )
                                )
                        if go_index and file_path in go_index["file_to_pkg"]:
                            pkg = go_index["file_to_pkg"][file_path]
                            deps = go_index["pkg_deps"].get(pkg, set())
                            for dep in deps:
                                if dep.startswith(rule.forbid_import_prefix):
                                    violations.append(
                                        GuardViolation(
                                            file=file_path,
                                            line=1,
                                            column=1,
                                            import_path=dep,
                                            rule_id=rule.id,
                                            message="forbidden transitive import",
                                        )
                                    )
                                    break
                    else:
                        for imp in self._scan_ts_imports(file_path):
                            if imp["import_path"].startswith(rule.forbid_import_prefix):
                                violations.append(
                                    GuardViolation(
                                        file=file_path,
                                        line=imp["line"],
                                        column=imp["column"],
                                        import_path=imp["import_path"],
                                        rule_id=rule.id,
                                        message="forbidden direct import",
                                    )
                                )
                        if ts_graph:
                            deps = self._ts_transitive_deps(file_path, ts_graph)
                            for dep in deps:
                                if dep.startswith(rule.forbid_import_prefix):
                                    violations.append(
                                        GuardViolation(
                                            file=file_path,
                                            line=1,
                                            column=1,
                                            import_path=dep,
                                            rule_id=rule.id,
                                            message="forbidden transitive import",
                                        )
                                    )
                                    break

                elif rule.type == "generated" and rule.forbid_writes:
                    # Check if file was recently modified (this is a simple check)
                    violations.append(
                        GuardViolation(
                            file=file_path,
                            line=1,
                            column=1,
                            text="Modification of generated file forbidden",
                            rule_id=rule.id,
                        )
                    )

            except Exception:
                # Skip files that can't be read
                continue

        return violations

    def _scan_go_imports(self, file_path: str) -> List[Dict[str, Any]]:
        imports: List[Dict[str, Any]] = []
        in_block = False
        with open(file_path, "r", encoding="utf-8") as f:
            for idx, raw in enumerate(f, 1):
                line = raw.strip()
                if line.startswith("import ("):
                    in_block = True
                    continue
                if in_block and line.startswith(")"):
                    in_block = False
                    continue
                if line.startswith("import "):
                    in_block = False
                    line = line[len("import ") :].strip()
                if (
                    in_block
                    or line.startswith(
                        (
                            '"',
                            "_",
                            ".",
                        )
                    )
                    or line.split(" ", 1)[0].isidentifier()
                ):
                    import_path = self._extract_go_import_path(line)
                    if import_path:
                        column = raw.find(import_path) + 1
                        imports.append(
                            {
                                "import_path": import_path,
                                "line": idx,
                                "column": max(1, column),
                            }
                        )
        return imports

    def _extract_go_import_path(self, line: str) -> Optional[str]:
        import re

        match = re.search(r"\"([^\"]+)\"", line)
        if not match:
            return None
        return match.group(1)

    def _scan_ts_imports(self, file_path: str) -> List[Dict[str, Any]]:
        import re

        imports: List[Dict[str, Any]] = []
        patterns = [
            re.compile(r"import\s+[^;]*?\s+from\s+['\"]([^'\"]+)['\"]"),
            re.compile(r"import\s+['\"]([^'\"]+)['\"]"),
            re.compile(r"export\s+[^;]*?\s+from\s+['\"]([^'\"]+)['\"]"),
        ]
        with open(file_path, "r", encoding="utf-8") as f:
            for idx, raw in enumerate(f, 1):
                for pattern in patterns:
                    match = pattern.search(raw)
                    if match:
                        module = match.group(1)
                        column = raw.find(module) + 1
                        imports.append(
                            {
                                "import_path": module,
                                "line": idx,
                                "column": max(1, column),
                            }
                        )
        return imports

    def _build_ts_dependency_graph(self, workspace_root: str) -> Dict[str, Any]:
        graph: Dict[str, List[str]] = {}
        module_deps: Dict[str, List[str]] = {}
        for root, _, files in os.walk(workspace_root):
            for name in files:
                if not name.endswith((".ts", ".tsx", ".js", ".jsx")):
                    continue
                file_path = os.path.join(root, name)
                imports = self._scan_ts_imports(file_path)
                rel_deps = []
                ext_deps = []
                for imp in imports:
                    module = imp["import_path"]
                    if module.startswith("."):
                        target = self._resolve_ts_relative(file_path, module)
                        if target:
                            rel_deps.append(target)
                    else:
                        ext_deps.append(module)
                graph[file_path] = rel_deps
                module_deps[file_path] = ext_deps
        return {"graph": graph, "modules": module_deps}

    def _resolve_ts_relative(self, source_file: str, module: str) -> Optional[str]:
        base = Path(source_file).parent / module
        candidates = [
            base,
            base.with_suffix(".ts"),
            base.with_suffix(".tsx"),
            base.with_suffix(".js"),
            base.with_suffix(".jsx"),
            base / "index.ts",
            base / "index.tsx",
            base / "index.js",
            base / "index.jsx",
        ]
        for cand in candidates:
            if cand.exists():
                return str(cand.resolve())
        return None

    def _ts_transitive_deps(self, start_file: str, graph: Dict[str, Any]) -> List[str]:
        visited = set()
        stack = [start_file]
        modules = set()
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            modules.update(graph["modules"].get(current, []))
            for neighbor in graph["graph"].get(current, []):
                if neighbor not in visited:
                    stack.append(neighbor)
        return sorted(modules)

    async def _go_package_index(self, workspace_root: str) -> Dict[str, Any]:
        cmd = ["go", "list", "-deps", "-json", "./..."]
        env = os.environ.copy()
        env["GOWORK"] = "auto"
        try:
            result = subprocess.run(
                cmd,
                cwd=workspace_root,
                capture_output=True,
                text=True,
                check=True,
                env=env,
            )
        except Exception:
            return {"file_to_pkg": {}, "pkg_deps": {}}

        decoder = json.JSONDecoder()
        data = result.stdout
        idx = 0
        packages = []
        while idx < len(data):
            while idx < len(data) and data[idx].isspace():
                idx += 1
            if idx >= len(data):
                break
            obj, idx = decoder.raw_decode(data, idx)
            packages.append(obj)

        file_to_pkg: Dict[str, str] = {}
        pkg_deps: Dict[str, set] = {}
        for pkg in packages:
            import_path = pkg.get("ImportPath", "")
            deps = set(pkg.get("Deps", []) or [])
            pkg_deps[import_path] = deps
            for name in (
                pkg.get("GoFiles", [])
                + pkg.get("CgoFiles", [])
                + pkg.get("CompiledGoFiles", [])
            ):
                file_to_pkg[str(Path(pkg.get("Dir", "")) / name)] = import_path
        return {"file_to_pkg": file_to_pkg, "pkg_deps": pkg_deps}


# Global instance
tools = HanzoTools()


# CLI interface for testing
if __name__ == "__main__":
    import argparse
    import asyncio
    import sys

    async def main():
        parser = argparse.ArgumentParser(description="Hanzo MCP Tools")
        parser.add_argument(
            "tool", choices=["edit", "fmt", "test", "build", "lint", "guard"]
        )
        parser.add_argument("target", help="Target specification")
        parser.add_argument("--language", default="auto")
        parser.add_argument("--backend", default="auto")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--op", help="Operation for edit tool")
        parser.add_argument("--file", help="File for edit operations")
        parser.add_argument("--new-name", help="New name for rename")
        parser.add_argument("--local-prefix", help="Local prefix for Go imports")

        args = parser.parse_args()

        target_spec = TargetSpec(
            target=args.target,
            language=args.language,
            backend=args.backend,
            dry_run=args.dry_run,
        )

        if args.tool == "edit":
            if not args.op:
                print("--op required for edit tool")
                sys.exit(1)

            edit_args = EditArgs(op=args.op)
            if args.file:
                edit_args.file = args.file
            if args.new_name:
                edit_args.new_name = args.new_name

            result = await tools.edit(target_spec, edit_args)

        elif args.tool == "fmt":
            fmt_args = FmtArgs()
            if args.local_prefix:
                fmt_args.opts["local_prefix"] = args.local_prefix

            result = await tools.fmt(target_spec, fmt_args)

        elif args.tool == "test":
            result = await tools.test(target_spec, TestArgs())

        elif args.tool == "build":
            result = await tools.build(target_spec, BuildArgs())

        elif args.tool == "lint":
            result = await tools.lint(target_spec, LintArgs())

        elif args.tool == "guard":
            # Example guard rules
            example_rules = [
                GuardRule(
                    id="no-node-in-sdk",
                    type="import",
                    glob="sdk/**/*.py",
                    forbid_import_prefix="node",
                )
            ]
            result = await tools.guard(target_spec, GuardArgs(rules=example_rules))

        print(json.dumps(asdict(result), indent=2))

    asyncio.run(main())
