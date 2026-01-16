"""
Lint Tool - Static analysis and type checking
============================================

Purpose: lint/typecheck in one place across languages.

Backends:
- go: golangci-lint + go vet (configurable)
- ts: eslint + optionally tsc --noEmit  
- py: ruff check + optionally pyright/mypy
- rs: cargo clippy
- cc: clang-tidy (optional)
- sol: slither (optional)
- schema: buf lint

Options:
- fix: Apply fixes where supported
"""

from typing import Optional, Dict, Any, List
from pathlib import Path

from .dev_tools import DevToolBase, DevResult, create_dev_result

class LintTool(DevToolBase):
    """Static analysis and linting tool"""
    
    def __init__(self, target: str, **kwargs):
        super().__init__(target, **kwargs)
        self.opts = kwargs.get('opts', {})
        self.fix = self.opts.get('fix', False)
        
    async def execute(self) -> DevResult:
        """Execute lint operation"""
        try:
            if self.language == "go":
                return await self._lint_go()
            elif self.language == "ts":
                return await self._lint_typescript()
            elif self.language == "py":
                return await self._lint_python()
            elif self.language == "rs":
                return await self._lint_rust()
            elif self.language == "cc":
                return await self._lint_cpp()
            elif self.language == "sol":
                return await self._lint_solidity()
            elif self.language == "schema":
                return await self._lint_protobuf()
            else:
                return create_dev_result(
                    ok=False,
                    root=self.workspace["root"],
                    language_used=self.language,
                    backend_used=self.backend,
                    scope_resolved=self.target,
                    errors=[f"Linting not supported for language: {self.language}"]
                )
        except Exception as e:
            return create_dev_result(
                ok=False,
                root=self.workspace["root"],
                language_used=self.language,
                backend_used=self.backend,
                scope_resolved=self.target,
                errors=[str(e)]
            )
    
    async def _lint_go(self) -> DevResult:
        """Lint Go code"""
        results = []
        
        # Run go vet first (always available)
        vet_result = await self._run_go_vet()
        results.append(("go vet", vet_result))
        
        # Run golangci-lint if available
        if self._has_golangci_lint():
            lint_result = await self._run_golangci_lint()
            results.append(("golangci-lint", lint_result))
        
        # Combine results
        overall_ok = all(result.returncode == 0 for _, result in results)
        combined_stdout = "\n".join(f"=== {name} ===\n{result.stdout}" for name, result in results)
        combined_stderr = "\n".join(f"=== {name} ===\n{result.stderr}" for name, result in results)
        
        return create_dev_result(
            ok=overall_ok,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="go vet + golangci-lint" if len(results) > 1 else "go vet",
            scope_resolved=self.resolved["scope"],
            stdout=combined_stdout,
            stderr=combined_stderr,
            exit_code=0 if overall_ok else 1
        )
    
    async def _lint_typescript(self) -> DevResult:
        """Lint TypeScript/JavaScript code"""
        results = []
        
        # Run ESLint
        eslint_result = await self._run_eslint()
        results.append(("eslint", eslint_result))
        
        # Run tsc --noEmit for type checking
        if self._has_typescript():
            tsc_result = await self._run_tsc_check()
            results.append(("tsc", tsc_result))
        
        # Combine results
        overall_ok = all(result.returncode == 0 for _, result in results)
        combined_stdout = "\n".join(f"=== {name} ===\n{result.stdout}" for name, result in results)
        combined_stderr = "\n".join(f"=== {name} ===\n{result.stderr}" for name, result in results)
        
        backend = " + ".join(name for name, _ in results)
        
        return create_dev_result(
            ok=overall_ok,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used=backend,
            scope_resolved=self.resolved["scope"],
            stdout=combined_stdout,
            stderr=combined_stderr,
            exit_code=0 if overall_ok else 1
        )
    
    async def _lint_python(self) -> DevResult:
        """Lint Python code"""
        results = []
        
        # Run ruff check
        if self._has_ruff():
            ruff_result = await self._run_ruff_check()
            results.append(("ruff", ruff_result))
        
        # Run type checker if available
        if self._has_pyright():
            pyright_result = await self._run_pyright()
            results.append(("pyright", pyright_result))
        elif self._has_mypy():
            mypy_result = await self._run_mypy()
            results.append(("mypy", mypy_result))
        
        if not results:
            return create_dev_result(
                ok=False,
                root=self.workspace["root"],
                language_used=self.language,
                backend_used="none",
                scope_resolved=self.target,
                errors=["No Python linter found (install ruff, pylint, or flake8)"]
            )
        
        # Combine results
        overall_ok = all(result.returncode == 0 for _, result in results)
        combined_stdout = "\n".join(f"=== {name} ===\n{result.stdout}" for name, result in results)
        combined_stderr = "\n".join(f"=== {name} ===\n{result.stderr}" for name, result in results)
        
        backend = " + ".join(name for name, _ in results)
        
        return create_dev_result(
            ok=overall_ok,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used=backend,
            scope_resolved=self.resolved["scope"],
            stdout=combined_stdout,
            stderr=combined_stderr,
            exit_code=0 if overall_ok else 1
        )
    
    async def _lint_rust(self) -> DevResult:
        """Lint Rust code"""
        cmd = ["cargo", "clippy"]
        
        # Add package filter if linting specific package
        if self.resolved["type"] == "file":
            cargo_toml = self._find_rust_package(self.resolved["scope"])
            if cargo_toml:
                package_name = self._get_rust_package_name(cargo_toml)
                if package_name:
                    cmd.extend(["-p", package_name])
        
        # Add clippy options
        cmd.append("--")
        if not self.fix:
            cmd.append("-D")
            cmd.append("warnings")
        
        result = self._run_command(cmd)
        
        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="cargo clippy",
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode
        )
    
    async def _lint_cpp(self) -> DevResult:
        """Lint C/C++ code"""
        if not self._has_clang_tidy():
            return create_dev_result(
                ok=True,
                root=self.workspace["root"],
                language_used=self.language,
                backend_used="none",
                scope_resolved=self.resolved["scope"],
                stdout="clang-tidy not available, skipping C++ linting"
            )
        
        files = [f for f in self.resolved["files"] if any(f.endswith(ext) for ext in ['.c', '.cpp', '.cc', '.cxx'])]
        
        if not files:
            return create_dev_result(
                ok=True,
                root=self.workspace["root"],
                language_used=self.language,
                backend_used="clang-tidy",
                scope_resolved=self.resolved["scope"],
                stdout="No C/C++ files to lint"
            )
        
        cmd = ["clang-tidy"] + files
        
        result = self._run_command(cmd)
        
        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="clang-tidy",
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode
        )
    
    async def _lint_solidity(self) -> DevResult:
        """Lint Solidity code"""
        if not self._has_slither():
            return create_dev_result(
                ok=True,
                root=self.workspace["root"],
                language_used=self.language,
                backend_used="none",
                scope_resolved=self.resolved["scope"],
                stdout="slither not available, skipping Solidity linting"
            )
        
        cmd = ["slither", "."]
        
        result = self._run_command(cmd)
        
        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="slither",
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode
        )
    
    async def _lint_protobuf(self) -> DevResult:
        """Lint Protocol Buffer files"""
        cmd = ["buf", "lint"]
        
        result = self._run_command(cmd)
        
        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="buf",
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode
        )
    
    async def _run_go_vet(self) -> object:
        """Run go vet"""
        cmd = ["go", "vet"]
        
        if self.resolved["type"] == "package":
            cmd.append(self.resolved["scope"])
        elif self.resolved["type"] == "workspace":
            cmd.append("./...")
        else:
            cmd.append(".")
        
        return self._run_command(cmd)
    
    async def _run_golangci_lint(self) -> object:
        """Run golangci-lint"""
        cmd = ["golangci-lint", "run"]
        
        if self.fix:
            cmd.append("--fix")
        
        return self._run_command(cmd)
    
    async def _run_eslint(self) -> object:
        """Run ESLint"""
        cmd = ["eslint"]
        
        if self.fix:
            cmd.append("--fix")
        
        # Add file patterns
        if self.resolved["type"] == "file":
            cmd.append(self.resolved["scope"])
        elif self.resolved["type"] == "directory":
            cmd.append(f"{self.resolved['scope']}/**/*.{{js,jsx,ts,tsx}}")
        else:
            cmd.extend(["**/*.{js,jsx,ts,tsx}"])
        
        return self._run_command(cmd)
    
    async def _run_tsc_check(self) -> object:
        """Run TypeScript compiler for type checking"""
        cmd = ["tsc", "--noEmit"]
        
        # Add project file if specific scope
        if self.resolved["type"] != "workspace":
            tsconfig = self._find_tsconfig(self.resolved["scope"])
            if tsconfig:
                cmd.extend(["-p", str(tsconfig.parent)])
        
        return self._run_command(cmd)
    
    async def _run_ruff_check(self) -> object:
        """Run ruff check"""
        cmd = ["ruff", "check"]
        
        if self.fix:
            cmd.append("--fix")
        
        # Add target files
        if self.resolved["type"] == "file":
            cmd.append(self.resolved["scope"])
        elif self.resolved["type"] == "directory":
            cmd.append(self.resolved["scope"])
        else:
            cmd.append(".")
        
        return self._run_command(cmd)
    
    async def _run_pyright(self) -> object:
        """Run Pyright type checker"""
        cmd = ["pyright"]
        
        if self.resolved["type"] == "file":
            cmd.append(self.resolved["scope"])
        elif self.resolved["type"] == "directory":
            cmd.append(self.resolved["scope"])
        
        return self._run_command(cmd)
    
    async def _run_mypy(self) -> object:
        """Run mypy type checker"""
        cmd = ["mypy"]
        
        if self.resolved["type"] == "file":
            cmd.append(self.resolved["scope"])
        elif self.resolved["type"] == "directory":
            cmd.append(self.resolved["scope"])
        else:
            cmd.append(".")
        
        return self._run_command(cmd)
    
    def _has_golangci_lint(self) -> bool:
        """Check if golangci-lint is available"""
        try:
            result = self._run_command(["golangci-lint", "--version"])
            return result.returncode == 0
        except:
            return False
    
    def _has_typescript(self) -> bool:
        """Check if TypeScript is available"""
        try:
            result = self._run_command(["tsc", "--version"])
            return result.returncode == 0
        except:
            return False
    
    def _has_ruff(self) -> bool:
        """Check if Ruff is available"""
        try:
            result = self._run_command(["ruff", "--version"])
            return result.returncode == 0
        except:
            return False
    
    def _has_pyright(self) -> bool:
        """Check if Pyright is available"""
        try:
            result = self._run_command(["pyright", "--version"])
            return result.returncode == 0
        except:
            return False
    
    def _has_mypy(self) -> bool:
        """Check if mypy is available"""
        try:
            result = self._run_command(["mypy", "--version"])
            return result.returncode == 0
        except:
            return False
    
    def _has_clang_tidy(self) -> bool:
        """Check if clang-tidy is available"""
        try:
            result = self._run_command(["clang-tidy", "--version"])
            return result.returncode == 0
        except:
            return False
    
    def _has_slither(self) -> bool:
        """Check if slither is available"""
        try:
            result = self._run_command(["slither", "--version"])
            return result.returncode == 0
        except:
            return False
    
    def _find_tsconfig(self, file_path: str) -> Optional[Path]:
        """Find nearest tsconfig.json"""
        path = Path(file_path)
        current = path.parent if path.is_file() else path
        
        while current >= Path(self.workspace["root"]):
            tsconfig = current / "tsconfig.json"
            if tsconfig.exists():
                return tsconfig
            current = current.parent
        
        return None
    
    def _find_rust_package(self, file_path: str) -> Optional[str]:
        """Find Cargo.toml for given file"""
        path = Path(file_path)
        current = path.parent if path.is_file() else path
        
        while current >= Path(self.workspace["root"]):
            cargo_toml = current / "Cargo.toml"
            if cargo_toml.exists():
                return str(cargo_toml)
            current = current.parent
        
        return None
    
    def _get_rust_package_name(self, cargo_toml_path: str) -> Optional[str]:
        """Extract package name from Cargo.toml"""
        try:
            import toml
            with open(cargo_toml_path) as f:
                data = toml.load(f)
            return data.get("package", {}).get("name")
        except:
            return None

# MCP tool integration
async def lint_tool_handler(
    target: str,
    language: str = "auto",
    backend: str = "auto",
    root: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
    opts: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """MCP handler for lint tool"""
    
    tool = LintTool(
        target=target,
        language=language,
        backend=backend,
        root=root,
        env=env,
        dry_run=dry_run,
        opts=opts or {}
    )
    
    result = await tool.execute()
    return result.dict()