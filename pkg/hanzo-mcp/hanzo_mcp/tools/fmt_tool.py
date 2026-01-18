"""
Format Tool - Code formatting + import normalization
===================================================

Purpose: formatting + import normalization across languages.

Backends:
- go: goimports (with local_prefix support)
- ts: prettier or biome
- py: ruff format or black
- rs: cargo fmt
- cc: clang-format
- sol: forge fmt / prettier
- schema: buf format (proto)
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from .dev_tools import DevResult, DevToolBase, create_dev_result


class FmtTool(DevToolBase):
    """Code formatting tool"""

    def __init__(self, target: str, **kwargs):
        super().__init__(target, **kwargs)
        self.opts = kwargs.get("opts", {})
        self.local_prefix = self.opts.get("local_prefix")  # For Go imports grouping

    async def execute(self) -> DevResult:
        """Execute formatting operation"""
        try:
            if self.language == "go":
                return await self._format_go()
            elif self.language == "ts":
                return await self._format_typescript()
            elif self.language == "py":
                return await self._format_python()
            elif self.language == "rs":
                return await self._format_rust()
            elif self.language == "cc":
                return await self._format_cpp()
            elif self.language == "sol":
                return await self._format_solidity()
            elif self.language == "schema":
                return await self._format_protobuf()
            else:
                return create_dev_result(
                    ok=False,
                    root=self.workspace["root"],
                    language_used=self.language,
                    backend_used=self.backend,
                    scope_resolved=self.target,
                    errors=[f"Formatting not supported for language: {self.language}"],
                )
        except Exception as e:
            return create_dev_result(
                ok=False,
                root=self.workspace["root"],
                language_used=self.language,
                backend_used=self.backend,
                scope_resolved=self.target,
                errors=[str(e)],
            )

    async def _format_go(self) -> DevResult:
        """Format Go code using goimports"""
        files = self.resolved["files"]
        go_files = [f for f in files if f.endswith(".go")]

        if not go_files:
            return create_dev_result(
                ok=True,
                root=self.workspace["root"],
                language_used=self.language,
                backend_used="goimports",
                scope_resolved=self.resolved["scope"],
                stdout="No Go files to format",
            )

        cmd = ["goimports", "-w"]

        # Add local prefix if specified
        if self.local_prefix:
            cmd.extend(["-local", self.local_prefix])

        cmd.extend(go_files)

        result = self._run_command(cmd)

        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="goimports",
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            touched_files=go_files if result.returncode == 0 else [],
        )

    async def _format_typescript(self) -> DevResult:
        """Format TypeScript/JavaScript code"""
        files = self.resolved["files"]
        ts_files = [f for f in files if any(f.endswith(ext) for ext in [".ts", ".tsx", ".js", ".jsx"])]

        if not ts_files:
            return create_dev_result(
                ok=True,
                root=self.workspace["root"],
                language_used=self.language,
                backend_used=self.backend,
                scope_resolved=self.resolved["scope"],
                stdout="No TypeScript/JavaScript files to format",
            )

        # Try biome first, then prettier
        if self.backend == "biome" or self._has_biome():
            return await self._format_with_biome(ts_files)
        else:
            return await self._format_with_prettier(ts_files)

    async def _format_python(self) -> DevResult:
        """Format Python code"""
        files = self.resolved["files"]
        py_files = [f for f in files if f.endswith(".py")]

        if not py_files:
            return create_dev_result(
                ok=True,
                root=self.workspace["root"],
                language_used=self.language,
                backend_used=self.backend,
                scope_resolved=self.resolved["scope"],
                stdout="No Python files to format",
            )

        # Use ruff format if available, otherwise black
        if self._has_ruff():
            cmd = ["ruff", "format"] + py_files
            backend = "ruff"
        else:
            cmd = ["black"] + py_files
            backend = "black"

        result = self._run_command(cmd)

        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used=backend,
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            touched_files=py_files if result.returncode == 0 else [],
        )

    async def _format_rust(self) -> DevResult:
        """Format Rust code using cargo fmt"""
        if self.resolved["type"] == "workspace":
            cmd = ["cargo", "fmt"]
        else:
            # Format specific files
            files = [f for f in self.resolved["files"] if f.endswith(".rs")]
            if not files:
                return create_dev_result(
                    ok=True,
                    root=self.workspace["root"],
                    language_used=self.language,
                    backend_used="cargo",
                    scope_resolved=self.resolved["scope"],
                    stdout="No Rust files to format",
                )
            cmd = ["rustfmt"] + files

        result = self._run_command(cmd)

        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="cargo",
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            touched_files=self.resolved["files"] if result.returncode == 0 else [],
        )

    async def _format_cpp(self) -> DevResult:
        """Format C/C++ code using clang-format"""
        files = self.resolved["files"]
        cpp_files = [f for f in files if any(f.endswith(ext) for ext in [".c", ".cpp", ".cc", ".cxx", ".h", ".hpp"])]

        if not cpp_files:
            return create_dev_result(
                ok=True,
                root=self.workspace["root"],
                language_used=self.language,
                backend_used="clang-format",
                scope_resolved=self.resolved["scope"],
                stdout="No C/C++ files to format",
            )

        cmd = ["clang-format", "-i"] + cpp_files

        result = self._run_command(cmd)

        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="clang-format",
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            touched_files=cpp_files if result.returncode == 0 else [],
        )

    async def _format_solidity(self) -> DevResult:
        """Format Solidity code"""
        files = self.resolved["files"]
        sol_files = [f for f in files if f.endswith(".sol")]

        if not sol_files:
            return create_dev_result(
                ok=True,
                root=self.workspace["root"],
                language_used=self.language,
                backend_used=self.backend,
                scope_resolved=self.resolved["scope"],
                stdout="No Solidity files to format",
            )

        # Try forge fmt first
        if self._has_forge():
            cmd = ["forge", "fmt"] + sol_files
            backend = "forge"
        else:
            # Fallback to prettier with solidity plugin
            cmd = ["prettier", "--write"] + sol_files
            backend = "prettier"

        result = self._run_command(cmd)

        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used=backend,
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            touched_files=sol_files if result.returncode == 0 else [],
        )

    async def _format_protobuf(self) -> DevResult:
        """Format Protocol Buffer files using buf"""
        files = self.resolved["files"]
        proto_files = [f for f in files if f.endswith(".proto")]

        if not proto_files:
            return create_dev_result(
                ok=True,
                root=self.workspace["root"],
                language_used=self.language,
                backend_used="buf",
                scope_resolved=self.resolved["scope"],
                stdout="No protobuf files to format",
            )

        cmd = ["buf", "format", "-w"] + proto_files

        result = self._run_command(cmd)

        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="buf",
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            touched_files=proto_files if result.returncode == 0 else [],
        )

    async def _format_with_prettier(self, files: List[str]) -> DevResult:
        """Format using Prettier"""
        cmd = ["prettier", "--write"] + files

        result = self._run_command(cmd)

        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="prettier",
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            touched_files=files if result.returncode == 0 else [],
        )

    async def _format_with_biome(self, files: List[str]) -> DevResult:
        """Format using Biome"""
        cmd = ["biome", "format", "--write"] + files

        result = self._run_command(cmd)

        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="biome",
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            touched_files=files if result.returncode == 0 else [],
        )

    def _has_biome(self) -> bool:
        """Check if Biome is available"""
        try:
            result = self._run_command(["biome", "--version"])
            return result.returncode == 0
        except (OSError, FileNotFoundError):
            return False

    def _has_ruff(self) -> bool:
        """Check if Ruff is available"""
        try:
            result = self._run_command(["ruff", "--version"])
            return result.returncode == 0
        except (OSError, FileNotFoundError):
            return False

    def _has_forge(self) -> bool:
        """Check if Forge is available"""
        try:
            result = self._run_command(["forge", "--version"])
            return result.returncode == 0
        except (OSError, FileNotFoundError):
            return False


# MCP tool integration
async def fmt_tool_handler(
    target: str,
    language: str = "auto",
    backend: str = "auto",
    root: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
    opts: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """MCP handler for fmt tool"""

    tool = FmtTool(
        target=target, language=language, backend=backend, root=root, env=env, dry_run=dry_run, opts=opts or {}
    )

    result = await tool.execute()
    return result.dict()
