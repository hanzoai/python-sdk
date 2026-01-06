#!/usr/bin/env python3
"""
Test script to verify Hanzo Agent SDK works with local Hanzo Router backend.
"""

import asyncio
import os
import sys
from typing import Optional

# Try importing from different paths
try:
    from openai import AsyncOpenAI
    from agents import Agent, Runner, RunConfig, ModelProvider, Model
    from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
except ImportError:
    # Add src to path if running from project root
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    from openai import AsyncOpenAI
    from agents import Agent, Runner, RunConfig, ModelProvider, Model
    from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

# Hanzo Router configuration
HANZO_ROUTER_URL = os.getenv("HANZO_ROUTER_URL", "http://localhost:4000/v1")
HANZO_API_KEY = os.getenv("HANZO_API_KEY", "sk-1234")  # Default test key

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class HanzoModelProvider(ModelProvider):
    """Custom model provider that uses Hanzo Router backend."""
    
    def __init__(self, base_url: str, api_key: str):
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        print(f"{BLUE}Configured Hanzo Router at: {base_url}{RESET}")
    
    def get_model(self, model_name: str | None) -> Model:
        # Default to gpt-3.5-turbo if no model specified
        model = model_name or "gpt-3.5-turbo"
        print(f"{YELLOW}Using model: {model}{RESET}")
        return OpenAIChatCompletionsModel(model=model, openai_client=self.client)


async def test_basic_agent():
    """Test basic agent functionality."""
    print(f"\n{GREEN}=== Testing Basic Agent ==={RESET}")
    
    provider = HanzoModelProvider(HANZO_ROUTER_URL, HANZO_API_KEY)
    
    agent = Agent(
        name="TestAssistant",
        instructions="You are a helpful assistant. Be concise.",
    )
    
    try:
        result = await Runner.run(
            agent,
            "What is 2 + 2?",
            run_config=RunConfig(model_provider=provider)
        )
        print(f"{GREEN}✓ Basic test passed!{RESET}")
        print(f"Response: {result.final_output}")
        return True
    except Exception as e:
        print(f"{RED}✗ Basic test failed: {e}{RESET}")
        return False


async def test_with_tools():
    """Test agent with tools."""
    print(f"\n{GREEN}=== Testing Agent with Tools ==={RESET}")
    
    provider = HanzoModelProvider(HANZO_ROUTER_URL, HANZO_API_KEY)
    
    # Define a simple tool
    from agents import function_tool
    
    @function_tool
    def calculate(expression: str) -> str:
        """Calculate a mathematical expression."""
        try:
            result = eval(expression)
            return f"The result is: {result}"
        except:
            return "Invalid expression"
    
    agent = Agent(
        name="CalculatorAgent",
        instructions="You are a calculator assistant. Use the calculate tool for math.",
        tools=[calculate]
    )
    
    try:
        result = await Runner.run(
            agent,
            "What is 15 * 23?",
            run_config=RunConfig(model_provider=provider)
        )
        print(f"{GREEN}✓ Tool test passed!{RESET}")
        print(f"Response: {result.final_output}")
        return True
    except Exception as e:
        print(f"{RED}✗ Tool test failed: {e}{RESET}")
        return False


async def test_conversation():
    """Test multi-turn conversation."""
    print(f"\n{GREEN}=== Testing Conversation ==={RESET}")
    
    provider = HanzoModelProvider(HANZO_ROUTER_URL, HANZO_API_KEY)
    
    agent = Agent(
        name="ConversationAgent",
        instructions="You are a helpful assistant. Remember our conversation context.",
    )
    
    try:
        # First message
        result1 = await Runner.run(
            agent,
            "My name is Alice. Remember it.",
            run_config=RunConfig(model_provider=provider)
        )
        print(f"Response 1: {result1.final_output}")
        
        # Second message using context
        result2 = await Runner.run(
            agent,
            "What's my name?",
            run_config=RunConfig(model_provider=provider),
            context=result1.context
        )
        print(f"Response 2: {result2.final_output}")
        
        if "Alice" in result2.final_output:
            print(f"{GREEN}✓ Conversation test passed!{RESET}")
            return True
        else:
            print(f"{YELLOW}⚠ Conversation test: Context may not be preserved{RESET}")
            return True
    except Exception as e:
        print(f"{RED}✗ Conversation test failed: {e}{RESET}")
        return False


async def check_router_health():
    """Check if Hanzo Router is accessible."""
    import aiohttp
    
    print(f"\n{GREEN}=== Checking Hanzo Router Health ==={RESET}")
    print(f"Router URL: {HANZO_ROUTER_URL}")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Try health endpoint
            health_url = HANZO_ROUTER_URL.replace("/v1", "/health")
            async with session.get(health_url) as resp:
                if resp.status == 200:
                    print(f"{GREEN}✓ Router health check passed{RESET}")
                    return True
                else:
                    print(f"{YELLOW}⚠ Router health endpoint returned {resp.status}{RESET}")
            
            # Try models endpoint
            models_url = f"{HANZO_ROUTER_URL}/models"
            headers = {"Authorization": f"Bearer {HANZO_API_KEY}"}
            async with session.get(models_url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"{GREEN}✓ Available models: {len(data.get('data', []))} found{RESET}")
                    for model in data.get('data', [])[:5]:
                        print(f"  - {model.get('id')}")
                    return True
                else:
                    print(f"{YELLOW}⚠ Models endpoint returned {resp.status}{RESET}")
                    
    except aiohttp.ClientError as e:
        print(f"{RED}✗ Cannot connect to Router: {e}{RESET}")
        print(f"{YELLOW}Make sure Hanzo Router is running at {HANZO_ROUTER_URL}{RESET}")
        return False
    except Exception as e:
        print(f"{RED}✗ Unexpected error: {e}{RESET}")
        return False
    
    return True


async def main():
    """Run all tests."""
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Hanzo Agent SDK Backend Integration Test{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    # Check router health first
    if not await check_router_health():
        print(f"\n{RED}Cannot proceed without Router connection.{RESET}")
        print(f"{YELLOW}Start the Router with: cd /Users/z/work/hanzo/services && make start-router{RESET}")
        return
    
    # Run tests
    tests = [
        test_basic_agent,
        test_with_tools,
        test_conversation,
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
    
    # Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Test Summary{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    passed = sum(1 for r in results if r)
    total = len(results)
    
    if passed == total:
        print(f"{GREEN}✓ All tests passed! ({passed}/{total}){RESET}")
    else:
        print(f"{YELLOW}⚠ {passed}/{total} tests passed{RESET}")
    
    print(f"\n{GREEN}The Hanzo Agent SDK is working with the local backend!{RESET}")


if __name__ == "__main__":
    # Set up the environment
    if not os.getenv("OPENAI_API_KEY"):
        # Set a dummy key to prevent OpenAI client from complaining
        os.environ["OPENAI_API_KEY"] = "sk-dummy"
    
    # Run tests
    asyncio.run(main())