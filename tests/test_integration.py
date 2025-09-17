#!/usr/bin/env python3
"""
Comprehensive integration test for Hanzo Dev v0.3.21.
Tests all major features end-to-end.
"""

import os
import sys
import asyncio
from pathlib import Path

from rich.panel import Panel
from rich.console import Console
from rich.progress import Progress, TextColumn, SpinnerColumn

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "pkg" / "hanzo" / "src"))


async def test_integration():
    """Run comprehensive integration tests."""
    console = Console()

    console.print(
        Panel.fit(
            "[bold]🧪 Hanzo Dev Integration Test Suite v0.3.21[/bold]\n"
            "Testing all major features end-to-end",
            border_style="bold cyan",
        )
    )

    test_results = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Test 1: Import and initialization
        task = progress.add_task("Testing imports...", total=None)
        try:
            from hanzo.cli import cli, __version__
            from hanzo.dev import HanzoDevREPL, MultiClaudeOrchestrator
            from hanzo.streaming import StreamingHandler
            from hanzo.rate_limiter import RateLimiter
            from hanzo.memory_manager import MemoryManager
            from hanzo.fallback_handler import FallbackHandler
            from hanzo.orchestrator_config import get_orchestrator_config

            assert __version__ == "0.3.21"
            test_results["imports"] = "✅ PASS"
            progress.update(task, description="✅ Imports successful")
        except Exception as e:
            test_results["imports"] = f"❌ FAIL: {e}"
            progress.update(task, description="❌ Import failed")

        # Test 2: Orchestrator configurations
        task = progress.add_task("Testing orchestrators...", total=None)
        try:
            configs_to_test = ["gpt-4", "claude", "local:llama3.2", "auto"]
            for config_name in configs_to_test:
                config = get_orchestrator_config(config_name)
                assert config is not None
            test_results["orchestrators"] = "✅ PASS"
            progress.update(task, description="✅ Orchestrators configured")
        except Exception as e:
            test_results["orchestrators"] = f"❌ FAIL: {e}"
            progress.update(task, description="❌ Orchestrator failed")

        # Test 3: Memory management
        task = progress.add_task("Testing memory...", total=None)
        try:
            manager = MemoryManager("/tmp/test_integration")

            # Add and retrieve memory
            mem_id = manager.add_memory("Integration test memory", type="fact")
            memories = manager.get_memories()
            assert len(memories) > 0

            # Save and load
            manager.save_memories()
            manager.load_memories()

            test_results["memory"] = "✅ PASS"
            progress.update(task, description="✅ Memory management working")
        except Exception as e:
            test_results["memory"] = f"❌ FAIL: {e}"
            progress.update(task, description="❌ Memory failed")

        # Test 4: Fallback handler
        task = progress.add_task("Testing fallback...", total=None)
        try:
            handler = FallbackHandler()

            # Check available options
            assert handler.available_options is not None
            assert len(handler.fallback_order) > 0

            # Get best option
            best = handler.get_best_option()
            assert best is not None or len(handler.fallback_order) == 0

            test_results["fallback"] = "✅ PASS"
            progress.update(task, description="✅ Fallback handler ready")
        except Exception as e:
            test_results["fallback"] = f"❌ FAIL: {e}"
            progress.update(task, description="❌ Fallback failed")

        # Test 5: Rate limiting
        task = progress.add_task("Testing rate limiting...", total=None)
        try:
            from hanzo.rate_limiter import RateLimiter, RateLimitConfig

            config = RateLimitConfig(requests_per_minute=10)
            limiter = RateLimiter(config)

            # Test rate limit check
            allowed, wait = await limiter.check_rate_limit()
            assert isinstance(allowed, bool)
            assert isinstance(wait, float)

            # Test acquire
            if allowed:
                await limiter.acquire()

            test_results["rate_limiting"] = "✅ PASS"
            progress.update(task, description="✅ Rate limiting active")
        except Exception as e:
            test_results["rate_limiting"] = f"❌ FAIL: {e}"
            progress.update(task, description="❌ Rate limiting failed")

        # Test 6: Streaming handler
        task = progress.add_task("Testing streaming...", total=None)
        try:
            # Create a separate console for streaming to avoid conflict
            from hanzo.streaming import StreamingHandler

            stream_console = Console()
            handler = StreamingHandler(stream_console)

            # Just test that handler initializes correctly
            assert handler is not None
            assert handler.current_response == ""
            assert handler.is_streaming == False

            test_results["streaming"] = "✅ PASS"
            progress.update(task, description="✅ Streaming ready")
        except Exception as e:
            test_results["streaming"] = f"❌ FAIL: {e}"
            progress.update(task, description="❌ Streaming failed")

        # Test 7: REPL initialization
        task = progress.add_task("Testing REPL...", total=None)
        try:
            orchestrator = MultiClaudeOrchestrator(
                workspace_dir="/tmp/test_integration",
                claude_path="claude",
                num_instances=1,
                enable_mcp=False,
                enable_networking=False,
                enable_guardrails=False,
                console=console,
                orchestrator_model="auto",
            )

            repl = HanzoDevREPL(orchestrator)

            # Check components
            assert repl.memory_manager is not None
            assert repl.commands is not None
            assert "help" in repl.commands

            test_results["repl"] = "✅ PASS"
            progress.update(task, description="✅ REPL initialized")
        except Exception as e:
            test_results["repl"] = f"❌ FAIL: {e}"
            progress.update(task, description="❌ REPL failed")

        # Test 8: AI connectivity (if available)
        task = progress.add_task("Testing AI connectivity...", total=None)
        try:
            from hanzo.fallback_handler import smart_chat

            # Quick test message
            response = await smart_chat("Reply with OK", console=None)

            if response:
                test_results["ai_connectivity"] = "✅ PASS"
                progress.update(task, description="✅ AI connected")
            else:
                test_results["ai_connectivity"] = "⚠️ No API keys"
                progress.update(task, description="⚠️ No API keys configured")
        except Exception as e:
            test_results["ai_connectivity"] = f"❌ FAIL: {e}"
            progress.update(task, description="❌ AI connection failed")

    # Print results summary
    console.print("\n" + "=" * 60)
    console.print("[bold]Test Results Summary:[/bold]\n")

    passed = 0
    failed = 0
    warned = 0

    for test_name, result in test_results.items():
        console.print(f"{test_name:20} {result}")
        if "✅" in result:
            passed += 1
        elif "❌" in result:
            failed += 1
        elif "⚠️" in result:
            warned += 1

    console.print("\n" + "=" * 60)
    console.print(
        f"[bold]Total:[/bold] {passed} passed, {failed} failed, {warned} warnings"
    )

    if failed == 0:
        console.print("\n[bold green]🎉 All critical tests passed![/bold green]")
        console.print("\nHanzo Dev v0.3.21 is fully operational!")
        return True
    else:
        console.print(
            "\n[bold red]Some tests failed. Please check the errors above.[/bold red]"
        )
        return False


if __name__ == "__main__":
    success = asyncio.run(test_integration())
    sys.exit(0 if success else 1)
