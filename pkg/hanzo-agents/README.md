# Hanzo Agents

[![PyPI](https://img.shields.io/pypi/v/hanzo-agents.svg)](https://pypi.org/project/hanzo-agents/)
[![Python Version](https://img.shields.io/pypi/pyversions/hanzo-agents.svg)](https://pypi.org/project/hanzo-agents/)

Advanced agent framework for building and orchestrating AI agents.

## Installation

```bash
pip install hanzo-agents
```

## Features

- **Agent Creation**: Build specialized AI agents
- **Swarm Orchestration**: Coordinate multiple agents
- **Tool Integration**: Equip agents with tools
- **Memory Systems**: Persistent agent memory
- **Hierarchical Control**: Parent-child agent relationships
- **Parallel Execution**: Run agents concurrently

## Quick Start

### Basic Agent

```python
from hanzo_agents import Agent

agent = Agent(
    name="assistant",
    model="gpt-4",
    instructions="You are a helpful assistant"
)

response = await agent.run("Help me with Python")
print(response)
```

### Agent Swarm

```python
from hanzo_agents import Agent, Swarm

# Create specialized agents
researcher = Agent(
    name="researcher",
    model="gpt-4",
    instructions="Research and analyze topics"
)

writer = Agent(
    name="writer",
    model="gpt-3.5-turbo",
    instructions="Write clear documentation"
)

# Create swarm
swarm = Swarm([researcher, writer])

# Run task
result = await swarm.run(
    "Research quantum computing and write a summary"
)
```

### Agent with Tools

```python
from hanzo_agents import Agent, Tool

# Define custom tool
def calculate(expression: str) -> float:
    """Calculate mathematical expression"""
    return eval(expression)

# Create agent with tool
agent = Agent(
    name="calculator",
    model="gpt-4",
    tools=[Tool(calculate)],
    instructions="You are a math assistant"
)

response = await agent.run("What is 25 * 4 + 10?")
```

## Advanced Usage

### Hierarchical Agents

```python
from hanzo_agents import Agent, HierarchicalSwarm

# Manager agent
manager = Agent(
    name="manager",
    model="gpt-4",
    instructions="Coordinate team members"
)

# Worker agents
workers = [
    Agent(name="dev1", model="gpt-3.5-turbo"),
    Agent(name="dev2", model="gpt-3.5-turbo"),
]

# Hierarchical swarm
swarm = HierarchicalSwarm(
    manager=manager,
    workers=workers
)

result = await swarm.run("Build a web application")
```

### Agent Memory

```python
from hanzo_agents import Agent, MemoryStore

# Create memory store
memory = MemoryStore()

# Agent with memory
agent = Agent(
    name="assistant",
    model="gpt-4",
    memory=memory
)

# Conversations are remembered
await agent.run("My name is Alice")
response = await agent.run("What's my name?")
# Response: "Your name is Alice"
```

### Parallel Execution

```python
from hanzo_agents import ParallelSwarm

swarm = ParallelSwarm([
    Agent(name="agent1", model="gpt-4"),
    Agent(name="agent2", model="gpt-3.5-turbo"),
    Agent(name="agent3", model="claude-2"),
])

# All agents work in parallel
results = await swarm.run_parallel([
    "Task 1",
    "Task 2",
    "Task 3"
])
```

## Agent Types

### Specialized Agents

```python
from hanzo_agents import (
    CodeAgent,
    ResearchAgent,
    WriterAgent,
    DataAgent
)

# Code generation agent
code_agent = CodeAgent(
    languages=["python", "javascript"],
    frameworks=["django", "react"]
)

# Research agent
research_agent = ResearchAgent(
    sources=["web", "papers", "docs"],
    depth="comprehensive"
)

# Writing agent
writer_agent = WriterAgent(
    style="technical",
    format="markdown"
)

# Data analysis agent
data_agent = DataAgent(
    tools=["pandas", "numpy", "matplotlib"]
)
```

## Configuration

### Agent Configuration

```python
agent = Agent(
    name="assistant",
    model="gpt-4",
    temperature=0.7,
    max_tokens=2000,
    timeout=30,
    retry_count=3,
    instructions="...",
    system_prompt="...",
    tools=[...],
    memory=...,
    callbacks=[...]
)
```

### Swarm Configuration

```python
swarm = Swarm(
    agents=[...],
    strategy="round_robin",  # round_robin, random, weighted
    max_concurrent=5,
    timeout=60,
    error_handling="continue"  # continue, stop, retry
)
```

## Callbacks and Events

```python
from hanzo_agents import Agent, EventCallback

class LoggingCallback(EventCallback):
    async def on_start(self, agent, task):
        print(f"{agent.name} starting: {task}")
    
    async def on_complete(self, agent, result):
        print(f"{agent.name} completed: {result}")
    
    async def on_error(self, agent, error):
        print(f"{agent.name} error: {error}")

agent = Agent(
    name="assistant",
    model="gpt-4",
    callbacks=[LoggingCallback()]
)
```

## Best Practices

1. **Agent Specialization**: Create focused agents with clear roles
2. **Resource Management**: Use appropriate models for tasks
3. **Error Handling**: Implement robust error recovery
4. **Memory Management**: Clean up memory periodically
5. **Tool Selection**: Choose minimal necessary tools
6. **Monitoring**: Track agent performance and costs

## Development

### Setup

```bash
cd pkg/hanzo-agents
uv sync --all-extras
```

### Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest tests/ --cov=hanzo_agents
```

### Building

```bash
uv build
```

## License

Apache License 2.0