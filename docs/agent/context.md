# Context

The context is a mutable object passed throughout an agent run.

## Basic Context

```python
from dataclasses import dataclass
from agents import Agent, Runner

@dataclass
class MyContext:
    user_id: str
    session_id: str
    request_count: int = 0

context = MyContext(user_id="123", session_id="abc")
result = await Runner.run(agent, "Hello!", context=context)
```

## Accessing Context in Tools

```python
from agents import function_tool, RunContextWrapper

@function_tool
def get_user_data(ctx: RunContextWrapper[MyContext]) -> str:
    """Get data for the current user."""
    user_id = ctx.context.user_id
    return f"Data for user {user_id}"

@function_tool
def increment_count(ctx: RunContextWrapper[MyContext]) -> str:
    """Increment request count."""
    ctx.context.request_count += 1
    return f"Count: {ctx.context.request_count}"
```

## Context in Instructions

Dynamic instructions based on context:

```python
from agents import Agent, RunContextWrapper

def dynamic_instructions(ctx: RunContextWrapper[MyContext], agent: Agent) -> str:
    user = ctx.context.user_id
    count = ctx.context.request_count
    return f"""You are helping user {user}.
This is request #{count} in this session.
Be concise and helpful."""

agent = Agent(
    name="contextual",
    instructions=dynamic_instructions,
)
```

## Context in Guardrails

```python
from agents import input_guardrail, InputGuardrailResult, RunContextWrapper

@input_guardrail
async def check_permissions(
    ctx: RunContextWrapper[MyContext],
    agent,
    input_text: str
) -> InputGuardrailResult:
    """Check user permissions."""
    if ctx.context.user_id not in allowed_users:
        return InputGuardrailResult(
            tripwire_triggered=True,
            output_info="User not authorized."
        )
    return InputGuardrailResult(tripwire_triggered=False)
```

## Context in Handoffs

```python
from agents import handoff, Handoff, RunContextWrapper

@handoff
def conditional_handoff(ctx: RunContextWrapper[MyContext]) -> Handoff | None:
    """Hand off based on context."""
    if ctx.context.user_id.startswith("vip_"):
        return Handoff(target=vip_agent)
    return None
```

## RunContextWrapper

The wrapper provides additional functionality:

```python
from agents import RunContextWrapper

@function_tool
def example(ctx: RunContextWrapper[MyContext]) -> str:
    # Access your context
    user = ctx.context.user_id
    
    # Access run metadata
    run_id = ctx.run_id
    
    # Check current agent
    agent_name = ctx.current_agent.name
    
    return f"User: {user}, Run: {run_id}, Agent: {agent_name}"
```

## Context Types

### Dataclass (Recommended)

```python
from dataclasses import dataclass, field

@dataclass
class AppContext:
    user_id: str
    permissions: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
```

### Pydantic Model

```python
from pydantic import BaseModel

class AppContext(BaseModel):
    user_id: str
    permissions: list[str] = []
    
    class Config:
        extra = "allow"  # Allow additional fields
```

### Simple Dict

```python
# Works but not type-safe
context = {"user_id": "123", "data": {}}
result = await Runner.run(agent, "Hello!", context=context)
```

## Context Mutation

Context can be modified during the run:

```python
@function_tool
def update_context(ctx: RunContextWrapper[MyContext], key: str, value: str) -> str:
    """Update context metadata."""
    ctx.context.metadata[key] = value
    return f"Updated {key}"
```

## Context Persistence

For multi-turn conversations:

```python
# Store context between requests
contexts: dict[str, MyContext] = {}

async def handle_message(session_id: str, message: str):
    # Get or create context
    if session_id not in contexts:
        contexts[session_id] = MyContext(
            user_id="user_123",
            session_id=session_id,
        )
    
    context = contexts[session_id]
    result = await Runner.run(agent, message, context=context)
    
    # Context is updated in place
    return result.final_output
```

## See Also

- [Tools](tools.md) - Using context in tools
- [Guardrails](guardrails.md) - Context in guardrails
- [Running Agents](running_agents.md) - Passing context
