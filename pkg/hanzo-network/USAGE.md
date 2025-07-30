# Hanzo Network SDK - Complete Usage Guide

## Table of Contents
1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Core Concepts](#core-concepts)
5. [Building Agent Networks](#building-agent-networks)
6. [Local Compute](#local-compute)
7. [Routing Strategies](#routing-strategies)
8. [Tools and Actions](#tools-and-actions)
9. [State Management](#state-management)
10. [Production Deployment](#production-deployment)
11. [Examples](#examples)
12. [API Reference](#api-reference)

## Overview

Hanzo Network is a powerful framework for creating and managing networks of AI agents, designed for building scalable, distributed AI workflows. It provides:

- **Agent Networks**: Orchestrate multiple AI agents working together
- **Local Compute**: Run AI models locally with hanzo.network integration
- **Flexible Routing**: Dynamic agent selection based on task requirements
- **State Management**: Shared state across agent networks
- **Tool Integration**: Extensible tool system for agent capabilities
- **Production Ready**: Built-in monitoring, error handling, and scaling

## Installation

```bash
# Basic installation
pip install hanzo-network

# With all dependencies
pip install hanzo-network[all]

# For development
pip install hanzo-network[dev]
```

## Quick Start

```python
from hanzo_network import create_network, create_agent, NetworkState
from dataclasses import dataclass
from typing import Optional

# Define your state
@dataclass
class TaskState(NetworkState):
    task: str
    result: Optional[str] = None
    done: bool = False

# Create agents
planner = create_agent(
    name="planner",
    instructions="You are a planning agent. Create a plan for the given task.",
    model="gpt-4"
)

executor = create_agent(
    name="executor",
    instructions="You are an execution agent. Execute the plan step by step.",
    model="gpt-3.5-turbo"
)

# Define routing logic
def task_router(agents, state):
    if state.done:
        return None
    if not state.result:
        return planner
    return executor

# Create and run network
network = create_network(
    agents=[planner, executor],
    router=task_router,
    state=TaskState(task="Build a web scraper")
)

result = network.run()
print(f"Result: {result.state.result}")
```

## Core Concepts

### Agents

Agents are the fundamental units of work in Hanzo Network:

```python
from hanzo_network import Agent, create_agent

# Class-based agent
class ResearchAgent(Agent):
    name = "researcher"
    description = "Conducts research and analysis"
    model = "claude-3-opus"
    
    instructions = """You are an expert researcher.
    Find accurate information and provide detailed analysis."""
    
    tools = ["search", "analyze", "summarize"]

# Function-based agent
researcher = create_agent(
    name="researcher",
    instructions="Research the given topic thoroughly",
    model="gpt-4",
    tools=["web_search", "document_analysis"]
)
```

### Networks

Networks orchestrate agent execution:

```python
from hanzo_network import Network, create_network

# Create network with configuration
network = create_network(
    agents=[agent1, agent2, agent3],
    router=routing_function,
    state=initial_state,
    max_iterations=50,
    checkpoint_interval=10
)

# Run network
result = network.run()

# Access results
final_state = result.state
execution_history = result.history
```

### Routers

Routers determine which agent to execute next:

```python
from hanzo_network import create_router, create_routing_agent

# Function-based router
def conditional_router(agents, state):
    if state.needs_research:
        return agents["researcher"]
    elif state.needs_analysis:
        return agents["analyst"]
    return None

# LLM-based routing agent
routing_agent = create_routing_agent(
    model="gpt-4",
    instructions="""Based on the current state, decide which agent should run next:
    - researcher: For gathering information
    - analyst: For processing data
    - writer: For creating content"""
)

# Hybrid router
hybrid_router = create_router(
    agents=agents,
    routing_agent=routing_agent,
    fallback=conditional_router
)
```

## Building Agent Networks

### Sequential Pipeline

```python
@dataclass
class PipelineState(NetworkState):
    input_data: str
    cleaned_data: Optional[str] = None
    analyzed_data: Optional[dict] = None
    report: Optional[str] = None
    done: bool = False

# Create specialized agents
cleaner = create_agent(
    name="cleaner",
    instructions="Clean and normalize the input data",
    tools=["data_cleaning", "validation"]
)

analyzer = create_agent(
    name="analyzer",
    instructions="Analyze the cleaned data for insights",
    tools=["statistical_analysis", "visualization"]
)

reporter = create_agent(
    name="reporter",
    instructions="Generate a comprehensive report",
    tools=["report_generation", "formatting"]
)

# Sequential router
def pipeline_router(agents, state):
    if state.done:
        return None
    if not state.cleaned_data:
        return agents["cleaner"]
    if not state.analyzed_data:
        return agents["analyzer"]
    if not state.report:
        return agents["reporter"]
    state.done = True
    return None

# Run pipeline
pipeline = create_network(
    agents=[cleaner, analyzer, reporter],
    router=pipeline_router,
    state=PipelineState(input_data="raw data...")
)
```

### Parallel Processing

```python
from hanzo_network import ParallelNetwork

# Define parallel tasks
parallel_network = ParallelNetwork(
    agents={
        "scraper1": create_agent("scraper1", "Scrape website A"),
        "scraper2": create_agent("scraper2", "Scrape website B"),
        "scraper3": create_agent("scraper3", "Scrape website C"),
    },
    aggregator=create_agent("aggregator", "Combine all scraped data"),
    state=ScrapingState()
)

# Run all scrapers in parallel, then aggregate
result = await parallel_network.run_async()
```

### Hierarchical Networks

```python
# Sub-network for research
research_network = create_network(
    agents=[web_searcher, paper_reader, note_taker],
    router=research_router,
    state=ResearchState()
)

# Sub-network for writing
writing_network = create_network(
    agents=[outliner, writer, editor],
    router=writing_router,
    state=WritingState()
)

# Main orchestrator
main_network = create_network(
    agents=[
        create_agent("research_lead", network=research_network),
        create_agent("writing_lead", network=writing_network),
        create_agent("reviewer", "Review the final output")
    ],
    router=main_router,
    state=ProjectState()
)
```

## Local Compute

Hanzo Network includes powerful local compute capabilities:

```python
from hanzo_network import LocalComputeOrchestrator, ModelConfig, ModelProvider

# Initialize local compute
orchestrator = LocalComputeOrchestrator()

# Add local models
orchestrator.add_model(ModelConfig(
    name="llama-7b",
    provider=ModelProvider.LLAMA_CPP,
    model_path="/path/to/llama-7b.gguf",
    context_length=4096,
    gpu_layers=35  # Use GPU acceleration
))

orchestrator.add_model(ModelConfig(
    name="codellama-13b",
    provider=ModelProvider.LLAMA_CPP,
    model_path="/path/to/codellama-13b.gguf",
    context_length=8192,
    gpu_layers=40
))

# Create agent using local model
local_agent = create_agent(
    name="local_coder",
    instructions="You are a helpful coding assistant",
    model="local:codellama-13b",  # Use local model
    compute_provider=orchestrator
)

# Run inference
result = await local_agent.run_async(
    "Write a Python function to sort a list"
)
```

### Load Balancing

```python
# Create compute nodes
node1 = LocalComputeNode(
    node_id="gpu-server-1",
    models=["llama-70b", "mixtral-8x7b"],
    max_concurrent=4
)

node2 = LocalComputeNode(
    node_id="gpu-server-2", 
    models=["llama-70b", "codellama-34b"],
    max_concurrent=4
)

# Orchestrator handles load balancing
orchestrator = LocalComputeOrchestrator(
    nodes=[node1, node2],
    strategy="least_loaded"  # or "round_robin", "model_affinity"
)

# Requests are automatically distributed
network = create_network(
    agents=[agent1, agent2, agent3],
    compute_provider=orchestrator
)
```

## Routing Strategies

### State-Based Routing

```python
def state_machine_router(agents, state):
    """Route based on state machine transitions"""
    transitions = {
        "init": "data_collector",
        "collected": "processor",
        "processed": "validator",
        "validated": "reporter",
        "reported": None
    }
    
    current_phase = state.phase
    next_agent_name = transitions.get(current_phase)
    
    if next_agent_name:
        return agents[next_agent_name]
    return None
```

### Score-Based Routing

```python
def score_based_router(agents, state):
    """Route to agent with highest relevance score"""
    scores = {}
    
    for name, agent in agents.items():
        # Calculate relevance score
        score = 0
        if state.needs_technical and "technical" in agent.capabilities:
            score += 10
        if state.urgency == "high" and agent.speed_rating > 8:
            score += 5
        if state.complexity == "high" and agent.expertise_level > 9:
            score += 8
        
        scores[name] = score
    
    # Return highest scoring agent
    if scores:
        best_agent = max(scores, key=scores.get)
        if scores[best_agent] > 0:
            return agents[best_agent]
    
    return None
```

### Consensus Routing

```python
from hanzo_network import ConsensusRouter

# Multiple agents vote on next action
consensus_router = ConsensusRouter(
    voters=[
        create_agent("strategist", "Decide strategic direction"),
        create_agent("analyst", "Analyze current situation"),
        create_agent("coordinator", "Coordinate team efforts")
    ],
    candidates=["researcher", "developer", "tester", "deployer"],
    threshold=0.6  # 60% agreement required
)
```

## Tools and Actions

### Creating Tools

```python
from hanzo_network import Tool, create_tool

# Class-based tool
class DatabaseTool(Tool):
    name = "database"
    description = "Query and update database"
    
    async def execute(self, action: str, query: str, state):
        if action == "query":
            results = await self.db.query(query)
            state.query_results = results
            return f"Found {len(results)} records"
        elif action == "update":
            affected = await self.db.update(query)
            return f"Updated {affected} records"

# Function-based tool
async def web_search_tool(query: str, max_results: int = 10, state=None):
    """Search the web for information"""
    results = await search_engine.search(query, max_results)
    if state:
        state.search_results = results
    return f"Found {len(results)} results for '{query}'"

# Register tool
search_tool = create_tool(
    name="web_search",
    description="Search the web",
    function=web_search_tool
)
```

### Tool Composition

```python
# Composite tool that uses multiple sub-tools
class ResearchTool(Tool):
    name = "research"
    description = "Comprehensive research tool"
    
    def __init__(self):
        self.search = WebSearchTool()
        self.scrape = WebScraperTool()
        self.summarize = SummarizerTool()
        self.cite = CitationTool()
    
    async def execute(self, topic: str, depth: str = "medium", state=None):
        # Search for sources
        sources = await self.search.execute(topic, max_results=20)
        
        # Scrape content
        contents = []
        for source in sources[:10]:
            content = await self.scrape.execute(source.url)
            contents.append(content)
        
        # Summarize findings
        summary = await self.summarize.execute(contents, length=depth)
        
        # Add citations
        cited_summary = await self.cite.execute(summary, sources)
        
        if state:
            state.research_result = cited_summary
        
        return cited_summary
```

## State Management

### Shared State

```python
from hanzo_network import SharedState, StateManager

@dataclass
class ProjectState(SharedState):
    project_id: str
    tasks: List[Task] = field(default_factory=list)
    completed_tasks: Set[str] = field(default_factory=set)
    team_members: Dict[str, Agent] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    
    def add_task(self, task: Task):
        self.tasks.append(task)
        self.emit_change("task_added", task)
    
    def complete_task(self, task_id: str):
        self.completed_tasks.add(task_id)
        self.emit_change("task_completed", task_id)
        self.update_metrics()

# State manager handles persistence and synchronization
state_manager = StateManager(
    state_class=ProjectState,
    persistence="redis",  # or "memory", "postgres"
    sync_interval=5  # seconds
)

# Networks share state
network1 = create_network(agents=[...], state_manager=state_manager)
network2 = create_network(agents=[...], state_manager=state_manager)
```

### State Versioning

```python
# Enable state history
state_manager = StateManager(
    state_class=ProjectState,
    enable_history=True,
    max_history=100
)

# Access state history
history = state_manager.get_history()
for version in history:
    print(f"Version {version.id} at {version.timestamp}")
    print(f"Changed by: {version.agent}")
    print(f"Changes: {version.diff}")

# Rollback to previous state
state_manager.rollback(version_id="v123")
```

## Production Deployment

### Configuration

```yaml
# network_config.yaml
network:
  name: "production-pipeline"
  max_iterations: 100
  timeout: 3600
  checkpoint_interval: 10
  
agents:
  - name: "data-processor"
    model: "gpt-4"
    temperature: 0.2
    max_retries: 3
    timeout: 300
    
  - name: "quality-checker"
    model: "claude-3-opus"
    temperature: 0.1
    tools: ["validation", "testing"]
    
compute:
  provider: "local"
  nodes:
    - id: "gpu-1"
      models: ["llama-70b", "mixtral-8x7b"]
      gpu: true
      max_concurrent: 4
      
monitoring:
  metrics_port: 9090
  enable_tracing: true
  trace_endpoint: "http://jaeger:14268"
  
persistence:
  state_store: "redis"
  redis_url: "redis://localhost:6379"
  checkpoint_dir: "/var/lib/hanzo/checkpoints"
```

### Deployment Script

```python
from hanzo_network import NetworkDeployment
import yaml

# Load configuration
with open("network_config.yaml") as f:
    config = yaml.safe_load(f)

# Create deployment
deployment = NetworkDeployment(config)

# Add health checks
deployment.add_health_check("/health", interval=30)

# Add monitoring
deployment.enable_prometheus_metrics(port=9090)
deployment.enable_opentelemetry_tracing(
    endpoint="http://jaeger:14268"
)

# Deploy with auto-scaling
deployment.deploy(
    min_replicas=2,
    max_replicas=10,
    scale_metric="cpu",
    scale_threshold=0.7
)
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Run network
CMD ["hanzo-network", "run", "--config", "network_config.yaml"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hanzo-network
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hanzo-network
  template:
    metadata:
      labels:
        app: hanzo-network
    spec:
      containers:
      - name: network
        image: hanzo/network:latest
        ports:
        - containerPort: 8080  # API
        - containerPort: 9090  # Metrics
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
            nvidia.com/gpu: "1"  # For local models
```

## Examples

### Customer Support Network

```python
@dataclass
class SupportState(NetworkState):
    customer_query: str
    customer_id: str
    ticket_id: Optional[str] = None
    knowledge_base_results: List[dict] = field(default_factory=list)
    suggested_solution: Optional[str] = None
    customer_satisfied: bool = False
    escalated: bool = False

# Agents
classifier = create_agent(
    name="classifier",
    instructions="Classify the customer query type and urgency",
    tools=["classify_query", "check_customer_history"]
)

kb_searcher = create_agent(
    name="kb_searcher",
    instructions="Search knowledge base for solutions",
    tools=["search_kb", "rank_solutions"]
)

solution_provider = create_agent(
    name="solution_provider",
    instructions="Provide solution to customer",
    tools=["generate_response", "send_email"]
)

escalation_agent = create_agent(
    name="escalator",
    instructions="Escalate to human support",
    tools=["create_ticket", "notify_support_team"]
)

# Router
def support_router(agents, state):
    if state.customer_satisfied or state.escalated:
        return None
    
    if not state.ticket_id:
        return agents["classifier"]
    
    if not state.knowledge_base_results:
        return agents["kb_searcher"]
    
    if not state.suggested_solution:
        return agents["solution_provider"]
    
    if state.customer_satisfied:
        return None
    
    return agents["escalator"]

# Create support network
support_network = create_network(
    agents=[classifier, kb_searcher, solution_provider, escalation_agent],
    router=support_router,
    state=SupportState(
        customer_query="My order hasn't arrived",
        customer_id="cust_123"
    )
)
```

### Code Review Network

```python
@dataclass
class CodeReviewState(NetworkState):
    pr_url: str
    files_changed: List[str] = field(default_factory=list)
    issues_found: List[dict] = field(default_factory=list)
    suggestions: List[dict] = field(default_factory=list)
    approved: bool = False
    changes_requested: bool = False

# Specialized review agents
security_reviewer = create_agent(
    name="security",
    instructions="Review code for security vulnerabilities",
    model="claude-3-opus",
    tools=["static_analysis", "dependency_check"]
)

performance_reviewer = create_agent(
    name="performance",
    instructions="Review code for performance issues",
    model="gpt-4",
    tools=["profile_code", "benchmark"]
)

style_reviewer = create_agent(
    name="style",
    instructions="Review code style and conventions",
    model="gpt-3.5-turbo",
    tools=["linter", "formatter"]
)

final_reviewer = create_agent(
    name="final",
    instructions="Make final review decision",
    model="claude-3-opus"
)

# Parallel review network
review_network = ParallelNetwork(
    agents=[security_reviewer, performance_reviewer, style_reviewer],
    aggregator=final_reviewer,
    state=CodeReviewState(pr_url="https://github.com/...")
)
```

### Research and Writing Network

```python
@dataclass
class ResearchWritingState(NetworkState):
    topic: str
    research_depth: str = "comprehensive"
    target_audience: str = "general"
    sources: List[dict] = field(default_factory=list)
    outline: Optional[dict] = None
    draft: Optional[str] = None
    final_article: Optional[str] = None
    done: bool = False

# Research team
researcher = create_agent(
    name="researcher",
    instructions="Conduct thorough research on the topic",
    tools=["web_search", "academic_search", "fact_check"]
)

outliner = create_agent(
    name="outliner",
    instructions="Create detailed article outline",
    tools=["structure_content", "identify_key_points"]
)

writer = create_agent(
    name="writer",
    instructions="Write engaging content based on research",
    tools=["generate_text", "cite_sources"]
)

editor = create_agent(
    name="editor",
    instructions="Edit and refine the article",
    tools=["grammar_check", "style_improve", "fact_verify"]
)

# Create research and writing pipeline
rw_network = create_network(
    agents=[researcher, outliner, writer, editor],
    router=sequential_router([researcher, outliner, writer, editor]),
    state=ResearchWritingState(
        topic="The Future of AI Agents",
        research_depth="comprehensive",
        target_audience="technical"
    )
)
```

## API Reference

### Core Classes

```python
# Agent base class
class Agent:
    name: str
    description: str
    instructions: str
    model: str
    tools: List[str]
    temperature: float = 0.7
    max_tokens: int = 4000
    
    async def run(self, state: NetworkState) -> AgentResponse
    async def run_with_tools(self, state: NetworkState) -> AgentResponse

# Network class
class Network:
    agents: Dict[str, Agent]
    router: Router
    state: NetworkState
    max_iterations: int = 100
    
    def run(self) -> NetworkResult
    async def run_async(self) -> NetworkResult
    def checkpoint(self) -> None
    def restore(self, checkpoint_path: str) -> None

# Router base class
class Router:
    def select_agent(self, agents: Dict[str, Agent], state: NetworkState) -> Optional[Agent]
    async def select_agent_async(self, agents: Dict[str, Agent], state: NetworkState) -> Optional[Agent]
```

### Factory Functions

```python
# Create agent
def create_agent(
    name: str,
    instructions: str,
    model: str = "gpt-4",
    tools: List[str] = None,
    **kwargs
) -> Agent

# Create network
def create_network(
    agents: List[Agent],
    router: Union[Router, Callable],
    state: NetworkState,
    **kwargs
) -> Network

# Create router
def create_router(
    agents: List[Agent],
    routing_agent: Optional[Agent] = None,
    fallback: Optional[Callable] = None
) -> Router

# Create tool
def create_tool(
    name: str,
    description: str,
    function: Callable
) -> Tool
```

### Local Compute

```python
# Compute orchestrator
class LocalComputeOrchestrator:
    def add_model(self, config: ModelConfig) -> None
    def add_node(self, node: LocalComputeNode) -> None
    async def run_inference(self, request: InferenceRequest) -> InferenceResult
    def get_stats(self) -> Dict[str, Any]

# Model configuration
@dataclass
class ModelConfig:
    name: str
    provider: ModelProvider
    model_path: str
    context_length: int = 4096
    gpu_layers: int = 0
    threads: int = 4
```

### State Management

```python
# Network state base class
class NetworkState:
    def to_dict(self) -> Dict[str, Any]
    def from_dict(cls, data: Dict[str, Any]) -> NetworkState
    def validate(self) -> bool
    def emit_change(self, event: str, data: Any) -> None

# State manager
class StateManager:
    def get_state(self) -> NetworkState
    def update_state(self, updates: Dict[str, Any]) -> None
    def get_history(self) -> List[StateVersion]
    def rollback(self, version_id: str) -> None
```

## Best Practices

1. **Agent Design**: Keep agents focused on single responsibilities
2. **State Management**: Use immutable state updates when possible
3. **Error Handling**: Implement retry logic and graceful degradation
4. **Tool Safety**: Validate tool inputs and handle errors appropriately
5. **Router Optimization**: Keep routing logic simple and deterministic
6. **Testing**: Test agents, tools, and routers independently
7. **Monitoring**: Use metrics and tracing in production
8. **Security**: Never expose API keys or sensitive data in state

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure hanzo-network and dependencies are installed
2. **Model Loading**: Check model paths and GPU availability
3. **State Synchronization**: Verify Redis/database connections
4. **Memory Issues**: Use streaming for large responses
5. **Performance**: Enable GPU acceleration for local models

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Create network with debug mode
network = create_network(
    agents=agents,
    router=router,
    state=state,
    debug=True,  # Enables detailed logging
    trace_execution=True  # Records all decisions
)

# Access debug information
print(network.execution_trace)
print(network.decision_log)
```

For more help, see our [GitHub issues](https://github.com/hanzoai/network/issues).