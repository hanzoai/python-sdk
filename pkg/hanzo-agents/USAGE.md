# Hanzo Agents SDK - Complete Usage Guide

## Table of Contents
1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Core Concepts](#core-concepts)
4. [Building Agents](#building-agents)
5. [Creating Tools](#creating-tools)
6. [Designing Networks](#designing-networks)
7. [State Management](#state-management)
8. [Routing Strategies](#routing-strategies)
9. [Memory Systems](#memory-systems)
10. [Production Deployment](#production-deployment)
11. [Examples](#examples)
12. [API Reference](#api-reference)

## Installation

```bash
# Basic installation
pip install hanzo-agents

# With all optional dependencies
pip install hanzo-agents[all]

# For development
pip install hanzo-agents[dev]
```

## Quick Start

```python
from hanzo_agents import Agent, Network, State, Tool
from typing import Optional
from dataclasses import dataclass

# 1. Define your state
@dataclass
class TaskState(State):
    task: str
    plan: Optional[str] = None
    result: Optional[str] = None
    done: bool = False

# 2. Create tools
class PlanTool(Tool[TaskState]):
    name = "create_plan"
    description = "Create a plan for the task"
    
    def handle(self, plan: str, network):
        network.state.plan = plan
        return f"Plan created: {plan}"

# 3. Define agents
class PlannerAgent(Agent[TaskState]):
    name = "planner"
    description = "Creates plans for tasks"
    tools = [PlanTool()]
    
    system_prompt = """You are a planning expert. 
    Analyze the task and create a detailed plan."""

class ExecutorAgent(Agent[TaskState]):
    name = "executor"
    description = "Executes plans"
    
    system_prompt = """You are an execution expert.
    Follow the plan and complete the task."""

# 4. Create routing logic
def task_router(network, call_count, last_result, stack):
    s = network.state
    if s.done or call_count > 10:
        return None
    if not s.plan:
        return PlannerAgent
    if not s.result:
        return ExecutorAgent
    s.done = True
    return None

# 5. Run the network
network = Network(
    state=TaskState(task="Build a web scraper"),
    agents=[PlannerAgent, ExecutorAgent],
    router=task_router
)

result = network.run()
print(f"Final result: {result.state.result}")
```

## Core Concepts

### Agents
Agents are the core units of work. They encapsulate:
- A specific role or expertise
- A set of tools they can use
- System prompts and model configuration

```python
from hanzo_agents import Agent, Tool

class ResearchAgent(Agent[ProjectState]):
    name = "researcher"
    description = "Conducts research and analysis"
    model = "claude-3-opus"  # or any LiteLLM-supported model
    
    tools = [
        SearchTool(),
        AnalyzeTool(),
        SummarizeTool()
    ]
    
    system_prompt = """You are an expert researcher.
    Your goal is to find accurate, relevant information."""
    
    # Optional: Custom model parameters
    model_config = {
        "temperature": 0.7,
        "max_tokens": 4000
    }
```

### Tools
Tools enable agents to perform actions and modify state:

```python
from hanzo_agents import Tool
from pydantic import BaseModel, Field

class SearchTool(Tool[ProjectState]):
    name = "search"
    description = "Search for information on a topic"
    
    class Parameters(BaseModel):
        query: str = Field(description="Search query")
        max_results: int = Field(default=10, description="Maximum results")
    
    def handle(self, query: str, max_results: int, network):
        # Perform the search (mock example)
        results = perform_search(query, max_results)
        
        # Modify state
        network.state.search_results = results
        
        # Return feedback to agent
        return f"Found {len(results)} results for '{query}'"
```

### Networks
Networks orchestrate agent execution:

```python
from hanzo_agents import Network, MemoryKV, MemoryVector

# Basic network
network = Network(
    state=initial_state,
    agents=[Agent1, Agent2, Agent3],
    router=routing_function
)

# Network with memory
network = Network(
    state=initial_state,
    agents=agents,
    router=router,
    memory_kv=SQLiteKV("project.db"),
    memory_vector=FAISSVector(dimension=1536)
)

# Network with checkpointing
network = Network(
    state=initial_state,
    agents=agents,
    router=router,
    checkpoint_path="checkpoints/project.chkpt"
)
```

## Building Agents

### Basic Agent

```python
class SimpleAgent(Agent[MyState]):
    name = "simple"
    description = "A simple agent"
    
    async def run(self, state: MyState, history: History) -> InferenceResult:
        # Custom execution logic
        prompt = self.build_prompt(state, history)
        result = await self.model.generate(prompt)
        return result
```

### Agent with Tools

```python
class AdvancedAgent(Agent[MyState]):
    name = "advanced"
    description = "Agent with multiple tools"
    
    tools = [
        FileTool(),
        DatabaseTool(),
        APICaller(),
        Calculator()
    ]
    
    # Tools are automatically made available to the LLM
```

### Agent with Memory

```python
class MemoryAgent(Agent[MyState]):
    name = "memory"
    description = "Agent that uses long-term memory"
    
    async def run(self, state: MyState, history: History) -> InferenceResult:
        # Query relevant memories
        context = await self.network.memory.vector.query(
            query=state.current_task,
            k=5
        )
        
        # Include in prompt
        prompt = f"""
        Task: {state.current_task}
        
        Relevant context from memory:
        {context}
        
        Please proceed with the task.
        """
        
        return await self.model.generate(prompt)
```

## Creating Tools

### Simple Tool

```python
class PrintTool(Tool[MyState]):
    name = "print"
    description = "Print a message"
    
    def handle(self, message: str, network):
        print(message)
        return "Message printed"
```

### Tool with Validation

```python
class CreateFileTool(Tool[MyState]):
    name = "create_file"
    description = "Create a new file"
    
    class Parameters(BaseModel):
        filename: str = Field(pattern=r'^[\w\-. ]+$')
        content: str
        overwrite: bool = False
    
    def handle(self, filename: str, content: str, overwrite: bool, network):
        path = Path(filename)
        
        if path.exists() and not overwrite:
            return f"Error: File {filename} already exists"
        
        path.write_text(content)
        network.state.files_created.append(filename)
        
        return f"Created file: {filename}"
```

### Async Tool

```python
class APITool(Tool[MyState]):
    name = "api_call"
    description = "Make an API request"
    
    async def handle_async(self, url: str, method: str, network):
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url) as response:
                data = await response.json()
                network.state.api_responses.append(data)
                return f"API call successful: {response.status}"
```

## Designing Networks

### Sequential Network

```python
def sequential_router(network, call_count, last_result, stack):
    """Execute agents in sequence"""
    agents = [PrepAgent, MainAgent, CleanupAgent]
    
    if call_count >= len(agents):
        return None
    
    return agents[call_count]
```

### Conditional Network

```python
def conditional_router(network, call_count, last_result, stack):
    """Route based on state conditions"""
    s = network.state
    
    if s.error:
        return ErrorHandler
    elif not s.data_loaded:
        return DataLoader
    elif not s.processed:
        return Processor
    elif not s.validated:
        return Validator
    else:
        return None
```

### Hybrid Router

```python
from hanzo_agents import HybridRouter

# Combines deterministic and LLM-based routing
hybrid_router = HybridRouter(
    agents=[Agent1, Agent2, Agent3],
    model="gpt-4",
    system_prompt="""
    You are a routing expert. Based on the current state,
    decide which agent should handle the next step.
    """
)

network = Network(
    state=state,
    agents=[Agent1, Agent2, Agent3],
    router=hybrid_router
)
```

## State Management

### Basic State

```python
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class ProjectState(State):
    # Required fields
    project_name: str
    tasks: List[str]
    
    # Optional fields with defaults
    completed_tasks: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    error: Optional[str] = None
    done: bool = False
```

### State Guards

```python
from hanzo_agents import StateGuard

class BudgetGuard(StateGuard[ProjectState]):
    """Ensure budget constraints are met"""
    
    def check(self, state: ProjectState) -> bool:
        return state.total_cost <= state.budget_limit
    
    def message(self) -> str:
        return "Budget limit exceeded"

# Apply guards to state
state = ProjectState(
    project_name="My Project",
    budget_limit=10000,
    guards=[BudgetGuard()]
)
```

### State History

```python
# Access state history
for version in network.state_history:
    print(f"Version {version.version} at {version.timestamp}")
    print(f"State: {version.state}")
    print(f"Changed by: {version.agent_name}")
```

## Routing Strategies

### State-Based Router

```python
def state_based_router(network, call_count, last_result, stack):
    """Route based on state machine"""
    s = network.state
    
    state_machine = {
        "init": PlannerAgent,
        "planning": DesignerAgent,
        "designing": BuilderAgent,
        "building": TesterAgent,
        "testing": DeployerAgent,
        "deploying": None
    }
    
    return state_machine.get(s.current_phase)
```

### Priority Router

```python
def priority_router(network, call_count, last_result, stack):
    """Route based on task priority"""
    s = network.state
    
    # Find highest priority incomplete task
    for task in sorted(s.tasks, key=lambda t: t.priority, reverse=True):
        if not task.completed:
            if task.type == "research":
                return ResearchAgent
            elif task.type == "code":
                return CoderAgent
            elif task.type == "review":
                return ReviewerAgent
    
    return None
```

### Stack-Based Router

```python
def stack_based_router(network, call_count, last_result, stack):
    """Use agent stack for complex workflows"""
    s = network.state
    
    # Push sub-agents onto stack
    if s.needs_research and ResearchAgent not in stack:
        stack.append(ResearchAgent)
        return ResearchAgent
    
    # Pop and continue
    if stack:
        return stack.pop()
    
    return None
```

## Memory Systems

### Key-Value Memory

```python
from hanzo_agents.memory import SQLiteKV

# Initialize KV store
kv_memory = SQLiteKV("project_memory.db")

# Store data
await kv_memory.set("project_config", {"name": "My Project", "version": "1.0"})

# Retrieve data
config = await kv_memory.get("project_config")

# List keys
keys = await kv_memory.list_keys(prefix="project_")
```

### Vector Memory

```python
from hanzo_agents.memory import FAISSVector

# Initialize vector store
vector_memory = FAISSVector(dimension=1536)

# Store embeddings
await vector_memory.store(
    key="doc_001",
    vector=embedding,
    metadata={"title": "Important Document", "date": "2024-01-01"}
)

# Query similar items
results = await vector_memory.query(
    vector=query_embedding,
    k=10,
    filter={"date": {"$gte": "2024-01-01"}}
)
```

### Memory in Agents

```python
class ResearchAgent(Agent[MyState]):
    async def run(self, state: MyState, history: History) -> InferenceResult:
        # Store findings in memory
        findings = self.analyze_topic(state.topic)
        await self.network.memory.kv.set(
            f"research_{state.topic}",
            findings
        )
        
        # Store embedding for semantic search
        embedding = self.embed_text(str(findings))
        await self.network.memory.vector.store(
            key=f"research_{state.topic}",
            vector=embedding,
            metadata={"topic": state.topic, "timestamp": datetime.now()}
        )
        
        return InferenceResult(
            content="Research completed and stored in memory"
        )
```

## Production Deployment

### Configuration

```yaml
# config.yaml
model:
  provider: "anthropic"
  name: "claude-3-opus"
  temperature: 0.7
  max_tokens: 4000

network:
  max_iterations: 50
  checkpoint_interval: 10
  timeout: 3600

telemetry:
  prometheus_port: 9464
  enable_tracing: true
  trace_endpoint: "http://localhost:4317"

memory:
  kv_backend: "postgres"
  kv_connection: "postgresql://user:pass@localhost/hanzo"
  vector_backend: "qdrant"
  vector_url: "http://localhost:6333"
```

### Running with CLI

```bash
# Basic execution
hanzo-agents run network.py --state '{"task": "Build API"}'

# With configuration
hanzo-agents run network.py --config config.yaml

# With checkpointing
hanzo-agents run network.py --checkpoint state.chkpt

# Resume from checkpoint
hanzo-agents run network.py --restore state.chkpt

# Enable metrics
hanzo-agents run network.py --metrics --port 9464

# JSON output for automation
hanzo-agents run network.py --json-lines > output.jsonl
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

# Run with proper configuration
CMD ["hanzo-agents", "run", "network.py", "--config", "production.yaml"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hanzo-agents
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hanzo-agents
  template:
    metadata:
      labels:
        app: hanzo-agents
    spec:
      containers:
      - name: agent-network
        image: hanzo/agents:latest
        ports:
        - containerPort: 9464  # Prometheus metrics
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai
        volumeMounts:
        - name: config
          mountPath: /app/config
      volumes:
      - name: config
        configMap:
          name: agent-config
```

## Examples

### Multi-Stage Data Pipeline

```python
@dataclass
class PipelineState(State):
    data_source: str
    raw_data: Optional[Dict] = None
    cleaned_data: Optional[Dict] = None
    analysis: Optional[Dict] = None
    report: Optional[str] = None
    done: bool = False

class DataCollector(Agent[PipelineState]):
    name = "collector"
    tools = [FetchDataTool(), ValidateDataTool()]

class DataCleaner(Agent[PipelineState]):
    name = "cleaner"
    tools = [CleanDataTool(), NormalizeDataTool()]

class DataAnalyzer(Agent[PipelineState]):
    name = "analyzer"
    tools = [StatisticalAnalysisTool(), VisualizationTool()]

class ReportGenerator(Agent[PipelineState]):
    name = "reporter"
    tools = [GenerateReportTool(), PublishTool()]

def pipeline_router(network, call_count, last_result, stack):
    s = network.state
    
    if s.done:
        return None
    if not s.raw_data:
        return DataCollector
    if not s.cleaned_data:
        return DataCleaner
    if not s.analysis:
        return DataAnalyzer
    if not s.report:
        return ReportGenerator
    
    s.done = True
    return None

# Run pipeline
network = Network(
    state=PipelineState(data_source="api.example.com/data"),
    agents=[DataCollector, DataCleaner, DataAnalyzer, ReportGenerator],
    router=pipeline_router
)
result = network.run()
```

### Code Review System

```python
@dataclass
class CodeReviewState(State):
    pr_url: str
    code_diff: Optional[str] = None
    issues: List[Dict] = field(default_factory=list)
    suggestions: List[Dict] = field(default_factory=list)
    approval_status: Optional[str] = None
    done: bool = False

class CodeFetcher(Agent[CodeReviewState]):
    name = "fetcher"
    tools = [FetchPRTool(), ParseDiffTool()]

class SecurityReviewer(Agent[CodeReviewState]):
    name = "security"
    system_prompt = "You are a security expert. Look for vulnerabilities."
    tools = [SecurityScanTool(), AddIssueTool()]

class PerformanceReviewer(Agent[CodeReviewState]):
    name = "performance"
    system_prompt = "You are a performance expert. Look for bottlenecks."
    tools = [ProfileCodeTool(), AddSuggestionTool()]

class FinalReviewer(Agent[CodeReviewState]):
    name = "final"
    system_prompt = "Make final decision based on all reviews."
    tools = [ApprovalTool(), RequestChangesTool()]

# Review process continues until approval or rejection
```

### Customer Support Bot

```python
@dataclass
class SupportState(State):
    customer_query: str
    customer_info: Optional[Dict] = None
    knowledge_base_results: List[Dict] = field(default_factory=list)
    solution: Optional[str] = None
    escalated: bool = False
    resolved: bool = False

class CustomerIdentifier(Agent[SupportState]):
    name = "identifier"
    tools = [LookupCustomerTool(), GetHistoryTool()]

class KnowledgeSearcher(Agent[SupportState]):
    name = "searcher"
    tools = [SearchKBTool(), RankResultsTool()]

class SolutionProvider(Agent[SupportState]):
    name = "solver"
    tools = [ProposeSolutionTool(), SendEmailTool()]

class Escalator(Agent[SupportState]):
    name = "escalator"
    tools = [CreateTicketTool(), NotifyTeamTool()]

def support_router(network, call_count, last_result, stack):
    s = network.state
    
    if s.resolved or s.escalated:
        return None
    if not s.customer_info:
        return CustomerIdentifier
    if not s.knowledge_base_results:
        return KnowledgeSearcher
    if not s.solution:
        return SolutionProvider
    if s.customer_satisfaction < 3:
        return Escalator
    
    s.resolved = True
    return None
```

## API Reference

### Core Classes

```python
# Agent base class
class Agent[S: State]:
    name: str
    description: str
    model: str
    tools: List[Tool[S]]
    system_prompt: str
    model_config: Dict[str, Any]
    
    async def run(self, state: S, history: History) -> InferenceResult

# Tool base class
class Tool[S: State]:
    name: str
    description: str
    
    class Parameters(BaseModel): ...
    
    def handle(self, **kwargs) -> str
    async def handle_async(self, **kwargs) -> str

# Network class
class Network[S: State]:
    def __init__(
        self,
        state: S,
        agents: List[Type[Agent[S]]],
        router: Union[Router, RouterFn],
        memory_kv: Optional[MemoryKV] = None,
        memory_vector: Optional[MemoryVector] = None,
        checkpoint_path: Optional[Path] = None,
        max_iterations: int = 100
    )
    
    def run(self) -> NetworkResult[S]
    async def run_async(self) -> NetworkResult[S]
    def checkpoint(self) -> None
    def restore(self, path: Path) -> None

# State base class
class State:
    guards: List[StateGuard] = field(default_factory=list)
    
    def validate(self) -> None
    def copy(self) -> State
    def diff(self, other: State) -> Dict[str, Any]
```

### Router Types

```python
# Function-based router
RouterFn = Callable[
    [Network, int, Optional[InferenceResult], List[Agent]],
    Optional[Type[Agent]]
]

# Class-based routers
class DeterministicRouter(Router): ...
class LLMRouter(Router): ...
class HybridRouter(Router): ...

# Helper functions
def sequential_router(agents: List[Type[Agent]]) -> RouterFn
def conditional_router(conditions: Dict[str, Type[Agent]]) -> RouterFn
def state_based_router(state_map: Dict[str, Type[Agent]]) -> RouterFn
```

### Memory Interfaces

```python
# Key-Value store
class MemoryKV:
    async def get(self, key: str) -> Optional[Any]
    async def set(self, key: str, value: Any) -> None
    async def delete(self, key: str) -> None
    async def list_keys(self, prefix: str = "") -> List[str]

# Vector store
class MemoryVector:
    async def store(self, key: str, vector: List[float], metadata: Dict) -> None
    async def query(self, vector: List[float], k: int, filter: Dict) -> List[Dict]
    async def delete(self, key: str) -> None
```

### Results and History

```python
# Inference result from agents
@dataclass
class InferenceResult:
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    model: Optional[str] = None
    usage: Optional[Dict[str, int]] = None

# Network execution result
@dataclass
class NetworkResult[S]:
    state: S
    history: History
    iterations: int
    final_agent: Optional[str]
    error: Optional[str] = None

# Interaction history
class History:
    interactions: List[Interaction]
    
    def add_interaction(self, interaction: Interaction) -> None
    def get_agent_history(self, agent_name: str) -> List[Interaction]
    def to_messages(self) -> List[Dict[str, str]]
```

## Best Practices

1. **State Design**: Keep state flat and serializable
2. **Tool Design**: Make tools atomic and side-effect-free except for explicit mutations
3. **Agent Responsibility**: Each agent should have a single, clear responsibility
4. **Router Logic**: Keep routing logic simple and deterministic when possible
5. **Error Handling**: Use state.error field and error-handling agents
6. **Memory Usage**: Store only necessary information in memory
7. **Testing**: Test agents, tools, and routers in isolation
8. **Monitoring**: Use Prometheus metrics and OpenTelemetry tracing

## Troubleshooting

Common issues and solutions:

1. **Import Errors**: Ensure all dependencies are installed with `pip install hanzo-agents[all]`
2. **State Validation**: Check StateGuard implementations
3. **Routing Loops**: Add iteration limits and done flags
4. **Memory Issues**: Use disk-based backends for large datasets
5. **API Rate Limits**: Implement backoff and retry logic in tools

For more help, see our [GitHub issues](https://github.com/hanzoai/agents/issues).