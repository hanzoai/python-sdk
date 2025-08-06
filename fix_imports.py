#!/usr/bin/env python3
"""Fix all remaining hanzo_cli imports to use relative imports."""

import os
import re
from pathlib import Path

def fix_imports_in_file(filepath):
    """Fix imports in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Replace hanzo_cli imports with relative imports
    replacements = [
        (r'from hanzo_cli\.utils\.output import', 'from ..utils.output import'),
        (r'from hanzo_cli\.utils\.config import', 'from ..utils.config import'),
        (r'from hanzo_cli\.utils import', 'from ..utils import'),
        (r'from hanzo_cli\.interactive\.dashboard import', 'from .interactive.dashboard import'),
        (r'from hanzo_cli\.interactive\.repl import', 'from .interactive.repl import'),
        (r'from hanzo_cli\.interactive import', 'from ..interactive import'),
        (r'from hanzo_cli\.cli import', 'from .cli import'),
        (r'from hanzo_cli import cli', 'from .. import cli'),
        (r'import hanzo_cli', 'from .. import cli as hanzo_cli'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    base_path = Path("/Users/z/work/hanzo/python-sdk/pkg/hanzo/src/hanzo")
    
    # Find all Python files
    python_files = list(base_path.rglob("*.py"))
    
    print(f"Found {len(python_files)} Python files to check")
    
    fixed_count = 0
    for filepath in python_files:
        if fix_imports_in_file(filepath):
            fixed_count += 1
            print(f"Fixed imports in: {filepath.relative_to(base_path.parent.parent)}")
    
    print(f"\nFixed {fixed_count} files")

if __name__ == "__main__":
    main()