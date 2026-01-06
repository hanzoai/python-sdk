# Models

Configure and use different LLM providers.

## Supported Models

### OpenAI

```python
from agents import Agent

# GPT-4o (recommended)
agent = Agent(name="gpt4", model="gpt-4o")

# GPT-4o mini (faster, cheaper)
agent = Agent(name="mini", model="gpt-4o-mini")

# GPT-4 Turbo
agent = Agent(name="turbo", model="gpt-4-turbo")
```

### Anthropic (via Hanzo)

```python
agent = Agent(name="claude", model="claude-3-5-sonnet-20241022")
agent = Agent(name="opus", model="claude-3-opus-20240229")
```

### Other Providers

```python
# Gemini
agent = Agent(name="gemini", model="gemini-pro")

# Mistral
agent = Agent(name="mistral", model="mistral-large")
```

## Model Providers

### OpenAI Provider (default)

```python
from agents import OpenAIProvider, RunConfig

provider = OpenAIProvider(
    api_key="sk-...",  # Or use OPENAI_API_KEY env var
)

config = RunConfig(model_provider=provider)
```

### Hanzo Node Provider

```python
from agents import create_hanzo_node_provider, RunConfig

provider = create_hanzo_node_provider(
    api_key="your-key",  # Or use HANZO_API_KEY env var
)

config = RunConfig(model_provider=provider)
result = await Runner.run(agent, "Hello!", run_config=config)
```

### Custom Base URL

```python
from agents import OpenAIProvider

# Use Azure OpenAI
provider = OpenAIProvider(
    api_key="azure-key",
    base_url="https://your-resource.openai.azure.com/",
)

# Use local model (Ollama, vLLM, etc.)
provider = OpenAIProvider(
    api_key="not-needed",
    base_url="http://localhost:11434/v1",
)
```

## Custom Model Implementation

```python
from agents import Model, ModelProvider

class MyModel(Model):
    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> dict:
        # Your implementation
        response = await my_api_call(messages, tools)
        return {
            "content": response.text,
            "tool_calls": response.tool_calls,
        }

class MyProvider(ModelProvider):
    def get_model(self, model_name: str) -> Model:
        return MyModel(model_name)
```

## Model Settings

```python
from agents import Agent, ModelSettings

agent = Agent(
    name="creative",
    model="gpt-4o",
    model_settings=ModelSettings(
        temperature=0.9,      # More creative
        top_p=0.95,
        max_tokens=2000,
        presence_penalty=0.1,
        frequency_penalty=0.1,
    ),
)

agent = Agent(
    name="precise",
    model="gpt-4o",
    model_settings=ModelSettings(
        temperature=0.1,      # More deterministic
        max_tokens=500,
    ),
)
```

## Model Tracing

Enable detailed model tracing:

```python
from agents import ModelTracing

class TracedModel(Model):
    tracing: ModelTracing = ModelTracing.ENABLED
    
    async def complete(self, messages, tools=None, **kwargs):
        # Automatically traced
        ...
```

## Response Models

### Chat Completions

Standard OpenAI-compatible response:

```python
from agents import OpenAIChatCompletionsModel

model = OpenAIChatCompletionsModel("gpt-4o")
```

### Responses API

For models supporting the newer responses format:

```python
from agents import OpenAIResponsesModel

model = OpenAIResponsesModel("gpt-4o")
```

## Model Selection Strategy

```python
from agents import Agent, RunConfig

# Development: faster, cheaper
dev_config = RunConfig(model="gpt-4o-mini")

# Production: best quality
prod_config = RunConfig(model="gpt-4o")

# Use based on environment
import os
config = prod_config if os.environ.get("ENV") == "prod" else dev_config

result = await Runner.run(agent, "Hello!", run_config=config)
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `OPENAI_BASE_URL` | Custom OpenAI-compatible endpoint |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `HANZO_API_KEY` | Hanzo API key |

## See Also

- [Configuration](config.md) - Model settings
- [Agents](agents.md) - Using models with agents
- [Running Agents](running_agents.md) - Runtime model selection
