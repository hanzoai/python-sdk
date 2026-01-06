# Results

Understanding and working with agent run results.

## RunResult

The result of a completed agent run:

```python
from agents import Agent, Runner

agent = Agent(name="assistant", instructions="Be helpful.")
result = await Runner.run(agent, "Hello!")

# Access the result
print(result.final_output)      # Final text output
print(result.last_agent)        # Agent that produced output
print(result.new_items)         # All conversation items
print(result.usage)             # Token usage
```

## RunResult Properties

| Property | Type | Description |
|----------|------|-------------|
| `final_output` | `str` | Final text response |
| `last_agent` | `Agent` | Agent that completed the run |
| `new_items` | `list[RunItem]` | All items from the run |
| `usage` | `Usage` | Token usage statistics |
| `input_guardrail_results` | `list` | Input guardrail results |
| `output_guardrail_results` | `list` | Output guardrail results |

## Conversation Items

Access all items from the conversation:

```python
from agents.items import (
    MessageOutputItem,
    ToolCallItem,
    ToolCallOutputItem,
    HandoffCallItem,
)

for item in result.new_items:
    match item:
        case MessageOutputItem(content=content):
            print(f"Message: {content}")
        case ToolCallItem(tool_name=name, arguments=args):
            print(f"Tool call: {name}({args})")
        case ToolCallOutputItem(output=output):
            print(f"Tool result: {output}")
        case HandoffCallItem(target_agent=agent):
            print(f"Handoff to: {agent.name}")
```

## Token Usage

```python
usage = result.usage

print(f"Input tokens: {usage.input_tokens}")
print(f"Output tokens: {usage.output_tokens}")
print(f"Total tokens: {usage.total_tokens}")
```

## Structured Output

When using output schemas:

```python
from pydantic import BaseModel
from agents import Agent, Runner

class Response(BaseModel):
    answer: str
    confidence: float

agent = Agent(
    name="structured",
    instructions="Always provide confidence.",
    output_type=Response,
)

result = await Runner.run(agent, "What is 2+2?")

# Parsed output
response: Response = result.final_output_parsed
print(response.answer)      # "4"
print(response.confidence)  # 0.99
```

## Guardrail Results

```python
# Input guardrail results
for gr in result.input_guardrail_results:
    print(f"Guardrail: {gr.guardrail_name}")
    print(f"Triggered: {gr.tripwire_triggered}")
    print(f"Info: {gr.output_info}")

# Output guardrail results
for gr in result.output_guardrail_results:
    print(f"Guardrail: {gr.guardrail_name}")
    print(f"Triggered: {gr.tripwire_triggered}")
```

## Streaming Results

For streaming runs:

```python
from agents import Runner

stream = Runner.run_streamed(agent, "Hello!")

# Collect events
async for event in stream:
    print(event)

# Get final result
result = stream.result
print(result.final_output)
```

## Multi-Agent Results

When handoffs occur:

```python
result = await Runner.run(main_agent, "Help with billing")

# Which agent finished?
print(f"Completed by: {result.last_agent.name}")

# Trace the path
agents_involved = set()
for item in result.new_items:
    if hasattr(item, "agent"):
        agents_involved.add(item.agent.name)
print(f"Agents involved: {agents_involved}")
```

## Error Results

Handle errors gracefully:

```python
from agents import Runner, MaxTurnsExceeded

try:
    result = await Runner.run(agent, user_input)
    print(result.final_output)
except MaxTurnsExceeded as e:
    # Partial result available
    partial = e.partial_result
    print(f"Partial output: {partial.final_output}")
    print(f"Turns used: {len(partial.new_items)}")
```

## Result Serialization

```python
# To dict
result_dict = {
    "output": result.final_output,
    "agent": result.last_agent.name,
    "usage": {
        "input": result.usage.input_tokens,
        "output": result.usage.output_tokens,
    },
}

# To JSON
import json
json.dumps(result_dict)
```

## See Also

- [Running Agents](running_agents.md) - Get results
- [Streaming](streaming.md) - Streaming results
- [Tracing](tracing.md) - Debug results
