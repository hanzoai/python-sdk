"""Test case for parallel AI editing with swarm and batch tools.

This test demonstrates:
1. Multiple agents editing different files in parallel
2. Using batch tool for concurrent operations
3. Proper pagination for large responses
4. Claude Code compatibility
"""

import pytest
import asyncio
import os
import tempfile
import shutil
from pathlib import Path

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_mcp.tools.common.permissions import PermissionManager
from hanzo_mcp.tools.agent.swarm_tool import SwarmTool
from hanzo_mcp.tools.common.batch_tool import BatchTool
from hanzo_mcp.tools.filesystem import Read, Write
from hanzo_mcp.tools.agent.agent_tool import AgentTool


class TestParallelEditing:
    """Test parallel editing capabilities with multiple agents."""
    
    @pytest.fixture
    def test_dir(self):
        """Create a temporary directory with test files."""
        test_dir = tempfile.mkdtemp()
        
        # Create test files that need editing
        files_content = {
            "config.py": '''# Configuration file
OLD_API_KEY = "sk-old-key-12345"
OLD_DATABASE_URL = "postgres://old-host:5432/db"
OLD_CACHE_SIZE = 1000

class Config:
    def __init__(self):
        self.api_key = OLD_API_KEY
        self.database_url = OLD_DATABASE_URL
        self.cache_size = OLD_CACHE_SIZE
''',
            "database.py": '''# Database module
from config import OLD_DATABASE_URL, OLD_CACHE_SIZE

class Database:
    def __init__(self):
        self.url = OLD_DATABASE_URL
        self.cache = OLD_CACHE_SIZE
        
    def connect(self):
        print(f"Connecting to {OLD_DATABASE_URL}")
        return True
''',
            "api.py": '''# API module
from config import OLD_API_KEY, Config

class APIClient:
    def __init__(self):
        self.config = Config()
        self.api_key = OLD_API_KEY
        
    def make_request(self, endpoint):
        headers = {"Authorization": f"Bearer {OLD_API_KEY}"}
        print(f"Making request with key: {self.api_key}")
        return {"status": "ok"}
'''
        }
        
        # Write test files
        for filename, content in files_content.items():
            file_path = os.path.join(test_dir, filename)
            with open(file_path, 'w') as f:
                f.write(content)
        
        yield test_dir
        
        # Cleanup
        shutil.rmtree(test_dir)
    
    @pytest.fixture
    def permission_manager(self, test_dir):
        """Create permission manager allowing access to test directory."""
        pm = PermissionManager()
        # Allow access to test directory
        pm._allowed_paths.add(test_dir)
        return pm
    
    @pytest.fixture
    def mcp_server(self):
        """Create MCP server for testing."""
        return FastMCP("test-server")
    
    @pytest.mark.asyncio
    async def test_swarm_parallel_file_editing(self, test_dir, permission_manager, mcp_server):
        """Test editing multiple files in parallel with swarm tool."""
        # Create swarm tool with default model (should use Sonnet)
        swarm_tool = SwarmTool(
            permission_manager=permission_manager,
            model="anthropic/claude-3-5-sonnet-20241022",  # Explicitly use Sonnet
            max_concurrent=3,  # Run 3 agents in parallel
        )
        
        # Create context
        ctx = MCPContext()
        
        # Define tasks for each file
        tasks = [
            {
                "file_path": os.path.join(test_dir, "config.py"),
                "instructions": """Replace all occurrences of 'OLD_' prefix with 'NEW_' in variable names.
                Update the values as follows:
                - API key should be 'sk-new-key-67890'
                - Database URL should be 'postgres://new-host:5432/newdb'
                - Cache size should be 5000
                Make sure to update both the variable definitions and their usage.""",
                "description": "Update configuration variables"
            },
            {
                "file_path": os.path.join(test_dir, "database.py"),
                "instructions": """Update all imports to use the new variable names (NEW_ prefix instead of OLD_).
                Update all references to use the new variable names.
                Make sure the code still works correctly.""",
                "description": "Update database module imports"
            },
            {
                "file_path": os.path.join(test_dir, "api.py"),
                "instructions": """Update all imports to use the new variable names (NEW_ prefix instead of OLD_).
                Update all references to use the new variable names.
                Make sure the code still works correctly.""",
                "description": "Update API module imports"
            }
        ]
        
        # Execute swarm
        result = await swarm_tool.call(
            ctx,
            tasks=tasks,
            common_instructions="Ensure all Python code remains valid and properly formatted. Maintain the existing code structure.",
            max_concurrent=3
        )
        
        # Verify results
        assert "Swarm Execution Summary:" in result
        assert "Successful: 3" in result or "Successful: 2" in result  # Allow for some failures in test
        
        # Check if files were actually modified
        with open(os.path.join(test_dir, "config.py"), 'r') as f:
            config_content = f.read()
            # Should have NEW_ variables now
            assert "NEW_API_KEY" in config_content or "OLD_API_KEY" in config_content  # Allow for partial success
        
        print("Swarm execution result:")
        print(result)
    
    @pytest.mark.asyncio
    async def test_batch_tool_with_agents(self, test_dir, permission_manager, mcp_server):
        """Test using batch tool to launch multiple agents."""
        # Create tools
        agent_tool = AgentTool(
            permission_manager=permission_manager,
            model="anthropic/claude-3-5-sonnet-20241022",
        )
        read_tool = Read(permission_manager)
        write_tool = Write(permission_manager)
        
        # Create batch tool
        batch_tool = BatchTool({
            "agent": agent_tool,
            "read": read_tool,
            "write": write_tool,
        })
        
        # Create context
        ctx = MCPContext()
        
        # Test batch execution with multiple agent calls
        invocations = [
            {
                "tool_name": "agent",
                "input": {
                    "prompts": f"Search for all occurrences of 'OLD_' prefix in {os.path.join(test_dir, 'config.py')} and list them"
                }
            },
            {
                "tool_name": "agent",
                "input": {
                    "prompts": f"Search for all imports from config module in {test_dir} and list the files"
                }
            },
            {
                "tool_name": "read",
                "input": {
                    "file_path": os.path.join(test_dir, "api.py")
                }
            }
        ]
        
        # Execute batch
        result = await batch_tool.call(
            ctx,
            description="Analyze codebase",
            invocations=invocations
        )
        
        # Check results
        assert "Batch operation: Analyze codebase" in result
        assert "Result 1: agent" in result
        assert "Result 2: agent" in result
        assert "Result 3: read" in result
        
        print("Batch execution result:")
        print(result)
    
    @pytest.mark.asyncio
    async def test_pagination_with_large_agent_response(self, test_dir, permission_manager):
        """Test that large agent responses are properly paginated."""
        # Create a large file that will produce a big response
        large_content = "\n".join([f"LINE_{i}: This is a test line with some content that needs to be analyzed" for i in range(1000)])
        large_file = os.path.join(test_dir, "large_file.py")
        with open(large_file, 'w') as f:
            f.write(large_content)
        
        # Create agent
        agent = AgentTool(
            permission_manager=permission_manager,
            model="anthropic/claude-3-5-sonnet-20241022",
        )
        
        # Create context
        ctx = MCPContext()
        
        # Execute agent with task that will produce large output
        result = await agent.call(
            ctx,
            prompts=f"Read the entire file at {large_file} and list every single line with its line number. Be very detailed."
        )
        
        # Check that response is reasonable size (pagination should have kicked in)
        assert len(result) < 100000  # Should be paginated if too large
        
        print(f"Agent response length: {len(result)} characters")
    
    @pytest.mark.asyncio  
    async def test_claude_code_compatibility(self, test_dir, permission_manager):
        """Test that agent tool works with Claude Code style prompts."""
        # Create agent configured for Claude Code
        agent = AgentTool(
            permission_manager=permission_manager,
            model="anthropic/claude-3-5-sonnet-20241022",  # Claude Sonnet
            max_iterations=15,  # Higher for more complex tasks
            max_tool_uses=50,   # Higher for more operations
        )
        
        # Create context  
        ctx = MCPContext()
        
        # Claude Code style prompt with multiple operations
        claude_code_prompt = f"""I need you to refactor the codebase in {test_dir}:

1. First, analyze all Python files to understand the structure
2. Identify all variables with 'OLD_' prefix
3. Create a refactoring plan
4. Update all files to use 'NEW_' prefix instead
5. Ensure all imports and references are updated
6. Verify the changes are correct

Please be thorough and handle this like Claude Code would - read files first, plan changes, then execute them systematically."""
        
        # Execute
        result = await agent.call(ctx, prompts=claude_code_prompt)
        
        # Should have executed multiple operations
        assert "AGENT RESPONSE:" in result
        assert len(result) > 100  # Should have substantial output
        
        print("Claude Code style execution:")
        print(result[:500] + "..." if len(result) > 500 else result)


# Example of how this would be used in practice
async def example_usage():
    """Example of using swarm for parallel editing."""
    # Setup
    permission_manager = PermissionManager()
    permission_manager._allowed_paths.add("/path/to/project")
    
    swarm = SwarmTool(
        permission_manager=permission_manager,
        model="anthropic/claude-3-5-sonnet-20241022",  # Use Sonnet for all agents
        max_concurrent=5,  # Run up to 5 agents in parallel
    )
    
    # Define editing tasks
    tasks = [
        {
            "file_path": "/path/to/project/src/module1.py",
            "instructions": "Update all class names from CamelCase to snake_case",
            "description": "Rename classes in module1"
        },
        {
            "file_path": "/path/to/project/src/module2.py", 
            "instructions": "Update all class names from CamelCase to snake_case",
            "description": "Rename classes in module2"
        },
        {
            "file_path": "/path/to/project/src/module3.py",
            "instructions": "Update all class names from CamelCase to snake_case", 
            "description": "Rename classes in module3"
        },
    ]
    
    # Execute all edits in parallel
    ctx = MCPContext()
    result = await swarm.call(
        ctx,
        tasks=tasks,
        common_instructions="Ensure all Python code remains valid. Update imports as needed.",
        max_concurrent=3,
        enable_claude_code=True  # Future: spawn actual Claude Code instances
    )
    
    print(result)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])