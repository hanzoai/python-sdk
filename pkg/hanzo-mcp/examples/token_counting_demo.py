#!/usr/bin/env python3
"""Demonstration of token counting and authentication features.

This shows:
1. How token counting works (using tiktoken)
2. Claude Code authentication management
3. Separate agent accounts
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hanzo_tools.agent.code_auth import CodeAuthManager, get_latest_claude_model
from hanzo_mcp.tools.common.truncate import estimate_tokens


def demonstrate_token_counting():
    """Show how token counting works."""
    print("=" * 60)
    print("TOKEN COUNTING DEMONSTRATION")
    print("=" * 60)

    # Test strings
    test_cases = [
        ("Hello, world!", "Short text"),
        ("The quick brown fox jumps over the lazy dog. " * 10, "Medium text"),
        (
            "import os\nimport sys\n\ndef main():\n    print('Hello')\n" * 50,
            "Code snippet",
        ),
        ("🚀 Emoji test 🎉 Unicode 你好 мир", "Unicode and emoji"),
        ("a" * 1000, "1000 characters"),
        ("word " * 5000, "5000 words"),
    ]

    print("\nMCP Token Limit: 25,000 tokens")
    print("Safety Buffer: 20,000 tokens (leaving 5k margin)")
    print("\nToken counting using tiktoken (cl100k_base encoding):")
    print("-" * 60)

    for text, description in test_cases:
        tokens = estimate_tokens(text)
        chars = len(text)
        ratio = tokens / chars if chars > 0 else 0

        print(f"\n{description}:")
        print(f"  Characters: {chars:,}")
        print(f"  Tokens: {tokens:,}")
        print(f"  Ratio: {ratio:.2f} tokens/char")

        if tokens > 20000:
            print("  ⚠️  WOULD TRIGGER PAGINATION")

    # Show how much text fits in one page
    print("\n" + "-" * 60)
    print("Approximate content per page:")

    # Estimate for different content types
    avg_chars_per_token = 4  # rough average
    max_chars = 20000 * avg_chars_per_token

    print(f"  Plain text: ~{max_chars:,} characters")
    print(f"  Lines of code: ~{max_chars // 80:,} lines (80 chars/line)")
    print(f"  JSON data: ~{max_chars // 2:,} characters (dense)")
    print(f"  Natural language: ~{20000 // 1.3:,.0f} words")


def demonstrate_auth_management():
    """Show authentication management features."""
    print("\n" + "=" * 60)
    print("AUTHENTICATION MANAGEMENT")
    print("=" * 60)

    auth_manager = CodeAuthManager()

    # Show current status
    current = auth_manager.get_active_account()
    print(f"\nCurrent account: {current}")

    # List accounts
    accounts = auth_manager.list_accounts()
    if accounts:
        print("\nConfigured accounts:")
        for account in accounts:
            info = auth_manager.get_account_info(account)
            print(f"  - {account}: {info['provider']} ({info.get('model', 'default')})")
    else:
        print("\nNo accounts configured")

    # Show how to create accounts
    print("\nTo create accounts:")
    print("  code_auth create --account personal --provider claude")
    print("  code_auth create --account work --provider openai")
    print("  code_auth create --account test --provider deepseek")

    # Show latest Claude model
    latest_model = get_latest_claude_model()
    print(f"\nLatest Claude Sonnet model: {latest_model}")

    # Check environment
    print("\nEnvironment variables detected:")
    providers = {
        "claude": ["ANTHROPIC_API_KEY", "CLAUDE_API_KEY"],
        "openai": ["OPENAI_API_KEY"],
        "google": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
    }

    for provider, env_vars in providers.items():
        for var in env_vars:
            if var in os.environ:
                print(f"  ✓ {var} (for {provider})")


def demonstrate_agent_accounts():
    """Show how agent accounts work."""
    print("\n" + "=" * 60)
    print("AGENT ACCOUNT MANAGEMENT")
    print("=" * 60)

    print("\nSwarm agents can use separate accounts:")
    print("1. Each agent gets a unique identifier")
    print("2. Credentials are cloned from parent account")
    print("3. Agents run independently with their own auth")

    print("\nExample agent accounts:")
    agent_ids = [
        "swarm_0_Update_config_py",
        "swarm_1_Fix_imports",
        "swarm_2_Add_type_hints",
    ]

    for agent_id in agent_ids:
        print(f"  - agent_{agent_id}")

    print("\nWhen enable_claude_code=True:")
    print("  - Each swarm agent gets its own account")
    print("  - Prevents rate limit conflicts")
    print("  - Allows parallel execution without auth issues")


def demonstrate_streaming_tokens():
    """Show how streaming token counting works."""
    print("\n" + "=" * 60)
    print("STREAMING TOKEN COUNTING")
    print("=" * 60)

    print("\nFor long-running commands:")
    print("1. Output streams to disk (no memory usage)")
    print("2. Tokens counted as chunks arrive")
    print("3. Pagination triggered at 20k tokens")
    print("4. Command continues in background")
    print("5. Cursor allows resuming from same position")

    # Simulate streaming
    print("\nSimulated streaming output:")
    total_tokens = 0
    chunk_num = 0

    while total_tokens < 25000:
        chunk_num += 1
        chunk = f"Chunk {chunk_num}: " + "x" * 100 + "\n"
        chunk_tokens = estimate_tokens(chunk)
        total_tokens += chunk_tokens

        if total_tokens < 20000:
            print(f"  Chunk {chunk_num}: {chunk_tokens} tokens (total: {total_tokens})")
        else:
            print(f"  Chunk {chunk_num}: PAGINATION TRIGGERED at {total_tokens} tokens")
            print("  → Response includes cursor for continuation")
            print("  → Command continues writing to log file")
            print("  → Next page starts from this position")
            break


def main():
    """Run all demonstrations."""
    demonstrate_token_counting()
    demonstrate_auth_management()
    demonstrate_agent_accounts()
    demonstrate_streaming_tokens()

    print("\n" + "=" * 60)
    print("KEY POINTS:")
    print("=" * 60)
    print("1. Token counting uses tiktoken (same as OpenAI/Anthropic)")
    print("2. MCP limit is 25,000 tokens per response")
    print("3. We use 20,000 token buffer for safety")
    print("4. Swarm can use separate accounts per agent")
    print("5. Streaming output handles unlimited content via pagination")
    print("6. Default model: claude-3-5-sonnet-20241022 (latest)")


if __name__ == "__main__":
    main()
