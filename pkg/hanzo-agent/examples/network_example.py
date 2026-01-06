"""Example demonstrating agent networks with routing and state sharing."""

import asyncio
from typing import Any, Dict

from agents import (
    Agent,
    AgentNetwork,
    NetworkConfig,
    SemanticRouter,
    RuleBasedRouter,
    routing_strategy,
    InMemoryStateStore,
    Memory,
    MemoryType,
    Orchestrator,
    OrchestrationConfig,
    function_tool,
    Runner,
)


# Define specialized agents
research_agent = Agent(
    name="research_agent",
    instructions="""You are a research specialist. You excel at:
    - Finding information on any topic
    - Analyzing data and trends
    - Summarizing complex information
    - Providing citations and sources
    
    When you receive a research request, provide thorough, well-sourced information.""",
    handoff_description="Handles research, data gathering, and analysis tasks",
)

writer_agent = Agent(
    name="writer_agent",
    instructions="""You are a writing specialist. You excel at:
    - Creating engaging content
    - Adapting tone and style
    - Structuring documents
    - Editing and proofreading
    
    When you receive a writing request, create polished, well-structured content.""",
    handoff_description="Handles content creation, editing, and writing tasks",
)

coder_agent = Agent(
    name="coder_agent",
    instructions="""You are a coding specialist. You excel at:
    - Writing clean, efficient code
    - Debugging and optimization
    - System design and architecture
    - Code reviews and best practices
    
    When you receive a coding request, provide working, well-documented solutions.""",
    handoff_description="Handles programming, debugging, and technical implementation",
)

coordinator_agent = Agent(
    name="coordinator_agent",
    instructions="""You are a project coordinator. You:
    - Break down complex tasks
    - Delegate to appropriate specialists
    - Ensure quality and consistency
    - Synthesize results from multiple agents
    
    Analyze each request and coordinate with the right specialists.""",
    handoff_description="Main coordinator that delegates tasks to specialists",
)


# Tools for agents
@function_tool
async def save_to_memory(ctx, key: str, value: str) -> str:
    """Save information to shared memory for other agents to access."""
    # Access network context
    if hasattr(ctx, 'network'):
        await ctx.set_state(key, value, namespace="shared")
        return f"Saved '{key}' to shared memory"
    return "Memory not available"


@function_tool
async def recall_from_memory(ctx, key: str) -> str:
    """Recall information from shared memory."""
    if hasattr(ctx, 'network'):
        value = await ctx.get_state(key, namespace="shared")
        if value:
            return f"Retrieved from memory: {value}"
        return f"No memory found for key '{key}'"
    return "Memory not available"


@function_tool
async def list_memories(ctx) -> str:
    """List all keys in shared memory."""
    if hasattr(ctx, 'network'):
        keys = await ctx.state_store.keys(namespace="shared")
        if keys:
            return f"Memory keys: {', '.join(keys)}"
        return "No memories stored"
    return "Memory not available"


# Add tools to agents
research_agent.tools = [save_to_memory, recall_from_memory, list_memories]
writer_agent.tools = [save_to_memory, recall_from_memory, list_memories]
coder_agent.tools = [save_to_memory, recall_from_memory, list_memories]
coordinator_agent.tools = [save_to_memory, recall_from_memory, list_memories]


async def basic_network_example():
    """Basic example of agent network with semantic routing."""
    print("=== Basic Network Example ===\n")
    
    # Create network with semantic router
    network = AgentNetwork(
        config=NetworkConfig(name="Research Network"),
        router=SemanticRouter(),
    )
    
    # Add agents with capabilities
    network.add_agent(
        research_agent,
        capabilities=["research", "analysis", "data", "information"],
    )
    network.add_agent(
        writer_agent,
        capabilities=["writing", "content", "editing", "documentation"],
    )
    network.add_agent(
        coder_agent,
        capabilities=["coding", "programming", "debugging", "implementation"],
    )
    
    # Test routing
    queries = [
        "Research the latest trends in AI",
        "Write a blog post about climate change",
        "Debug this Python function that's not working",
    ]
    
    for query in queries:
        print(f"Query: {query}")
        result = await network.run(input=query, max_turns=1)
        print(f"Response: {result.final_output}\n")


async def advanced_network_with_rules():
    """Advanced example with rule-based routing and state sharing."""
    print("\n=== Advanced Network with Rules ===\n")
    
    # Create router with rules
    router = RuleBasedRouter()
    router.add_rule(r"research|analyze|find", "research_agent", priority=10)
    router.add_rule(r"write|draft|compose", "writer_agent", priority=10)
    router.add_rule(r"code|program|debug|implement", "coder_agent", priority=10)
    
    # Create network with state store
    state_store = InMemoryStateStore()
    network = AgentNetwork(
        config=NetworkConfig(
            name="Advanced Network",
            state_store=state_store,
        ),
        router=router,
    )
    
    # Add agents
    network.add_agent(research_agent)
    network.add_agent(writer_agent)
    network.add_agent(coder_agent)
    
    # Complex task that requires multiple agents
    print("Task: Research AI trends and write a technical blog post\n")
    
    # Step 1: Research
    result1 = await network.run(
        input="Research the top 3 AI trends in 2024 and save them to memory",
        starting_agent="research_agent",
    )
    print(f"Research complete: {result1.final_output}\n")
    
    # Step 2: Write based on research
    result2 = await network.run(
        input="Recall the AI trends from memory and write a technical blog post about them",
        starting_agent="writer_agent",
    )
    print(f"Blog post: {result2.final_output}\n")


async def orchestrated_workflow_example():
    """Example using the orchestrator for complex workflows."""
    print("\n=== Orchestrated Workflow Example ===\n")
    
    # Create orchestrator
    orchestrator = Orchestrator(
        config=OrchestrationConfig(
            name="AI Project Orchestrator",
            enable_ui_streaming=True,
        ),
    )
    
    # Register agents
    orchestrator.register_agent(coordinator_agent, capabilities=["coordination"])
    orchestrator.register_agent(research_agent, capabilities=["research"])
    orchestrator.register_agent(writer_agent, capabilities=["writing"])
    orchestrator.register_agent(coder_agent, capabilities=["coding"])
    
    # Create a workflow
    workflow = orchestrator.create_workflow_from_agents(
        name="AI Article Workflow",
        agents=["coordinator_agent"],
    )
    
    # Register and execute workflow
    orchestrator.register_workflow(workflow)
    
    result = await orchestrator.execute_workflow(
        workflow_id=workflow.id,
        input="""Create a comprehensive guide about implementing 
        a simple neural network in Python. Include:
        1. Research on neural network basics
        2. Code implementation
        3. Well-written explanation
        """,
    )
    
    print(f"Workflow completed: {result.success}")
    print(f"Duration: {result.duration:.2f}s")
    print(f"Output: {result.output}")


async def memory_system_example():
    """Example demonstrating the memory system."""
    print("\n=== Memory System Example ===\n")
    
    # Create memory system
    memory = Memory(max_entries=100)
    
    # Create memory-enabled agent
    memory_agent = Agent(
        name="memory_agent",
        instructions="""You are an agent with long-term memory.
        You can remember facts, conversations, and learn from experience.
        Always check your memory before responding.""",
    )
    
    # Wrap with memory capabilities
    memory_enabled = memory.create_agent_wrapper(memory_agent)
    
    # Store some memories
    await memory.remember(
        "The user's favorite color is blue",
        type=MemoryType.FACT,
        agent_name="memory_agent",
    )
    
    await memory.remember(
        "The user is interested in machine learning",
        type=MemoryType.FACT,
        agent_name="memory_agent",
    )
    
    # Test memory recall
    result = await Runner.run(
        starting_agent=memory_enabled,
        input="What do you remember about me?",
    )
    
    print(f"Memory recall: {result.final_output}")
    
    # Generate reflection
    reflection = await memory.reflect(memory_agent)
    print(f"\nReflection: {reflection.content}")


async def parallel_network_example():
    """Example of parallel task execution in a network."""
    print("\n=== Parallel Network Execution ===\n")
    
    # Create network
    network = AgentNetwork(
        config=NetworkConfig(
            name="Parallel Network",
            enable_parallel_execution=True,
            max_parallel_agents=3,
        ),
    )
    
    # Add agents
    network.add_agent(research_agent)
    network.add_agent(writer_agent)
    network.add_agent(coder_agent)
    
    # Define parallel tasks
    tasks = [
        {"input": "Research quantum computing basics", "agent": "research_agent"},
        {"input": "Write a haiku about technology", "agent": "writer_agent"},
        {"input": "Implement a fibonacci function", "agent": "coder_agent"},
    ]
    
    print("Running 3 tasks in parallel...\n")
    
    start_time = asyncio.get_event_loop().time()
    results = await network.run_parallel(tasks)
    duration = asyncio.get_event_loop().time() - start_time
    
    for i, result in enumerate(results):
        print(f"Task {i+1} result: {result.final_output[:100]}...")
    
    print(f"\nTotal execution time: {duration:.2f}s")


async def main():
    """Run all examples."""
    await basic_network_example()
    await advanced_network_with_rules()
    await orchestrated_workflow_example()
    await memory_system_example()
    await parallel_network_example()


if __name__ == "__main__":
    asyncio.run(main())