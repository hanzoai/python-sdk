#!/usr/bin/env python3
"""
Example of using Hanzo Agent SDK with Hanzo Router backend.

This shows how to configure the Agent SDK to use your local or remote
Hanzo AI infrastructure instead of OpenAI directly.
"""

import asyncio
import os
from openai import AsyncOpenAI

from agents import (
    Agent,
    Model,
    ModelProvider,
    OpenAIChatCompletionsModel,
    RunConfig,
    Runner,
    function_tool,
)

# Configuration for Hanzo Router
# These can be set via environment variables or directly in code
HANZO_ROUTER_URL = os.getenv("HANZO_ROUTER_URL", "http://localhost:4000/v1")
HANZO_API_KEY = os.getenv("HANZO_API_KEY", "sk-1234")  # Get from Router dashboard


class HanzoModelProvider(ModelProvider):
    """
    Custom model provider that routes requests through Hanzo Router.
    
    The Router provides:
    - Unified access to 100+ LLM providers
    - Cost tracking and rate limiting
    - Model fallbacks and load balancing
    - Observability with Cloud dashboard
    """
    
    def __init__(self, base_url: str = HANZO_ROUTER_URL, api_key: str = HANZO_API_KEY):
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        print(f"Connected to Hanzo Router at: {base_url}")
    
    def get_model(self, model_name: str | None) -> Model:
        # The Router supports many models, including:
        # - OpenAI: gpt-4, gpt-3.5-turbo, etc.
        # - Anthropic: claude-3-opus, claude-3-sonnet, etc.
        # - Open models: llama-3, mixtral, etc.
        return OpenAIChatCompletionsModel(
            model=model_name or "gpt-3.5-turbo",
            openai_client=self.client
        )


# Create a global provider instance
hanzo_provider = HanzoModelProvider()


# Example 1: Basic Agent
async def basic_example():
    """Simple example using Hanzo backend."""
    print("\n=== Basic Agent Example ===")
    
    agent = Agent(
        name="Assistant",
        instructions="You are a helpful AI assistant powered by Hanzo infrastructure.",
    )
    
    result = await Runner.run(
        agent,
        "Tell me about the benefits of using a unified LLM gateway.",
        run_config=RunConfig(model_provider=hanzo_provider)
    )
    
    print(f"Response: {result.final_output}")


# Example 2: Agent with Tools
@function_tool
def search_knowledge_base(query: str) -> str:
    """Search the company knowledge base."""
    # In a real implementation, this would connect to your vector DB
    # via Hanzo's infrastructure
    return f"Found 3 relevant documents about '{query}' in the knowledge base."


@function_tool
def create_support_ticket(title: str, description: str, priority: str = "medium") -> str:
    """Create a support ticket in the system."""
    # This would integrate with your ticketing system
    return f"Created ticket: {title} (Priority: {priority})"


async def tools_example():
    """Example with custom tools."""
    print("\n=== Agent with Tools Example ===")
    
    agent = Agent(
        name="SupportAgent",
        instructions="""You are a customer support agent.
        Use the search_knowledge_base tool to find information.
        Create support tickets when customers report issues.""",
        tools=[search_knowledge_base, create_support_ticket]
    )
    
    result = await Runner.run(
        agent,
        "I'm having trouble connecting to the API. It returns 401 errors.",
        run_config=RunConfig(model_provider=hanzo_provider)
    )
    
    print(f"Response: {result.final_output}")


# Example 3: Multi-Model Strategy
async def multi_model_example():
    """Example using different models for different tasks."""
    print("\n=== Multi-Model Example ===")
    
    # Use a fast model for simple tasks
    fast_agent = Agent(
        name="FastResponder",
        instructions="You provide quick, concise responses.",
    )
    
    result = await Runner.run(
        fast_agent,
        "What's the current time in UTC?",
        run_config=RunConfig(
            model_provider=hanzo_provider,
            model="gpt-3.5-turbo"  # Fast, cost-effective
        )
    )
    print(f"Fast response: {result.final_output}")
    
    # Use a powerful model for complex tasks
    analyst_agent = Agent(
        name="DataAnalyst",
        instructions="You are an expert data analyst. Provide detailed analysis.",
    )
    
    result = await Runner.run(
        analyst_agent,
        "Analyze the pros and cons of microservices vs monolithic architecture.",
        run_config=RunConfig(
            model_provider=hanzo_provider,
            model="gpt-4"  # More capable for complex analysis
        )
    )
    print(f"Detailed analysis: {result.final_output[:200]}...")


# Example 4: Production Configuration
class ProductionHanzoProvider(HanzoModelProvider):
    """Production-ready provider with additional configuration."""
    
    def __init__(self):
        # In production, load from secure configuration
        base_url = os.getenv("HANZO_ROUTER_URL", "https://router.hanzo.ai/v1")
        api_key = os.getenv("HANZO_API_KEY")
        
        if not api_key:
            raise ValueError("HANZO_API_KEY environment variable is required")
        
        super().__init__(base_url=base_url, api_key=api_key)
        
        # Additional configuration
        self.client.timeout = 30.0  # 30 second timeout
        self.client.max_retries = 3


async def main():
    """Run all examples."""
    print("="*60)
    print("Hanzo Agent SDK - Backend Integration Examples")
    print("="*60)
    print(f"\nUsing Hanzo Router at: {HANZO_ROUTER_URL}")
    print("Make sure the Router is running locally or update HANZO_ROUTER_URL")
    
    try:
        await basic_example()
        await tools_example()
        await multi_model_example()
        
        print("\n" + "="*60)
        print("✓ All examples completed successfully!")
        print("\nTo use in your own code:")
        print("1. Set HANZO_ROUTER_URL to your Router endpoint")
        print("2. Set HANZO_API_KEY to your Router API key")
        print("3. Use HanzoModelProvider with RunConfig")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure Hanzo Router is running: cd /path/to/services && make start-router")
        print("2. Check your HANZO_API_KEY is valid")
        print("3. Verify network connectivity to the Router")


if __name__ == "__main__":
    asyncio.run(main())