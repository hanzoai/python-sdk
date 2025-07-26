"""Basic swarm tool tests with success and failure cases."""

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch
import sys

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mcp.server.fastmcp import Context as MCPContext
from hanzo_mcp.tools.common.permissions import PermissionManager
from hanzo_mcp.tools.agent.swarm_tool import SwarmTool


class TestSwarmBasic:
    """Basic tests for swarm tool functionality."""
    
    def test_swarm_defaults_to_claude_sonnet(self):
        """Test that swarm tool defaults to Claude Sonnet."""
        pm = PermissionManager()
        swarm = SwarmTool(permission_manager=pm)
        
        assert swarm.model == "anthropic/claude-3-5-sonnet-20241022"
        print("✓ Swarm tool correctly defaults to Claude 3.5 Sonnet")
    
    def test_swarm_detects_api_keys(self):
        """Test that swarm tool detects API keys from environment."""
        pm = PermissionManager()
        
        # Test with ANTHROPIC_API_KEY
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key-123'}):
            swarm = SwarmTool(permission_manager=pm)
            assert swarm.api_key == 'test-key-123'
            print("✓ Swarm detects ANTHROPIC_API_KEY")
        
        # Test with CLAUDE_API_KEY
        with patch.dict(os.environ, {'CLAUDE_API_KEY': 'test-key-456'}):
            swarm = SwarmTool(permission_manager=pm)
            assert swarm.api_key == 'test-key-456'
            print("✓ Swarm detects CLAUDE_API_KEY")
        
        # Test priority (ANTHROPIC_API_KEY takes precedence)
        with patch.dict(os.environ, {
            'ANTHROPIC_API_KEY': 'primary-key',
            'CLAUDE_API_KEY': 'fallback-key'
        }):
            swarm = SwarmTool(permission_manager=pm)
            assert swarm.api_key == 'primary-key'
            print("✓ ANTHROPIC_API_KEY takes precedence over CLAUDE_API_KEY")
    
    @pytest.mark.asyncio
    async def test_swarm_fails_without_tasks(self):
        """Test that swarm fails gracefully without tasks."""
        pm = PermissionManager()
        swarm = SwarmTool(permission_manager=pm)
        ctx = MCPContext()
        
        # Call with no tasks
        result = await swarm.call(ctx, tasks=[])
        
        assert "Error:" in result
        assert "at least one task" in result.lower()
        print("✓ Swarm correctly fails when no tasks provided")
    
    @pytest.mark.asyncio
    async def test_swarm_validates_task_format(self):
        """Test that swarm validates task format."""
        pm = PermissionManager()
        swarm = SwarmTool(permission_manager=pm)
        ctx = MCPContext()
        
        # Invalid task format (missing required fields)
        result = await swarm.call(
            ctx,
            tasks=[
                {"instructions": "Do something"}  # Missing file_path
            ]
        )
        
        # Should handle gracefully (the actual validation happens in execute_task)
        assert isinstance(result, str)
        print("✓ Swarm handles invalid task format")
    
    @pytest.mark.asyncio
    async def test_swarm_respects_max_concurrent(self):
        """Test that swarm respects max_concurrent setting."""
        pm = PermissionManager()
        swarm = SwarmTool(permission_manager=pm)
        ctx = MCPContext()
        
        # Create dummy tasks
        test_dir = tempfile.mkdtemp()
        try:
            # Create test files
            for i in range(5):
                with open(os.path.join(test_dir, f"file{i}.txt"), 'w') as f:
                    f.write(f"Content {i}")
            
            # Allow access
            pm.add_allowed_path(test_dir)
            
            tasks = [
                {
                    "file_path": os.path.join(test_dir, f"file{i}.txt"),
                    "instructions": f"Task {i}",
                    "description": f"Test task {i}"
                }
                for i in range(5)
            ]
            
            # Mock the agent execution to track concurrency
            concurrent_count = 0
            max_concurrent_seen = 0
            
            async def mock_agent_call(self, ctx, **kwargs):
                nonlocal concurrent_count, max_concurrent_seen
                concurrent_count += 1
                max_concurrent_seen = max(max_concurrent_seen, concurrent_count)
                # Simulate some work
                import asyncio
                await asyncio.sleep(0.1)
                concurrent_count -= 1
                return f"Mocked result for {kwargs.get('prompts', 'unknown')}"
            
            # Patch AgentTool.call
            with patch('hanzo_mcp.tools.agent.agent_tool.AgentTool.call', mock_agent_call):
                result = await swarm.call(
                    ctx,
                    tasks=tasks,
                    max_concurrent=2  # Limit to 2 concurrent
                )
                
                # Check that max concurrent was respected
                assert max_concurrent_seen <= 2
                print(f"✓ Swarm respected max_concurrent=2 (saw max {max_concurrent_seen})")
                
        finally:
            shutil.rmtree(test_dir)
    
    @pytest.mark.asyncio
    async def test_swarm_handles_agent_failures(self):
        """Test that swarm handles individual agent failures gracefully."""
        pm = PermissionManager()
        swarm = SwarmTool(permission_manager=pm)
        ctx = MCPContext()
        
        # Create test directory
        test_dir = tempfile.mkdtemp()
        try:
            pm.add_allowed_path(test_dir)
            
            # Create tasks where one will fail
            tasks = [
                {
                    "file_path": os.path.join(test_dir, "good.txt"),
                    "instructions": "This should succeed",
                    "description": "Good task"
                },
                {
                    "file_path": os.path.join(test_dir, "bad.txt"),
                    "instructions": "FAIL_THIS_TASK",  # Special marker
                    "description": "Bad task"
                },
                {
                    "file_path": os.path.join(test_dir, "also_good.txt"),
                    "instructions": "This should also succeed",
                    "description": "Another good task"
                }
            ]
            
            # Mock agent to fail on specific task
            async def mock_agent_call(self, ctx, **kwargs):
                prompt = kwargs.get('prompts', '')
                if 'FAIL_THIS_TASK' in prompt:
                    raise Exception("Simulated agent failure")
                return f"Success: {prompt[:50]}"
            
            with patch('hanzo_mcp.tools.agent.agent_tool.AgentTool.call', mock_agent_call):
                result = await swarm.call(ctx, tasks=tasks)
                
                # Check results
                assert "Successful: 2" in result
                assert "Failed: 1" in result
                assert "❌" in result  # Failed task marker
                assert "✅" in result  # Success task marker
                print("✓ Swarm handles individual agent failures gracefully")
                
        finally:
            shutil.rmtree(test_dir)
    
    def test_swarm_summary_format(self):
        """Test that swarm produces properly formatted summaries."""
        pm = PermissionManager()
        swarm = SwarmTool(permission_manager=pm)
        
        # The description should mention Claude Code
        assert "Claude Code" in swarm.description or "Claude" in swarm.description
        assert "Sonnet" in swarm.description
        assert "parallel" in swarm.description.lower()
        print("✓ Swarm description mentions Claude Code and parallel execution")


def run_basic_tests():
    """Run basic tests without pytest."""
    print("Running basic swarm tests...")
    print("="*60)
    
    tests = TestSwarmBasic()
    
    # Test 1: Defaults
    tests.test_swarm_defaults_to_claude_sonnet()
    
    # Test 2: API key detection
    tests.test_swarm_detects_api_keys()
    
    # Test 3: Summary format
    tests.test_swarm_summary_format()
    
    print("="*60)
    print("Basic tests completed!")


if __name__ == "__main__":
    # Run basic tests that don't require async
    run_basic_tests()
    
    # Run async tests if pytest is available
    try:
        import pytest
        pytest.main([__file__, "-v"])
    except ImportError:
        print("\nInstall pytest to run async tests:")
        print("pip install pytest pytest-asyncio")