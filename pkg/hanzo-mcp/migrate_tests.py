#!/usr/bin/env python3
"""Migrate existing tests to use DRY test utilities.

This script updates test files to use the new test_utils infrastructure.
"""

import re
from typing import List
from pathlib import Path

# Patterns to replace
REPLACEMENTS = [
    # Replace result assertions
    (r'assert "(.*?)" in result\b', r'tool_helper.assert_in_result("\1", result)'),
    (r'assert "(.*?)" in str\(result\)', r'tool_helper.assert_in_result("\1", result)'),
    # Replace common tool call patterns
    (
        r'result = await tool\.call\(\s*mock_ctx,\s*(.*?)\s*\)\s*if isinstance\(result, dict\) and "output" in result:\s*result = result\["output"\]',
        r"result = await tool_helper.call_tool(tool, mock_ctx, \1)",
    ),
    # Replace mock context creation
    (r"mock_ctx = Mock\(\)", r"mock_ctx = create_mock_ctx()"),
    # Replace permission manager creation
    (
        r"permission_manager = PermissionManager\(\)\s*permission_manager\.add_allowed_path\((.*?)\)",
        r"permission_manager = create_permission_manager([\1])",
    ),
    # Import test utilities
    (
        r"from unittest\.mock import (.*)",
        r"from unittest.mock import \1\nfrom tests.test_utils import ToolTestHelper, create_mock_ctx, create_permission_manager",
    ),
]


# Test files to migrate
def find_test_files(test_dir: Path) -> List[Path]:
    """Find all test files to migrate."""
    return list(test_dir.rglob("test_*.py"))


def migrate_file(file_path: Path, dry_run: bool = False) -> bool:
    """Migrate a single test file."""
    try:
        with open(file_path, "r") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False

    original_content = content
    modified = False

    # Apply replacements
    for pattern, replacement in REPLACEMENTS:
        new_content = re.sub(
            pattern, replacement, content, flags=re.MULTILINE | re.DOTALL
        )
        if new_content != content:
            content = new_content
            modified = True

    # Add tool_helper fixture if using it
    if "tool_helper" in content and "@pytest.fixture" not in content:
        # Find the first test method and add fixture
        content = re.sub(r"(def test_\w+\(self,)", r"\1 tool_helper,", content, count=1)
        modified = True

    # Ensure imports are at the top
    if "from tests.test_utils import" in content:
        lines = content.split("\n")
        import_lines = []
        other_lines = []

        for line in lines:
            if line.startswith("from tests.test_utils import"):
                import_lines.append(line)
            else:
                other_lines.append(line)

        # Move imports after other imports
        new_lines = []
        import_section_done = False
        for line in other_lines:
            new_lines.append(line)
            if (
                not import_section_done
                and line.startswith("import ")
                or line.startswith("from ")
            ):
                if not other_lines[other_lines.index(line) + 1].startswith(
                    ("import ", "from ")
                ):
                    new_lines.extend(import_lines)
                    import_section_done = True

        content = "\n".join(new_lines)
        modified = True

    if modified:
        if dry_run:
            print(f"Would update: {file_path}")
            print("Changes:")
            # Show diff
            import difflib

            diff = difflib.unified_diff(
                original_content.splitlines(keepends=True),
                content.splitlines(keepends=True),
                fromfile=str(file_path),
                tofile=str(file_path),
            )
            print(
                "".join(diff)[:1000] + "..."
                if len("".join(diff)) > 1000
                else "".join(diff)
            )
        else:
            with open(file_path, "w") as f:
                f.write(content)
            print(f"Updated: {file_path}")
        return True

    return False


def main():
    """Main migration function."""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate tests to use DRY utilities")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files",
    )
    parser.add_argument("--file", help="Migrate a specific file only")
    args = parser.parse_args()

    test_dir = Path("tests")

    if args.file:
        files = [Path(args.file)]
    else:
        files = find_test_files(test_dir)

    print(f"Found {len(files)} test files to check")

    updated = 0
    for file_path in files:
        if file_path.name == "test_utils.py" or file_path.name == "conftest.py":
            continue

        if migrate_file(file_path, dry_run=args.dry_run):
            updated += 1

    print(f"\n{'Would update' if args.dry_run else 'Updated'} {updated} files")

    if not args.dry_run and updated > 0:
        print("\nNext steps:")
        print("1. Run tests to ensure they still pass")
        print("2. Add type hints to test files")
        print("3. Run mypy to check types")
        print("4. Run coverage to ensure 96.3%+ coverage")


if __name__ == "__main__":
    main()
