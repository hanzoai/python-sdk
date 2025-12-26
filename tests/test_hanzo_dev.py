#!/usr/bin/env python3
"""
Comprehensive test script for hanzo dev functionality.
Tests all orchestrator modes and ensures everything works.
"""

import os
import sys
import time
import asyncio
import subprocess
from pathlib import Path

# Add src to path for local testing
sys.path.insert(0, str(Path(__file__).parent / "pkg" / "hanzo" / "src"))


def print_test(name):
    """Print test header."""
    print(f"\n{'=' * 60}")
    print(f"TESTING: {name}")
    print("=" * 60)


def check_command_exists(cmd):
    """Check if a command exists."""
    try:
        result = subprocess.run(["which", cmd], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False


async def test_imports():
    """Test that all necessary imports work."""
    print_test("Module Imports")

    try:
        from hanzo.cli import cli, __version__

        print(f"✓ CLI module imported successfully (version {__version__})")

        from hanzo.dev import (
            HanzoDevREPL,
            HanzoDevOrchestrator,
            MultiClaudeOrchestrator,
        )

        print("✓ Dev module imported successfully")

        from hanzo.orchestrator_config import OrchestratorMode, get_orchestrator_config

        print("✓ Orchestrator config module imported successfully")

        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False


async def test_orchestrator_configs():
    """Test orchestrator configuration system."""
    print_test("Orchestrator Configurations")

    from hanzo.orchestrator_config import OrchestratorMode, get_orchestrator_config

    test_configs = [
        "gpt-4",
        "gpt-5",
        "codex",
        "claude",
        "router:gpt-4",
        "direct:claude-3-5",
        "local:llama3.2",
        "codestral",
        "gpt-5-pro-codex",
    ]

    for config_name in test_configs:
        try:
            config = get_orchestrator_config(config_name)
            print(f"✓ Config '{config_name}': mode={config.mode.value}, primary={config.primary_model}")
        except Exception as e:
            print(f"✗ Config '{config_name}' failed: {e}")
            return False

    return True


async def test_repl_initialization():
    """Test REPL initialization without running."""
    print_test("REPL Initialization")

    try:
        from hanzo.dev import (
            HanzoDevREPL,
            HanzoDevOrchestrator,
            MultiClaudeOrchestrator,
        )
        from rich.console import Console

        # Create a mock orchestrator
        console = Console()
        orchestrator = MultiClaudeOrchestrator(
            workspace_dir="/tmp/test_workspace",
            claude_path="/usr/bin/claude",  # Mock path
            num_instances=2,
            enable_mcp=True,
            enable_networking=True,
            enable_guardrails=True,
            console=console,
            orchestrator_model="gpt-4",
        )

        # Create REPL
        repl = HanzoDevREPL(orchestrator)
        print("✓ REPL created successfully")

        # Test command registration
        assert "help" in repl.commands
        assert "exit" in repl.commands
        assert "status" in repl.commands
        print("✓ Commands registered successfully")

        return True
    except Exception as e:
        print(f"✗ REPL initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_cli_tool_detection():
    """Test detection of CLI tools."""
    print_test("CLI Tool Detection")

    tools = {
        "openai": "OpenAI CLI",
        "claude": "Claude Desktop",
        "gemini": "Gemini CLI",
        "ollama": "Ollama (local models)",
    }

    for cmd, name in tools.items():
        if check_command_exists(cmd):
            print(f"✓ {name} detected ({cmd})")
        else:
            print(f"✗ {name} not found ({cmd})")

    # Check for Hanzo IDE
    ide_path = Path.home() / "work" / "hanzo" / "ide"
    if ide_path.exists():
        print(f"✓ Hanzo IDE detected at {ide_path}")
    else:
        print(f"✗ Hanzo IDE not found at {ide_path}")

    return True


async def test_api_keys():
    """Test API key availability."""
    print_test("API Keys")

    keys = {
        "OPENAI_API_KEY": "OpenAI",
        "ANTHROPIC_API_KEY": "Anthropic",
        "GOOGLE_API_KEY": "Google/Gemini",
        "MISTRAL_API_KEY": "Mistral",
    }

    has_any_key = False
    for env_var, service in keys.items():
        if os.getenv(env_var):
            print(f"✓ {service} API key found")
            has_any_key = True
        else:
            print(f"✗ {service} API key not set")

    if not has_any_key:
        print("\n⚠️  No API keys found. You can still use:")
        print("  • Local models (Ollama)")
        print("  • CLI tools (OpenAI CLI, Claude Desktop)")
        print("  • Free APIs (Codestral, StarCoder)")

    return True


async def test_ui_components():
    """Test UI components render without errors."""
    print_test("UI Components")

    try:
        from rich.box import ROUNDED
        from rich.panel import Panel
        from rich.console import Console

        console = Console()

        # Test header panel
        console.print(
            Panel(
                "[bold cyan]Test Header[/bold cyan]\n[dim]Test subtitle[/dim]",
                box=ROUNDED,
                style="dim white",
                padding=(0, 1),
            )
        )
        print("✓ Header panel renders successfully")

        # Test input box borders
        console.print("[dim white]╭" + "─" * 40 + "╮[/dim white]")
        console.print("[dim white]│[/dim white] › Test input")
        console.print("[dim white]╰" + "─" * 40 + "╯[/dim white]")
        print("✓ Input box borders render successfully")

        # Test response panel
        console.print(
            Panel(
                "Test AI response",
                title="[bold cyan]AI Response[/bold cyan]",
                title_align="left",
                border_style="dim cyan",
                padding=(1, 2),
            )
        )
        print("✓ Response panel renders successfully")

        return True
    except Exception as e:
        print(f"✗ UI component error: {e}")
        return False


async def test_chat_methods():
    """Test chat method availability."""
    print_test("Chat Methods")

    try:
        from hanzo.dev import HanzoDevREPL, MultiClaudeOrchestrator
        from rich.console import Console

        console = Console()
        orchestrator = MultiClaudeOrchestrator(
            workspace_dir="/tmp/test",
            claude_path="claude",
            num_instances=1,
            enable_mcp=False,
            enable_networking=False,
            enable_guardrails=False,
            console=console,
            orchestrator_model="gpt-4",
        )

        repl = HanzoDevREPL(orchestrator)

        # Check methods exist
        methods = [
            "_direct_api_chat",
            "_use_openai_cli",
            "_use_claude_cli",
            "_use_gemini_cli",
            "_use_hanzo_ide",
            "_use_free_codestral",
            "_use_free_starcoder",
            "_use_local_model",
        ]

        for method in methods:
            if hasattr(repl, method):
                print(f"✓ Method {method} exists")
            else:
                print(f"✗ Method {method} missing")
                return False

        return True
    except Exception as e:
        print(f"✗ Chat method test failed: {e}")
        return False


async def test_subprocess_commands():
    """Test subprocess command execution."""
    print_test("Subprocess Commands")

    try:
        # Test basic command execution
        result = subprocess.run(["echo", "test"], capture_output=True, text=True, timeout=5)

        if result.returncode == 0 and result.stdout.strip() == "test":
            print("✓ Subprocess execution works")
        else:
            print("✗ Subprocess execution failed")
            return False

        return True
    except Exception as e:
        print(f"✗ Subprocess test failed: {e}")
        return False


async def test_package_version():
    """Test package version consistency."""
    print_test("Package Version")

    try:
        # Check pyproject.toml version
        pyproject_path = Path(__file__).parent / "pkg" / "hanzo" / "pyproject.toml"
        with open(pyproject_path) as f:
            content = f.read()
            for line in content.split("\n"):
                if line.startswith("version ="):
                    pyproject_version = line.split('"')[1]
                    break

        # Check CLI version
        from hanzo.cli import __version__ as cli_version

        print(f"PyProject version: {pyproject_version}")
        print(f"CLI version: {cli_version}")

        if pyproject_version == cli_version:
            print("✓ Versions match")
            return True
        else:
            print("✗ Version mismatch!")
            return False

    except Exception as e:
        print(f"✗ Version check failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("HANZO DEV COMPREHENSIVE TEST SUITE")
    print("=" * 60)

    tests = [
        test_imports(),
        test_orchestrator_configs(),
        test_repl_initialization(),
        test_cli_tool_detection(),
        test_api_keys(),
        test_ui_components(),
        test_chat_methods(),
        test_subprocess_commands(),
        test_package_version(),
    ]

    results = []
    for test in tests:
        try:
            result = await test
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test crashed: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("✅ All tests passed!")
    else:
        print(f"⚠️  {total - passed} test(s) failed")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
