# Multi-Agent Systems

Build complex workflows with multiple cooperating agents.

## Agent Teams

Create specialized agents that work together:

```python
from agents import Agent

# Specialist agents
researcher = Agent(
    name="researcher",
    instructions="Research topics thoroughly and provide facts.",
    handoff_description="Researches information and facts.",
)

writer = Agent(
    name="writer", 
    instructions="Write clear, engaging content based on research.",
    handoff_description="Writes content and articles.",
)

editor = Agent(
    name="editor",
    instructions="Review and improve written content.",
    handoff_description="Edits and improves content quality.",
)

# Coordinator
coordinator = Agent(
    name="coordinator",
    instructions="""Coordinate the team to produce quality content.
    1. Use researcher for facts
    2. Use writer to draft content
    3. Use editor to polish""",
    handoffs=[researcher, writer, editor],
)
```

## Sequential Workflow

Agents pass work in sequence:

```python
from agents import Agent, handoff, Handoff

@handoff
def to_next_stage(ctx) -> Handoff:
    """Move to the next processing stage."""
    stages = ctx.context.get("stages", [])
    current = ctx.context.get("current_stage", 0)
    
    if current < len(stages):
        ctx.context["current_stage"] = current + 1
        return Handoff(target=stages[current])
    return None

stage1 = Agent(name="stage1", handoffs=[to_next_stage])
stage2 = Agent(name="stage2", handoffs=[to_next_stage])
stage3 = Agent(name="stage3", instructions="Final stage.")
```

## Parallel Execution

Run multiple agents simultaneously:

```python
import asyncio
from agents import Agent, Runner

agents = [
    Agent(name="analyst1", instructions="Analyze from perspective A"),
    Agent(name="analyst2", instructions="Analyze from perspective B"),
    Agent(name="analyst3", instructions="Analyze from perspective C"),
]

async def parallel_analysis(prompt: str):
    tasks = [Runner.run(agent, prompt) for agent in agents]
    results = await asyncio.gather(*tasks)
    return [r.final_output for r in results]

# Combine results
outputs = await parallel_analysis("Analyze this data")
```

## Supervisor Pattern

One agent oversees others:

```python
from agents import Agent, function_tool, Runner

workers = {
    "data": Agent(name="data_worker", instructions="Process data."),
    "analysis": Agent(name="analysis_worker", instructions="Analyze results."),
}

@function_tool
async def delegate(task_type: str, task: str) -> str:
    """Delegate a task to a worker agent."""
    if task_type not in workers:
        return f"Unknown worker type: {task_type}"
    
    result = await Runner.run(workers[task_type], task)
    return result.final_output

supervisor = Agent(
    name="supervisor",
    instructions="Coordinate workers to complete complex tasks.",
    tools=[delegate],
)
```

## Debate Pattern

Agents discuss and reach consensus:

```python
from agents import Agent, Runner

pro_agent = Agent(
    name="pro",
    instructions="Argue in favor of the proposition.",
)

con_agent = Agent(
    name="con", 
    instructions="Argue against the proposition.",
)

judge_agent = Agent(
    name="judge",
    instructions="Evaluate arguments and reach a conclusion.",
)

async def debate(topic: str, rounds: int = 3):
    history = [f"Topic: {topic}"]
    
    for _ in range(rounds):
        # Pro argument
        pro_result = await Runner.run(pro_agent, "\n".join(history))
        history.append(f"Pro: {pro_result.final_output}")
        
        # Con argument
        con_result = await Runner.run(con_agent, "\n".join(history))
        history.append(f"Con: {con_result.final_output}")
    
    # Final judgment
    verdict = await Runner.run(judge_agent, "\n".join(history))
    return verdict.final_output
```

## Router Pattern

Route requests to appropriate specialists:

```python
from agents import Agent

specialists = {
    "billing": Agent(name="billing", instructions="Handle billing."),
    "technical": Agent(name="technical", instructions="Handle tech issues."),
    "sales": Agent(name="sales", instructions="Handle sales inquiries."),
}

router = Agent(
    name="router",
    instructions="""Route customer requests to the right specialist:
    - Billing questions → billing
    - Technical issues → technical  
    - Purchase inquiries → sales""",
    handoffs=list(specialists.values()),
)
```

## Shared Context

Agents share state through context:

```python
from dataclasses import dataclass, field
from agents import Agent, Runner, function_tool

@dataclass
class SharedState:
    findings: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)

@function_tool
def add_finding(ctx, finding: str) -> str:
    """Add a finding to shared state."""
    ctx.context.findings.append(finding)
    return f"Added finding: {finding}"

@function_tool
def add_decision(ctx, decision: str) -> str:
    """Record a decision."""
    ctx.context.decisions.append(decision)
    return f"Recorded: {decision}"

state = SharedState()
result = await Runner.run(coordinator, "Analyze and decide", context=state)
print(f"Findings: {state.findings}")
print(f"Decisions: {state.decisions}")
```

## Error Recovery

Handle agent failures:

```python
from agents import Runner, AgentsException

async def run_with_fallback(primary: Agent, fallback: Agent, prompt: str):
    try:
        return await Runner.run(primary, prompt)
    except AgentsException:
        return await Runner.run(fallback, prompt)
```

## See Also

- [Agents](agents.md) - Creating agents
- [Handoffs](handoffs.md) - Agent delegation
- [Context](context.md) - Shared state
