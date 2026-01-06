# Running Agents

Execute agents with the `Runner` class.

## Basic Usage

### Synchronous

```python
from agents import Agent, Runner

agent = Agent(name="assistant", instructions="Be helpful.")

result = Runner.run_sync(agent, "Hello!")
print(result.final_output)
```

### Asynchronous

```python
import asyncio
from agents import Agent, Runner

agent = Agent(name="assistant", instructions="Be helpful.")

async def main():
    result = await Runner.run(agent, "Hello!")
    print(result.final_output)

asyncio.run(main())
```

## Run Configuration

```python
from agents import Runner, RunConfig, ModelSettings

config = RunConfig(
    model="gpt-4o",
    model_settings=ModelSettings(temperature=0.5),
    max_turns=20,
    tracing_disabled=False,
)

result = await Runner.run(agent, "Hello!", run_config=config)
```

## RunConfig Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `model` | None | Override agent model |
| `model_provider` | OpenAI | Model provider |
| `model_settings` | None | Global model settings |
| `max_turns` | 10 | Maximum conversation turns |
| `input_guardrails` | None | Global input guardrails |
| `output_guardrails` | None | Global output guardrails |
| `tracing_disabled` | False | Disable tracing |

## Context

Pass custom context to tools and guardrails:

```python
from dataclasses import dataclass
from agents import Agent, Runner, function_tool

@dataclass
class MyContext:
    user_id: str
    permissions: list[str]

@function_tool
def get_user_data(ctx: MyContext) -> str:
    return f"Data for user {ctx.user_id}"

agent = Agent(
    name="contextual",
    instructions="Access user data as needed.",
    tools=[get_user_data],
)

context = MyContext(user_id="123", permissions=["read"])
result = await Runner.run(agent, "Get my data", context=context)
```

## Run Result

The `RunResult` contains:

```python
result = await Runner.run(agent, "Hello!")

# Final output text
print(result.final_output)

# All conversation items
for item in result.new_items:
    print(item)

# Last agent that ran (for handoffs)
print(result.last_agent.name)

# Input/output guardrail results
print(result.input_guardrail_results)
print(result.output_guardrail_results)

# Token usage
print(result.usage)
```

## Max Turns

Limit conversation turns to prevent infinite loops:

```python
from agents import Runner, RunConfig

config = RunConfig(max_turns=5)

try:
    result = await Runner.run(agent, "Complex task", run_config=config)
except MaxTurnsExceeded:
    print("Agent hit max turns limit")
```

## Run Hooks

Monitor run lifecycle:

```python
from agents import Runner, RunHooks

class MyRunHooks(RunHooks):
    async def on_agent_start(self, context, agent):
        print(f"Starting: {agent.name}")
    
    async def on_tool_start(self, context, agent, tool):
        print(f"Calling tool: {tool.name}")
    
    async def on_handoff(self, context, from_agent, to_agent):
        print(f"Handoff: {from_agent.name} -> {to_agent.name}")

result = await Runner.run(
    agent,
    "Hello!",
    run_hooks=MyRunHooks(),
)
```

## Error Handling

```python
from agents import (
    Runner,
    AgentsException,
    MaxTurnsExceeded,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
)

try:
    result = await Runner.run(agent, user_input)
except MaxTurnsExceeded:
    print("Too many turns")
except InputGuardrailTripwireTriggered as e:
    print(f"Input blocked: {e}")
except OutputGuardrailTripwireTriggered as e:
    print(f"Output blocked: {e}")
except AgentsException as e:
    print(f"Agent error: {e}")
```

## See Also

- [Agents](agents.md) - Creating agents
- [Streaming](streaming.md) - Stream responses
- [Tracing](tracing.md) - Debug runs
