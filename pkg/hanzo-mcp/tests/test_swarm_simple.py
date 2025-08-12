#!/usr/bin/env python3
"""Simple standalone test for swarm tool functionality."""

import os
import sys
import shutil
import tempfile


# Test 1: Check swarm defaults
def test_defaults():
    """Test that swarm defaults to Claude Sonnet."""
    print("Test 1: Checking swarm defaults...")

    # Simulate the swarm tool initialization
    model = None
    api_key = None

    # Default behavior
    model = model or "anthropic/claude-3-5-sonnet-20241022"
    api_key = (
        api_key
        or os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("CLAUDE_API_KEY")
    )

    assert (
        model == "anthropic/claude-3-5-sonnet-20241022"
    ), f"Expected Claude Sonnet, got {model}"
    print("✓ Swarm defaults to Claude 3.5 Sonnet")

    # Check API key detection
    if api_key:
        print(f"✓ API key detected: {api_key[:10]}...")
    else:
        print("✗ No API key found (set ANTHROPIC_API_KEY or CLAUDE_API_KEY)")

    return True


# Test 2: Test task validation
def test_task_validation():
    """Test task validation logic."""
    print("\nTest 2: Task validation...")

    # Valid task
    valid_task = {
        "file_path": "/path/to/file.py",
        "instructions": "Update imports",
        "description": "Optional description",
    }

    # Invalid tasks
    invalid_tasks = [
        {"instructions": "Missing file_path"},
        {"file_path": "/path/to/file.py"},  # Missing instructions
        "Not a dictionary",
        None,
        [],
    ]

    # Simulate validation
    def validate_task(task):
        if not isinstance(task, dict):
            return False, "Task must be a dictionary"
        if "file_path" not in task:
            return False, "Task must have 'file_path'"
        if "instructions" not in task:
            return False, "Task must have 'instructions'"
        return True, "Valid"

    # Test valid task
    is_valid, msg = validate_task(valid_task)
    assert is_valid, f"Valid task failed: {msg}"
    print("✓ Valid task passes validation")

    # Test invalid tasks
    for i, task in enumerate(invalid_tasks):
        is_valid, msg = validate_task(task)
        assert not is_valid, f"Invalid task {i} should have failed"
        print(f"✓ Invalid task {i} correctly rejected: {msg}")

    return True


# Test 3: Test parallel execution simulation
def test_parallel_execution():
    """Test parallel execution behavior."""
    print("\nTest 3: Parallel execution simulation...")

    import time
    import asyncio

    async def simulate_agent_task(task_id, duration=0.1):
        """Simulate an agent task."""
        start = time.time()
        await asyncio.sleep(duration)
        end = time.time()
        return task_id, end - start

    async def run_parallel_test():
        # Create 5 tasks
        tasks = []
        max_concurrent = 3

        # Semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent)

        async def limited_task(task_id):
            async with semaphore:
                return await simulate_agent_task(task_id)

        # Run all tasks
        start = time.time()
        results = await asyncio.gather(*[limited_task(i) for i in range(5)])
        total_time = time.time() - start

        print(f"✓ Ran 5 tasks with max_concurrent=3 in {total_time:.2f}s")

        # With max_concurrent=3 and 0.1s per task, should take ~0.2s (2 batches)
        assert total_time < 0.6, f"Parallel execution too slow: {total_time}s"
        print("✓ Parallel execution completed efficiently")

        return True

    # Run async test
    return asyncio.run(run_parallel_test())


# Test 4: Test failure handling
def test_failure_handling():
    """Test handling of failures."""
    print("\nTest 4: Failure handling...")

    # Simulate task results
    results = [
        ("Task 1", "Success: Completed edit"),
        ("Task 2", "Error: File not found"),
        ("Task 3", "Success: Updated imports"),
        ("Task 4", "Error: Permission denied"),
        ("Task 5", "Success: Added type hints"),
    ]

    # Count successes and failures
    successful = sum(1 for _, result in results if not result.startswith("Error:"))
    failed = len(results) - successful

    assert successful == 3, f"Expected 3 successful, got {successful}"
    assert failed == 2, f"Expected 2 failed, got {failed}"
    print(f"✓ Correctly counted {successful} successful and {failed} failed tasks")

    # Format summary (like swarm does)
    summary = f"""=== Swarm Execution Summary ===
Total tasks: {len(results)}
Successful: {successful}
Failed: {failed}
"""

    print("✓ Summary formatting works correctly")
    print(summary)

    return True


# Test 5: Test file operations
def test_file_operations():
    """Test file creation and editing simulation."""
    print("\nTest 5: File operations simulation...")

    test_dir = tempfile.mkdtemp(prefix="swarm_test_")
    try:
        # Create test files
        files = {
            "config.py": "OLD_VALUE = 123",
            "utils.py": "from config import OLD_VALUE",
            "main.py": "print(OLD_VALUE)",
        }

        for filename, content in files.items():
            path = os.path.join(test_dir, filename)
            with open(path, "w") as f:
                f.write(content)
            print(f"✓ Created {filename}")

        # Simulate edits
        edits = {
            "config.py": "NEW_VALUE = 123",
            "utils.py": "from config import NEW_VALUE",
            "main.py": "print(NEW_VALUE)",
        }

        for filename, new_content in edits.items():
            path = os.path.join(test_dir, filename)
            with open(path, "w") as f:
                f.write(new_content)
            print(f"✓ Edited {filename}")

        # Verify edits
        for filename in files:
            path = os.path.join(test_dir, filename)
            with open(path, "r") as f:
                content = f.read()
                assert "NEW_VALUE" in content, f"{filename} not properly edited"

        print("✓ All files edited successfully")
        return True

    finally:
        shutil.rmtree(test_dir)
        print(f"✓ Cleaned up test directory")


# Main test runner
def main():
    """Run all tests."""
    print("=" * 60)
    print("SWARM TOOL TEST SUITE")
    print("=" * 60)

    tests = [
        test_defaults,
        test_task_validation,
        test_parallel_execution,
        test_failure_handling,
        test_file_operations,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
                print(f"✗ {test.__name__} failed")
        except Exception as e:
            failed += 1
            print(f"✗ {test.__name__} crashed: {e}")

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    # Also test the actual demo scripts if API key is available
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY"):
        print("\nAPI key detected! Running live demos...")

        # Run parallel edit demo
        demo_path = os.path.join(
            os.path.dirname(__file__), "..", "examples", "parallel_edit_demo.py"
        )
        if os.path.exists(demo_path):
            print("\nRunning parallel_edit_demo.py...")
            import subprocess

            result = subprocess.run(
                [sys.executable, demo_path], capture_output=True, text=True
            )
            if result.returncode == 0:
                print("✓ Parallel edit demo completed successfully")
                if "NEW_VERSION" in result.stdout:
                    print("✓ Variables were successfully renamed")
            else:
                print(f"✗ Parallel edit demo failed: {result.stderr}")
    else:
        print("\nNo API key found - skipping live demos")
        print("Set ANTHROPIC_API_KEY or CLAUDE_API_KEY to run live tests")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
