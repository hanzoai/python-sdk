#!/usr/bin/env python3
"""Example: Fix Go import errors in parallel using swarm and batch tools.

This example shows how to achieve 10-100x performance gains when fixing
multiple files with similar errors by using the swarm tool for parallel execution.
"""

import asyncio
import json
import re
from pathlib import Path
from typing import Dict, List, Set

from hanzo_tools.agent.swarm_tool import SwarmTool

from hanzo_mcp.tools.common.permissions import PermissionManager


class GoImportFixer:
    """Fixes Go import errors in parallel using swarm."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.permission_manager = PermissionManager(allowed_paths=[project_root])
        self.swarm = SwarmTool(self.permission_manager)

    def parse_go_errors(self, error_output: str) -> Dict[str, Set[str]]:
        """Parse Go compiler errors to find undefined symbols per file.

        Returns:
            Dict mapping file paths to sets of undefined symbols
        """
        file_errors = {}

        # Pattern: filename:line:col: undefined: symbol
        pattern = r"([^:]+\.go):\d+:\d+: undefined: (\w+)"

        for match in re.finditer(pattern, error_output):
            file_path = match.group(1)
            symbol = match.group(2)

            if file_path not in file_errors:
                file_errors[file_path] = set()
            file_errors[file_path].add(symbol)

        return file_errors

    def generate_swarm_tasks(self, file_errors: Dict[str, Set[str]]) -> List[Dict]:
        """Generate swarm tasks for fixing each file in parallel.

        Each task will:
        1. Analyze the file to understand current imports
        2. Determine the correct import path for undefined symbols
        3. Use multi_edit to add all missing imports in one operation
        """
        tasks = []

        for file_path, undefined_symbols in file_errors.items():
            # Create detailed instructions for the agent
            symbols_list = ", ".join(sorted(undefined_symbols))

            instruction = f"""Fix undefined symbols in this Go file: {symbols_list}

Steps:
1. Read the file to understand its current imports and structure
2. Identify the correct import paths for these undefined symbols:
   - If 'common' is undefined, add import "github.com/luxfi/node/common"
   - If 'utils' is undefined, add import "github.com/luxfi/node/utils"
   - For other symbols, determine the appropriate import based on the project structure
3. Use multi_edit to add all missing imports in a single operation:
   - Find the existing import block (or create one after 'package' if none exists)
   - Add the new imports in alphabetical order
   - Ensure proper formatting with tabs/spaces matching the file's style
4. Verify the changes are correct and the file is still valid Go code

IMPORTANT: Use multi_edit for efficiency - add all imports in one operation!
"""

            tasks.append({"file": file_path, "instruction": instruction})

        return tasks

    async def fix_imports_parallel(self, error_output: str, max_concurrency: int = 10):
        """Fix all import errors in parallel using swarm.

        Args:
            error_output: Go compiler error output
            max_concurrency: Maximum number of files to fix simultaneously
        """
        # Parse errors
        file_errors = self.parse_go_errors(error_output)

        if not file_errors:
            print("No undefined symbol errors found.")
            return

        print(f"Found {len(file_errors)} files with undefined symbols")
        for file_path, symbols in file_errors.items():
            print(f"  {file_path}: {', '.join(symbols)}")

        # Generate swarm tasks
        tasks = self.generate_swarm_tasks(file_errors)

        print(f"\nLaunching swarm with {len(tasks)} parallel agents...")
        print(f"Max concurrency: {max_concurrency}")

        # Execute fixes in parallel
        ctx = type("Context", (), {})()  # Mock context for example

        start_time = asyncio.get_event_loop().time()
        result = await self.swarm.call(
            ctx, tasks=tasks, max_concurrency=max_concurrency
        )
        end_time = asyncio.get_event_loop().time()

        # Parse and display results
        results = json.loads(result)

        print(f"\n{'=' * 60}")
        print("SWARM EXECUTION COMPLETE")
        print(f"{'=' * 60}")
        print(f"Total time: {results['total_time']:.2f}s")
        print(f"Actual time: {end_time - start_time:.2f}s")
        print(f"Files processed: {len(tasks)}")
        print(f"Successful: {results['completed']}")
        print(f"Failed: {results['failed']}")

        if results["failed"] > 0:
            print("\nFailed tasks:")
            for r in results["results"]:
                if r["status"] == "failed":
                    print(f"  - {tasks[r['task_index']]['file']}")
                    print(f"    Error: {r.get('error', 'Unknown error')}")

        # Calculate performance gain
        sequential_estimate = len(tasks) * 2.0  # Assume 2s per file sequentially
        parallel_time = results["total_time"]
        speedup = sequential_estimate / parallel_time if parallel_time > 0 else 1

        print("\nPerformance Analysis:")
        print(f"  Sequential estimate: {sequential_estimate:.1f}s")
        print(f"  Parallel actual: {parallel_time:.1f}s")
        print(f"  Speedup: {speedup:.1f}x")
        print(
            f"  Efficiency: {(speedup / min(max_concurrency, len(tasks))) * 100:.1f}%"
        )


async def main():
    """Example usage with the error output from the user's message."""

    error_output = """
# github.com/luxfi/node/vms/xvm/network
vms/xvm/network/atomic.go:18:2: undefined: common
vms/xvm/network/atomic.go:20:6: undefined: common
vms/xvm/network/atomic.go:24:23: undefined: common
vms/xvm/network/atomic.go:27:18: undefined: common
vms/xvm/network/atomic.go:54:10: undefined: common
vms/xvm/network/atomic.go:101:10: undefined: common
vms/xvm/network/atomic.go:140:24: undefined: common
vms/xvm/network/network.go:25:4: undefined: common
vms/xvm/network/network.go:35:12: undefined: common
vms/xvm/network/gossip.go:55:13: undefined: common
vms/xvm/network/network.go:25:4: too many errors
"""

    # Initialize fixer with project root
    # In real usage, this would be the actual project path
    fixer = GoImportFixer("/path/to/luxfi/node")

    # Fix all imports in parallel
    # Using max_concurrency=3 since we have 3 files
    # Could use higher values for larger projects
    await fixer.fix_imports_parallel(error_output, max_concurrency=3)

    print("\n" + "=" * 60)
    print("EXAMPLE: Using Batch + Swarm for Complex Analysis")
    print("=" * 60)

    # Example of combining batch for analysis + swarm for fixes
    print(
        """
# Step 1: Use batch tool for rapid analysis across all files
batch_tasks = [
    {"tool": "grep", "args": {"pattern": "undefined: common", "path": "vms/"}},
    {"tool": "grep", "args": {"pattern": "^package", "path": "vms/"}},
    {"tool": "grep", "args": {"pattern": "^import", "path": "vms/"}}
]

# Step 2: Analyze results to understand import patterns

# Step 3: Use swarm for parallel fixes with context from batch analysis
swarm_tasks = generate_informed_tasks(batch_results)

# This combination provides:
# - Batch: Fast whole-codebase analysis (100+ files in seconds)
# - Swarm: Parallel fixes with full context per file
# - Result: 10-100x speedup vs sequential processing
"""
    )


if __name__ == "__main__":
    print("Go Import Fixer - Swarm Parallel Execution Example")
    print("=" * 60)
    print("\nThis example demonstrates how to:")
    print("1. Parse Go compiler errors")
    print("2. Generate parallel fix tasks for each file")
    print("3. Use swarm to fix all files simultaneously")
    print("4. Achieve 10-100x performance gains")
    print("\nKey insight: Each file is independent, so they can be fixed in parallel!")
    print("=" * 60)

    # Run the example
    asyncio.run(main())
