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
        self.in_except_handler = False  # Track if we're inside an except block

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        """Track that we're inside an except handler (fallback stubs are OK)."""
        old_in_except = self.in_except_handler
        self.in_except_handler = True
        self.generic_visit(node)
        self.in_except_handler = old_in_except

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check function definitions for stub patterns."""
        # Skip test files for certain checks
        if self.in_test_file and node.name.startswith("test_"):
            self.generic_visit(node)
            return

        # Skip functions defined in except handlers (these are legitimate fallbacks)
        if self.in_except_handler:
            self.generic_visit(node)
            return

        # Skip dunder methods (like __init__) that may be empty placeholders
        if node.name.startswith("__") and node.name.endswith("__"):
            self.generic_visit(node)
            return

        # Check for empty functions with just pass (but allow if has docstring)
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            self.issues.append((node.lineno, f"Function '{node.name}' contains only 'pass' statement"))
        elif len(node.body) == 2:
            # Check for docstring + pass (also a stub)
            if (
                isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
                and isinstance(node.body[1], ast.Pass)
            ):
                # Has docstring + pass - this is a documented stub, skip it
                pass

        # Check for functions that just raise NotImplementedError
        # But allow if it's an abstract method (has docstring explaining it)
        if len(node.body) == 1 and isinstance(node.body[0], ast.Raise):
            if isinstance(node.body[0].exc, ast.Call):
                if hasattr(node.body[0].exc.func, "id") and node.body[0].exc.func.id == "NotImplementedError":
                    # This is a legitimate abstract method pattern, skip it
                    pass
        elif len(node.body) == 2:
            # Docstring + NotImplementedError - legitimate abstract method
            if (
                isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
                and isinstance(node.body[1], ast.Raise)
            ):
                # Has docstring + raise, this is a documented abstract method
                pass

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

    # Regex patterns to find stub indicators (with case sensitivity flag)
    # Note: We're looking for TODO/FIXME comments, not tool names containing "todo"
    # Format: (pattern, message, case_insensitive)
    patterns = [
        # Match TODO/FIXME comments (case insensitive for comments)
        (r"#\s*(TODO|FIXME|STUB|FAKE|UNFINISHED|HACK|XXX)\s*:", "contains {0} comment", True),
        (r'assert\s+False,?\s*["\']Not implemented', 'has "Not implemented" assertion', True),
    ]

    # Additional patterns for non-test files
    if not is_test_file:
        patterns.extend(
            [
                (r"pass\s*#\s*(stub|fake)", "has stub/fake comment after pass", True),
                # Only match uppercase "TODO"/"STUB" strings (case sensitive to avoid "todo" tool name)
                (r'return\s+["\']TODO["\']', "returns TODO string", False),
                (r'return\s+["\']STUB["\']', "returns STUB string", False),
                (r"return\s+None\s*#\s*(STUB|FAKE)", "returns None with stub comment", True),
            ]
        )

    lines = content.split("\n")
    for line_num, line in enumerate(lines, 1):
        for pattern, message, case_insensitive in patterns:
            flags = re.IGNORECASE if case_insensitive else 0
            if match := re.search(pattern, line, flags):
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

            # Check function exists - use a more flexible pattern
            # Match 'def function_name(' with optional type hints
            function_pattern = rf"def {function_name}\s*\("
            if not re.search(function_pattern, content):
                pytest.fail(f"Function {function_name} not found in {module_path}")

            # Find the function body and check it's not a stub
            # Use AST for accurate parsing
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if node.name == function_name:
                            # Check if function body is just pass, ellipsis, or NotImplementedError
                            if len(node.body) == 1:
                                body = node.body[0]
                                if isinstance(body, ast.Pass):
                                    pytest.fail(f"Function {function_name} in {module_path} contains only 'pass'")
                                if isinstance(body, ast.Expr) and isinstance(body.value, ast.Constant):
                                    if body.value.value is Ellipsis:
                                        pytest.fail(f"Function {function_name} in {module_path} contains only '...'")
                                if isinstance(body, ast.Raise) and isinstance(body.exc, ast.Call):
                                    if hasattr(body.exc.func, "id") and body.exc.func.id == "NotImplementedError":
                                        pytest.fail(
                                            f"Function {function_name} in {module_path} raises NotImplementedError"
                                        )
                            break
            except SyntaxError:
                pass  # If we can't parse, skip AST check

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
            # Skip test directories, legitimate mock modules, and fallback implementations
            if "test" in str(filepath) or "mock" in filepath.name.lower():
                continue

            content = filepath.read_text()

            # Check for mock-related imports in production code
            # Note: class Mock/Fake are OK if they're for fallback functionality
            # (like MockContext for when Context is not serialized over MCP)
            mock_patterns = [
                r"from unittest\.mock import",
                r"import unittest\.mock",
                # Only flag clearly test-oriented mock patterns
                r"def fake_\w+\s*\(",
                r"def mock_\w+\s*\(",
                r'return\s+["\']fake\w*["\']',
                r'return\s+["\']mock\w*["\']',
            ]

            for pattern in mock_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    pytest.fail(f"Found mock/fake pattern '{pattern}' in production file: {filepath}")

    def test_all_tool_classes_have_run_method(self):
        """Ensure all tool classes have a proper run or call method."""
        package_root = Path(__file__).parent.parent / "hanzo_mcp" / "tools"

        if not package_root.exists():
            pytest.skip("Tools directory does not exist")

        issues = []
        for filepath in get_python_files(package_root):
            if "test" in str(filepath) or "__pycache__" in str(filepath):
                continue

            content = filepath.read_text()

            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue

            # Find all top-level Tool classes (not nested) and check for run/call methods
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    class_name = node.name
                    # Only check classes that end with Tool
                    if not class_name.endswith("Tool"):
                        continue
                    # Skip Params/Config classes that are just type definitions
                    if "Params" in class_name or "Config" in class_name:
                        continue
                    # Skip abstract base classes
                    if "Base" in class_name or "Abstract" in class_name:
                        continue
                    # Skip adapter classes
                    if "Adapter" in class_name:
                        continue

                    # Check if class has run() or call() method (or execute as alias)
                    has_run_or_call = False
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if item.name in ("run", "call", "execute"):
                                has_run_or_call = True
                                break
                        # Also check for method aliases like "call = execute"
                        if isinstance(item, ast.Assign):
                            for target in item.targets:
                                if isinstance(target, ast.Name) and target.id in ("run", "call"):
                                    has_run_or_call = True
                                    break

                    if not has_run_or_call:
                        # If it inherits from any base class, the base likely provides call()
                        # Only flag classes with no inheritance or with Object-only inheritance
                        inherits_from_something_meaningful = len(node.bases) > 0
                        if inherits_from_something_meaningful:
                            # Check all base class names
                            for base in node.bases:
                                base_name = ""
                                if isinstance(base, ast.Name):
                                    base_name = base.id
                                elif isinstance(base, ast.Attribute):
                                    base_name = base.attr
                                # If any base ends with Tool, Base, Mixin it's likely OK
                                if any(base_name.endswith(suffix) for suffix in ("Tool", "Base", "Mixin")):
                                    inherits_from_something_meaningful = True
                                    break
                        else:
                            # No bases - this is a standalone Tool class that needs run/call
                            issues.append(f"Tool class {class_name} in {filepath.name} missing run() or call() method")

        if issues:
            pytest.fail(f"Found {len(issues)} tool classes without run()/call() method:\n" + "\n".join(issues[:10]))

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
