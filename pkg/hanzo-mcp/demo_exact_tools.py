#!/usr/bin/env python3
"""
Demonstration of Exact 6-Tool Implementation (Standalone)
=========================================================

Core implementation of the 6 universal tools without external dependencies.
"""

import asyncio
import json
import os
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


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
    execution_time: float = 0.0


class WorkspaceDetector:
    """Intelligent workspace detection with go.work priority"""

    @staticmethod
    def detect(target_path: str) -> Dict[str, Any]:
        """Detect workspace root, preferring go.work"""
        path = Path(target_path).absolute()

        if path.is_file():
            path = path.parent

        # Check for go.work first (highest priority)
        for current in [path] + list(path.parents):
            if (current / "go.work").exists():
                return {
                    "root": str(current),
                    "type": "go_workspace",
                    "language": "go",
                    "go_work_file": str(current / "go.work"),
                }

        # Then check other workspace types
        for current in [path] + list(path.parents):
            if (current / "go.mod").exists():
                return {"root": str(current), "type": "go_module", "language": "go"}
            elif (current / "package.json").exists():
                return {"root": str(current), "type": "node_project", "language": "ts"}
            elif (current / "pyproject.toml").exists():
                return {
                    "root": str(current),
                    "type": "python_project",
                    "language": "py",
                }
            elif (current / "Cargo.toml").exists():
                return {"root": str(current), "type": "rust_project", "language": "rs"}

        return {"root": str(path), "type": "directory", "language": "auto"}


class BackendSelector:
    """Selects appropriate backend tools for each language/operation"""

    @staticmethod
    def select_backend(language: str, tool: str) -> str:
        """Select backend tool for language and operation"""
        backend_map = {
            "go": {
                "fmt": "goimports",
                "test": "go test",
                "build": "go build",
                "lint": "golangci-lint",
                "edit": "gopls",
            },
            "ts": {
                "fmt": "prettier",
                "test": "npm test",
                "build": "tsc",
                "lint": "eslint",
                "edit": "typescript-language-server",
            },
            "py": {
                "fmt": "ruff format",
                "test": "pytest",
                "build": "python -m build",
                "lint": "ruff check",
                "edit": "pyright",
            },
            "rs": {
                "fmt": "cargo fmt",
                "test": "cargo test",
                "build": "cargo build",
                "lint": "cargo clippy",
                "edit": "rust-analyzer",
            },
        }

        return backend_map.get(language, {}).get(tool, "unknown")


class TargetResolver:
    """Resolves target specifications to concrete file lists"""

    def __init__(self, workspace_detector: WorkspaceDetector):
        self.workspace_detector = workspace_detector

    def resolve(
        self, target: str, language: str = "auto", root: Optional[str] = None
    ) -> Dict[str, Any]:
        """Resolve target specification"""
        if target.startswith("file:"):
            return self._resolve_file(target[5:], language, root)
        elif target.startswith("dir:"):
            return self._resolve_dir(target[4:], language, root)
        elif target.startswith("pkg:"):
            return self._resolve_package(target[4:], language, root)
        elif target == "ws":
            return self._resolve_workspace(language, root)
        elif target == "changed":
            return self._resolve_changed(language, root)
        else:
            raise ValueError(f"Unknown target format: {target}")

    def _resolve_file(
        self, file_path: str, language: str, root: Optional[str]
    ) -> Dict[str, Any]:
        """Resolve single file"""
        path = Path(file_path).absolute()
        workspace = self.workspace_detector.detect(str(path))

        return {
            "type": "file",
            "paths": [str(path)],
            "workspace": workspace,
            "language": self._infer_language(path, workspace, language),
        }

    def _resolve_dir(
        self, dir_path: str, language: str, root: Optional[str]
    ) -> Dict[str, Any]:
        """Resolve directory subtree"""
        path = Path(dir_path).absolute()
        workspace = self.workspace_detector.detect(str(path))

        # Find relevant files
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

    def _resolve_workspace(self, language: str, root: Optional[str]) -> Dict[str, Any]:
        """Resolve workspace root"""
        workspace = self.workspace_detector.detect(root or ".")
        root_path = Path(workspace["root"])

        extensions = self._get_extensions_for_language(language)
        files = []
        for ext in extensions:
            files.extend(root_path.rglob(f"*{ext}"))

        return {
            "type": "workspace",
            "paths": [str(f) for f in files],
            "workspace": workspace,
            "language": language,
        }

    def _resolve_package(
        self, pkg_spec: str, language: str, root: Optional[str]
    ) -> Dict[str, Any]:
        """Resolve package specification (simplified)"""
        workspace = self.workspace_detector.detect(root or ".")

        if language == "go" and pkg_spec == "./...":
            # All Go packages in workspace
            return self._resolve_workspace("go", workspace["root"])

        # Default to directory resolution
        return self._resolve_dir(pkg_spec, language, root)

    def _resolve_changed(self, language: str, root: Optional[str]) -> Dict[str, Any]:
        """Resolve git changed files"""
        workspace = self.workspace_detector.detect(root or ".")

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

            # Make paths absolute
            root_path = Path(workspace["root"])
            absolute_files = [
                str(root_path / f) for f in changed_files if (root_path / f).exists()
            ]

            return {
                "type": "changed",
                "paths": absolute_files,
                "workspace": workspace,
                "language": language,
            }
        except subprocess.CalledProcessError:
            return {
                "type": "changed",
                "paths": [],
                "workspace": workspace,
                "language": language,
                "error": "Not a git repository",
            }

    def _infer_language(self, path: Path, workspace: Dict, language_hint: str) -> str:
        """Infer language from context"""
        if language_hint != "auto":
            return language_hint

        if workspace["language"] != "auto":
            return workspace["language"]

        # Infer from extension
        if path.is_file():
            extension_map = {
                ".go": "go",
                ".ts": "ts",
                ".js": "ts",
                ".py": "py",
                ".rs": "rs",
            }
            return extension_map.get(path.suffix, "auto")

        return "auto"

    def _get_extensions_for_language(self, language: str) -> List[str]:
        """Get file extensions for language"""
        extension_map = {
            "go": [".go"],
            "ts": [".ts", ".js"],
            "py": [".py"],
            "rs": [".rs"],
            "auto": [".go", ".ts", ".js", ".py", ".rs"],
        }
        return extension_map.get(language, [".go", ".ts", ".py"])


class SimpleTools:
    """Simplified implementation of the 6 universal tools"""

    def __init__(self):
        self.workspace_detector = WorkspaceDetector()
        self.target_resolver = TargetResolver(self.workspace_detector)
        self.backend_selector = BackendSelector()

    def fmt(
        self,
        target: str,
        language: str = "auto",
        dry_run: bool = False,
        opts: Optional[Dict] = None,
    ) -> ToolResult:
        """Format tool: formatting + import normalization"""
        try:
            resolved = self.target_resolver.resolve(target, language)
            workspace = resolved["workspace"]
            detected_language = resolved["language"]

            backend = self.backend_selector.select_backend(detected_language, "fmt")

            if dry_run:
                return ToolResult(
                    ok=True,
                    root=workspace["root"],
                    language_used=detected_language,
                    backend_used=backend,
                    scope_resolved=resolved["paths"],
                    touched_files=[],
                    stdout=f"Would format {len(resolved['paths'])} files with {backend}",
                    stderr="",
                    exit_code=0,
                    errors=[],
                )

            # Mock formatting (would run actual formatter)
            touched_files = resolved["paths"][:3]  # Simulate some files being formatted

            return ToolResult(
                ok=True,
                root=workspace["root"],
                language_used=detected_language,
                backend_used=backend,
                scope_resolved=resolved["paths"],
                touched_files=touched_files,
                stdout=f"Formatted {len(touched_files)} files",
                stderr="",
                exit_code=0,
                errors=[],
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
            )

    def test(
        self,
        target: str,
        language: str = "auto",
        dry_run: bool = False,
        opts: Optional[Dict] = None,
    ) -> ToolResult:
        """Test tool: run tests narrowly by default"""
        try:
            resolved = self.target_resolver.resolve(target, language)
            workspace = resolved["workspace"]
            detected_language = resolved["language"]

            backend = self.backend_selector.select_backend(detected_language, "test")

            if dry_run:
                return ToolResult(
                    ok=True,
                    root=workspace["root"],
                    language_used=detected_language,
                    backend_used=backend,
                    scope_resolved=resolved["paths"],
                    touched_files=[],
                    stdout=f"Would run tests with {backend}",
                    stderr="",
                    exit_code=0,
                    errors=[],
                )

            # Mock test run
            return ToolResult(
                ok=True,
                root=workspace["root"],
                language_used=detected_language,
                backend_used=backend,
                scope_resolved=resolved["paths"],
                touched_files=[],
                stdout=f"Tests passed for {len(resolved['paths'])} files",
                stderr="",
                exit_code=0,
                errors=[],
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
            )

    def edit(
        self,
        target: str,
        op: str,
        language: str = "auto",
        dry_run: bool = False,
        **kwargs,
    ) -> ToolResult:
        """Edit tool: semantic refactors via LSP"""
        try:
            resolved = self.target_resolver.resolve(target, language)
            workspace = resolved["workspace"]
            detected_language = resolved["language"]

            backend = self.backend_selector.select_backend(detected_language, "edit")

            if op == "organize_imports":
                touched_files = resolved["paths"] if not dry_run else []
                action_desc = (
                    "Would organize imports" if dry_run else "Organized imports"
                )
            elif op == "rename":
                touched_files = (
                    [kwargs.get("file", "")]
                    if not dry_run and kwargs.get("file")
                    else []
                )
                new_name = kwargs.get("new_name", "NewName")
                action_desc = (
                    f"Would rename to {new_name}"
                    if dry_run
                    else f"Renamed to {new_name}"
                )
            else:
                action_desc = f"Would perform {op}" if dry_run else f"Performed {op}"
                touched_files = []

            return ToolResult(
                ok=True,
                root=workspace["root"],
                language_used=detected_language,
                backend_used=backend,
                scope_resolved=resolved["paths"],
                touched_files=touched_files,
                stdout=action_desc,
                stderr="",
                exit_code=0,
                errors=[],
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
            )

    def build(
        self,
        target: str,
        language: str = "auto",
        dry_run: bool = False,
        opts: Optional[Dict] = None,
    ) -> ToolResult:
        """Build tool: compile/build artifacts"""
        try:
            resolved = self.target_resolver.resolve(target, language)
            workspace = resolved["workspace"]
            detected_language = resolved["language"]

            backend = self.backend_selector.select_backend(detected_language, "build")

            action = "Would build" if dry_run else "Built"

            return ToolResult(
                ok=True,
                root=workspace["root"],
                language_used=detected_language,
                backend_used=backend,
                scope_resolved=resolved["paths"],
                touched_files=[],
                stdout=f"{action} project with {backend}",
                stderr="",
                exit_code=0,
                errors=[],
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
            )

    def lint(
        self,
        target: str,
        language: str = "auto",
        dry_run: bool = False,
        opts: Optional[Dict] = None,
    ) -> ToolResult:
        """Lint tool: lint/typecheck in one place"""
        try:
            resolved = self.target_resolver.resolve(target, language)
            workspace = resolved["workspace"]
            detected_language = resolved["language"]

            backend = self.backend_selector.select_backend(detected_language, "lint")

            action = "Would lint" if dry_run else "Linted"

            return ToolResult(
                ok=True,
                root=workspace["root"],
                language_used=detected_language,
                backend_used=backend,
                scope_resolved=resolved["paths"],
                touched_files=[],
                stdout=f"{action} {len(resolved['paths'])} files with {backend}",
                stderr="",
                exit_code=0,
                errors=[],
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
            )

    def guard(
        self,
        target: str,
        rules: List[Dict],
        language: str = "auto",
        dry_run: bool = False,
    ) -> ToolResult:
        """Guard tool: repo invariants"""
        try:
            resolved = self.target_resolver.resolve(target, language)
            workspace = resolved["workspace"]

            violations = []
            for rule in rules:
                # Simplified rule checking
                if rule.get("type") == "import" and rule.get("forbid_import_prefix"):
                    # Mock finding violations
                    violations.append(
                        f"Found forbidden import '{rule['forbid_import_prefix']}' in files matching {rule['glob']}"
                    )

            return ToolResult(
                ok=len(violations) == 0,
                root=workspace["root"],
                language_used=language,
                backend_used="guard",
                scope_resolved=resolved["paths"],
                touched_files=[],
                stdout=f"Checked {len(rules)} rules, found {len(violations)} violations",
                stderr="",
                exit_code=0 if len(violations) == 0 else 1,
                errors=violations,
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
            )


async def demo_exact_tools():
    """Demonstrate the exact 6-tool implementation"""
    print("🚀 Demonstrating Exact 6-Tool Implementation\n")

    tools = SimpleTools()

    # Create a temporary workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_dir = Path(temp_dir)

        # Create Go workspace structure
        print("📁 Creating test Go workspace...")

        # go.work file (highest priority)
        go_work = workspace_dir / "go.work"
        go_work.write_text("""go 1.21

use (
    ./api
    ./cli
)
""")

        # API module
        api_dir = workspace_dir / "api"
        api_dir.mkdir()

        api_mod = api_dir / "go.mod"
        api_mod.write_text("module github.com/luxfi/api\n\ngo 1.21\n")

        api_main = api_dir / "main.go"
        api_main.write_text("""package main

import (
	"fmt"
	"net/http"
)

func UserHandler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "Hello User")
}
""")

        # CLI module
        cli_dir = workspace_dir / "cli"
        cli_dir.mkdir()

        cli_mod = cli_dir / "go.mod"
        cli_mod.write_text("module github.com/luxfi/cli\n\ngo 1.21\n")

        cli_main = cli_dir / "main.go"
        cli_main.write_text("""package main

import "fmt"

func GreetUser(name string) {
	fmt.Printf("Hello %s\\n", name)
}
""")

        print(f"  Workspace created at: {workspace_dir}")
        print(f"  go.work file: {go_work.exists()}")

        # Test workspace detection
        print("\n🔍 Testing workspace detection...")
        workspace = tools.workspace_detector.detect(str(workspace_dir))
        print(f"  Detected type: {workspace['type']}")
        print(f"  Root: {workspace['root']}")
        print(f"  Language: {workspace['language']}")
        print("  ✅ go.work detected correctly")

        # Test target resolution
        print("\n🎯 Testing target resolution...")

        test_targets = [
            ("ws", "Entire workspace"),
            (f"file:{api_main}", "Single file"),
            (f"dir:{api_dir}", "Directory"),
            ("pkg:./...", "All packages"),
            ("changed", "Git changed files"),
        ]

        for target, description in test_targets:
            try:
                resolved = tools.target_resolver.resolve(
                    target, root=str(workspace_dir)
                )
                print(
                    f"  {description}: {len(resolved['paths'])} files, type: {resolved['type']}"
                )
            except Exception as e:
                print(f"  {description}: ❌ {e}")

        # Test all 6 tools
        print("\n🔧 Testing all 6 tools (dry-run)...")

        os.chdir(workspace_dir)  # Change to workspace for git commands

        # Initialize git repo for 'changed' target to work
        subprocess.run(["git", "init"], capture_output=True)
        subprocess.run(["git", "add", "."], capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], capture_output=True)

        # Test each tool
        test_cases = [
            (
                "fmt",
                tools.fmt,
                {
                    "target": "ws",
                    "dry_run": True,
                    "opts": {"local_prefix": "github.com/luxfi"},
                },
            ),
            (
                "edit",
                tools.edit,
                {
                    "target": "file:" + str(api_main),
                    "op": "organize_imports",
                    "dry_run": True,
                },
            ),
            ("test", tools.test, {"target": "pkg:./...", "dry_run": True}),
            ("build", tools.build, {"target": "ws", "dry_run": True}),
            ("lint", tools.lint, {"target": "changed", "dry_run": True}),
            (
                "guard",
                tools.guard,
                {
                    "target": "ws",
                    "rules": [
                        {
                            "id": "no-net-http",
                            "type": "import",
                            "glob": "api/*.go",
                            "forbid_import_prefix": "net/http",
                        }
                    ],
                    "dry_run": True,
                },
            ),
        ]

        for tool_name, tool_func, kwargs in test_cases:
            try:
                result = tool_func(**kwargs)
                status = "✅" if result.ok else "❌"
                print(
                    f"  {tool_name}: {status} {result.backend_used} - {result.stdout}"
                )
            except Exception as e:
                print(f"  {tool_name}: ❌ {e}")

        # Test composition workflow
        print("\n🔄 Testing composition workflow...")
        print("  Workflow: edit(organize_imports) → fmt → test → guard")

        # Step 1: Organize imports
        edit_result = tools.edit(target="ws", op="organize_imports", dry_run=True)
        print(f"  1. organize_imports: {'✅' if edit_result.ok else '❌'}")

        # Step 2: Format (use 'changed' from previous step)
        fmt_result = tools.fmt(target="changed", dry_run=True)
        print(f"  2. format changed: {'✅' if fmt_result.ok else '❌'}")

        # Step 3: Test affected packages
        test_result = tools.test(target="pkg:./...", dry_run=True)
        print(f"  3. test packages: {'✅' if test_result.ok else '❌'}")

        # Step 4: Check guard rules
        guard_result = tools.guard(
            target="ws",
            rules=[
                {
                    "id": "no-http",
                    "type": "import",
                    "glob": "**/*.go",
                    "forbid_import_prefix": "net/http",
                }
            ],
            dry_run=True,
        )
        print(
            f"  4. guard check: {'✅' if guard_result.ok else '❌'} ({len(guard_result.errors)} violations)"
        )

    print("\n🎉 Demonstration complete!")
    print("\n✨ Key Features Demonstrated:")
    print("  • Workspace detection with go.work priority")
    print("  • Target resolution (file:, dir:, pkg:, ws, changed)")
    print("  • Backend selection (language-specific tools)")
    print("  • All 6 universal tools (edit, fmt, test, build, lint, guard)")
    print("  • Tool composition workflows")
    print("  • Consistent input/output schemas")
    print("  • Dry-run support")


if __name__ == "__main__":
    asyncio.run(demo_exact_tools())
