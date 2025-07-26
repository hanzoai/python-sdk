"""Test suite for MCP tools in REPL context."""

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Any, Dict

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from hanzo_mcp.server import HanzoMCPServer


async def run_tool_tests(console: Console, mcp_server: HanzoMCPServer, tool_executor: Any):
    """Run comprehensive tests for MCP tools."""
    
    console.print("\n[bold cyan]Running MCP Tool Tests[/bold cyan]\n")
    
    test_results = []
    
    # Test categories
    test_suites = [
        ("File Operations", test_file_operations),
        ("Search Operations", test_search_operations),
        ("Shell Commands", test_shell_commands),
        ("LLM Integration", test_llm_integration),
        ("Agent Delegation", test_agent_delegation),
    ]
    
    for suite_name, test_func in test_suites:
        console.print(f"\n[bold]{suite_name}[/bold]")
        try:
            results = await test_func(mcp_server, tool_executor)
            for test_name, success, message in results:
                test_results.append((suite_name, test_name, success, message))
                status = "[green]✓[/green]" if success else "[red]✗[/red]"
                console.print(f"  {status} {test_name}: {message}")
        except Exception as e:
            console.print(f"  [red]Suite failed: {e}[/red]")
    
    # Summary
    console.print("\n[bold]Test Summary[/bold]")
    table = Table()
    table.add_column("Suite", style="cyan")
    table.add_column("Test", style="white")
    table.add_column("Status", style="green")
    
    passed = sum(1 for _, _, success, _ in test_results if success)
    total = len(test_results)
    
    for suite, test, success, _ in test_results:
        status = "PASS" if success else "FAIL"
        style = "green" if success else "red"
        table.add_row(suite, test, f"[{style}]{status}[/{style}]")
    
    console.print(table)
    console.print(f"\nTotal: {passed}/{total} passed ({passed/total*100:.1f}%)")


async def test_file_operations(mcp_server: HanzoMCPServer, tool_executor: Any) -> list:
    """Test file operations."""
    results = []
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        
        # Test 1: Write file
        try:
            tool = mcp_server.tools.get("write_file")
            await tool.execute(
                file_path=str(test_file),
                content="Hello, MCP!"
            )
            results.append(("Write file", True, "File created successfully"))
        except Exception as e:
            results.append(("Write file", False, str(e)))
        
        # Test 2: Read file
        try:
            tool = mcp_server.tools.get("read_file")
            content = await tool.execute(file_path=str(test_file))
            success = "Hello, MCP!" in content
            results.append(("Read file", success, f"Content: {content[:50]}..."))
        except Exception as e:
            results.append(("Read file", False, str(e)))
        
        # Test 3: Edit file
        try:
            tool = mcp_server.tools.get("edit_file")
            await tool.execute(
                file_path=str(test_file),
                old_string="Hello, MCP!",
                new_string="Hello, Hanzo MCP!"
            )
            # Verify edit
            read_tool = mcp_server.tools.get("read_file")
            content = await read_tool.execute(file_path=str(test_file))
            success = "Hello, Hanzo MCP!" in content
            results.append(("Edit file", success, "File edited successfully"))
        except Exception as e:
            results.append(("Edit file", False, str(e)))
    
    return results


async def test_search_operations(mcp_server: HanzoMCPServer, tool_executor: Any) -> list:
    """Test search operations."""
    results = []
    
    # Test 1: Grep search
    try:
        tool = mcp_server.tools.get("grep")
        result = await tool.execute(
            pattern="def ",
            path=".",
            include="*.py"
        )
        success = isinstance(result, list) or isinstance(result, str)
        results.append(("Grep search", success, f"Found {len(result) if isinstance(result, list) else 1} matches"))
    except Exception as e:
        results.append(("Grep search", False, str(e)))
    
    # Test 2: File search
    try:
        tool = mcp_server.tools.get("search")
        result = await tool.execute(
            query="class",
            path=".",
            max_results=5
        )
        success = isinstance(result, (list, dict, str))
        results.append(("File search", success, "Search completed"))
    except Exception as e:
        results.append(("File search", False, str(e)))
    
    return results


async def test_shell_commands(mcp_server: HanzoMCPServer, tool_executor: Any) -> list:
    """Test shell command execution."""
    results = []
    
    # Test 1: Simple command
    try:
        tool = mcp_server.tools.get("run_command")
        result = await tool.execute(command="echo 'Hello from MCP'")
        success = "Hello from MCP" in str(result)
        results.append(("Echo command", success, "Command executed"))
    except Exception as e:
        results.append(("Echo command", False, str(e)))
    
    # Test 2: Python version
    try:
        tool = mcp_server.tools.get("run_command")
        result = await tool.execute(command="python --version")
        success = "Python" in str(result)
        results.append(("Python version", success, str(result)[:50]))
    except Exception as e:
        results.append(("Python version", False, str(e)))
    
    return results


async def test_llm_integration(mcp_server: HanzoMCPServer, tool_executor: Any) -> list:
    """Test LLM integration."""
    results = []
    
    # Test 1: Simple chat
    try:
        response = await tool_executor.execute_with_tools("What is 2+2?")
        success = "4" in response
        results.append(("Simple math", success, "LLM responded correctly"))
    except Exception as e:
        results.append(("Simple math", False, str(e)))
    
    # Test 2: Tool usage
    try:
        response = await tool_executor.execute_with_tools(
            "Create a file called test_llm.txt with the content 'LLM test'"
        )
        # Check if file was created
        import os
        success = os.path.exists("test_llm.txt")
        if success:
            os.remove("test_llm.txt")  # Cleanup
        results.append(("LLM tool use", success, "LLM used tools correctly"))
    except Exception as e:
        results.append(("LLM tool use", False, str(e)))
    
    return results


async def test_agent_delegation(mcp_server: HanzoMCPServer, tool_executor: Any) -> list:
    """Test agent delegation."""
    results = []
    
    # Test 1: Agent dispatch
    try:
        tool = mcp_server.tools.get("dispatch_agent")
        if tool:
            result = await tool.execute(
                instruction="List the current directory contents"
            )
            success = result is not None
            results.append(("Agent dispatch", success, "Agent completed task"))
        else:
            results.append(("Agent dispatch", False, "Agent tool not available"))
    except Exception as e:
        results.append(("Agent dispatch", False, str(e)))
    
    return results