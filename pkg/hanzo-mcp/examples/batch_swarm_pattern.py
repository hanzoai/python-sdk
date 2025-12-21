#!/usr/bin/env python3
"""Example: Batch + Swarm Pattern for 10-100x Performance Gains

This example demonstrates the powerful pattern of:
1. Using batch tool for rapid parallel analysis
2. Using swarm tool for parallel fixes based on analysis
3. Achieving massive performance gains for complex refactoring
"""

import json
import asyncio
from typing import Any, Dict, List

# This example shows the pattern - in real usage you'd import the actual tools
# from hanzo_mcp.tools.agent.swarm_tool import SwarmTool
# from hanzo_mcp.tools.common.batch_tool import BatchTool


async def batch_analyze_codebase(project_path: str) -> Dict[str, Any]:
    """Step 1: Use batch tool for rapid parallel analysis.

    Batch tool runs multiple operations in parallel:
    - grep for patterns
    - read multiple files
    - analyze directory structure
    - search for specific code patterns
    """

    # Example batch tasks for analyzing a Go project with import issues
    batch_tasks = [
        {
            "tool_name": "grep",
            "input": {
                "pattern": "undefined: (\\w+)",
                "path": project_path,
                "include": "*.go",
            },
        },
        {
            "tool_name": "grep",
            "input": {
                "pattern": "^package (\\w+)",
                "path": project_path,
                "include": "*.go",
            },
        },
        {
            "tool_name": "grep",
            "input": {
                "pattern": "^import \\(",
                "path": project_path,
                "include": "*.go",
                "-A": 10,  # Get 10 lines after to see full import block
            },
        },
        {"tool_name": "tree", "input": {"path": project_path, "depth": 3}},
    ]

    print(f"Running {len(batch_tasks)} analysis tasks in parallel...")

    # In real usage:
    # results = await batch_tool.call(ctx, tasks=batch_tasks)

    # Simulated results for example
    results = {
        "results": [
            {
                "status": "success",
                "output": """
vms/xvm/network/atomic.go:18: undefined: common
vms/xvm/network/network.go:25: undefined: common
vms/xvm/network/gossip.go:55: undefined: common
""",
            },
            {
                "status": "success",
                "output": """
vms/xvm/network/atomic.go:1: package network
vms/xvm/network/network.go:1: package network
vms/xvm/network/gossip.go:1: package network
""",
            },
            {"status": "success", "output": "Import blocks found in 15 files..."},
            {"status": "success", "output": "Directory structure analyzed..."},
        ],
        "completed": 4,
        "failed": 0,
        "total_time": 0.5,  # Batch runs all in parallel!
    }

    print(f"Analysis complete in {results['total_time']}s")
    return results


def generate_swarm_tasks_from_analysis(analysis: Dict[str, Any]) -> List[Dict]:
    """Step 2: Generate targeted swarm tasks based on batch analysis."""

    # Parse the analysis results to identify files needing fixes
    undefined_errors = analysis["results"][0]["output"]

    files_to_fix = set()
    for line in undefined_errors.strip().split("\n"):
        if ":" in line and "undefined:" in line:
            file_path = line.split(":")[0]
            files_to_fix.add(file_path)

    # Generate a swarm task for each file
    tasks = []
    for file_path in sorted(files_to_fix):
        task = {
            "file": file_path,
            "instruction": f"""Fix undefined symbol errors in {file_path}:

1. Read the file to understand current imports
2. Add missing import "github.com/luxfi/node/common"
3. Use multi_edit to:
   - Add the import in the correct location
   - Ensure proper formatting
   - Handle both single import and import block cases
4. Verify the file compiles after changes

Use multi_edit for atomic changes!""",
        }
        tasks.append(task)

    return tasks


async def execute_parallel_fixes(tasks: List[Dict], max_concurrency: int = 10):
    """Step 3: Execute all fixes in parallel using swarm."""

    print(f"\nExecuting {len(tasks)} file fixes in parallel...")
    print(f"Max concurrency: {max_concurrency}")

    # In real usage:
    # results = await swarm_tool.call(ctx, tasks=tasks, max_concurrency=max_concurrency)

    # Simulated results for example
    start_time = asyncio.get_event_loop().time()
    await asyncio.sleep(0.5)  # Simulate parallel execution
    end_time = asyncio.get_event_loop().time()

    results = {
        "results": [
            {
                "task_index": i,
                "status": "completed",
                "agent_output": f"Fixed {tasks[i]['file']}",
            }
            for i in range(len(tasks))
        ],
        "completed": len(tasks),
        "failed": 0,
        "total_time": end_time - start_time,
    }

    return results


async def demonstrate_performance_gains():
    """Demonstrate the performance gains from batch + swarm pattern."""

    print("BATCH + SWARM PATTERN DEMONSTRATION")
    print("=" * 60)

    # Simulate a large project
    num_files = 50

    print(f"\nScenario: Fix undefined imports in {num_files} Go files")
    print("\nApproach 1: Sequential (Traditional)")
    print("-" * 40)

    # Sequential approach
    sequential_time_per_file = 2.0  # Read, analyze, fix
    sequential_total = num_files * sequential_time_per_file

    print(f"Time per file: {sequential_time_per_file}s")
    print(f"Total time: {sequential_total}s ({sequential_total / 60:.1f} minutes)")

    print("\nApproach 2: Batch + Swarm (Parallel)")
    print("-" * 40)

    # Parallel approach
    batch_analysis_time = 0.5  # All analysis in parallel
    swarm_fix_time = 2.0  # All fixes in parallel (limited by slowest)
    parallel_total = batch_analysis_time + swarm_fix_time

    print(f"Batch analysis (all files): {batch_analysis_time}s")
    print(f"Swarm fixes (all parallel): {swarm_fix_time}s")
    print(f"Total time: {parallel_total}s")

    speedup = sequential_total / parallel_total
    print(f"\nSPEEDUP: {speedup:.1f}x faster!")
    print(f"Time saved: {sequential_total - parallel_total}s ({(sequential_total - parallel_total) / 60:.1f} minutes)")

    print("\n" + "=" * 60)
    print("KEY INSIGHTS:")
    print("=" * 60)
    print(
        """
1. Batch Tool Benefits:
   - Runs multiple analysis operations in parallel
   - Gathers context from entire codebase quickly
   - Identifies patterns and dependencies

2. Swarm Tool Benefits:
   - Fixes multiple files in parallel
   - Each agent has focused context (one file)
   - Multi-edit ensures atomic changes

3. Combined Pattern:
   - Batch: 0.5s to analyze 50+ files
   - Swarm: 2s to fix all files (parallel)
   - Total: 2.5s vs 100s sequential = 40x speedup!

4. Scalability:
   - 10 files: ~10x speedup
   - 50 files: ~40x speedup
   - 100 files: ~50x speedup
   - 1000 files: ~100x speedup!
"""
    )


async def real_world_example():
    """Show a real-world example of the pattern."""

    print("\n" + "=" * 60)
    print("REAL WORLD EXAMPLE: Refactoring Entire Codebase")
    print("=" * 60)

    print(
        """
Task: Update all deprecated API calls across 500 files

Step 1: Batch Analysis (0.5s)
"""
    )

    batch_config = {
        "description": "Analyze deprecated API usage",
        "invocations": [
            {
                "tool_name": "grep",
                "input": {
                    "pattern": "OldAPI\\.\\w+\\(",
                    "path": "/project",
                    "include": "*.go",
                },
            },
            {
                "tool_name": "grep_ast",
                "input": {"pattern": "OldAPI", "path": "/project"},
            },
            {
                "tool_name": "grep",
                "input": {"pattern": "import.*OldAPI", "path": "/project"},
            },
        ],
    }

    print(f"Batch tasks: {json.dumps(batch_config, indent=2)}")

    print(
        """
Step 2: Generate Swarm Tasks (instant)
- Parse batch results
- Create targeted fix task for each file
- Include specific instructions based on usage pattern

Step 3: Swarm Execution (2-3s for all files!)
"""
    )

    swarm_tasks_example = [
        {
            "file": "user_service.go",
            "instruction": "Replace OldAPI.GetUser() with NewAPI.User.Get() using multi_edit",
        },
        {
            "file": "auth_handler.go",
            "instruction": "Replace OldAPI.Authenticate() with NewAPI.Auth.Verify() using multi_edit",
        },
        # ... 498 more tasks
    ]

    print(f"Swarm tasks (first 2 of 500): {json.dumps(swarm_tasks_example, indent=2)}")

    print(
        """
Results:
- Sequential approach: 500 files × 3s = 1500s (25 minutes)
- Batch + Swarm: 0.5s + 3s = 3.5s total
- Speedup: 428x faster!
- Developer time saved: 24.9 minutes
"""
    )


async def main():
    """Run all examples."""

    # Example 1: Basic batch + swarm workflow
    project_path = "/path/to/project"

    print("EXAMPLE 1: Basic Workflow")
    print("=" * 60)

    # Step 1: Analyze
    analysis = await batch_analyze_codebase(project_path)

    # Step 2: Generate tasks
    tasks = generate_swarm_tasks_from_analysis(analysis)
    print(f"\nGenerated {len(tasks)} swarm tasks from analysis")

    # Step 3: Fix in parallel
    results = await execute_parallel_fixes(tasks, max_concurrency=10)
    print(f"Fixed {results['completed']} files in {results['total_time']}s")

    # Example 2: Performance comparison
    await demonstrate_performance_gains()

    # Example 3: Real world use case
    await real_world_example()


if __name__ == "__main__":
    print("Batch + Swarm Pattern for 10-100x Performance Gains")
    print("=" * 60)
    print("\nThis pattern combines:")
    print("- Batch tool for parallel analysis")
    print("- Swarm tool for parallel execution")
    print("- Result: Massive performance gains!")
    print("\nRunning examples...\n")

    asyncio.run(main())
