"""Test to ensure no stub/fake/incomplete code exists in production."""

import os
import re
import ast
from typing import List, Tuple
from pathlib import Path

import pytest


class StubDetector(ast.NodeVisitor):
    """AST visitor to detect stub implementations."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.issues: List[Tuple[int, str]] = []
        self.in_test_file = "test" in filepath or "mock" in filepath.lower()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check function definitions for stub patterns."""
        # Skip test files for certain checks
        if self.in_test_file and node.name.startswith("test_"):
            self.generic_visit(node)
            return

        # Check for empty functions with just pass
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            # Check if there's a comment indicating it's a stub
            if node.body[0].lineno:
                self.issues.append((node.lineno, f"Function '{node.name}' contains only 'pass' statement"))

        # Check for functions that just raise NotImplementedError
        if len(node.body) == 1 and isinstance(node.body[0], ast.Raise):
            if isinstance(node.body[0].exc, ast.Call):
                if hasattr(node.body[0].exc.func, "id") and node.body[0].exc.func.id == "NotImplementedError":
                    self.issues.append((node.lineno, f"Function '{node.name}' raises NotImplementedError"))

        # Check for functions with only ellipsis
        if len(node.body) == 1 and isinstance(node.body[0], ast.Expr):
            if isinstance(node.body[0].value, ast.Constant):
                if node.body[0].value.value is Ellipsis:
                    self.issues.append((node.lineno, f"Function '{node.name}' contains only ellipsis"))

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Check async function definitions."""
        # Treat async functions same as regular functions
        self.visit_FunctionDef(node)


def find_stub_patterns(filepath: Path) -> List[Tuple[int, str, str]]:
    """Find stub patterns in a Python file."""
    issues = []

    # Skip test files for most checks
    is_test_file = "test" in filepath.name or "mock" in filepath.name.lower()

    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return issues

    # Regex patterns to find stub indicators
    patterns = [
        (r"#\s*(TODO|FIXME|STUB|FAKE|UNFINISHED|HACK|XXX)\s*:?", "contains {0} comment"),
        (r"raise\s+NotImplementedError", "raises NotImplementedError"),
        (r'assert\s+False,?\s*["\']Not implemented', 'has "Not implemented" assertion'),
    ]

    # Additional patterns for non-test files
    if not is_test_file:
        patterns.extend(
            [
                (r"pass\s*#\s*(stub|todo|fake)", "has stub/todo/fake comment after pass"),
                (r'return\s+["\']TODO', "returns TODO string"),
                (r'return\s+["\']STUB', "returns STUB string"),
                (r"return\s+None\s*#\s*(TODO|STUB|FAKE)", "returns None with stub comment"),
            ]
        )

    lines = content.split("\n")
    for line_num, line in enumerate(lines, 1):
        for pattern, message in patterns:
            if match := re.search(pattern, line, re.IGNORECASE):
                keyword = match.group(1) if match.groups() else "stub pattern"
                issues.append((line_num, message.format(keyword), filepath.name))

    # Parse AST for deeper inspection
    try:
        tree = ast.parse(content)
        detector = StubDetector(str(filepath))
        detector.visit(tree)
        for line_num, message in detector.issues:
            issues.append((line_num, message, filepath.name))
    except SyntaxError:
        pass  # Ignore files with syntax errors

    return issues


def get_python_files(root_dir: Path, exclude_dirs: set = None) -> List[Path]:
    """Get all Python files in directory, excluding certain directories."""
    if exclude_dirs is None:
        exclude_dirs = {
            "__pycache__",
            ".git",
            ".tox",
            ".pytest_cache",
            "build",
            "dist",
            "*.egg-info",
            ".venv",
            "venv",
            "node_modules",
            ".mypy_cache",
        }

    python_files = []
    for path in root_dir.rglob("*.py"):
        # Skip excluded directories
        if any(excluded in path.parts for excluded in exclude_dirs):
            continue
        python_files.append(path)

    return python_files


class TestNoStubs:
    """Test suite to ensure no stub implementations exist."""

    def test_no_stub_functions_in_source(self):
        """Ensure no stub functions exist in source code."""
        # Get the package root
        package_root = Path(__file__).parent.parent / "hanzo_mcp"

        if not package_root.exists():
            pytest.skip(f"Package root {package_root} does not exist")

        all_issues = []
        python_files = get_python_files(package_root)

        for filepath in python_files:
            issues = find_stub_patterns(filepath)
            for line_num, message, filename in issues:
                all_issues.append(f"{filepath.relative_to(package_root.parent)}:{line_num} - {message}")

        if all_issues:
            report = "\n".join(all_issues)
            pytest.fail(f"Found {len(all_issues)} stub/incomplete implementations:\n{report}")

    def test_critical_functions_implemented(self):
        """Ensure critical functions are actually implemented."""
        package_root = Path(__file__).parent.parent / "hanzo_mcp"

        # Critical modules and functions that must be implemented
        critical_checks = [
            ("tools/__init__.py", "register_all_tools"),
            ("server.py", "__init__"),
            ("server.py", "run"),
            ("cli.py", "main"),
        ]

        for module_path, function_name in critical_checks:
            filepath = package_root / module_path
            if not filepath.exists():
                pytest.fail(f"Critical module {module_path} does not exist")

            content = filepath.read_text()
            # Check function exists and has more than just pass/raise
            pattern = rf'def {function_name}\([^)]*\):[^:]*\n(?:\s+"""[^"]*"""\n)?(\s+.+)'
            match = re.search(pattern, content, re.MULTILINE)

            if not match:
                pytest.fail(f"Function {function_name} not found in {module_path}")

            function_body = match.group(1).strip()
            if function_body in ["pass", "raise NotImplementedError", "raise NotImplementedError()", "..."]:
                pytest.fail(f"Function {function_name} in {module_path} is not implemented")

    def test_no_pytest_skip_in_non_test_files(self):
        """Ensure pytest.skip is only used in test files."""
        package_root = Path(__file__).parent.parent / "hanzo_mcp"

        for filepath in get_python_files(package_root):
            # Skip test directories
            if "test" in str(filepath):
                continue

            content = filepath.read_text()
            if "pytest.skip" in content or "@pytest.mark.skip" in content:
                pytest.fail(f"Found pytest.skip in non-test file: {filepath}")

    def test_no_mock_implementations_in_production(self):
        """Ensure no mock implementations exist in production code."""
        package_root = Path(__file__).parent.parent / "hanzo_mcp"

        for filepath in get_python_files(package_root):
            # Skip test directories and legitimate mock modules
            if "test" in str(filepath) or "mock" in filepath.name:
                continue

            content = filepath.read_text()

            # Check for mock-related imports in production code
            mock_patterns = [
                r"from unittest\.mock import",
                r"import unittest\.mock",
                r"class Mock",
                r"class Fake",
                r"def fake_",
                r"def mock_",
                r'return\s+["\']fake',
                r'return\s+["\']mock',
            ]

            for pattern in mock_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    pytest.fail(f"Found mock/fake pattern '{pattern}' in production file: {filepath}")

    def test_all_tool_classes_have_run_method(self):
        """Ensure all tool classes have a proper run method."""
        package_root = Path(__file__).parent.parent / "hanzo_mcp" / "tools"

        if not package_root.exists():
            pytest.skip("Tools directory does not exist")

        for filepath in get_python_files(package_root):
            if "test" in str(filepath) or "__pycache__" in str(filepath):
                continue

            content = filepath.read_text()

            # Find all class definitions that inherit from BaseTool or end with Tool
            class_pattern = r"class\s+(\w*Tool\w*)\s*\([^)]*\):"
            classes = re.findall(class_pattern, content)

            for class_name in classes:
                # Check if class has a run method
                run_pattern = rf"class\s+{class_name}.*?def\s+run\s*\([^)]*\):"
                if not re.search(run_pattern, content, re.DOTALL):
                    # Check if it's an abstract base class
                    if "Base" not in class_name and "Abstract" not in class_name:
                        pytest.fail(f"Tool class {class_name} in {filepath.name} missing run() method")

    def test_no_debug_prints_in_production(self):
        """Ensure no debug print statements in production code."""
        package_root = Path(__file__).parent.parent / "hanzo_mcp"

        for filepath in get_python_files(package_root):
            # Skip test files
            if "test" in str(filepath):
                continue

            content = filepath.read_text()

            # Check for debug patterns
            debug_patterns = [
                (r"print\s*\([^)]*#\s*DEBUG", "debug print statement"),
                (r"print\s*\([^)]*#\s*TODO", "TODO print statement"),
                (r"print\s*\([^)]*#\s*REMOVE", "REMOVE print statement"),
                (r"console\.log", "console.log statement"),
                (r"debugger;?", "debugger statement"),
            ]

            for pattern, description in debug_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    pytest.fail(f"Found {description} in production file: {filepath}")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
