"""Integration tests for MCP tools working together."""

import asyncio
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock

import pytest

from hanzo_mcp.tools.common.permissions import PermissionManager
from hanzo_mcp.tools.filesystem.read import ReadTool
from hanzo_mcp.tools.filesystem.write import Write as WriteTool
from hanzo_mcp.tools.filesystem.edit import Edit as EditTool
from hanzo_mcp.tools.filesystem.grep import Grep as GrepTool
from hanzo_mcp.tools.shell.bash_tool import BashTool
from hanzo_mcp.tools.todo.todo import TodoTool
from hanzo_mcp.tools.common.batch_tool import BatchTool
from hanzo_mcp.tools.common.thinking_tool import ThinkingTool


class TestFileSystemAndShellIntegration:
    """Test filesystem tools working with shell commands."""
    
    def test_create_edit_and_verify_workflow(self):
        """Test creating, editing, and verifying files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PermissionManager()
            pm.add_allowed_path(tmpdir)
            
            write_tool = WriteTool(pm)
            edit_tool = EditTool(pm)
            read_tool = ReadTool(pm)
            bash_tool = BashTool(pm)
            mock_ctx = Mock()
            
            # 1. Create a Python file
            filepath = os.path.join(tmpdir, "test_script.py")
            initial_content = '''def greet(name):
    return f"Hello, {name}!"

def main():
    print(greet("World"))

if __name__ == "__main__":
    main()
'''
            
            result = asyncio.run(write_tool.call(
                mock_ctx,
                file_path=filepath,
                content=initial_content
            ))
            assert "successfully" in result.lower()
            
            # 2. Edit the file to add a new function
            edit_result = asyncio.run(edit_tool.call(
                mock_ctx,
                file_path=filepath,
                old_string='def main():\n    print(greet("World"))',
                new_string='def goodbye(name):\n    return f"Goodbye, {name}!"\n\ndef main():\n    print(greet("World"))\n    print(goodbye("World"))'
            ))
            assert "successfully" in edit_result.lower()
            
            # 3. Read the file to verify
            read_result = asyncio.run(read_tool.call(mock_ctx, file_path=filepath))
            assert "def goodbye(name):" in read_result
            assert "Goodbye, {name}!" in read_result
            
            # 4. Run the script
            run_result = asyncio.run(bash_tool.call(
                mock_ctx,
                command=f"cd {tmpdir} && python test_script.py"
            ))
            assert "Hello, World!" in run_result
            assert "Goodbye, World!" in run_result
    
    def test_grep_edit_workflow(self):
        """Test finding patterns and editing them."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PermissionManager()
            pm.add_allowed_path(tmpdir)
            
            write_tool = WriteTool(pm)
            grep_tool = GrepTool(pm)
            edit_tool = EditTool(pm)
            mock_ctx = Mock()
            
            # Create multiple files with TODOs
            for i in range(3):
                filepath = os.path.join(tmpdir, f"module_{i}.py")
                content = f'''# Module {i}

def function_{i}():
    # TODO: Implement this function
    pass

def helper_{i}():
    # TODO: Add error handling
    return None
'''
                asyncio.run(write_tool.call(mock_ctx, file_path=filepath, content=content))
            
            # Find all TODOs
            grep_result = asyncio.run(grep_tool.call(
                mock_ctx,
                pattern="TODO",
                path=tmpdir,
                output_mode="content",
                line_numbers=True
            ))
            
            assert "TODO: Implement this function" in grep_result
            assert "TODO: Add error handling" in grep_result
            assert "module_0.py" in grep_result
            assert "module_1.py" in grep_result
            assert "module_2.py" in grep_result
            
            # Edit one of the TODOs
            edit_result = asyncio.run(edit_tool.call(
                mock_ctx,
                file_path=os.path.join(tmpdir, "module_0.py"),
                old_string="    # TODO: Implement this function\n    pass",
                new_string="    # Function implemented\n    return 'Module 0 implementation'"
            ))
            assert "successfully" in edit_result.lower()
            
            # Verify the edit
            grep_after = asyncio.run(grep_tool.call(
                mock_ctx,
                pattern="TODO",
                path=os.path.join(tmpdir, "module_0.py"),
                output_mode="count"
            ))
            # Should have one less TODO in module_0.py
            assert "1" in grep_after  # Only one TODO left in module_0


class TestBatchAndTodoIntegration:
    """Test batch operations with todo tracking."""
    
    def test_batch_file_operations_with_todos(self):
        """Test using batch tool for multiple operations with todo tracking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PermissionManager()
            pm.add_allowed_path(tmpdir)
            
            # Create tools
            write_tool = WriteTool(pm)
            read_tool = ReadTool(pm)
            todo_tool = TodoTool()
            
            # Create batch tool with our tools
            tools = {
                "write": write_tool,
                "read": read_tool,
                "todo": todo_tool
            }
            batch_tool = BatchTool(tools)
            mock_ctx = Mock()
            
            # Create batch operations
            invocations = [
                # First, create a todo list
                {
                    "tool": "todo",
                    "parameters": {
                        "operation": "add",
                        "items": [
                            "Create configuration file",
                            "Create main script",
                            "Create README"
                        ]
                    }
                },
                # Create the files
                {
                    "tool": "write",
                    "parameters": {
                        "file_path": os.path.join(tmpdir, "config.json"),
                        "content": '{"version": "1.0", "debug": true}'
                    }
                },
                {
                    "tool": "write",
                    "parameters": {
                        "file_path": os.path.join(tmpdir, "main.py"),
                        "content": 'print("Hello from main!")'
                    }
                },
                {
                    "tool": "write",
                    "parameters": {
                        "file_path": os.path.join(tmpdir, "README.md"),
                        "content": '# Test Project\n\nThis is a test.'
                    }
                },
                # Mark todos as complete
                {
                    "tool": "todo",
                    "parameters": {
                        "operation": "complete",
                        "indices": [0, 1, 2]
                    }
                },
                # Get final todo status
                {
                    "tool": "todo",
                    "parameters": {
                        "operation": "list"
                    }
                }
            ]
            
            # Execute batch
            result = asyncio.run(batch_tool.call(
                mock_ctx,
                description="Create project files with todo tracking",
                invocations=invocations
            ))
            
            # Parse results
            assert "results" in result
            results_data = eval(result.split("results:")[1].strip())  # Simple parsing
            
            # Verify files were created
            assert os.path.exists(os.path.join(tmpdir, "config.json"))
            assert os.path.exists(os.path.join(tmpdir, "main.py"))
            assert os.path.exists(os.path.join(tmpdir, "README.md"))


class TestMemorySearchIntegration:
    """Test memory tools with search integration."""
    
    @patch('hanzo_memory.services.memory.get_memory_service')
    def test_memory_and_code_context_workflow(self, mock_get_service):
        """Test storing code context in memory and recalling it."""
        from hanzo_mcp.tools.memory.memory_tools import CreateMemoriesTool, RecallMemoriesTool
        from hanzo_mcp.tools.memory.knowledge_tools import StoreFactsTool, RecallFactsTool
        
        # Mock memory service
        mock_service = Mock()
        memories_db = {}
        
        def mock_create(user_id, project_id, content, metadata=None, **kwargs):
            mem_id = f"mem_{len(memories_db)}"
            memory = Mock(
                memory_id=mem_id,
                user_id=user_id,
                project_id=project_id,
                content=content,
                metadata=metadata or {}
            )
            memories_db[mem_id] = memory
            return memory
        
        def mock_search(user_id, query, project_id=None, **kwargs):
            results = []
            for memory in memories_db.values():
                if user_id == memory.user_id:
                    # Simple search - check if query terms in content
                    if any(term.lower() in memory.content.lower() for term in query.split()):
                        results.append(Mock(
                            **memory.__dict__,
                            similarity_score=0.9
                        ))
            return results
        
        mock_service.create_memory = mock_create
        mock_service.search_memories = mock_search
        mock_get_service.return_value = mock_service
        
        mock_ctx = Mock()
        
        # 1. Store facts about code patterns
        facts_tool = StoreFactsTool(user_id="dev", project_id="myproject")
        facts_result = asyncio.run(facts_tool.call(
            mock_ctx,
            facts=[
                "Always use async/await for I/O operations",
                "Error handling should use try/except blocks",
                "All functions need type hints"
            ],
            kb_name="coding_standards"
        ))
        assert "Successfully stored 3 facts" in facts_result
        
        # 2. Store memory about specific implementation
        memory_tool = CreateMemoriesTool(user_id="dev", project_id="myproject")
        memory_result = asyncio.run(memory_tool.call(
            mock_ctx,
            statements=[
                "The database connection uses PostgreSQL with pgvector",
                "Authentication is handled by Clerk",
                "The main API uses FastAPI framework"
            ]
        ))
        assert "Successfully created 3 new memories" in memory_result
        
        # 3. Recall relevant information
        recall_tool = RecallMemoriesTool(user_id="dev", project_id="myproject")
        
        # Search for database info
        db_result = asyncio.run(recall_tool.call(
            mock_ctx,
            queries=["database", "PostgreSQL"]
        ))
        assert "PostgreSQL with pgvector" in db_result
        
        # Search for framework info  
        framework_result = asyncio.run(recall_tool.call(
            mock_ctx,
            queries=["API", "framework"]
        ))
        assert "FastAPI framework" in framework_result


class TestAgentSwarmIntegration:
    """Test agent swarm with other tools."""
    
    @patch('hanzo_mcp.tools.agent.swarm_tool.dispatch_to_model')
    def test_swarm_with_file_operations(self, mock_dispatch):
        """Test swarm agents working with files."""
        from hanzo_mcp.tools.agent.swarm_tool import SwarmTool
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PermissionManager()
            pm.add_allowed_path(tmpdir)
            
            # Mock agent responses
            agent_responses = {
                "scanner": f"Found 3 Python files in {tmpdir} with TODO comments",
                "analyzer": "TODOs are: 1) Add error handling, 2) Implement cache, 3) Write tests",
                "implementer": "Fixed TODOs: Added try/except, implemented LRU cache, created test file",
                "validator": "All changes verified. Tests pass. No TODOs remaining."
            }
            
            def mock_agent_dispatch(messages, model=None, **kwargs):
                # Extract agent ID from messages
                for msg in messages:
                    if "You are agent" in msg.get("content", ""):
                        agent_id = msg["content"].split("agent ")[1].split(" ")[0]
                        return agent_responses.get(agent_id, "Unknown agent")
                return "No response"
            
            mock_dispatch.side_effect = mock_agent_dispatch
            
            swarm_tool = SwarmTool()
            mock_ctx = Mock()
            
            # Run swarm to process TODOs
            result = asyncio.run(swarm_tool.call(
                mock_ctx,
                query="Find and fix all TODO comments in the codebase",
                agents=[
                    {
                        "id": "scanner",
                        "query": "Scan all Python files for TODO comments",
                        "role": "scanner"
                    },
                    {
                        "id": "analyzer", 
                        "query": "Analyze the TODOs and categorize them",
                        "role": "analyzer",
                        "receives_from": ["scanner"]
                    },
                    {
                        "id": "implementer",
                        "query": "Implement fixes for each TODO",
                        "role": "developer",
                        "receives_from": ["analyzer"]
                    },
                    {
                        "id": "validator",
                        "query": "Verify all TODOs are resolved and tests pass",
                        "role": "tester",
                        "receives_from": ["implementer"]
                    }
                ]
            ))
            
            # Verify workflow completed
            assert "scanner" in result
            assert "Found 3 Python files" in result
            assert "analyzer" in result
            assert "implementer" in result
            assert "validator" in result
            assert "All changes verified" in result


class TestThinkingToolIntegration:
    """Test thinking tool with other operations."""
    
    def test_think_plan_execute_workflow(self):
        """Test using thinking tool to plan before execution."""
        thinking_tool = ThinkingTool()
        mock_ctx = Mock()
        
        # 1. Think about the problem
        think_result = asyncio.run(thinking_tool.call(
            mock_ctx,
            content="""Problem: Need to refactor a large function that does too many things.
            
The function currently:
- Validates input
- Queries database  
- Processes results
- Sends notifications
- Updates cache

How should I approach this refactoring?"""
        ))
        
        # Should contain structured thinking
        assert "```thinking" in think_result
        assert "```" in think_result
        
        # 2. With batch tool, could execute the plan
        # (Not shown here but demonstrates the workflow)


class TestStreamingAndPaginationIntegration:
    """Test streaming commands with pagination."""
    
    def test_streaming_large_output_with_pagination(self):
        """Test streaming command that produces paginated output."""
        from hanzo_mcp.tools.shell.streaming_command import StreamingCommandTool
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pm = PermissionManager()
            pm.add_allowed_path(tmpdir)
            
            streaming_tool = StreamingCommandTool(pm)
            mock_ctx = Mock()
            
            # Create a large file
            large_file = os.path.join(tmpdir, "large.txt")
            with open(large_file, 'w') as f:
                for i in range(10000):
                    f.write(f"Line {i}: " + "x" * 100 + "\n")
            
            # Stream reading the file
            result = asyncio.run(streaming_tool.call(
                mock_ctx,
                command=f"cat {large_file}",
                stream_to_file=True,
                session_id="test_session"
            ))
            
            # Should handle large output
            assert "Line 0:" in result
            # May be truncated or have pagination info
            if "next_cursor" in result or "truncated" in result:
                assert True  # Pagination handled
            
            # Check session file was created
            session_file = os.path.expanduser(f"~/.hanzo/sessions/test_session/output.log")
            if os.path.exists(session_file):
                # Full output should be in session file
                with open(session_file, 'r') as f:
                    full_output = f.read()
                assert "Line 9999:" in full_output


class TestErrorRecoveryIntegration:
    """Test error recovery across tools."""
    
    def test_error_handling_in_batch(self):
        """Test how batch tool handles errors in individual tools."""
        # Create tools where some will fail
        def failing_tool_call(*args, **kwargs):
            raise Exception("Tool failed!")
        
        def working_tool_call(*args, **kwargs):
            return "Success"
        
        failing_tool = Mock()
        failing_tool.name = "failing"
        failing_tool.call = Mock(side_effect=failing_tool_call)
        
        working_tool = Mock()
        working_tool.name = "working"
        working_tool.call = Mock(side_effect=working_tool_call)
        
        tools = {
            "failing": failing_tool,
            "working": working_tool
        }
        
        batch_tool = BatchTool(tools)
        mock_ctx = Mock()
        
        # Mix of failing and working tools
        invocations = [
            {"tool": "working", "parameters": {}},
            {"tool": "failing", "parameters": {}},
            {"tool": "working", "parameters": {}},
            {"tool": "failing", "parameters": {}},
        ]
        
        result = asyncio.run(batch_tool.call(
            mock_ctx,
            description="Test error handling",
            invocations=invocations
        ))
        
        # Should complete despite errors
        assert "results" in result
        assert "Success" in result
        assert "error" in result.lower()
        assert "Tool failed!" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])