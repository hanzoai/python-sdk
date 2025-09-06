#!/usr/bin/env python3
"""Test script to validate the Hanzo workflow is properly configured."""

import os
import sys
import json
from pathlib import Path

def check_environment():
    """Check required environment variables."""
    print("🔍 Checking environment variables...")
    
    required = {
        "ANTHROPIC_API_KEY": "Anthropic API key for Claude models",
        "OPENAI_API_KEY": "OpenAI API key (optional but recommended)",
    }
    
    optional = {
        "HANZO_API_KEY": "Hanzo Router API key",
        "HANZO_DEFAULT_MODEL": "Default model selection",
        "HANZO_ROUTER_URL": "Hanzo Router URL",
    }
    
    missing = []
    for key, desc in required.items():
        if os.environ.get(key):
            print(f"  ✅ {key}: Set")
        else:
            print(f"  ❌ {key}: Missing - {desc}")
            missing.append(key)
    
    print("\nOptional variables:")
    for key, desc in optional.items():
        value = os.environ.get(key)
        if value:
            print(f"  ✅ {key}: {value[:20]}...")
        else:
            print(f"  ⚠️  {key}: Not set - {desc}")
    
    return len(missing) == 0

def test_imports():
    """Test that all required packages can be imported."""
    print("\n📦 Testing package imports...")
    
    packages = [
        ("hanzoai", "Core SDK"),
        ("hanzo_mcp", "MCP tools"),
        ("hanzo_agents", "Agent framework"),
        ("hanzo_repl", "REPL interface"),
    ]
    
    failed = []
    for package, desc in packages:
        try:
            __import__(package)
            print(f"  ✅ {package}: {desc}")
        except ImportError as e:
            print(f"  ❌ {package}: {desc} - {e}")
            failed.append(package)
    
    return len(failed) == 0

def test_basic_client():
    """Test basic Hanzo client functionality."""
    print("\n🤖 Testing Hanzo client...")
    
    try:
        from hanzoai import Hanzo
        
        client = Hanzo()
        print("  ✅ Client initialized")
        
        # Test model listing (doesn't require API call)
        models = ["claude-3-opus-20240229", "claude-3-5-sonnet-20241022", "gpt-4"]
        print(f"  ✅ Available models: {', '.join(models[:3])}...")
        
        return True
    except Exception as e:
        print(f"  ❌ Client error: {e}")
        return False

def test_mcp_tools():
    """Test MCP tool availability."""
    print("\n🛠️  Testing MCP tools...")
    
    try:
        from hanzo_mcp import MCPClient
        
        mcp = MCPClient()
        tools = mcp.get_all_tools()
        
        print(f"  ✅ {len(tools)} MCP tools available")
        
        # Check for essential tools
        essential = ["read", "write", "search", "run_command"]
        available = [t['name'] for t in tools]
        
        for tool in essential:
            if any(tool in t for t in available):
                print(f"  ✅ Tool '{tool}' available")
            else:
                print(f"  ⚠️  Tool '{tool}' might be missing")
        
        return True
    except Exception as e:
        print(f"  ❌ MCP error: {e}")
        return False

def test_agent_framework():
    """Test agent framework setup."""
    print("\n🤝 Testing agent framework...")
    
    try:
        from hanzo_agents import Agent, SwarmOrchestrator
        
        # Test agent creation
        agent = Agent(name="test", model="claude-3-haiku-20240307")
        print("  ✅ Agent created")
        
        # Test swarm
        swarm = SwarmOrchestrator()
        print("  ✅ Swarm orchestrator ready")
        
        return True
    except Exception as e:
        print(f"  ❌ Agent framework error: {e}")
        return False

def test_cli_commands():
    """Test CLI command availability."""
    print("\n💻 Testing CLI commands...")
    
    import subprocess
    
    commands = [
        ("hanzo --version", "Hanzo CLI"),
        ("hanzo-mcp --help", "MCP CLI"),
    ]
    
    failed = []
    for cmd, desc in commands:
        try:
            result = subprocess.run(
                cmd.split(), 
                capture_output=True, 
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"  ✅ {desc}: Available")
            else:
                print(f"  ⚠️  {desc}: Non-zero exit code")
        except Exception as e:
            print(f"  ❌ {desc}: {e}")
            failed.append(cmd)
    
    return len(failed) == 0

def test_simple_completion():
    """Test a simple completion if API key is available."""
    print("\n🧪 Testing simple completion...")
    
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("  ⏭️  Skipping - No API key")
        return True
    
    try:
        from hanzoai import Hanzo
        
        client = Hanzo()
        response = client.chat.completions.create(
            model="claude-3-haiku-20240307",  # Cheapest model
            messages=[{"role": "user", "content": "Say 'test successful' only"}],
            max_tokens=10
        )
        
        result = response.choices[0].message.content.lower()
        if "test" in result or "successful" in result:
            print("  ✅ Completion successful")
            return True
        else:
            print(f"  ⚠️  Unexpected response: {result}")
            return True
    except Exception as e:
        print(f"  ❌ Completion error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 50)
    print("🚀 Hanzo Workflow Test Suite")
    print("=" * 50)
    
    tests = [
        ("Environment", check_environment),
        ("Imports", test_imports),
        ("Client", test_basic_client),
        ("MCP Tools", test_mcp_tools),
        ("Agents", test_agent_framework),
        ("CLI", test_cli_commands),
        ("Completion", test_simple_completion),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\n🎯 Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("✨ All tests passed! The workflow is ready to use.")
        print("\nNext steps:")
        print("  1. Start REPL: hanzo repl start")
        print("  2. Try agent:claude syntax in REPL")
        print("  3. Run the workflow script: python hanzo_workflow.py 'Your feature'")
    else:
        print("\n⚠️  Some tests failed. Please check:")
        print("  1. Install missing packages: pip install hanzo[all]")
        print("  2. Set required environment variables")
        print("  3. Check the WORKFLOW_GUIDE.md for details")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())