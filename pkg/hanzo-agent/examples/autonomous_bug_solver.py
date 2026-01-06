#!/usr/bin/env python3
"""
Autonomous Bug Solver - Advanced Multi-Agent Example

This example demonstrates building an autonomous bug-solving system using
Hanzo Agent SDK's network and orchestration features. Inspired by AgentKit's
guided tour, this shows how multiple specialized agents can work together
to understand, diagnose, and fix bugs in code.
"""

import asyncio
from typing import Dict, Any, List
import os

from agents import Agent, create_network, create_workflow, Step
from agents.routers import SemanticRouter, RuleBasedRouter, RoutingStrategy
from agents.state import InMemoryStateStore
from agents.memory import MemoryManager, VectorMemoryStore
from agents.tools import function_tool, create_composite_tool
from agents.models import HanzoModelProvider

# Configure Hanzo backend
HANZO_ROUTER_URL = os.getenv("HANZO_ROUTER_URL", "http://localhost:4000/v1")
HANZO_API_KEY = os.getenv("HANZO_API_KEY", "sk-1234")

# Initialize model provider
model_provider = HanzoModelProvider(HANZO_ROUTER_URL, HANZO_API_KEY)


# ==================== Tools ====================

@function_tool
async def read_file(file_path: str) -> str:
    """Read a file from the filesystem."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


@function_tool
async def write_file(file_path: str, content: str) -> str:
    """Write content to a file."""
    try:
        # Create backup first
        if os.path.exists(file_path):
            backup_path = f"{file_path}.backup"
            with open(file_path, 'r') as f:
                backup_content = f.read()
            with open(backup_path, 'w') as f:
                f.write(backup_content)
        
        with open(file_path, 'w') as f:
            f.write(content)
        return f"File written successfully to {file_path}"
    except Exception as e:
        return f"Error writing file: {e}"


@function_tool
async def run_tests(test_command: str = "pytest") -> Dict[str, Any]:
    """Run tests and return results."""
    import subprocess
    try:
        result = subprocess.run(
            test_command.split(),
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@function_tool
async def analyze_stack_trace(error_text: str) -> Dict[str, Any]:
    """Analyze a stack trace to identify the error location and type."""
    lines = error_text.split('\n')
    
    # Simple parser - in production use proper parsing
    error_info = {
        "error_type": None,
        "error_message": None,
        "file_path": None,
        "line_number": None,
        "function_name": None
    }
    
    for i, line in enumerate(lines):
        if "File " in line and "line " in line:
            # Extract file path and line number
            parts = line.split('"')
            if len(parts) >= 2:
                error_info["file_path"] = parts[1]
                
            if "line " in line:
                line_parts = line.split("line ")
                if len(line_parts) >= 2:
                    error_info["line_number"] = line_parts[1].split(",")[0].strip()
                    
        if i < len(lines) - 1 and not lines[i+1].startswith(" "):
            # This might be the error type and message
            if "Error" in line or "Exception" in line:
                parts = line.split(":", 1)
                if len(parts) >= 2:
                    error_info["error_type"] = parts[0].strip()
                    error_info["error_message"] = parts[1].strip()
    
    return error_info


@function_tool
async def search_codebase(pattern: str, file_types: List[str] = None) -> List[Dict[str, Any]]:
    """Search codebase for specific patterns."""
    import os
    import re
    
    if file_types is None:
        file_types = ['.py', '.js', '.ts', '.java', '.go']
    
    results = []
    
    for root, dirs, files in os.walk('.'):
        # Skip hidden directories and common ignore patterns
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
        
        for file in files:
            if any(file.endswith(ft) for ft in file_types):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        matches = list(re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE))
                        if matches:
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                results.append({
                                    "file": file_path,
                                    "line": line_num,
                                    "match": match.group(),
                                    "context": content.split('\n')[line_num-1]
                                })
                except:
                    pass
    
    return results


# Composite tool for automated fixing
fix_and_test = create_composite_tool(
    name="fix_and_test",
    tools=[write_file, run_tests],
    description="Apply a fix and immediately run tests"
)


# ==================== Agents ====================

# Bug Analyzer Agent
bug_analyzer = Agent(
    name="BugAnalyzer",
    instructions="""You are an expert at analyzing bugs and errors in code.
    Your role is to:
    1. Analyze error messages and stack traces
    2. Identify the root cause of issues
    3. Determine the scope and impact of bugs
    4. Suggest investigation strategies
    
    Be thorough and systematic in your analysis.""",
    tools=[analyze_stack_trace, read_file, search_codebase],
    model="gpt-4"
)

# Code Reader Agent
code_reader = Agent(
    name="CodeReader",
    instructions="""You are an expert at reading and understanding code.
    Your role is to:
    1. Read relevant code files
    2. Understand code structure and dependencies
    3. Identify potential problem areas
    4. Explain code functionality clearly
    
    Focus on understanding the code's intent and implementation.""",
    tools=[read_file, search_codebase],
    model="gpt-3.5-turbo"  # Faster for simple reading tasks
)

# Solution Designer Agent
solution_designer = Agent(
    name="SolutionDesigner",
    instructions="""You are an expert software architect and problem solver.
    Your role is to:
    1. Design solutions for identified bugs
    2. Consider multiple approaches
    3. Evaluate trade-offs
    4. Propose the best fix strategy
    
    Think about edge cases, performance, and maintainability.""",
    tools=[read_file],
    model="gpt-4"
)

# Code Fixer Agent
code_fixer = Agent(
    name="CodeFixer",
    instructions="""You are an expert at implementing bug fixes.
    Your role is to:
    1. Implement the proposed solutions
    2. Write clean, maintainable code
    3. Add appropriate error handling
    4. Update related code if needed
    
    Always test your fixes and handle edge cases.""",
    tools=[read_file, write_file, fix_and_test],
    model="gpt-4"
)

# Test Writer Agent
test_writer = Agent(
    name="TestWriter",
    instructions="""You are an expert at writing comprehensive tests.
    Your role is to:
    1. Write tests that cover the bug fix
    2. Add edge case tests
    3. Ensure regression prevention
    4. Follow testing best practices
    
    Write clear, maintainable tests with good coverage.""",
    tools=[read_file, write_file, run_tests],
    model="gpt-3.5-turbo"
)

# Quality Reviewer Agent
quality_reviewer = Agent(
    name="QualityReviewer",
    instructions="""You are a senior engineer reviewing code changes.
    Your role is to:
    1. Review the implemented fix
    2. Check for potential issues
    3. Verify tests are adequate
    4. Ensure code quality standards
    
    Be constructive but thorough in your review.""",
    tools=[read_file, run_tests],
    model="gpt-4"
)


# ==================== Network Setup ====================

# Create memory stores for agents
memory_store = VectorMemoryStore(collection_name="bug_solver_memory")

# Set up routers
semantic_router = SemanticRouter(similarity_threshold=0.7)

rule_router = RuleBasedRouter()
rule_router.add_rule(r".*error.*|.*exception.*|.*trace.*", "BugAnalyzer")
rule_router.add_rule(r".*read.*|.*understand.*|.*explain.*", "CodeReader")
rule_router.add_rule(r".*design.*|.*approach.*|.*solution.*", "SolutionDesigner")
rule_router.add_rule(r".*fix.*|.*implement.*|.*patch.*", "CodeFixer")
rule_router.add_rule(r".*test.*|.*coverage.*", "TestWriter")
rule_router.add_rule(r".*review.*|.*quality.*|.*check.*", "QualityReviewer")

# Composite router with both strategies
main_router = RoutingStrategy([
    (rule_router, 0.7),
    (semantic_router, 0.3)
])

# Create the network
bug_solver_network = create_network(
    agents=[
        bug_analyzer,
        code_reader,
        solution_designer,
        code_fixer,
        test_writer,
        quality_reviewer
    ],
    router=main_router,
    state_store=InMemoryStateStore(),
    model_provider=model_provider,
    memory_manager=MemoryManager(store=memory_store),
    default_model="gpt-4"
)


# ==================== Workflow ====================

# Define the bug-solving workflow
bug_solving_workflow = create_workflow(
    name="Autonomous Bug Solver",
    agents=bug_solver_network.agents,
    steps=[
        # 1. Initial Analysis
        Step.agent("BugAnalyzer", "Analyze the error: {error_message}"),
        
        # 2. Parallel investigation
        Step.parallel([
            Step.agent("CodeReader", "Read and understand {error_info.file_path}"),
            Step.agent("CodeReader", "Search for related code using {error_info.function_name}")
        ]),
        
        # 3. Design solution
        Step.agent("SolutionDesigner", "Design a fix based on the analysis"),
        
        # 4. Implementation
        Step.agent("CodeFixer", "Implement the proposed solution"),
        
        # 5. Testing
        Step.parallel([
            Step.agent("TestWriter", "Write tests for the fix"),
            Step.agent("CodeFixer", "Run existing tests to verify the fix")
        ]),
        
        # 6. Review
        Step.agent("QualityReviewer", "Review the complete fix and tests"),
        
        # 7. Conditional refinement
        Step.conditional(
            condition=lambda state: state.get("review_result", {}).get("needs_revision", False),
            true_step=Step.loop(
                steps=[
                    Step.agent("CodeFixer", "Address review feedback: {review_feedback}"),
                    Step.agent("QualityReviewer", "Re-review the changes")
                ],
                max_iterations=3,
                break_condition=lambda state: not state.get("review_result", {}).get("needs_revision", True)
            ),
            false_step=Step.transform(lambda x: {"status": "completed", "result": x})
        )
    ],
    enable_streaming=True
)


# ==================== Main Example ====================

async def solve_bug(error_message: str, context: Dict[str, Any] = None):
    """Autonomously solve a bug given an error message."""
    
    print(f"🐛 Autonomous Bug Solver Started")
    print(f"{'='*60}")
    print(f"Error: {error_message}")
    print(f"{'='*60}\n")
    
    # Initialize context
    if context is None:
        context = {}
    
    context["error_message"] = error_message
    
    # Stream handler for real-time updates
    async def stream_handler(event):
        agent_name = event.data.get("agent", "System")
        message = event.data.get("message", "")
        
        if event.type == "agent_start":
            print(f"\n🤖 {agent_name}: Starting...")
        elif event.type == "agent_complete":
            print(f"✅ {agent_name}: Complete")
        elif event.type == "tool_call":
            tool_name = event.data.get("tool", "")
            print(f"  🔧 Using tool: {tool_name}")
        elif event.type == "message":
            print(f"  💬 {message}")
    
    # Run the workflow
    result = await bug_solving_workflow.run(
        context,
        stream_callback=stream_handler
    )
    
    # Summary
    print(f"\n{'='*60}")
    print(f"🎉 Bug Solving Complete!")
    print(f"{'='*60}")
    
    if result.get("status") == "completed":
        print(f"✅ Status: Success")
        print(f"📝 Summary: {result.get('result', {}).get('summary', 'Bug fixed successfully')}")
        
        # Show memory insights
        memories = await bug_solver_network.memory_manager.search("bug fix", limit=3)
        if memories:
            print(f"\n💡 Learned from this experience:")
            for memory in memories:
                print(f"  - {memory.content}")
    else:
        print(f"❌ Status: Failed")
        print(f"📝 Error: {result.get('error', 'Unknown error')}")
    
    return result


# ==================== Example Usage ====================

async def main():
    """Run example bug-solving scenarios."""
    
    # Example 1: Simple syntax error
    print("\n" + "="*80)
    print("Example 1: Solving a Simple Syntax Error")
    print("="*80)
    
    error1 = """
    Traceback (most recent call last):
      File "app.py", line 42, in process_data
        result = calculate_total(items)
      File "utils/calculator.py", line 15, in calculate_total
        total += item.price * item.quantty
    AttributeError: 'Item' object has no attribute 'quantty'
    """
    
    await solve_bug(error1)
    
    # Example 2: Complex logic error
    print("\n" + "="*80)
    print("Example 2: Solving a Complex Logic Error")
    print("="*80)
    
    error2 = """
    Test test_payment_processing failed:
    AssertionError: Payment total mismatch
    Expected: 150.00
    Actual: 135.00
    
    This happens when applying multiple discount codes to an order.
    The discount calculation in checkout.py might not be handling
    overlapping discounts correctly.
    """
    
    await solve_bug(error2, context={
        "test_file": "tests/test_checkout.py",
        "suspected_files": ["checkout.py", "models/discount.py"]
    })
    
    # Show network statistics
    print("\n" + "="*80)
    print("Network Statistics")
    print("="*80)
    
    stats = bug_solver_network.get_statistics()
    for agent_name, agent_stats in stats.items():
        print(f"\n{agent_name}:")
        print(f"  Calls: {agent_stats['total_calls']}")
        print(f"  Avg Duration: {agent_stats['avg_duration']:.2f}ms")
        print(f"  Success Rate: {agent_stats['success_rate']:.1%}")


if __name__ == "__main__":
    asyncio.run(main())