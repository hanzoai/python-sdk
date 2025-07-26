#!/usr/bin/env python3
"""Simple demonstration of parallel editing with Claude Code agents.

This example shows how to use the swarm tool to edit variables across
multiple files in parallel using Claude 3.5 Sonnet.
"""

import asyncio
import os
import tempfile
import shutil
from pathlib import Path

from mcp.server.fastmcp import Context as MCPContext
from hanzo_mcp.tools.common.permissions import PermissionManager
from hanzo_mcp.tools.agent.swarm_tool import SwarmTool


async def main():
    """Run parallel editing demonstration."""
    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("CLAUDE_API_KEY"):
        print("Error: No Claude API key found!")
        print("Set ANTHROPIC_API_KEY or CLAUDE_API_KEY environment variable")
        return
    
    # Create temporary project directory
    test_dir = tempfile.mkdtemp(prefix="parallel_edit_demo_")
    print(f"Created test project at: {test_dir}")
    
    try:
        # Create 3 files with old variable names
        files = {
            "constants.py": '''# Application constants
OLD_VERSION = "1.0.0"
OLD_APP_NAME = "Legacy App"
OLD_MAX_USERS = 100
OLD_TIMEOUT = 30

def get_version():
    return OLD_VERSION
''',
            "utils.py": '''# Utility functions
from constants import OLD_VERSION, OLD_APP_NAME

def print_header():
    print(f"{OLD_APP_NAME} v{OLD_VERSION}")
    print("=" * 40)

def validate_app_name(name):
    return name == OLD_APP_NAME
''',
            "main.py": '''# Main application
from constants import OLD_VERSION, OLD_APP_NAME, OLD_MAX_USERS, OLD_TIMEOUT
from utils import print_header

def main():
    print_header()
    print(f"Max users: {OLD_MAX_USERS}")
    print(f"Timeout: {OLD_TIMEOUT}s")
    print(f"Running {OLD_APP_NAME} version {OLD_VERSION}")

if __name__ == "__main__":
    main()
'''
        }
        
        # Write files
        for filename, content in files.items():
            filepath = os.path.join(test_dir, filename)
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"Created: {filename}")
        
        # Set up permissions
        pm = PermissionManager()
        # Add to allowed paths using the public method
        pm.add_allowed_path(test_dir)
        
        # Create swarm tool (defaults to Claude Sonnet)
        swarm = SwarmTool(permission_manager=pm)
        
        # Create MCP context
        ctx = MCPContext()
        
        # Define parallel editing tasks
        tasks = [
            {
                "file_path": os.path.join(test_dir, "constants.py"),
                "instructions": "Change all variable names from OLD_ prefix to NEW_ prefix. Keep the same values.",
                "description": "Update constants.py variables"
            },
            {
                "file_path": os.path.join(test_dir, "utils.py"),
                "instructions": "Update imports and all references to use NEW_ prefix instead of OLD_",
                "description": "Update utils.py imports"
            },
            {
                "file_path": os.path.join(test_dir, "main.py"),
                "instructions": "Update imports and all references to use NEW_ prefix instead of OLD_",
                "description": "Update main.py imports"
            }
        ]
        
        print("\n" + "="*60)
        print("Starting parallel editing with 3 Claude agents...")
        print("="*60 + "\n")
        
        # Execute parallel edits
        result = await swarm.call(
            ctx,
            tasks=tasks,
            common_instructions="Ensure all Python code remains valid. Only change the variable names.",
            max_concurrent=3
        )
        
        print("\n" + "="*60)
        print("SWARM EXECUTION RESULT:")
        print("="*60)
        print(result)
        
        # Show the edited files
        print("\n" + "="*60)
        print("EDITED FILES:")
        print("="*60)
        
        for filename in files.keys():
            filepath = os.path.join(test_dir, filename)
            print(f"\n--- {filename} ---")
            with open(filepath, 'r') as f:
                print(f.read())
    
    finally:
        # Cleanup
        shutil.rmtree(test_dir)
        print(f"\nCleaned up test directory: {test_dir}")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())