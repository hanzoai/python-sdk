#!/usr/bin/env python3
"""Example of using the unified Hanzo AI SDK.

This demonstrates:
1. Local AI cluster with exo
2. Agent networks 
3. MCP tools
4. Cloud AI fallback
"""

import asyncio
from hanzoai import cluster, agents, mcp, completion


async def main():
    """Run the example."""
    
    # 1. Start a local AI cluster
    print("Starting local AI cluster...")
    local_cluster = await cluster.start_local_cluster(
        name="my-cluster",
        model_path="~/.cache/huggingface/hub"  # Use local models
    )
    
    # 2. Create agents
    print("\nCreating AI agents...")
    
    # Local agent using the cluster
    local_agent = agents.create_agent(
        name="local-helper",
        model="llama-3.2-3b",  # Uses local cluster
        base_url=local_cluster.get_api_endpoint()
    )
    
    # Cloud agent as fallback
    cloud_agent = agents.create_agent(
        name="cloud-helper", 
        model="anthropic/claude-3-5-sonnet-20241022"
    )
    
    # 3. Create an agent network
    print("\nCreating agent network...")
    network = agents.create_network(
        agents=[local_agent, cloud_agent],
        router=agents.state_based_router()  # Smart routing
    )
    
    # 4. Create MCP server with tools
    print("\nStarting MCP server...")
    mcp_server = mcp.create_mcp_server(
        name="hanzo-unified",
        allowed_paths=[".", "/tmp"],
        enable_agent_tool=True
    )
    
    # 5. Example: Use local AI for simple tasks
    print("\n--- Local AI Example ---")
    local_result = await local_cluster.inference(
        prompt="Write a haiku about distributed AI",
        max_tokens=50
    )
    print(f"Local AI: {local_result}")
    
    # 6. Example: Use cloud AI for complex tasks
    print("\n--- Cloud AI Example ---")
    cloud_result = completion(
        model="anthropic/claude-3-5-sonnet-20241022",
        messages=[{
            "role": "user",
            "content": "Explain the benefits of local AI clusters"
        }]
    )
    print(f"Cloud AI: {cloud_result}")
    
    # 7. Join mining network (optional)
    if input("\nJoin mining network? (y/n): ").lower() == 'y':
        wallet = input("Enter wallet address: ")
        miner = await cluster.join_mining_network(
            wallet_address=wallet
        )
        print(f"Mining stats: {miner.get_stats()}")
    
    # Cleanup
    print("\nShutting down...")
    await local_cluster.stop()


if __name__ == "__main__":
    print("=== Hanzo AI Unified SDK Example ===")
    print("Local, Private, Free AI Infrastructure")
    print("=====================================\n")
    
    asyncio.run(main())