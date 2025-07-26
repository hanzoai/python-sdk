#!/usr/bin/env python3
"""Simple demonstration of Claude Code parallel editing.

This shows the core concept without full MCP infrastructure.
"""

import os
import tempfile
import shutil


def create_test_files():
    """Create test files for demonstration."""
    test_dir = tempfile.mkdtemp(prefix="claude_edit_")
    
    files = {
        "config.py": """# Configuration
OLD_API_KEY = "sk-old-123"
OLD_DB_URL = "postgres://old"
OLD_TIMEOUT = 30
""",
        "utils.py": """# Utils
from config import OLD_API_KEY, OLD_DB_URL

def connect():
    print(f"Using {OLD_API_KEY}")
    print(f"Connecting to {OLD_DB_URL}")
""",
        "main.py": """# Main
from config import OLD_API_KEY, OLD_TIMEOUT
from utils import connect

def main():
    print(f"API: {OLD_API_KEY}")
    print(f"Timeout: {OLD_TIMEOUT}")
    connect()

if __name__ == "__main__":
    main()
"""
    }
    
    for name, content in files.items():
        path = os.path.join(test_dir, name)
        with open(path, 'w') as f:
            f.write(content)
    
    return test_dir, files


def show_files(test_dir, files, title):
    """Display file contents."""
    print(f"\n{title}")
    print("="*60)
    for name in files:
        path = os.path.join(test_dir, name)
        print(f"\n--- {name} ---")
        with open(path, 'r') as f:
            print(f.read())


def simulate_parallel_edits(test_dir, files):
    """Simulate what parallel Claude agents would do."""
    print("\n🤖 SIMULATING PARALLEL CLAUDE CODE EDITS")
    print("="*60)
    
    # Agent 1: Edit config.py
    print("\n✅ Agent 1 (Claude Sonnet): Editing config.py...")
    config_path = os.path.join(test_dir, "config.py")
    with open(config_path, 'r') as f:
        content = f.read()
    content = content.replace("OLD_", "NEW_")
    content = content.replace("sk-old-123", "sk-new-456")
    content = content.replace("postgres://old", "postgres://new")
    with open(config_path, 'w') as f:
        f.write(content)
    print("   - Renamed all OLD_ variables to NEW_")
    print("   - Updated values")
    
    # Agent 2: Edit utils.py
    print("\n✅ Agent 2 (Claude Sonnet): Editing utils.py...")
    utils_path = os.path.join(test_dir, "utils.py")
    with open(utils_path, 'r') as f:
        content = f.read()
    content = content.replace("OLD_", "NEW_")
    with open(utils_path, 'w') as f:
        f.write(content)
    print("   - Updated imports to use NEW_ prefix")
    print("   - Updated variable references")
    
    # Agent 3: Edit main.py
    print("\n✅ Agent 3 (Claude Sonnet): Editing main.py...")
    main_path = os.path.join(test_dir, "main.py")
    with open(main_path, 'r') as f:
        content = f.read()
    content = content.replace("OLD_", "NEW_")
    with open(main_path, 'w') as f:
        f.write(content)
    print("   - Updated imports to use NEW_ prefix")
    print("   - Updated variable references")
    
    print("\n✨ All agents completed successfully!")


def main():
    """Run the demonstration."""
    print("CLAUDE CODE PARALLEL EDITING DEMO")
    print("="*60)
    print("This demonstrates how the swarm tool works:")
    print("- Defaults to Claude 3.5 Sonnet")
    print("- Runs multiple agents in parallel")
    print("- Each agent edits a different file")
    print("="*60)
    
    # Check for API key
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY"))
    if has_key:
        print("\n✅ Claude API key detected!")
        print("   In real usage, actual Claude agents would edit the files.")
    else:
        print("\n⚠️  No Claude API key found.")
        print("   Set ANTHROPIC_API_KEY or CLAUDE_API_KEY for real agents.")
    
    # Create test files
    test_dir, files = create_test_files()
    print(f"\nCreated test project at: {test_dir}")
    
    try:
        # Show original files
        show_files(test_dir, files, "ORIGINAL FILES")
        
        # Simulate parallel edits
        simulate_parallel_edits(test_dir, files)
        
        # Show edited files
        show_files(test_dir, files, "EDITED FILES (after parallel Claude edits)")
        
        # Verify changes
        print("\n✅ VERIFICATION")
        print("="*60)
        all_good = True
        for name in files:
            path = os.path.join(test_dir, name)
            with open(path, 'r') as f:
                content = f.read()
            if "OLD_" in content:
                print(f"❌ {name}: Still contains OLD_ variables")
                all_good = False
            else:
                print(f"✅ {name}: Successfully updated to NEW_ variables")
        
        if all_good:
            print("\n🎉 All files successfully edited in parallel!")
        
        # Show the swarm tool configuration
        print("\n📋 SWARM TOOL CONFIGURATION")
        print("="*60)
        print("Default model: anthropic/claude-3-5-sonnet-20241022")
        print("Max concurrent: 10 (default)")
        print("Each agent has full editing capabilities")
        print("Automatic pagination for large responses")
        
    finally:
        # Cleanup
        shutil.rmtree(test_dir)
        print(f"\n✨ Cleaned up: {test_dir}")


if __name__ == "__main__":
    main()