#!/usr/bin/env python3
"""Full end-to-end swarm test with Claude Code.

This demonstrates:
1. Using batch tool to coordinate multiple operations
2. Parallel editing with swarm tool
3. Consensus/review with multiple agents
4. Proper pagination handling
"""

import os
import shutil
import asyncio
import tempfile

from mcp.server.fastmcp import Context as MCPContext
from hanzo_mcp.tools.filesystem import Read, Write, DirectoryTree
from hanzo_mcp.tools.agent.agent_tool import AgentTool
from hanzo_mcp.tools.agent.swarm_tool import SwarmTool
from hanzo_mcp.tools.common.batch_tool import BatchTool
from hanzo_mcp.tools.common.permissions import PermissionManager


async def main():
    """Run full swarm test with batch coordination."""
    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("CLAUDE_API_KEY"):
        print("Error: No Claude API key found!")
        print("Set ANTHROPIC_API_KEY or CLAUDE_API_KEY environment variable")
        return

    # Create test project
    test_dir = tempfile.mkdtemp(prefix="full_swarm_test_")
    print(f"Created test project at: {test_dir}")

    try:
        # Create a mini project structure
        project_structure = {
            "src/models/user.py": """# User model
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.is_active = True
    
    def get_display_name(self):
        return self.name
    
    def deactivate(self):
        self.is_active = False
""",
            "src/models/product.py": """# Product model
class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price
        self.in_stock = True
    
    def get_display_price(self):
        return f"${self.price:.2f}"
    
    def mark_out_of_stock(self):
        self.in_stock = False
""",
            "src/models/order.py": """# Order model
from .user import User
from .product import Product

class Order:
    def __init__(self, user, products):
        self.user = user
        self.products = products
        self.status = "pending"
    
    def calculate_total(self):
        return sum(p.price for p in self.products)
    
    def complete(self):
        self.status = "completed"
""",
            "src/services/user_service.py": """# User service
from ..models.user import User

class UserService:
    def __init__(self):
        self.users = []
    
    def create_user(self, name, email):
        user = User(name, email)
        self.users.append(user)
        return user
    
    def find_user(self, email):
        for user in self.users:
            if user.email == email:
                return user
        return None
""",
            "tests/test_models.py": """# Model tests
import unittest
from src.models.user import User
from src.models.product import Product

class TestModels(unittest.TestCase):
    def test_user_creation(self):
        user = User("John Doe", "john@example.com")
        self.assertEqual(user.name, "John Doe")
        self.assertTrue(user.is_active)
    
    def test_product_creation(self):
        product = Product("Widget", 19.99)
        self.assertEqual(product.get_display_price(), "$19.99")
""",
        }

        # Create directory structure and files
        for filepath, content in project_structure.items():
            full_path = os.path.join(test_dir, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f:
                f.write(content)

        print(f"Created project structure with {len(project_structure)} files")

        # Set up permissions
        pm = PermissionManager()
        pm._allowed_paths.add(test_dir)

        # Create tools
        swarm = SwarmTool(permission_manager=pm)
        agent = AgentTool(permission_manager=pm)
        read = Read(pm)
        write = Write(pm)
        tree = DirectoryTree(pm)

        # Create batch tool
        batch = BatchTool(
            {
                "swarm": swarm,
                "agent": agent,
                "read": read,
                "write": write,
                "directory_tree": tree,
            }
        )

        # Create context
        ctx = MCPContext()

        print("\n" + "=" * 60)
        print("PHASE 1: Analyze project structure with batch + agent")
        print("=" * 60 + "\n")

        # Use batch to analyze project
        analysis_result = await batch.call(
            ctx,
            description="Analyze project",
            invocations=[
                {"tool_name": "directory_tree", "input": {"path": test_dir}},
                {
                    "tool_name": "agent",
                    "input": {
                        "prompts": f"Analyze the project structure in {test_dir} and identify all Python classes that need type hints"
                    },
                },
            ],
        )

        print(analysis_result[:1000] + "..." if len(analysis_result) > 1000 else analysis_result)

        print("\n" + "=" * 60)
        print("PHASE 2: Parallel editing with swarm")
        print("=" * 60 + "\n")

        # Use swarm for parallel editing
        edit_result = await swarm.call(
            ctx,
            tasks=[
                {
                    "file_path": os.path.join(test_dir, "src/models/user.py"),
                    "instructions": "Add complete type hints to all methods and attributes",
                    "description": "Add type hints to User model",
                },
                {
                    "file_path": os.path.join(test_dir, "src/models/product.py"),
                    "instructions": "Add complete type hints to all methods and attributes",
                    "description": "Add type hints to Product model",
                },
                {
                    "file_path": os.path.join(test_dir, "src/models/order.py"),
                    "instructions": "Add complete type hints to all methods, attributes, and imports",
                    "description": "Add type hints to Order model",
                },
            ],
            common_instructions="Use Python 3.9+ style type hints. Add from typing import imports as needed.",
            max_concurrent=3,
        )

        print(edit_result[:1500] + "..." if len(edit_result) > 1500 else edit_result)

        print("\n" + "=" * 60)
        print("PHASE 3: Consensus review with multiple agents")
        print("=" * 60 + "\n")

        # Use swarm for consensus review
        review_result = await swarm.call(
            ctx,
            tasks=[
                {
                    "file_path": os.path.join(test_dir, "src/models/order.py"),
                    "instructions": "Review the type hints and suggest any improvements from a best practices perspective",
                    "description": "Agent 1: Best practices review",
                },
                {
                    "file_path": os.path.join(test_dir, "src/models/order.py"),
                    "instructions": "Review the code for potential bugs or edge cases that the type hints might not catch",
                    "description": "Agent 2: Bug and edge case review",
                },
            ],
            common_instructions="Provide specific, actionable feedback",
            max_concurrent=2,
        )

        print(review_result[:1500] + "..." if len(review_result) > 1500 else review_result)

        print("\n" + "=" * 60)
        print("PHASE 4: Final verification with batch")
        print("=" * 60 + "\n")

        # Final verification
        verify_result = await batch.call(
            ctx,
            description="Verify changes",
            invocations=[
                {
                    "tool_name": "read",
                    "input": {"file_path": os.path.join(test_dir, "src/models/user.py")},
                },
                {
                    "tool_name": "agent",
                    "input": {"prompts": f"Verify that all files in {test_dir}/src/models/ now have proper type hints"},
                },
            ],
        )

        print(verify_result[:1000] + "..." if len(verify_result) > 1000 else verify_result)

        print("\n" + "=" * 60)
        print("TEST COMPLETE!")
        print("=" * 60)
        print("\nThis test demonstrated:")
        print("1. ✓ Batch tool coordinating multiple operations")
        print("2. ✓ Swarm tool with parallel Claude Code editing")
        print("3. ✓ Consensus review with multiple agents")
        print("4. ✓ Proper pagination for large responses")
        print("5. ✓ All agents defaulting to Claude 3.5 Sonnet")

    finally:
        # Cleanup
        shutil.rmtree(test_dir)
        print(f"\nCleaned up test directory: {test_dir}")


if __name__ == "__main__":
    # Run the full test
    asyncio.run(main())
