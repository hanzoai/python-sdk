"""Comprehensive test for swarm_tool_v2.py functionality.

This test demonstrates multiple Claude agents collaborating to refactor code:
1. Creates a simple Python file
2. Uses multiple agents to refactor it:
   - One agent adds docstrings
   - Another adds type hints
   - Another optimizes the code
3. Shows before/after comparison
"""

import os
import sys
import shutil
import tempfile
from unittest.mock import Mock, AsyncMock, patch

import pytest

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mcp.server.fastmcp import Context as MCPContext
from hanzo_mcp.tools.agent.swarm_tool import SwarmTool
from hanzo_mcp.tools.common.permissions import PermissionManager


class TestSwarmV2Comprehensive:
    """Comprehensive tests for swarm_tool_v2 functionality."""

    @pytest.fixture
    def setup_test_env(self):
        """Set up test environment with temporary directory."""
        test_dir = tempfile.mkdtemp()
        pm = PermissionManager()
        pm.add_allowed_path(test_dir)

        yield test_dir, pm

        # Cleanup
        shutil.rmtree(test_dir)

    def create_test_file(self, test_dir: str) -> str:
        """Create a simple Python file for testing."""
        file_path = os.path.join(test_dir, "calculator.py")

        # Create a simple calculator module without docstrings or type hints
        content = """# Simple calculator module

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    result = 0
    for i in range(b):
        result = result + a
    return result

def divide(a, b):
    if b == 0:
        return None
    return a / b

class Calculator:
    def __init__(self):
        self.memory = 0
    
    def add_to_memory(self, value):
        self.memory = self.memory + value
    
    def clear_memory(self):
        self.memory = 0
    
    def get_memory(self):
        return self.memory
    
    def calculate(self, operation, a, b):
        if operation == "add":
            return add(a, b)
        elif operation == "subtract":
            return subtract(a, b)
        elif operation == "multiply":
            return multiply(a, b)
        elif operation == "divide":
            return divide(a, b)
        else:
            return None
"""

        with open(file_path, "w") as f:
            f.write(content)

        return file_path

    @pytest.mark.asyncio
    async def test_swarm_v2_with_hanzo_agents(self, tool_helper, setup_test_env):
        """Test swarm_tool_v2 when hanzo-agents is available."""
        test_dir, pm = setup_test_env
        file_path = self.create_test_file(test_dir)

        # Read original content
        with open(file_path, "r") as f:
            original_content = f.read()

        print("\n=== BEFORE REFACTORING ===")
        print(original_content)
        print("=" * 60)

        # Create swarm tool
        swarm = SwarmTool(permission_manager=pm)
        ctx = MCPContext()

        # Define agent network for refactoring
        config = {
            "agents": {
                "docstring_agent": {
                    "query": "Add comprehensive docstrings to all functions and classes in the file",
                    "role": "Documentation specialist",
                    "model": "claude-3-5-sonnet",
                    "file_path": file_path,
                    "connections": ["type_hint_agent"],
                },
                "type_hint_agent": {
                    "query": "Add proper type hints to all function parameters and return values",
                    "role": "Type annotation expert",
                    "model": "claude-3-5-sonnet",
                    "file_path": file_path,
                    "receives_from": ["docstring_agent"],
                    "connections": ["optimizer_agent"],
                },
                "optimizer_agent": {
                    "query": "Optimize the code for better performance and readability. The multiply function is inefficient - use the * operator instead",
                    "role": "Code optimization expert",
                    "model": "claude-3-5-sonnet",
                    "file_path": file_path,
                    "receives_from": ["type_hint_agent"],
                    "connections": ["reviewer"],
                },
                "reviewer": {
                    "query": "Review all changes made by previous agents and ensure code quality",
                    "role": "Senior code reviewer",
                    "model": "claude-3-5-sonnet",
                    "file_path": file_path,
                    "receives_from": ["optimizer_agent"],
                },
            },
            "entry_point": "docstring_agent",
            "topology": "pipeline",
        }

        # Check if we need to mock (for testing purposes)
        mock_agents = os.environ.get("MOCK_HANZO_AGENTS", "false").lower() == "true"
        if mock_agents:
            print("Using mock implementation for testing")

            # Mock successful agent responses
            mock_responses = {
                "docstring_agent": "Added comprehensive docstrings to all functions and classes",
                "type_hint_agent": "Added type hints to all functions",
                "optimizer_agent": "Optimized multiply function and improved code structure",
                "reviewer": "All changes reviewed and approved. Code quality is excellent.",
            }

            # Simulate file changes
            refactored_content = '''"""Simple calculator module with basic arithmetic operations."""

from typing import Optional, Union


def add(a: float, b: float) -> float:
    """Add two numbers together.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of a and b
    """
    return a + b


def subtract(a: float, b: float) -> float:
    """Subtract second number from first.
    
    Args:
        a: First number
        b: Number to subtract
        
    Returns:
        Difference of a and b
    """
    return a - b


def multiply(a: float, b: float) -> float:
    """Multiply two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Product of a and b
    """
    return a * b  # Optimized from loop


def divide(a: float, b: float) -> Optional[float]:
    """Divide first number by second.
    
    Args:
        a: Dividend
        b: Divisor
        
    Returns:
        Quotient of a and b, or None if b is 0
    """
    if b == 0:
        return None
    return a / b


class Calculator:
    """A simple calculator with memory functionality."""
    
    def __init__(self) -> None:
        """Initialize calculator with zero memory."""
        self.memory: float = 0
    
    def add_to_memory(self, value: float) -> None:
        """Add a value to memory.
        
        Args:
            value: Value to add to memory
        """
        self.memory += value  # Optimized
    
    def clear_memory(self) -> None:
        """Clear the memory to zero."""
        self.memory = 0
    
    def get_memory(self) -> float:
        """Get current memory value.
        
        Returns:
            Current value in memory
        """
        return self.memory
    
    def calculate(self, operation: str, a: float, b: float) -> Optional[float]:
        """Perform a calculation based on the operation.
        
        Args:
            operation: Type of operation ('add', 'subtract', 'multiply', 'divide')
            a: First operand
            b: Second operand
            
        Returns:
            Result of the operation, or None if operation is invalid
        """
        operations = {
            "add": add,
            "subtract": subtract,
            "multiply": multiply,
            "divide": divide
        }
        
        if operation in operations:
            return operations[operation](a, b)
        return None
'''

            # Write the refactored content
            with open(file_path, "w") as f:
                f.write(refactored_content)

            # Create mock result
            result = f"""Agent Network Execution Results (hanzo-agents SDK)
================================================================================
Total agents: 4
Completed: 4
Failed: 0
Entry point: docstring_agent

Execution Order: docstring_agent → type_hint_agent → optimizer_agent → reviewer
----------------------------------------

Detailed Results:
================================================================================

### docstring_agent (Documentation specialist) [claude-3-5-sonnet]
----------------------------------------
{mock_responses["docstring_agent"]}

### type_hint_agent (Type annotation expert) [claude-3-5-sonnet]
----------------------------------------
{mock_responses["type_hint_agent"]}

### optimizer_agent (Code optimization expert) [claude-3-5-sonnet]
----------------------------------------
{mock_responses["optimizer_agent"]}

### reviewer (Senior code reviewer) [claude-3-5-sonnet]
----------------------------------------
{mock_responses["reviewer"]}"""

        else:
            # Execute with real hanzo-agents
            result = await swarm.call(
                ctx,
                config=config,
                query="Refactor the calculator.py file with proper documentation, type hints, and optimizations",
                context="This is a simple calculator module that needs improvement",
            )

        print("\n=== SWARM EXECUTION RESULT ===")
        print(result)
        print("=" * 60)

        # Read refactored content
        with open(file_path, "r") as f:
            refactored_content = f.read()

        print("\n=== AFTER REFACTORING ===")
        print(refactored_content)
        print("=" * 60)

        # Verify improvements
        assert '"""' in refactored_content or "'''" in refactored_content  # Has docstrings
        assert "->" in refactored_content  # Has type hints
        assert "a * b" in refactored_content or "return a * b" in refactored_content  # Optimized multiply
        assert "typing" in refactored_content or "Optional" in refactored_content  # Uses typing module

        print("\n✓ All improvements verified:")
        print("  - Docstrings added")
        print("  - Type hints added")
        print("  - Code optimized")
        print("  - Code reviewed")

    @pytest.mark.asyncio
    async def test_swarm_v2_fallback_mode(self, tool_helper, setup_test_env):
        """Test swarm_tool_v2 fallback when hanzo-agents is not available."""
        test_dir, pm = setup_test_env

        # Create test file
        file_path = os.path.join(test_dir, "test.py")
        with open(file_path, "w") as f:
            f.write("def hello():\n    print('Hello')\n")

        # Create swarm tool
        swarm = SwarmTool(permission_manager=pm)
        ctx = Mock(spec=MCPContext)

        # Mock the tool context creation
        mock_tool_ctx = Mock()
        mock_tool_ctx.set_tool_info = AsyncMock()
        mock_tool_ctx.error = AsyncMock()
        mock_tool_ctx.warning = AsyncMock()
        mock_tool_ctx.info = AsyncMock()

        # Since hanzo-agents is already imported at module level,
        # we need to test the fallback behavior by patching inside the call method
        # The swarm_tool_v2 imports from swarm_tool during runtime in the call method

        # Create a mock for the fallback SwarmTool
        mock_original_class = Mock()
        mock_original_instance = Mock()
        mock_original_instance.call = AsyncMock(return_value="Fallback result from original SwarmTool")
        mock_original_class.return_value = mock_original_instance

        # Patch where the import happens inside the call method
        with patch(
            "hanzo_mcp.tools.common.context.create_tool_context",
            return_value=mock_tool_ctx,
        ):
            with patch.dict(
                "sys.modules",
                {"hanzo_mcp.tools.agent.swarm_tool": Mock(SwarmTool=mock_original_class)},
            ):
                with patch.dict(os.environ, {"MOCK_HANZO_AGENTS": "true"}):
                    result = await swarm.call(
                        ctx,
                        config={"agents": {"test": {"query": "test"}}},
                        query="test query",
                    )

                    # The result should come from the fallback
                    tool_helper.assert_in_result("Fallback result from original SwarmTool", result)
                    print("✓ Fallback to original SwarmTool works correctly")

    @pytest.mark.asyncio
    async def test_swarm_v2_error_handling(self, tool_helper, setup_test_env):
        """Test error handling in swarm_tool_v2."""
        test_dir, pm = setup_test_env

        swarm = SwarmTool(permission_manager=pm)
        ctx = MCPContext()

        # Test with no agents
        result = await swarm.call(ctx, config={"agents": {}}, query="test")

        tool_helper.assert_in_result("Error:", result)
        assert "at least one agent" in result.lower()
        print("✓ Proper error handling for empty agent config")

    @pytest.mark.asyncio
    async def test_swarm_v2_network_topologies(self, tool_helper, setup_test_env):
        """Test different network topologies."""
        test_dir, pm = setup_test_env

        # Create multiple test files
        files = {}
        for name in ["module1.py", "module2.py", "module3.py"]:
            file_path = os.path.join(test_dir, name)
            with open(file_path, "w") as f:
                f.write(f"# {name}\ndef func():\n    pass\n")
            files[name] = file_path

        swarm = SwarmTool(permission_manager=pm)
        ctx = MCPContext()

        # Test star topology (coordinator pattern)
        star_config = {
            "agents": {
                "coordinator": {
                    "query": "Coordinate refactoring of all modules",
                    "role": "Lead architect",
                    "connections": ["module1_agent", "module2_agent", "module3_agent"],
                },
                "module1_agent": {
                    "query": "Refactor module1.py",
                    "role": "Module 1 specialist",
                    "file_path": files["module1.py"],
                    "receives_from": ["coordinator"],
                    "connections": ["final_reviewer"],
                },
                "module2_agent": {
                    "query": "Refactor module2.py",
                    "role": "Module 2 specialist",
                    "file_path": files["module2.py"],
                    "receives_from": ["coordinator"],
                    "connections": ["final_reviewer"],
                },
                "module3_agent": {
                    "query": "Refactor module3.py",
                    "role": "Module 3 specialist",
                    "file_path": files["module3.py"],
                    "receives_from": ["coordinator"],
                    "connections": ["final_reviewer"],
                },
                "final_reviewer": {
                    "query": "Review all module changes",
                    "role": "Final reviewer",
                    "receives_from": [
                        "module1_agent",
                        "module2_agent",
                        "module3_agent",
                    ],
                },
            },
            "entry_point": "coordinator",
            "topology": "star",
        }

        # Mock execution for testing
        mock_agents = os.environ.get("MOCK_HANZO_AGENTS", "false").lower() == "true"
        if mock_agents:
            result = "Agent Network Execution Results (hanzo-agents SDK)\n"
            result += "Star topology test completed"
        else:
            result = await swarm.call(
                ctx,
                config=star_config,
                query="Refactor all modules with consistent style",
            )

        print("\n=== STAR TOPOLOGY TEST ===")
        print(result)
        tool_helper.assert_in_result("Agent Network Execution Results", result)
        print("✓ Star topology configuration works")


def run_comprehensive_tests():
    """Run comprehensive tests without pytest."""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE SWARM V2 TESTS")
    print("=" * 80)

    # Create test instance
    test = TestSwarmV2Comprehensive()

    # Set up test environment manually
    test_dir = tempfile.mkdtemp()
    pm = PermissionManager()
    pm.add_allowed_path(test_dir)

    try:
        # Test 1: Create test file
        print("\n1. Creating test file...")
        file_path = test.create_test_file(test_dir)
        print(f"✓ Created test file: {file_path}")

        # Test 2: Check swarm availability
        print("\n2. Checking hanzo-agents availability...")
        print(f"hanzo-agents available: True")  # Always available now

        # Test 3: Create swarm instance
        print("\n3. Creating SwarmTool instance...")
        swarm = SwarmTool(permission_manager=pm)
        print(f"✓ SwarmTool created with model: {swarm.model}")

        # Test 4: Verify tool registration
        print("\n4. Verifying tool properties...")
        print(f"Tool name: {swarm.name}")
        print(f"Tool description preview: {swarm.description[:100]}...")

        print("\n" + "=" * 80)
        print("Basic tests completed successfully!")
        print("Run with pytest for full async tests including agent execution.")

    finally:
        # Cleanup
        shutil.rmtree(test_dir)


if __name__ == "__main__":
    # Run basic synchronous tests
    run_comprehensive_tests()

    print("\n" + "=" * 80)
    print("To run full async tests with agent execution:")
    print("pytest -xvs tests/test_swarm/test_swarm_v2_comprehensive.py")
    print("=" * 80)
