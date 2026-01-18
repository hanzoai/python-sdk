"""
Test Tool - Run tests narrowly by default
=========================================

Purpose: run tests narrowly by default with smart scope resolution.

Target resolution:
- file → derive owning package/project and run its tests
- dir → run tests for that subtree
- pkg → use explicitly
- ws → workspace-wide (discouraged unless asked)

Backends:
- go: go test with -run, -count, -race flags
- ts: test runner with --filter, --watch=false
- py: pytest with -k, -m flags
- rs: cargo test with -p, --features
"""

import re
from typing import Any, Dict, List, Optional
from pathlib import Path

from .dev_tools import DevResult, DevToolBase, create_dev_result


class TestTool(DevToolBase):
    """Test execution tool"""

    def __init__(self, target: str, **kwargs):
        super().__init__(target, **kwargs)
        self.opts = kwargs.get("opts", {})

    async def execute(self) -> DevResult:
        """Execute test operation"""
        try:
            if self.language == "go":
                return await self._test_go()
            elif self.language == "ts":
                return await self._test_typescript()
            elif self.language == "py":
                return await self._test_python()
            elif self.language == "rs":
                return await self._test_rust()
            else:
                return create_dev_result(
                    ok=False,
                    root=self.workspace["root"],
                    language_used=self.language,
                    backend_used=self.backend,
                    scope_resolved=self.target,
                    errors=[f"Testing not supported for language: {self.language}"],
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

    async def _test_go(self) -> DevResult:
        """Run Go tests"""
        cmd = ["go", "test"]

        # Determine test scope
        if self.resolved["type"] == "file":
            # Get package containing the file
            pkg = self.resolved["package"]
            if pkg and pkg != ".":
                cmd.append(f"./{pkg}")
            else:
                cmd.append(".")
        elif self.resolved["type"] == "directory":
            # Test directory subtree
            dir_path = self.resolved["scope"]
            cmd.append(f"./{dir_path}/...")
        elif self.resolved["type"] == "package":
            # Test specific package(s)
            pkg_spec = self.resolved["scope"]
            cmd.append(pkg_spec)
        elif self.resolved["type"] == "workspace":
            # Test all packages
            cmd.append("./...")
        else:
            cmd.append(".")

        # Add common flags
        if self.opts.get("run"):
            cmd.extend(["-run", self.opts["run"]])
        if self.opts.get("count"):
            cmd.extend(["-count", str(self.opts["count"])])
        if self.opts.get("race"):
            cmd.append("-race")

        # Always run verbosely for better output
        cmd.append("-v")

        result = self._run_command(cmd)

        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="go",
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
        )

    async def _test_typescript(self) -> DevResult:
        """Run TypeScript/JavaScript tests"""
        # Detect test runner
        if self.backend == "jest" or self._has_jest():
            return await self._test_with_jest()
        elif self.backend == "vitest" or self._has_vitest():
            return await self._test_with_vitest()
        elif self.backend in ["pnpm", "npm", "yarn"]:
            return await self._test_with_package_script()
        else:
            return create_dev_result(
                ok=False,
                root=self.workspace["root"],
                language_used=self.language,
                backend_used=self.backend,
                scope_resolved=self.target,
                errors=["No test runner detected (jest, vitest, or package.json script)"],
            )

    async def _test_python(self) -> DevResult:
        """Run Python tests"""
        # Use pytest by default
        cmd = ["pytest"]

        # Determine test scope
        if self.resolved["type"] == "file":
            # Test specific file or its test counterpart
            file_path = self.resolved["scope"]
            test_file = self._find_python_test_file(file_path)
            if test_file:
                cmd.append(test_file)
            else:
                # Run tests in same directory
                cmd.append(str(Path(file_path).parent))
        elif self.resolved["type"] == "directory":
            # Test directory
            cmd.append(self.resolved["scope"])
        elif self.resolved["type"] == "workspace":
            # Test entire workspace - don't add specific path
            pass
        else:
            cmd.append(".")

        # Add options
        if self.opts.get("k"):
            cmd.extend(["-k", self.opts["k"]])
        if self.opts.get("m"):
            cmd.extend(["-m", self.opts["m"]])

        # Add verbose output
        cmd.append("-v")

        result = self._run_command(cmd)

        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="pytest",
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
        )

    async def _test_rust(self) -> DevResult:
        """Run Rust tests"""
        cmd = ["cargo", "test"]

        # Add package filter if testing specific package
        if self.resolved["type"] == "file":
            # Find Cargo.toml for this file
            cargo_toml = self._find_rust_package(self.resolved["scope"])
            if cargo_toml:
                package_name = self._get_rust_package_name(cargo_toml)
                if package_name:
                    cmd.extend(["-p", package_name])

        # Add options
        if self.opts.get("p"):
            cmd.extend(["-p", self.opts["p"]])
        if self.opts.get("features"):
            cmd.extend(["--features", self.opts["features"]])

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
        )

    async def _test_with_jest(self) -> DevResult:
        """Run tests with Jest"""
        cmd = ["jest"]

        # Add test pattern based on scope
        if self.resolved["type"] == "file":
            # Test specific file or related tests
            file_path = self.resolved["scope"]
            test_pattern = self._get_jest_pattern(file_path)
            if test_pattern:
                cmd.append(test_pattern)
        elif self.resolved["type"] == "directory":
            cmd.append(self.resolved["scope"])

        # Add options
        if self.opts.get("filter"):
            cmd.extend(["--testNamePattern", self.opts["filter"]])

        # Disable watch mode
        cmd.append("--watchAll=false")

        result = self._run_command(cmd)

        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="jest",
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
        )

    async def _test_with_vitest(self) -> DevResult:
        """Run tests with Vitest"""
        cmd = ["vitest", "run"]  # run mode instead of watch

        # Add test pattern
        if self.resolved["type"] == "file":
            file_path = self.resolved["scope"]
            test_pattern = self._get_vitest_pattern(file_path)
            if test_pattern:
                cmd.append(test_pattern)
        elif self.resolved["type"] == "directory":
            cmd.append(self.resolved["scope"])

        # Add options
        if self.opts.get("filter"):
            cmd.extend(["-t", self.opts["filter"]])

        result = self._run_command(cmd)

        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used="vitest",
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
        )

    async def _test_with_package_script(self) -> DevResult:
        """Run tests via package.json script"""
        # Use package manager test script
        if self.backend == "pnpm":
            cmd = ["pnpm", "test"]
        elif self.backend == "yarn":
            cmd = ["yarn", "test"]
        else:
            cmd = ["npm", "test"]

        result = self._run_command(cmd)

        return create_dev_result(
            ok=result.returncode == 0,
            root=self.workspace["root"],
            language_used=self.language,
            backend_used=self.backend,
            scope_resolved=self.resolved["scope"],
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
        )

    def _find_python_test_file(self, file_path: str) -> Optional[str]:
        """Find corresponding test file for Python module"""
        path = Path(file_path)

        # Common test patterns
        test_patterns = [
            path.parent / f"test_{path.stem}.py",
            path.parent / f"{path.stem}_test.py",
            path.parent / "tests" / f"test_{path.stem}.py",
            path.parent.parent / "tests" / f"test_{path.stem}.py",
        ]

        for test_path in test_patterns:
            if test_path.exists():
                return str(test_path)

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
        except (OSError, ImportError, ValueError, KeyError):
            return None

    def _get_jest_pattern(self, file_path: str) -> Optional[str]:
        """Get Jest test pattern for file"""
        path = Path(file_path)

        # If it's already a test file, run it directly
        if "test" in path.stem or "spec" in path.stem:
            return str(path)

        # Look for corresponding test files
        patterns = [f"**/*{path.stem}*.test.*", f"**/*{path.stem}*.spec.*", f"**/test*{path.stem}*"]

        return patterns[0]  # Return first pattern as fallback

    def _get_vitest_pattern(self, file_path: str) -> Optional[str]:
        """Get Vitest test pattern for file"""
        return self._get_jest_pattern(file_path)  # Similar patterns

    def _has_jest(self) -> bool:
        """Check if Jest is available"""
        try:
            result = self._run_command(["jest", "--version"])
            return result.returncode == 0
        except (OSError, FileNotFoundError):
            return False

    def _has_vitest(self) -> bool:
        """Check if Vitest is available"""
        try:
            result = self._run_command(["vitest", "--version"])
            return result.returncode == 0
        except (OSError, FileNotFoundError):
            return False


# MCP tool integration
async def test_tool_handler(
    target: str,
    language: str = "auto",
    backend: str = "auto",
    root: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
    opts: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """MCP handler for test tool"""

    tool = TestTool(
        target=target, language=language, backend=backend, root=root, env=env, dry_run=dry_run, opts=opts or {}
    )

    result = await tool.execute()
    return result.dict()
