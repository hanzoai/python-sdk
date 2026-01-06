# Configuration

Configure agent behavior with `RunConfig` and `ModelSettings`.

## RunConfig

Global settings for an agent run:

```python
from agents import Runner, RunConfig, ModelSettings

config = RunConfig(
    model="gpt-4o",
    model_settings=ModelSettings(temperature=0.7),
    max_turns=20,
)

result = await Runner.run(agent, "Hello!", run_config=config)
```

## RunConfig Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str \| Model` | None | Override all agent models |
| `model_provider` | `ModelProvider` | OpenAI | Model provider |
| `model_settings` | `ModelSettings` | None | Global model settings |
| `max_turns` | `int` | 10 | Max conversation turns |
| `input_guardrails` | `list` | None | Global input guardrails |
| `output_guardrails` | `list` | None | Global output guardrails |
| `handoff_input_filter` | `HandoffInputFilter` | None | Global handoff filter |
| `tracing_disabled` | `bool` | False | Disable tracing |

## ModelSettings

Fine-tune model behavior:

```python
from agents import Agent, ModelSettings

settings = ModelSettings(
    temperature=0.7,
    top_p=0.9,
    max_tokens=1000,
    presence_penalty=0.0,
    frequency_penalty=0.0,
)

agent = Agent(
    name="creative",
    instructions="Be creative.",
    model_settings=settings,
)
```

## ModelSettings Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `temperature` | `float` | 1.0 | Randomness (0-2) |
| `top_p` | `float` | 1.0 | Nucleus sampling |
| `max_tokens` | `int` | None | Max output tokens |
| `presence_penalty` | `float` | 0.0 | Presence penalty |
| `frequency_penalty` | `float` | 0.0 | Frequency penalty |
| `stop` | `list[str]` | None | Stop sequences |

## Model Selection

### By String

```python
agent = Agent(name="gpt4", model="gpt-4o")
agent = Agent(name="claude", model="claude-3-5-sonnet-20241022")
```

### Override at Runtime

```python
config = RunConfig(model="gpt-4o-mini")
result = await Runner.run(agent, "Hello!", run_config=config)
```

## Model Providers

### OpenAI (default)

```python
from agents import OpenAIProvider

provider = OpenAIProvider(
    api_key="sk-...",
    base_url="https://api.openai.com/v1",
)

config = RunConfig(model_provider=provider)
```

### Hanzo Node

```python
from agents import create_hanzo_node_provider

provider = create_hanzo_node_provider(
    api_key="your-hanzo-key",
    base_url="https://api.hanzo.ai/v1",
)

config = RunConfig(model_provider=provider)
```

### Custom Provider

```python
from agents import ModelProvider, Model

class MyProvider(ModelProvider):
    def get_model(self, model_name: str) -> Model:
        return MyCustomModel(model_name)
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `HANZO_API_KEY` | Hanzo API key |

## Default Model

Set a default model for all agents:

```python
import agents

# Set default
agents.set_default_model("gpt-4o")

# All agents use gpt-4o unless overridden
agent = Agent(name="default", instructions="...")
```

## Configuration Hierarchy

Settings are applied in order (later overrides earlier):

1. Default settings
2. Agent-level settings (`agent.model_settings`)
3. RunConfig settings (`config.model_settings`)

```python
# Agent settings
agent = Agent(
    model_settings=ModelSettings(temperature=0.5),
)

# RunConfig overrides
config = RunConfig(
    model_settings=ModelSettings(temperature=0.9),
)

# Result uses temperature=0.9
result = await Runner.run(agent, "Hello!", run_config=config)
```

## See Also

- [Agents](agents.md) - Agent configuration
- [Models](models.md) - Model details
- [Running Agents](running_agents.md) - Using RunConfig
