# Handoffs

Handoffs allow agents to delegate tasks to specialized sub-agents.

## Basic Handoffs

```python
from agents import Agent

# Specialist agents
billing_agent = Agent(
    name="billing",
    instructions="Handle billing inquiries, refunds, and payments.",
    handoff_description="Handles billing, payments, and refunds.",
)

tech_agent = Agent(
    name="tech_support",
    instructions="Help with technical issues and troubleshooting.",
    handoff_description="Handles technical support and troubleshooting.",
)

# Main agent with handoffs
main_agent = Agent(
    name="support",
    instructions="Route customers to the appropriate specialist.",
    handoffs=[billing_agent, tech_agent],
)
```

## Handoff Decorator

For more control over handoff behavior:

```python
from agents import Agent, handoff, Handoff

@handoff
def to_billing(context) -> Handoff:
    """Transfer to billing specialist."""
    return Handoff(
        target=billing_agent,
        input_filter=lambda items: items[-5:],  # Last 5 messages
    )

main_agent = Agent(
    name="support",
    instructions="Route to specialists as needed.",
    handoffs=[to_billing],
)
```

## Handoff Input Filter

Control what conversation history transfers:

```python
from agents import Handoff, HandoffInputFilter

def last_n_messages(n: int) -> HandoffInputFilter:
    """Only send last N messages to new agent."""
    def filter_fn(items):
        return items[-n:]
    return filter_fn

billing_handoff = Handoff(
    target=billing_agent,
    input_filter=last_n_messages(3),
)
```

## Conditional Handoffs

```python
from agents import Agent, handoff, Handoff, RunContextWrapper

@handoff
def smart_handoff(ctx: RunContextWrapper) -> Handoff | None:
    """Conditionally hand off based on context."""
    if ctx.context.get("is_vip"):
        return Handoff(target=vip_agent)
    elif ctx.context.get("issue_type") == "billing":
        return Handoff(target=billing_agent)
    return None  # No handoff
```

## Handoff Data

Pass data to the new agent:

```python
from agents import Handoff, HandoffInputData

handoff = Handoff(
    target=specialist_agent,
    input_data=HandoffInputData(
        summary="Customer needs help with order #12345",
        metadata={"order_id": "12345", "priority": "high"},
    ),
)
```

## Tracking Handoffs

```python
from agents import Runner, RunHooks

class HandoffTracker(RunHooks):
    async def on_handoff(self, context, from_agent, to_agent):
        print(f"Handoff: {from_agent.name} -> {to_agent.name}")

result = await Runner.run(
    main_agent,
    "I need help with my bill",
    run_hooks=HandoffTracker(),
)

# Check which agent completed the run
print(f"Handled by: {result.last_agent.name}")
```

## Recursive Handoffs

Agents can hand off to agents that also have handoffs:

```python
level1 = Agent(name="level1", handoffs=[level2])
level2 = Agent(name="level2", handoffs=[level3])
level3 = Agent(name="level3", instructions="Final handler")
```

## Preventing Infinite Loops

Use `max_turns` to prevent circular handoffs:

```python
from agents import Runner, RunConfig

config = RunConfig(max_turns=10)
result = await Runner.run(agent, input_text, run_config=config)
```

## Handoff vs Tools

| Feature | Handoffs | Tools |
|---------|----------|-------|
| Control flow | Transfers to new agent | Returns to same agent |
| Context | New agent takes over | Same agent continues |
| Use case | Specialization | Actions/data retrieval |

## See Also

- [Agents](agents.md) - Creating agents
- [Multi-Agent](multi_agent.md) - Complex workflows
- [Running Agents](running_agents.md) - Execution
