#!/usr/bin/env python3
"""
Quick test of Agent SDK
"""

import os
import sys
sys.path.insert(0, 'src')

# For synchronous execution
from agents import Agent, Runner

# Create a simple agent
agent = Agent(
    name="MathHelper",
    instructions="You are a helpful assistant. Answer concisely.",
)

# Make sure we have an API key
if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
    # Set a dummy key for now
    os.environ["OPENAI_API_KEY"] = "sk-dummy"

print("Testing Agent SDK...")
print("Question: What's 1+2?")
print("-" * 40)

try:
    # Use the synchronous runner
    result = Runner.run_sync(agent, "What's 1+2?")
    print(f"Answer: {result.final_output}")
except Exception as e:
    print(f"Error: {e}")
    
    # Try with explicit provider
    print("\nTrying with Hanzo Router...")
    from agents.models.openai_provider import OpenAIProvider
    
    provider = OpenAIProvider(
        base_url="http://localhost:4000/v1",
        api_key="sk-1234"
    )
    
    try:
        from agents import RunConfig
        result = Runner.run_sync(
            agent, 
            "What's 1+2?",
            run_config=RunConfig(model_provider=provider, model="gpt-3.5-turbo")
        )
        print(f"Answer: {result.final_output}")
    except Exception as e2:
        print(f"Router Error: {e2}")