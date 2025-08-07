#!/usr/bin/env python3
"""Fix all imports in hanzo_network package to use relative imports."""

import os
import re
from pathlib import Path

def fix_imports_in_file(filepath):
    """Fix imports in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Replace absolute imports with relative imports
    # For files in the main hanzo_network directory
    if '/hanzo_network/' in str(filepath) and not '/hanzo_network/core/' in str(filepath):
        content = re.sub(r'from hanzo_network\.', 'from .', content)
        content = re.sub(r'import hanzo_network\.', 'from . import ', content)
    
    # For files in subdirectories like core/
    if '/hanzo_network/core/' in str(filepath):
        # Replace imports from hanzo_network.core with relative
        content = re.sub(r'from hanzo_network\.core\.', 'from .', content)
        # Replace imports from hanzo_network. with parent relative
        content = re.sub(r'from hanzo_network\.', 'from ..', content)
        
    # For files in other subdirectories
    for subdir in ['distributed', 'inference', 'llm', 'download', 'topology', 'tools']:
        if f'/hanzo_network/{subdir}/' in str(filepath):
            content = re.sub(r'from hanzo_network\.' + subdir + r'\.', 'from .', content)
            content = re.sub(r'from hanzo_network\.', 'from ..', content)
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    base_path = Path("/Users/z/work/hanzo/python-sdk/pkg/hanzo-network/src/hanzo_network")
    
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