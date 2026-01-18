"""
Unified Development Tools - 6 Orthogonal Commands
=================================================

edit, fmt, test, build, lint, guard

Each tool is one word, orthogonal, composable, works across languages/backends,
and is go.work aware.
"""

import os
import json
import subprocess
from enum import Enum
from typing import Any, Dict, List, Union, Literal, Optional
from pathlib import Path
from dataclasses import field, dataclass

from pydantic import Field, BaseModel

# Common types
LanguageType = Literal["auto", "go", "ts", "py", "rs", "cc", "sol", "schema"]
BackendType = Literal[
    "auto",
    "go",
    "pnpm",
    "yarn",
    "npm",
    "bun",
    "pytest",
    "uv",
    "poetry",
    "cargo",
    "cmake",
    "ninja",
    "make",
    "buf",
    "capnp",
]


class DevResult(BaseModel):
    """Common output for all dev tools"""

    ok: bool
    root: str
    language_used: Union[str, List[str]]
    backend_used: Union[str, List[str]]
    scope_resolved: Union[str, List[str]]
    touched_files: List[str] = Field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    errors: List[str] = Field(default_factory=list)


class WorkspaceDetector:
    """Detects workspace root and configuration"""

    @staticmethod
    def detect(target_path: str) -> Dict[str, Any]:
        """Detect workspace root and type from target path"""
        path = Path(target_path).resolve()

        # Walk up to find workspace markers
        current = path if path.is_dir() else path.parent

        while current != current.parent:
            # Check for workspace files in order of preference
            if (current / "go.work").exists():
                return {"root": str(current), "type": "go", "config": "go.work", "primary_language": "go"}

            if (current / "pnpm-workspace.yaml").exists():
                return {"root": str(current), "type": "pnpm", "config": "pnpm-workspace.yaml", "primary_language": "ts"}

            if (current / "package.json").exists():
                return {"root": str(current), "type": "npm", "config": "package.json", "primary_language": "ts"}

            if (current / "pyproject.toml").exists():
                return {"root": str(current), "type": "python", "config": "pyproject.toml", "primary_language": "py"}

            if (current / "Cargo.toml").exists():
                return {"root": str(current), "type": "rust", "config": "Cargo.toml", "primary_language": "rs"}

            current = current.parent

        # Fallback to target directory
        return {
            "root": str(path.parent if path.is_file() else path),
            "type": "unknown",
            "config": None,
            "primary_language": "auto",
        }


class TargetResolver:
    """Resolves target specifications to file lists and scopes"""

    @staticmethod
    def resolve(target: str, workspace: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve target to concrete scope"""

        if target.startswith("file:"):
            file_path = target[5:]
            return {
                "type": "file",
                "files": [file_path],
                "scope": file_path,
                "package": TargetResolver._infer_package(file_path, workspace),
            }

        if target.startswith("dir:"):
            dir_path = target[4:]
            return {
                "type": "directory",
                "files": TargetResolver._scan_directory(dir_path),
                "scope": dir_path,
                "package": dir_path,
            }

        if target.startswith("pkg:"):
            pkg_spec = target[4:]
            return {
                "type": "package",
                "files": TargetResolver._resolve_package(pkg_spec, workspace),
                "scope": pkg_spec,
                "package": pkg_spec,
            }

        if target == "ws":
            return {
                "type": "workspace",
                "files": TargetResolver._scan_workspace(workspace),
                "scope": "workspace",
                "package": ".",
            }

        if target == "changed":
            return {
                "type": "changed",
                "files": TargetResolver._get_changed_files(workspace),
                "scope": "changed files",
                "package": ".",
            }

        # Default to file if it's a plain path
        return TargetResolver.resolve(f"file:{target}", workspace)

    @staticmethod
    def _infer_package(file_path: str, workspace: Dict[str, Any]) -> str:
        """Infer package from file path"""
        path = Path(file_path)
        root = Path(workspace["root"])

        if workspace["type"] == "go":
            # Walk up to find go.mod
            current = path.parent
            while current >= root:
                if (current / "go.mod").exists():
                    return str(current.relative_to(root)) or "."
                current = current.parent
            return "."

        elif workspace["type"] in ["npm", "pnpm"]:
            # Walk up to find package.json
            current = path.parent
            while current >= root:
                if (current / "package.json").exists():
                    return str(current.relative_to(root)) or "."
                current = current.parent
            return "."

        return str(path.parent.relative_to(root)) if path.parent >= root else "."

    @staticmethod
    def _scan_directory(dir_path: str) -> List[str]:
        """Scan directory for relevant files"""
        path = Path(dir_path)
        files = []

        # Common source file patterns
        patterns = ["**/*.go", "**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx", "**/*.py", "**/*.rs"]

        for pattern in patterns:
            files.extend([str(f) for f in path.glob(pattern) if f.is_file()])

        return files

    @staticmethod
    def _resolve_package(pkg_spec: str, workspace: Dict[str, Any]) -> List[str]:
        """Resolve package specification to files"""
        root = Path(workspace["root"])

        if workspace["type"] == "go":
            # Use go list to resolve package
            try:
                result = subprocess.run(
                    ["go", "list", "-f", "{{.Dir}}", pkg_spec],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    env={**os.environ, "GOWORK": "auto"},
                )
                if result.returncode == 0:
                    pkg_dirs = result.stdout.strip().split("\n")
                    files = []
                    for pkg_dir in pkg_dirs:
                        files.extend(Path(pkg_dir).glob("*.go"))
                    return [str(f) for f in files]
            except Exception:
                pass

        # Fallback to directory scan
        pkg_path = root / pkg_spec.replace("./", "").replace("...", "")
        return TargetResolver._scan_directory(str(pkg_path))

    @staticmethod
    def _scan_workspace(workspace: Dict[str, Any]) -> List[str]:
        """Scan entire workspace"""
        return TargetResolver._scan_directory(workspace["root"])

    @staticmethod
    def _get_changed_files(workspace: Dict[str, Any]) -> List[str]:
        """Get changed files from git"""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"], cwd=workspace["root"], capture_output=True, text=True
            )
            if result.returncode == 0:
                files = [f.strip() for f in result.stdout.split("\n") if f.strip()]
                return [str(Path(workspace["root"]) / f) for f in files]
        except Exception:
            pass

        return []


class DevToolBase:
    """Base class for development tools"""

    def __init__(
        self,
        target: str,
        language: LanguageType = "auto",
        backend: BackendType = "auto",
        root: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        dry_run: bool = False,
    ):
        self.target = target
        self.language = language
        self.backend = backend
        self.env = env or {}
        self.dry_run = dry_run

        # Detect workspace
        workspace_root = root or TargetResolver.resolve(target, {"root": "."})["package"]
        self.workspace = WorkspaceDetector.detect(workspace_root)

        # Resolve target
        self.resolved = TargetResolver.resolve(target, self.workspace)

        # Auto-detect language if needed
        if language == "auto":
            self.language = self._detect_language()

        # Auto-detect backend if needed
        if backend == "auto":
            self.backend = self._detect_backend()

    def _detect_language(self) -> str:
        """Auto-detect language from files and workspace"""
        if self.workspace["primary_language"] != "auto":
            return self.workspace["primary_language"]

        # Analyze file extensions
        files = self.resolved["files"]
        extensions = [Path(f).suffix for f in files]

        if any(ext == ".go" for ext in extensions):
            return "go"
        if any(ext in [".ts", ".tsx", ".js", ".jsx"] for ext in extensions):
            return "ts"
        if any(ext == ".py" for ext in extensions):
            return "py"
        if any(ext == ".rs" for ext in extensions):
            return "rs"

        return self.workspace["primary_language"]

    def _detect_backend(self) -> str:
        """Auto-detect backend from workspace type and language"""
        lang = self.language
        ws_type = self.workspace["type"]

        backend_map = {
            "go": "go",
            "ts": "pnpm" if ws_type == "pnpm" else "npm",
            "py": "uv" if Path(self.workspace["root"], "uv.lock").exists() else "pytest",
            "rs": "cargo",
            "cc": "cmake",
            "sol": "forge",
            "schema": "buf",
        }

        return backend_map.get(lang, "auto")

    def _run_command(self, cmd: List[str], cwd: Optional[str] = None) -> subprocess.CompletedProcess:
        """Run command with proper environment"""
        env = {**os.environ, **self.env}

        # Add go.work environment for Go
        if self.language == "go":
            env["GOWORK"] = "auto"

        work_dir = cwd or self.workspace["root"]

        if self.dry_run:
            return subprocess.CompletedProcess(cmd, 0, f"DRY RUN: {' '.join(cmd)}", "")

        return subprocess.run(cmd, cwd=work_dir, env=env, capture_output=True, text=True)


# Individual tool implementations will be in separate files
# This establishes the foundation for edit, fmt, test, build, lint, guard


def create_dev_result(
    ok: bool,
    root: str,
    language_used: Union[str, List[str]],
    backend_used: Union[str, List[str]],
    scope_resolved: Union[str, List[str]],
    stdout: str = "",
    stderr: str = "",
    exit_code: int = 0,
    touched_files: List[str] = None,
    errors: List[str] = None,
) -> DevResult:
    """Helper to create DevResult"""
    return DevResult(
        ok=ok,
        root=root,
        language_used=language_used,
        backend_used=backend_used,
        scope_resolved=scope_resolved,
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        touched_files=touched_files or [],
        errors=errors or [],
    )
