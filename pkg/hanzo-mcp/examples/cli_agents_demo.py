#!/usr/bin/env python3
"""Demonstration of CLI agent tools.

This shows how to use the 4 CLI-based agent tools:
1. Claude Code CLI (claude)
2. OpenAI Codex CLI (openai)
3. Google Gemini CLI (gemini)
4. xAI Grok CLI (grok)

These can be used individually or composed in swarms.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hanzo_mcp.tools.agent.claude_cli_tool import ClaudeCLITool
from hanzo_mcp.tools.agent.codex_cli_tool import CodexCLITool
from hanzo_mcp.tools.agent.gemini_cli_tool import GeminiCLITool
from hanzo_mcp.tools.agent.grok_cli_tool import GrokCLITool
from hanzo_mcp.tools.agent.code_auth import CodeAuthManager
from hanzo_mcp.tools.common.permissions import PermissionManager


def check_cli_availability():
    """Check which CLI tools are available."""
    print("="*60)
    print("CLI AGENT AVAILABILITY CHECK")
    print("="*60)
    
    pm = PermissionManager()
    
    # Check each CLI tool
    tools = [
        ("Claude Code", ClaudeCLITool(pm)),
        ("OpenAI Codex", CodexCLITool(pm)),
        ("Google Gemini", GeminiCLITool(pm)),
        ("xAI Grok", GrokCLITool(pm)),
    ]
    
    for name, tool in tools:
        print(f"\n{name} ({tool.command_name}):")
        
        # Check if installed
        installed = tool.is_installed()
        print(f"  Installed: {'✓' if installed else '✗'}")
        
        if installed:
            print(f"  Command: {tool.command_name}")
        else:
            print(f"  Install: See documentation for {name}")
        
        # Check API key
        has_key = tool.has_api_key()
        print(f"  API Key: {'✓' if has_key else '✗'}")
        
        if not has_key and tool.env_vars:
            print(f"  Required: {' or '.join(tool.env_vars)}")
        
        # Show default model
        print(f"  Default Model: {tool.default_model}")


def show_usage_examples():
    """Show usage examples for each CLI agent."""
    print("\n" + "="*60)
    print("USAGE EXAMPLES")
    print("="*60)
    
    print("\n1. Claude Code CLI:")
    print("   claude_cli(prompts='Fix the type errors in main.py')")
    print("   claude_cli(prompts='Refactor this function', model='claude-3-opus-20240229')")
    
    print("\n2. OpenAI Codex CLI:")
    print("   codex_cli(prompts='Generate unit tests for the Calculator class')")
    print("   codex_cli(prompts='Optimize this algorithm', model='gpt-4-turbo')")
    
    print("\n3. Google Gemini CLI:")
    print("   gemini_cli(prompts='Create a REST API with FastAPI')")
    print("   gemini_cli(prompts='Analyze security vulnerabilities', model='gemini-1.5-flash')")
    
    print("\n4. xAI Grok CLI:")
    print("   grok_cli(prompts='Explain this regex pattern')")
    print("   grok_cli(prompts='Write a web scraper', system_prompt='Be concise')")


def show_swarm_examples():
    """Show how to use CLI agents in swarms."""
    print("\n" + "="*60)
    print("SWARM COMPOSITION EXAMPLES")
    print("="*60)
    
    print("\n1. Multi-Agent Code Review:")
    print("""
swarm(
    tasks=[
        {
            "file_path": "/src/core/engine.py",
            "instructions": "Review for architecture and design patterns",
            "description": "Claude architectural review"
        },
        {
            "file_path": "/src/core/engine.py", 
            "instructions": "Check for performance issues and optimizations",
            "description": "GPT-4 performance review"
        },
        {
            "file_path": "/src/core/engine.py",
            "instructions": "Analyze for security vulnerabilities", 
            "description": "Gemini security audit"
        }
    ],
    common_instructions="Provide specific, actionable feedback"
)
""")
    
    print("\n2. Parallel Refactoring with Different Agents:")
    print("""
swarm(
    tasks=[
        {
            "file_path": "/src/api/auth.py",
            "instructions": "Refactor to use async/await",
            "description": "Claude async refactor"
        },
        {
            "file_path": "/src/api/database.py",
            "instructions": "Add type hints and docstrings",
            "description": "Codex type annotations"
        },
        {
            "file_path": "/src/api/validators.py",
            "instructions": "Simplify validation logic",
            "description": "Gemini simplification"
        }
    ]
)
""")
    
    print("\n3. Consensus-Based Decision Making:")
    print("""
# Get multiple perspectives on the same problem
consensus_prompt = "Should we migrate from REST to GraphQL for our API?"

# Each agent provides their perspective
claude_response = await claude_cli(prompts=consensus_prompt)
codex_response = await codex_cli(prompts=consensus_prompt)  
gemini_response = await gemini_cli(prompts=consensus_prompt)
grok_response = await grok_cli(prompts=consensus_prompt)

# Synthesize responses for a balanced decision
""")


def show_auth_management():
    """Show authentication management features."""
    print("\n" + "="*60)
    print("AUTHENTICATION MANAGEMENT")
    print("="*60)
    
    print("\nManaging API keys and accounts:")
    print("1. Create accounts for different projects:")
    print("   code_auth create --account work --provider claude")
    print("   code_auth create --account personal --provider openai")
    print("   code_auth create --account research --provider google")
    
    print("\n2. Switch between accounts:")
    print("   code_auth switch --account work")
    print("   code_auth switch --account personal")
    
    print("\n3. Agent-specific accounts (for swarms):")
    print("   code_auth agent --agent_id refactor_agent --parent_account work")
    print("   code_auth agent --agent_id review_agent --parent_account work")
    
    print("\n4. Check status:")
    print("   code_auth status")
    print("   code_auth list")


def show_configuration():
    """Show how to configure CLI agents."""
    print("\n" + "="*60)
    print("CONFIGURATION OPTIONS")
    print("="*60)
    
    print("\n1. Environment Variables:")
    for provider, vars in [
        ("Claude", ["ANTHROPIC_API_KEY", "CLAUDE_API_KEY"]),
        ("OpenAI", ["OPENAI_API_KEY"]),
        ("Google", ["GOOGLE_API_KEY", "GEMINI_API_KEY"]),
        ("xAI", ["XAI_API_KEY", "GROK_API_KEY"]),
    ]:
        print(f"\n   {provider}:")
        for var in vars:
            value = "***" if os.environ.get(var) else "not set"
            print(f"     {var}: {value}")
    
    print("\n2. Model Selection:")
    print("   - Claude: claude-3-5-sonnet-20241022 (default), claude-3-opus-20240229")
    print("   - OpenAI: gpt-4o (default), gpt-4-turbo, gpt-4")
    print("   - Gemini: gemini-1.5-pro (default), gemini-1.5-flash")
    print("   - Grok: grok-2 (default), grok-1")
    
    print("\n3. Working Directory:")
    print("   All CLI agents support working_dir parameter:")
    print("   claude_cli(prompts='...', working_dir='/path/to/project')")


def main():
    """Run all demonstrations."""
    check_cli_availability()
    show_usage_examples()
    show_swarm_examples()
    show_auth_management()
    show_configuration()
    
    print("\n" + "="*60)
    print("KEY FEATURES")
    print("="*60)
    print("• All 4 CLI agents are now available as MCP tools")
    print("• Can be used individually or composed in swarms")
    print("• Support separate accounts to avoid rate limits")
    print("• Work with existing CLI installations")
    print("• No API keys needed if already logged in to CLIs")
    print("• Claude Code is the default for swarm agents")
    print("• Full programmatic control over AI coding assistants")
    print("• Composable for multi-agent workflows")


if __name__ == "__main__":
    main()