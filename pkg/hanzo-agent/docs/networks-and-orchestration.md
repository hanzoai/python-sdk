# Networks and Orchestration

The Hanzo Agent SDK now supports building complex multi-agent systems with intelligent routing, shared state, and orchestration capabilities inspired by AgentKit.

## Quick Start

```python
from agents import Agent, create_network, create_workflow
from agents.routers import SemanticRouter
from agents.state import InMemoryStateStore

# Create specialized agents
researcher = Agent(
    name="Researcher",
    instructions="You search and analyze information from various sources.",
    tools=[search_web, analyze_document]
)

writer = Agent(
    name="Writer", 
    instructions="You create well-structured content based on research.",
    tools=[format_markdown, check_grammar]
)

reviewer = Agent(
    name="Reviewer",
    instructions="You review content for accuracy and quality.",
    tools=[fact_check, suggest_improvements]
)

# Create a network with intelligent routing
network = create_network(
    agents=[researcher, writer, reviewer],
    router=SemanticRouter(),
    state_store=InMemoryStateStore(),
    default_model="gpt-4"
)

# Run the network
result = await network.run(
    "Write a comprehensive guide about quantum computing",
    max_iterations=10
)
```

## Core Concepts

### Networks

Networks are collections of agents that work together to accomplish complex tasks. They provide:

- **Intelligent Routing**: Automatically route requests to the most appropriate agent
- **Shared State**: Agents can share information through network state
- **Orchestration**: Control the flow of execution across multiple agents
- **Monitoring**: Track performance and execution across all agents

### Routers

Routers determine which agent should handle a given request. Available routers:

#### Semantic Router
Routes based on semantic understanding of agent capabilities:

```python
from agents.routers import SemanticRouter

router = SemanticRouter(
    model="text-embedding-3-small",
    similarity_threshold=0.7
)
```

#### Rule-Based Router
Routes using patterns and rules:

```python
from agents.routers import RuleBasedRouter

router = RuleBasedRouter()
router.add_rule(r".*search.*|.*find.*", "Researcher")
router.add_rule(r".*write.*|.*create.*", "Writer")
router.add_rule(r".*review.*|.*check.*", "Reviewer")
```

#### Load Balancing Router
Distributes work across agents:

```python
from agents.routers import LoadBalancingRouter

router = LoadBalancingRouter(
    strategy="round_robin",  # or "least_loaded", "random"
    health_check_interval=30
)
```

#### Composite Router
Combine multiple routing strategies:

```python
from agents.routers import RoutingStrategy

router = RoutingStrategy([
    (RuleBasedRouter(), 0.8),      # 80% weight
    (SemanticRouter(), 0.2)        # 20% weight
])
```

### State Management

Network state allows agents to share information:

```python
# In an agent
async def research_task(state, query):
    results = await search_web(query)
    
    # Store in shared state
    await state.set("research_results", results)
    await state.append("research_history", query)
    
    # Read from shared state
    previous = await state.get("previous_queries", [])
    
    return results

# Access state in network
network.state.set("project_context", context_data)
```

### Memory System

Agents can maintain different types of memory:

```python
from agents.memory import MemoryManager, VectorMemoryStore

# Create memory manager
memory = MemoryManager(
    store=VectorMemoryStore(collection_name="agent_memory"),
    enable_reflection=True,
    max_memories=1000
)

# Add to agent
agent = Agent(
    name="Assistant",
    instructions="...",
    memory=memory
)

# Memory is automatically managed during conversations
```

## Orchestration and Workflows

Build complex workflows with multiple agents:

```python
from agents import create_workflow, Step

workflow = create_workflow(
    name="Research and Write",
    agents=[researcher, writer, reviewer],
    steps=[
        Step.agent("researcher", "Research {topic}"),
        Step.parallel([
            Step.agent("writer", "Write introduction"),
            Step.agent("writer", "Write main content")
        ]),
        Step.agent("reviewer", "Review complete document"),
        Step.conditional(
            condition=lambda state: state.get("review_score") < 8,
            true_step=Step.agent("writer", "Revise based on feedback"),
            false_step=Step.transform(lambda x: {"status": "approved", "content": x})
        )
    ]
)

result = await workflow.run({"topic": "AI Safety"})
```

## Advanced Patterns

### Human in the Loop

```python
from agents.tools import human_approval_tool

agent = Agent(
    name="Assistant",
    tools=[human_approval_tool],
    instructions="Get human approval before making changes"
)
```

### UI Streaming

Stream updates to your UI in real-time:

```python
async def stream_handler(event):
    # Send to websocket, SSE, etc.
    await websocket.send_json({
        "type": event.type,
        "data": event.data
    })

result = await network.run(
    query,
    stream_callback=stream_handler
)
```

### Multi-Step Tools

Create tools that involve multiple steps:

```python
from agents.tools import create_composite_tool

research_and_summarize = create_composite_tool(
    name="research_and_summarize",
    tools=[search_web, extract_key_points, generate_summary],
    description="Research a topic and provide a summary"
)
```

### Deterministic State Routing

Route based on application state:

```python
def state_based_router(state, query):
    if state.get("mode") == "research":
        return "Researcher"
    elif state.get("mode") == "writing":
        return "Writer"
    else:
        return "Assistant"

network = create_network(
    agents=[...],
    router=state_based_router
)
```

## Integration with Hanzo Infrastructure

### Using with Hanzo Router

All network requests automatically route through the Hanzo Router:

```python
from agents.models import HanzoModelProvider

network = create_network(
    agents=[...],
    model_provider=HanzoModelProvider(
        base_url="http://localhost:4000/v1",
        api_key="your-key"
    )
)
```

### Distributed Execution

Networks can execute across different compute backends:

```python
# Configure agents for different backends
researcher = Agent(
    name="Researcher",
    compute_backend="hanzo-cloud"  # Centralized
)

processor = Agent(
    name="Processor",
    compute_backend="lux-network"  # Decentralized
)

validator = Agent(
    name="Validator",
    compute_backend="local"  # Local execution
)
```

### Observability

All network operations are automatically traced:

```python
# View in Hanzo Cloud dashboard
# http://localhost:3082/traces

# Or access programmatically
traces = network.get_traces()
for trace in traces:
    print(f"{trace.agent} -> {trace.duration}ms")
```

## Best Practices

1. **Design Focused Agents**: Each agent should have a specific role
2. **Use Appropriate Routers**: Choose routers based on your use case
3. **Manage State Carefully**: Don't store sensitive data in shared state
4. **Monitor Performance**: Use tracing to identify bottlenecks
5. **Test Networks**: Use mock agents for testing complex flows

## Examples

See the `examples/` directory for more examples:
- `network_example.py` - Basic multi-agent network
- `workflow_example.py` - Complex orchestrated workflow
- `memory_example.py` - Using the memory system
- `distributed_example.py` - Distributed agent execution