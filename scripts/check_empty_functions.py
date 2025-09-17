#!/usr/bin/env python3
"""Check for empty/stub functions in the codebase."""

import ast
import sys
from pathlib import Path


def check_file(filepath: Path) -> list:
    """Check a Python file for empty functions."""
    issues = []

    try:
        content = filepath.read_text()
        tree = ast.parse(content)
    except:
        return issues

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Skip test functions
            if node.name.startswith('test_'):
                continue

            # Check for empty body
            if len(node.body) == 1:
                stmt = node.body[0]

                # Check for pass
                if isinstance(stmt, ast.Pass):
                    issues.append(f"{filepath}:{node.lineno} - Function '{node.name}' only contains 'pass'")

                # Check for ellipsis
                elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                    if stmt.value.value is Ellipsis:
                        issues.append(f"{filepath}:{node.lineno} - Function '{node.name}' only contains '...'")

                # Check for NotImplementedError
                elif isinstance(stmt, ast.Raise):
                    if hasattr(stmt, 'exc') and isinstance(stmt.exc, ast.Call):
                        if hasattr(stmt.exc.func, 'id') and stmt.exc.func.id == 'NotImplementedError':
                            issues.append(f"{filepath}:{node.lineno} - Function '{node.name}' raises NotImplementedError")

    return issues


def main():
    """Main function."""
    pkg_dir = Path('pkg/hanzo-mcp')
    if not pkg_dir.exists():
        pkg_dir = Path('.')

    all_issues = []

    # Check all Python files
    for pyfile in pkg_dir.rglob('*.py'):
        # Skip test files
        if 'test' in str(pyfile) or '__pycache__' in str(pyfile):
            continue

        issues = check_file(pyfile)
        all_issues.extend(issues)

    if all_issues:
        print("❌ EMPTY/STUB FUNCTIONS FOUND:")
        for issue in all_issues:
            print(f"  {issue}")
        print(f"\n🚫 Found {len(all_issues)} empty/stub functions. Implement them!")
        sys.exit(1)

    print("✅ No empty/stub functions found")
    sys.exit(0)


if __name__ == '__main__':
    main()