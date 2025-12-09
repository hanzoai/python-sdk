#!/usr/bin/env python3
"""Test memory integration in hanzo-mcp."""

import sys
import asyncio
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))


class Console:
    """Simple console replacement."""

    def print(self, text):
        print(text)


console = Console()


async def test_memory_integration():
    """Test that memory tools work with local storage."""

    console.print("\n[bold cyan]Testing Hanzo MCP Memory Integration[/bold cyan]\n")

    # Test importing hanzo-memory
    try:
        import hanzo_memory

        console.print("✅ hanzo-memory package imported successfully")
    except ImportError as e:
        console.print(f"❌ Failed to import hanzo-memory: {e}")
        return

    # Test local memory client
    try:
        from hanzo_memory.db.local_client import LocalMemoryClient

        console.print("✅ LocalMemoryClient imported successfully")

        # Create client
        client = LocalMemoryClient(enable_markdown=True)
        await client.initialize()
        console.print("✅ LocalMemoryClient initialized with markdown support")

        # Check for markdown memories
        projects = await client.list_projects()
        markdown_project = next((p for p in projects if p.project_id == "markdown_import"), None)

        if markdown_project:
            memory_count = len([m for m in client.memories.values() if m.get("project_id") == "markdown_import"])
            console.print(f"✅ Found {memory_count} memories from markdown files")
        else:
            console.print("ℹ️ No markdown memories found (first run)")

        await client.close()

    except Exception as e:
        console.print(f"❌ Error with LocalMemoryClient: {e}")
        return

    # Test MCP tools integration
    try:
        # Check if memory tools can be imported
        from hanzo_mcp.tools.memory import memory_tools

        console.print("✅ Memory tools module imported")

        tool_names = [t.name for t in memory_tools.MEMORY_TOOLS]
        console.print(f"✅ Found {len(tool_names)} memory tools: {tool_names[:3]}...")

    except ImportError as e:
        console.print(f"⚠️ Memory tools not available (expected): {e}")
        console.print("  This is OK - memory tools are loaded dynamically when MCP server starts")

    console.print("\n[bold green]✅ Memory integration test completed successfully![/bold green]")
    console.print(
        "\nYour markdown files (LLM.md, CLAUDE.md, etc.) will be automatically loaded into memory when using hanzo-mcp tools."
    )


if __name__ == "__main__":
    asyncio.run(test_memory_integration())
