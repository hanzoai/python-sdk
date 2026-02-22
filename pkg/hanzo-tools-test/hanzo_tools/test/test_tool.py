"""Unified validation tool for HIP-0300 architecture.

This module provides a single unified 'test' tool for three distinct feedback loops:

1. CHECK (fast, incremental, per-file)
   - Static properties: syntax, types, lint rules
   - Substrate: LSP / linters
   - Output: Diagnostics + quickfix edits
   - Composition: Check → Fix → Apply → Check

2. BUILD (slower, whole-project)
   - Validates: linkability, packaging, compile graph
   - Substrate: build system
   - Output: logs + artifacts
   - Composition: Build → ParseErrors → Patch → Build

3. TEST (executes code, validates behavior)
   - Validates: runtime behavior, specs, invariants
   - Substrate: test runner
   - Output: pass/fail + traces
   - Composition: Test → Locate(failure) → Patch → Test

Effect lattice position: NONDETERMINISTIC_EFFECT
Representation: Report (Diagnostics | BuildResult | TestResult)
Scope: Buffer → File → Package → Repo
"""

import asyncio
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Literal

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import (
    BaseTool,
    InvalidParamsError,
    ToolError,
    content_hash,
)

# Test runner detection and commands
TEST_RUNNERS = {
    # Python
    "pytest": {
        "detect": ["pytest.ini", "pyproject.toml", "setup.py"],
        "cmd": ["pytest", "-v", "--tb=short"],
        "parse": "pytest",
    },
    "unittest": {
        "detect": ["test*.py"],
        "cmd": ["python", "-m", "unittest", "discover", "-v"],
        "parse": "unittest",
    },
    # JavaScript/TypeScript
    "jest": {
        "detect": ["jest.config.js", "jest.config.ts", "package.json"],
        "cmd": ["npx", "jest", "--json"],
        "parse": "jest",
    },
    "vitest": {
        "detect": ["vitest.config.ts", "vitest.config.js"],
        "cmd": ["npx", "vitest", "run", "--reporter=json"],
        "parse": "vitest",
    },
    "mocha": {
        "detect": [".mocharc.js", ".mocharc.json"],
        "cmd": ["npx", "mocha", "--reporter", "json"],
        "parse": "mocha",
    },
    # Go
    "go_test": {
        "detect": ["go.mod"],
        "cmd": ["go", "test", "-v", "-json", "./..."],
        "parse": "go_test",
    },
    # Rust
    "cargo_test": {
        "detect": ["Cargo.toml"],
        "cmd": ["cargo", "test", "--", "--format=json", "-Z", "unstable-options"],
        "parse": "cargo_test",
    },
}

# Build tools
BUILD_TOOLS = {
    # Python
    "pip": {
        "detect": ["pyproject.toml", "setup.py"],
        "cmd": ["pip", "install", "-e", "."],
        "parse": "pip",
    },
    "poetry": {
        "detect": ["poetry.lock"],
        "cmd": ["poetry", "build"],
        "parse": "poetry",
    },
    # JavaScript/TypeScript
    "npm": {
        "detect": ["package.json"],
        "cmd": ["npm", "run", "build"],
        "parse": "npm",
    },
    "pnpm": {
        "detect": ["pnpm-lock.yaml"],
        "cmd": ["pnpm", "build"],
        "parse": "pnpm",
    },
    # Go
    "go_build": {
        "detect": ["go.mod"],
        "cmd": ["go", "build", "./..."],
        "parse": "go_build",
    },
    # Rust
    "cargo_build": {
        "detect": ["Cargo.toml"],
        "cmd": ["cargo", "build"],
        "parse": "cargo_build",
    },
    # Make
    "make": {
        "detect": ["Makefile"],
        "cmd": ["make"],
        "parse": "make",
    },
}

# Check tools (fast, incremental linting/typechecking)
CHECK_TOOLS = {
    # Python
    "ruff": {
        "detect": ["ruff.toml", "pyproject.toml"],
        "cmd": ["ruff", "check", "--output-format=json"],
        "parse": "ruff",
    },
    "mypy": {
        "detect": ["mypy.ini", "pyproject.toml"],
        "cmd": ["mypy", "--output=json"],
        "parse": "mypy",
    },
    "pylint": {
        "detect": [".pylintrc", "pyproject.toml"],
        "cmd": ["pylint", "--output-format=json"],
        "parse": "pylint",
    },
    # JavaScript/TypeScript
    "eslint": {
        "detect": [".eslintrc", ".eslintrc.js", ".eslintrc.json"],
        "cmd": ["npx", "eslint", "--format=json"],
        "parse": "eslint",
    },
    "tsc": {
        "detect": ["tsconfig.json"],
        "cmd": ["npx", "tsc", "--noEmit"],
        "parse": "tsc",
    },
    # Go
    "golangci-lint": {
        "detect": [".golangci.yml", ".golangci.yaml"],
        "cmd": ["golangci-lint", "run", "--out-format=json"],
        "parse": "golangci",
    },
    # Rust
    "cargo_clippy": {
        "detect": ["Cargo.toml"],
        "cmd": ["cargo", "clippy", "--message-format=json"],
        "parse": "clippy",
    },
}


@dataclass
class TestResult:
    """Single test result."""

    name: str
    status: Literal["pass", "fail", "skip", "error"]
    duration_ms: float = 0
    message: str | None = None
    location: dict | None = None  # {file, line}


@dataclass
class Report:
    """Structured test/lint report."""

    kind: str  # test, lint, typecheck
    tool: str
    passed: bool
    total: int = 0
    passed_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    error_count: int = 0
    duration_ms: float = 0
    results: list[TestResult] = field(default_factory=list)
    raw_output: str = ""
    exit_code: int = 0


class TestTool(BaseTool):
    """Unified test/validation tool (HIP-0300).

    Handles all assurance operations:
    - run: Execute test/lint/typecheck
    - report: Format results

    Wraps proc.run with structured Report output.
    Effect: NONDETERMINISTIC_EFFECT
    """

    name: ClassVar[str] = "test"
    VERSION: ClassVar[str] = "0.1.0"

    def __init__(self, cwd: str | None = None):
        super().__init__()
        self.cwd = cwd or os.getcwd()
        self._register_test_actions()

    @property
    def description(self) -> str:
        return """Unified validation tool (HIP-0300).

Three feedback loops:
- check: Fast, incremental (lint/typecheck) → Diagnostics
- build: Whole-project compilation → BuildResult
- test: Runtime behavior validation → TestResult

Actions:
- run: Execute check/build/test with structured Report output
- detect: Auto-detect available tools for each loop

Compositions:
- Check loop: check → fix → apply → check
- Build loop: build → locate(errors) → patch → build
- Test loop: test → locate(failure) → patch → test

Effect: NONDETERMINISTIC_EFFECT
"""

    def _detect_runner(self, cwd: str, kind: str) -> tuple[str, list[str]] | None:
        """Auto-detect appropriate runner for the loop type.

        Args:
            cwd: Working directory
            kind: check | build | test
        """
        if kind == "test":
            tools = TEST_RUNNERS
        elif kind == "build":
            tools = BUILD_TOOLS
        else:  # check (lint/typecheck)
            tools = CHECK_TOOLS

        for name, config in tools.items():
            for detect_file in config["detect"]:
                if "*" in detect_file:
                    # Glob pattern
                    if list(Path(cwd).glob(detect_file)):
                        return name, config["cmd"]
                else:
                    if (Path(cwd) / detect_file).exists():
                        return name, config["cmd"]

        return None

    def _parse_pytest_output(self, output: str, exit_code: int) -> Report:
        """Parse pytest output."""
        results = []
        total = passed = failed = skipped = errors = 0

        # Parse summary line
        _summary_match = re.search(
            r"(\d+) passed.*?(\d+) failed.*?(\d+) error|"
            r"(\d+) passed.*?(\d+) skipped|"
            r"(\d+) passed",
            output,
        )

        # Parse individual test results
        for match in re.finditer(
            r"(PASSED|FAILED|SKIPPED|ERROR)\s+(\S+)::",
            output,
        ):
            status_map = {
                "PASSED": "pass",
                "FAILED": "fail",
                "SKIPPED": "skip",
                "ERROR": "error",
            }
            status = status_map.get(match.group(1), "error")
            name = match.group(2)

            results.append(TestResult(name=name, status=status))

            total += 1
            if status == "pass":
                passed += 1
            elif status == "fail":
                failed += 1
            elif status == "skip":
                skipped += 1
            else:
                errors += 1

        return Report(
            kind="test",
            tool="pytest",
            passed=exit_code == 0,
            total=total,
            passed_count=passed,
            failed_count=failed,
            skipped_count=skipped,
            error_count=errors,
            results=results,
            raw_output=output,
            exit_code=exit_code,
        )

    def _parse_generic_output(
        self, output: str, exit_code: int, kind: str, tool: str
    ) -> Report:
        """Generic output parser."""
        # Try JSON parsing first
        try:
            data = json.loads(output)
            # Handle various JSON formats
            if isinstance(data, dict):
                if "testResults" in data:  # Jest
                    results = []
                    for suite in data.get("testResults", []):
                        for test in suite.get("assertionResults", []):
                            results.append(
                                TestResult(
                                    name=test.get("fullName", ""),
                                    status=(
                                        "pass"
                                        if test.get("status") == "passed"
                                        else "fail"
                                    ),
                                )
                            )
                    return Report(
                        kind=kind,
                        tool=tool,
                        passed=data.get("success", exit_code == 0),
                        total=len(results),
                        passed_count=sum(1 for r in results if r.status == "pass"),
                        failed_count=sum(1 for r in results if r.status == "fail"),
                        results=results,
                        raw_output=output,
                        exit_code=exit_code,
                    )
        except json.JSONDecodeError:
            pass

        # Fallback: line-based parsing
        lines = output.strip().split("\n")
        error_lines = [
            line for line in lines if "error" in line.lower() or "fail" in line.lower()
        ]

        return Report(
            kind=kind,
            tool=tool,
            passed=exit_code == 0 and len(error_lines) == 0,
            total=len(lines),
            failed_count=len(error_lines),
            raw_output=output,
            exit_code=exit_code,
        )

    def _register_test_actions(self):
        """Register all test actions."""

        @self.action("run", "Execute check/build/test loop")
        async def run(
            ctx: MCPContext,
            kind: str = "test",
            selector: str | None = None,
            cwd: str | None = None,
            tool: str | None = None,
            timeout: int = 300,
        ) -> dict:
            """Run validation loop and return structured Report.

            Args:
                kind: check | build | test
                    - check: Fast incremental (lint/typecheck) → Diagnostics
                    - build: Whole-project compilation → BuildResult
                    - test: Runtime behavior validation → TestResult
                selector: File/target selector (e.g., "test_foo.py", "src/")
                cwd: Working directory
                tool: Specific tool to use (auto-detect if not specified)
                timeout: Timeout in seconds

            Returns:
                Report with pass/fail, counts, results

            Effect: NONDETERMINISTIC_EFFECT
            """
            work_dir = cwd or self.cwd

            # Detect or use specified tool
            if tool:
                if kind == "test":
                    tools = TEST_RUNNERS
                elif kind == "build":
                    tools = BUILD_TOOLS
                else:
                    tools = CHECK_TOOLS
                if tool not in tools:
                    raise InvalidParamsError(f"Unknown tool: {tool}")
                cmd = tools[tool]["cmd"].copy()
                tool_name = tool
            else:
                detected = self._detect_runner(work_dir, kind)
                if not detected:
                    raise ToolError(
                        code="NOT_FOUND",
                        message=f"No {kind} runner detected in {work_dir}",
                    )
                tool_name, cmd = detected
                cmd = cmd.copy()

            # Add selector if provided
            if selector:
                cmd.append(selector)

            # Run command
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=work_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout,
                )

                output = stdout.decode("utf-8", errors="replace")
                if stderr:
                    output += "\n" + stderr.decode("utf-8", errors="replace")

                exit_code = proc.returncode or 0

            except asyncio.TimeoutError:
                raise ToolError(
                    code="TIMEOUT", message=f"{kind} timed out after {timeout}s"
                )
            except FileNotFoundError as e:
                raise ToolError(code="NOT_FOUND", message=f"Tool not found: {e}")

            # Parse output
            if tool_name == "pytest":
                report = self._parse_pytest_output(output, exit_code)
            else:
                report = self._parse_generic_output(output, exit_code, kind, tool_name)

            return {
                "report": {
                    "kind": report.kind,
                    "tool": report.tool,
                    "passed": report.passed,
                    "total": report.total,
                    "passed_count": report.passed_count,
                    "failed_count": report.failed_count,
                    "skipped_count": report.skipped_count,
                    "error_count": report.error_count,
                    "duration_ms": report.duration_ms,
                    "results": [
                        {
                            "name": r.name,
                            "status": r.status,
                            "message": r.message,
                        }
                        for r in report.results[:50]  # Limit results
                    ],
                },
                "pass": report.passed,
                "exit_code": exit_code,
                "raw_ref": content_hash(output),  # Reference to full output
            }

        @self.action("detect", "Detect available test/lint tools")
        async def detect(
            ctx: MCPContext,
            cwd: str | None = None,
        ) -> dict:
            """Detect available test runners and lint tools.

            Returns:
                Dict of detected tools by category
            """
            work_dir = cwd or self.cwd
            detected = {
                "check": [],  # Fast incremental (lint/typecheck)
                "build": [],  # Whole-project compilation
                "test": [],  # Runtime behavior validation
            }

            # Detect test runners
            for name, config in TEST_RUNNERS.items():
                for detect_file in config["detect"]:
                    if "*" in detect_file:
                        if list(Path(work_dir).glob(detect_file)):
                            detected["test"].append(name)
                            break
                    else:
                        if (Path(work_dir) / detect_file).exists():
                            detected["test"].append(name)
                            break

            # Detect build tools
            for name, config in BUILD_TOOLS.items():
                for detect_file in config["detect"]:
                    if (Path(work_dir) / detect_file).exists():
                        detected["build"].append(name)
                        break

            # Detect check tools (lint/typecheck)
            for name, config in CHECK_TOOLS.items():
                for detect_file in config["detect"]:
                    if (Path(work_dir) / detect_file).exists():
                        detected["check"].append(name)
                        break

            return {
                "detected": detected,
                "cwd": work_dir,
            }

    def register(self, mcp_server: FastMCP) -> None:
        """Register as 'test' tool with MCP server."""
        tool_name = self.name
        tool_description = self.description

        @mcp_server.tool(name=tool_name, description=tool_description)
        async def handler(
            ctx: MCPContext,
            action: str = "help",
            **kwargs: Any,
        ) -> str:
            result = await self.call(ctx, action=action, **kwargs)
            return json.dumps(result, indent=2, default=str)


# Singleton
test_tool = TestTool
