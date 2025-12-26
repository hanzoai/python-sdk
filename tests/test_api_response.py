#!/usr/bin/env python3
"""Test actual AI API responses."""

import os
import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "pkg" / "hanzo" / "src"))


async def test_openai_api():
    """Test OpenAI API response."""
    if not os.getenv("OPENAI_API_KEY"):
        print("✗ OpenAI API key not set")
        return False

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI()
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Reply with exactly: 'API test successful'",
                },
                {"role": "user", "content": "Test"},
            ],
            max_tokens=50,
        )

        if response.choices and "successful" in response.choices[0].message.content:
            print(f"✓ OpenAI API works: {response.choices[0].message.content}")
            return True
        else:
            print("✗ OpenAI API response unexpected")
            return False

    except Exception as e:
        print(f"✗ OpenAI API error: {e}")
        return False


async def test_anthropic_api():
    """Test Anthropic API response."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("✗ Anthropic API key not set")
        return False

    try:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic()
        response = await client.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=[{"role": "user", "content": "Reply with exactly: 'API test successful'"}],
            max_tokens=50,
        )

        if response.content and "successful" in response.content[0].text:
            print(f"✓ Anthropic API works: {response.content[0].text}")
            return True
        else:
            print("✗ Anthropic API response unexpected")
            return False

    except Exception as e:
        print(f"✗ Anthropic API error: {e}")
        return False


async def test_ollama_local():
    """Test Ollama local model."""
    try:
        import httpx

        async with httpx.AsyncClient() as client:
            # Check if Ollama is running
            response = await client.get("http://localhost:11434/api/tags")

            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])

                if models:
                    print(f"✓ Ollama running with {len(models)} model(s)")

                    # Try a simple generation
                    model_name = models[0]["name"]
                    gen_response = await client.post(
                        "http://localhost:11434/api/generate",
                        json={
                            "model": model_name,
                            "prompt": "Reply with: test",
                            "stream": False,
                        },
                        timeout=30.0,
                    )

                    if gen_response.status_code == 200:
                        print(f"✓ Ollama model {model_name} responds")
                        return True
                else:
                    print("✗ Ollama running but no models installed")
                    print("  Install with: ollama pull llama3.2")
                    return False
            else:
                print("✗ Ollama not responding")
                return False

    except Exception as e:
        print(f"✗ Ollama not available: {e}")
        print("  Install with: curl -fsSL https://ollama.com/install.sh | sh")
        return False


async def main():
    """Run API tests."""
    print("\n" + "=" * 60)
    print("TESTING ACTUAL AI API RESPONSES")
    print("=" * 60 + "\n")

    results = []

    # Test OpenAI
    print("Testing OpenAI API...")
    results.append(await test_openai_api())
    print()

    # Test Anthropic
    print("Testing Anthropic API...")
    results.append(await test_anthropic_api())
    print()

    # Test Ollama
    print("Testing Ollama (local)...")
    results.append(await test_ollama_local())
    print()

    # Summary
    print("=" * 60)
    if any(results):
        print("✅ At least one AI API is working!")
        print("You can use hanzo dev with the working APIs")
    else:
        print("⚠️  No AI APIs are currently working")
        print("You can still use CLI tools or free APIs")

    return any(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
