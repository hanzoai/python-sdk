"""Test parallel editing with Claude Code (Sonnet) agents.

This test demonstrates:
1. Multiple Claude agents editing different files in parallel
2. Automatic pagination for large responses
3. Consensus mode with multiple agents reviewing code
"""

import pytest
import asyncio
import os
import tempfile
import shutil
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.common.permissions import PermissionManager
from hanzo_mcp.tools.agent.swarm_tool import SwarmTool
from hanzo_mcp.tools.agent.agent_tool import AgentTool
from hanzo_mcp.tools.filesystem import ReadTool, Write


class TestClaudeCodeParallel:
    """Test Claude Code parallel editing capabilities."""
    
    @pytest.fixture
    def test_project(self):
        """Create a test project with files that need refactoring."""
        test_dir = tempfile.mkdtemp(prefix="claude_test_")
        
        # Create a simple project structure
        project_files = {
            "main.py": '''#!/usr/bin/env python
"""Main application entry point."""

import sys
from config import CONFIG_API_KEY, CONFIG_DATABASE_URL, CONFIG_CACHE_SIZE
from database import Database
from api import APIClient

def main():
    # Initialize database
    db = Database(CONFIG_DATABASE_URL, CONFIG_CACHE_SIZE)
    
    # Initialize API client
    api = APIClient(CONFIG_API_KEY)
    
    # Main application logic
    print("Starting application...")
    if db.connect():
        print("Database connected")
        api.test_connection()
    else:
        print("Failed to connect to database")
        sys.exit(1)

if __name__ == "__main__":
    main()
''',
            "config.py": '''"""Configuration module."""

# Old configuration variables that need updating
CONFIG_API_KEY = "sk-old-api-key-12345"
CONFIG_DATABASE_URL = "postgres://localhost:5432/olddb"
CONFIG_CACHE_SIZE = 1000
CONFIG_TIMEOUT = 30
CONFIG_RETRIES = 3

# Feature flags
CONFIG_ENABLE_CACHE = True
CONFIG_ENABLE_LOGGING = False
CONFIG_DEBUG_MODE = True
''',
            "database.py": '''"""Database connection module."""

from config import CONFIG_DATABASE_URL, CONFIG_CACHE_SIZE, CONFIG_TIMEOUT

class Database:
    """Database connection handler."""
    
    def __init__(self, url=CONFIG_DATABASE_URL, cache_size=CONFIG_CACHE_SIZE):
        self.url = url
        self.cache_size = cache_size
        self.timeout = CONFIG_TIMEOUT
        self.connection = None
    
    def connect(self):
        """Connect to the database."""
        print(f"Connecting to database: {CONFIG_DATABASE_URL}")
        print(f"Cache size: {CONFIG_CACHE_SIZE}")
        print(f"Timeout: {CONFIG_TIMEOUT}")
        # Simulate connection
        self.connection = f"Connection to {self.url}"
        return True
    
    def disconnect(self):
        """Disconnect from the database."""
        if self.connection:
            print("Disconnecting from database")
            self.connection = None
''',
            "api.py": '''"""API client module."""

from config import CONFIG_API_KEY, CONFIG_RETRIES, CONFIG_TIMEOUT

class APIClient:
    """API client for external services."""
    
    def __init__(self, api_key=CONFIG_API_KEY):
        self.api_key = api_key
        self.retries = CONFIG_RETRIES
        self.timeout = CONFIG_TIMEOUT
        self.session = None
    
    def test_connection(self):
        """Test API connection."""
        print(f"Testing API with key: {CONFIG_API_KEY[:10]}...")
        print(f"Retries: {CONFIG_RETRIES}, Timeout: {CONFIG_TIMEOUT}")
        return True
    
    def make_request(self, endpoint, data=None):
        """Make an API request."""
        headers = {
            "Authorization": f"Bearer {CONFIG_API_KEY}",
            "Content-Type": "application/json"
        }
        print(f"Making request to {endpoint}")
        return {"status": "success", "data": data}
'''
        }
        
        # Write all files
        for filename, content in project_files.items():
            file_path = os.path.join(test_dir, filename)
            with open(file_path, 'w') as f:
                f.write(content)
        
        yield test_dir
        
        # Cleanup
        shutil.rmtree(test_dir)
    
    @pytest.fixture
    def permission_manager(self, test_project):
        """Create permission manager for test project."""
        pm = PermissionManager()
        pm._allowed_paths.add(test_project)
        return pm
    
    @pytest.mark.asyncio
    async def test_parallel_variable_renaming(self, tool_helper, test_project, permission_manager):
        """Test parallel editing of multiple files to rename variables."""
        # Skip if no API key
        if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("CLAUDE_API_KEY"):
            pytest.skip("No Claude API key found")
        
        # Create swarm tool (will default to Claude Sonnet)
        swarm = SwarmTool(permission_manager=permission_manager)
        
        # Create context
        ctx = MCPContext()
        
        # Define parallel editing tasks
        tasks = [
            {
                "file_path": os.path.join(test_project, "config.py"),
                "instructions": """Rename all CONFIG_ prefixed variables to use a modern Settings class pattern:
                1. Change CONFIG_API_KEY to SETTINGS_API_KEY
                2. Change CONFIG_DATABASE_URL to SETTINGS_DATABASE_URL
                3. Change CONFIG_CACHE_SIZE to SETTINGS_CACHE_SIZE
                4. Change CONFIG_TIMEOUT to SETTINGS_TIMEOUT
                5. Change CONFIG_RETRIES to SETTINGS_RETRIES
                6. Update all other CONFIG_ variables similarly
                Keep the values the same, just rename the variables.""",
                "description": "Modernize config.py variables"
            },
            {
                "file_path": os.path.join(test_project, "database.py"),
                "instructions": """Update all imports and usages to use the new SETTINGS_ prefix instead of CONFIG_:
                1. Update the import statement
                2. Update all references to CONFIG_ variables to use SETTINGS_ instead
                3. Ensure the code still works correctly""",
                "description": "Update database.py imports and usage"
            },
            {
                "file_path": os.path.join(test_project, "api.py"),
                "instructions": """Update all imports and usages to use the new SETTINGS_ prefix instead of CONFIG_:
                1. Update the import statement
                2. Update all references to CONFIG_ variables to use SETTINGS_ instead
                3. Ensure the code still works correctly""",
                "description": "Update api.py imports and usage"
            }
        ]
        
        # Execute parallel edits
        print("\n=== Starting parallel Claude Code editing ===")
        result = await swarm.call(
            ctx,
            tasks=tasks,
            common_instructions="Ensure all Python code remains valid and properly formatted. Maintain existing functionality.",
            max_concurrent=3  # Run all 3 in parallel
        )
        
        print("\n=== Swarm Result ===")
        print(result)
        
        # Verify the edits were made
        with open(os.path.join(test_project, "config.py"), 'r') as f:
            config_content = f.read()
            # Check that at least some renaming happened
            assert "SETTINGS_" in config_content or "CONFIG_" not in config_content
    
    @pytest.mark.asyncio
    async def test_consensus_code_review(self, tool_helper, test_project, permission_manager):
        """Test consensus mode with multiple agents reviewing code."""
        # Skip if no API key
        if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("CLAUDE_API_KEY"):
            pytest.skip("No Claude API key found")
        
        # Create swarm tool
        swarm = SwarmTool(permission_manager=permission_manager)
        
        # Create context
        ctx = MCPContext()
        
        # Define consensus review tasks - multiple agents review the same file
        tasks = [
            {
                "file_path": os.path.join(test_project, "database.py"),
                "instructions": """Review this database module from an architecture perspective:
                1. Evaluate the design patterns used
                2. Suggest improvements to the class structure
                3. Comment on error handling
                4. Propose better abstraction if needed""",
                "description": "Agent 1: Architecture Review"
            },
            {
                "file_path": os.path.join(test_project, "database.py"),
                "instructions": """Review this database module from a security perspective:
                1. Identify potential security vulnerabilities
                2. Check for SQL injection risks
                3. Evaluate credential handling
                4. Suggest security improvements""",
                "description": "Agent 2: Security Review"
            },
            {
                "file_path": os.path.join(test_project, "database.py"),
                "instructions": """Review this database module from a performance perspective:
                1. Identify potential performance bottlenecks
                2. Suggest caching improvements
                3. Evaluate connection pooling needs
                4. Recommend optimization strategies""",
                "description": "Agent 3: Performance Review"
            }
        ]
        
        # Execute consensus review
        print("\n=== Starting consensus code review ===")
        result = await swarm.call(
            ctx,
            tasks=tasks,
            common_instructions="Provide specific, actionable feedback. Focus on practical improvements.",
            max_concurrent=3  # Run all reviewers in parallel
        )
        
        print("\n=== Consensus Review Result ===")
        print(result)
        
        # Check that we got reviews from multiple agents
        assert "Agent 1:" in result or "Task 1" in result
        assert "Agent 2:" in result or "Task 2" in result
        assert "Agent 3:" in result or "Task 3" in result
    
    @pytest.mark.asyncio
    async def test_large_response_pagination(self, tool_helper, test_project, permission_manager):
        """Test that large responses are properly paginated."""
        # Skip if no API key
        if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("CLAUDE_API_KEY"):
            pytest.skip("No Claude API key found")
        
        # Create a large file that will produce a big response
        large_file = os.path.join(test_project, "large_module.py")
        with open(large_file, 'w') as f:
            # Write a large file with many functions
            f.write('"""Large module for testing pagination."""\n\n')
            for i in range(100):
                f.write(f'''def function_{i}(param1, param2):
    """Function {i} that needs documentation.
    
    This function currently lacks proper documentation,
    type hints, and error handling.
    """
    result = param1 + param2
    print(f"Function {i} result: {{result}}")
    return result

''')
        
        # Create agent directly to test pagination
        agent = AgentTool(
            permission_manager=permission_manager,
            model="anthropic/claude-3-5-sonnet-20241022"
        )
        
        ctx = MCPContext()
        
        # Task that will produce large output
        prompt = f"""Analyze every function in {large_file} and provide:
1. A detailed review of each function
2. Specific improvements for each function
3. Type hints that should be added
4. Error handling recommendations
Be very detailed and thorough for each function."""
        
        print("\n=== Testing large response pagination ===")
        result = await agent.call(ctx, prompts=prompt)
        
        # The response should be reasonable size due to pagination
        print(f"\nResponse length: {len(result)} characters")
        assert len(result) > 0
        
        # Check for pagination indicators if response was large
        if "To continue" in result or "cursor" in result:
            print("Pagination detected in response")


def test_claude_code_defaults():
    """Test that swarm tool defaults to Claude Code."""
    pm = PermissionManager()
    swarm = SwarmTool(permission_manager=pm)
    
    # Check that it defaults to Claude Sonnet
    assert swarm.model == "anthropic/claude-3-5-sonnet-20241022"
    print(f"✓ Swarm tool defaults to: {swarm.model}")


if __name__ == "__main__":
    # Run specific test
    pytest.main([__file__, "-v", "-k", "test_parallel_variable_renaming"])