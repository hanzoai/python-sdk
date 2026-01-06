# Streaming

Stream agent responses for real-time output.

## Basic Streaming

```python
from agents import Agent, Runner

agent = Agent(name="assistant", instructions="Be helpful.")

async def stream_response():
    async for event in Runner.run_streamed(agent, "Tell me a story"):
        if event.type == "raw_response_event":
            # Token-by-token output
            print(event.data, end="", flush=True)
        elif event.type == "agent_updated_event":
            # Agent changed (handoff)
            print(f"\n[Agent: {event.new_agent.name}]")
```

## Stream Events

| Event Type | Description |
|------------|-------------|
| `raw_response_event` | Raw LLM response chunks |
| `agent_updated_event` | Agent changed (handoff) |
| `tool_call_event` | Tool being called |
| `tool_output_event` | Tool returned result |
| `run_item_event` | New run item added |

## Processing Events

```python
from agents import Runner
from agents.stream_events import (
    RawResponsesStreamEvent,
    AgentUpdatedStreamEvent,
)

async for event in Runner.run_streamed(agent, user_input):
    match event:
        case RawResponsesStreamEvent(data=chunk):
            # Handle text chunk
            print(chunk, end="")
        
        case AgentUpdatedStreamEvent(new_agent=new_agent):
            # Handle agent switch
            print(f"\n[Switched to: {new_agent.name}]")
```

## Streaming with Context

```python
from dataclasses import dataclass
from agents import Agent, Runner

@dataclass
class MyContext:
    user_id: str

context = MyContext(user_id="123")

async for event in Runner.run_streamed(
    agent,
    "Hello!",
    context=context,
):
    print(event)
```

## Streaming Result

Get the final result after streaming:

```python
from agents import Runner, RunResultStreaming

stream = Runner.run_streamed(agent, "Hello!")
result: RunResultStreaming = None

async for event in stream:
    print(event)
    result = stream.result

# After streaming completes
print(f"Final output: {result.final_output}")
print(f"Usage: {result.usage}")
```

## Buffered Streaming

Collect output while streaming:

```python
from agents import Runner

buffer = []

async for event in Runner.run_streamed(agent, "Hello!"):
    if event.type == "raw_response_event":
        buffer.append(event.data)
        print(event.data, end="")

full_response = "".join(buffer)
```

## Streaming with Tools

Tool calls appear as events:

```python
from agents import Runner

async for event in Runner.run_streamed(agent, "What's the weather?"):
    match event.type:
        case "tool_call_event":
            print(f"Calling: {event.tool_name}")
        case "tool_output_event":
            print(f"Result: {event.output}")
        case "raw_response_event":
            print(event.data, end="")
```

## Streaming with Handoffs

```python
from agents import Runner

current_agent = None

async for event in Runner.run_streamed(main_agent, "Help me"):
    if event.type == "agent_updated_event":
        current_agent = event.new_agent
        print(f"\n--- Transferred to {current_agent.name} ---\n")
    elif event.type == "raw_response_event":
        print(event.data, end="")
```

## Error Handling in Streams

```python
from agents import Runner, AgentsException

try:
    async for event in Runner.run_streamed(agent, user_input):
        print(event)
except AgentsException as e:
    print(f"Stream error: {e}")
```

## See Also

- [Running Agents](running_agents.md) - Non-streaming execution
- [Tracing](tracing.md) - Debug streams
- [Results](results.md) - Result handling
