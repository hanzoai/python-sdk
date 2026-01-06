# Tracing

Built-in observability for debugging and monitoring agent runs.

## Automatic Tracing

Tracing is enabled by default:

```python
from agents import Agent, Runner

agent = Agent(name="assistant", instructions="Be helpful.")
result = await Runner.run(agent, "Hello!")

# Traces are automatically collected
```

## Trace Structure

Each run creates a trace with spans:

```
Trace (run_id)
├── Agent Span (assistant)
│   ├── LLM Call
│   ├── Tool Call (get_weather)
│   └── LLM Call
└── Agent Span (specialist)  # if handoff
    └── LLM Call
```

## Custom Spans

Add custom spans for your code:

```python
from agents import trace, Span

@trace("my_operation")
async def my_function():
    # Automatically traced
    pass

# Or manually
async def manual_trace():
    with Span("custom_span") as span:
        span.set_attribute("key", "value")
        # Your code here
```

## Span Attributes

```python
from agents import Span

with Span("process_data") as span:
    span.set_attribute("input_size", len(data))
    span.set_attribute("user_id", user_id)
    
    result = process(data)
    
    span.set_attribute("output_size", len(result))
```

## Error Tracking

```python
from agents import Span, SpanError

with Span("risky_operation") as span:
    try:
        result = risky_call()
    except Exception as e:
        span.record_error(SpanError(
            message=str(e),
            type=type(e).__name__,
        ))
        raise
```

## Agent Span Data

Access agent-specific span data:

```python
from agents.tracing.span_data import AgentSpanData

# In hooks or custom code
span_data = AgentSpanData(
    agent_name="assistant",
    model="gpt-4o",
    input_tokens=100,
    output_tokens=50,
)
```

## Accessing Current Trace

```python
from agents import get_current_trace

trace = get_current_trace()
if trace:
    print(f"Trace ID: {trace.trace_id}")
    print(f"Spans: {len(trace.spans)}")
```

## Trace Export

### Console (default)

```python
from agents import Runner, RunConfig

config = RunConfig(
    tracing_disabled=False,  # Default
)
```

### Custom Exporter

```python
from agents.tracing import TraceExporter

class MyExporter(TraceExporter):
    async def export(self, trace):
        # Send to your observability platform
        await send_to_datadog(trace)

# Register exporter
from agents.tracing import register_exporter
register_exporter(MyExporter())
```

## Disabling Tracing

```python
from agents import Runner, RunConfig

# Disable for a single run
config = RunConfig(tracing_disabled=True)
result = await Runner.run(agent, "Hello!", run_config=config)

# Disable globally
import agents
agents.tracing.disable()
```

## Trace Context

Propagate trace context across services:

```python
from agents import get_current_trace

# Get context to pass to another service
trace = get_current_trace()
context = {
    "trace_id": trace.trace_id,
    "span_id": trace.current_span.span_id,
}

# In the other service
from agents import trace_from_context
with trace_from_context(context):
    # Operations here are linked to parent trace
    pass
```

## Performance

Tracing adds minimal overhead:

| Operation | Overhead |
|-----------|----------|
| Span creation | ~1μs |
| Attribute set | ~0.5μs |
| Export (async) | Non-blocking |

## Integration

### OpenTelemetry

```python
from agents.tracing.otel import OTelExporter

exporter = OTelExporter(
    endpoint="http://localhost:4317",
    service_name="my-agent-app",
)
register_exporter(exporter)
```

### LangSmith

```python
from agents.tracing.langsmith import LangSmithExporter

exporter = LangSmithExporter(
    api_key=os.environ["LANGSMITH_API_KEY"],
    project="my-project",
)
register_exporter(exporter)
```

## See Also

- [Running Agents](running_agents.md) - Execution
- [Streaming](streaming.md) - Stream with traces
- [Results](results.md) - Access trace data in results
