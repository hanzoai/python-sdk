#!/usr/bin/env python3
"""
Simple test of Hanzo Agent SDK with Anthropic
"""

import asyncio
import os
from openai import AsyncOpenAI

# Import from the local source
import sys
sys.path.insert(0, 'src')

from agents import Agent, Runner, RunConfig, ModelProvider, Model
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

# Anthropic configuration through OpenAI-compatible endpoint
ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not ANTHROPIC_API_KEY:
    print("Please set ANTHROPIC_API_KEY environment variable")
    sys.exit(1)


class AnthropicProvider(ModelProvider):
    """Provider for Anthropic models via OpenAI-compatible API."""
    
    def __init__(self):
        # Note: Anthropic requires special headers, so we'll use the Hanzo Router instead
        # which handles Anthropic properly
        self.client = AsyncOpenAI(
            base_url="http://localhost:4000/v1",  # Use Hanzo Router
            api_key=os.getenv("HANZO_API_KEY", "sk-1234"),
        )
    
    def get_model(self, model_name: str | None) -> Model:
        # Use Claude through the router
        model = model_name or "claude-3-sonnet-20240229"
        return OpenAIChatCompletionsModel(model=model, openai_client=self.client)


async def test_simple_question():
    """Test a simple math question."""
    
    # Create provider
    provider = AnthropicProvider()
    
    # Create a simple agent
    agent = Agent(
        name="MathAssistant",
        instructions="You are a helpful math assistant. Be concise.",
    )
    
    print("Testing Hanzo Agent SDK with Anthropic...")
    print(f"Question: What's 1+2?")
    print("-" * 40)
    
    try:
        # Run the agent
        result = await Runner.run(
            agent,
            "What's 1+2?",
            run_config=RunConfig(
                model_provider=provider,
                model="claude-3-sonnet-20240229"
            )
        )
        
        print(f"Answer: {result.final_output}")
        print("-" * 40)
        print("✅ Test successful!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Hanzo Router is running: cd /Users/z/work/hanzo/services && docker compose -f docker-compose.mothership.yml up router")
        print("2. Ensure ANTHROPIC_API_KEY is set in your environment")


async def test_direct_anthropic():
    """Test direct Anthropic API call (without Agent SDK)."""
    import aiohttp
    
    print("\nTesting direct Anthropic API...")
    
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    data = {
        "model": "claude-3-sonnet-20240229",
        "messages": [{"role": "user", "content": "What's 1+2?"}],
        "max_tokens": 100
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print(f"Direct API Answer: {result['content'][0]['text']}")
                else:
                    print(f"API Error {resp.status}: {await resp.text()}")
    except Exception as e:
        print(f"Direct API Error: {e}")


if __name__ == "__main__":
    # First try direct API
    asyncio.run(test_direct_anthropic())
    
    # Then try through Agent SDK
    print("\n" + "="*50 + "\n")
    asyncio.run(test_simple_question())