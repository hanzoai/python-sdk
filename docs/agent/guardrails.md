# Guardrails

Guardrails validate agent inputs and outputs to ensure safety and quality.

## Input Guardrails

Validate user input before the agent processes it:

```python
from agents import Agent, input_guardrail, InputGuardrailResult

@input_guardrail
async def check_input_length(ctx, agent, input_text: str) -> InputGuardrailResult:
    """Reject inputs that are too long."""
    if len(input_text) > 10000:
        return InputGuardrailResult(
            tripwire_triggered=True,
            output_info="Input too long. Please shorten your message."
        )
    return InputGuardrailResult(tripwire_triggered=False)

agent = Agent(
    name="guarded",
    instructions="Be helpful.",
    input_guardrails=[check_input_length],
)
```

## Output Guardrails

Validate agent output before returning to user:

```python
from agents import Agent, output_guardrail, OutputGuardrailResult

@output_guardrail
async def check_pii(ctx, agent, output: str) -> OutputGuardrailResult:
    """Block outputs containing PII."""
    pii_patterns = ["SSN:", "credit card:", "password:"]
    
    for pattern in pii_patterns:
        if pattern.lower() in output.lower():
            return OutputGuardrailResult(
                tripwire_triggered=True,
                output_info="Response contained sensitive information."
            )
    
    return OutputGuardrailResult(tripwire_triggered=False)

agent = Agent(
    name="safe_agent",
    instructions="Help users with their accounts.",
    output_guardrails=[check_pii],
)
```

## Guardrail Results

### Input Guardrail Result

```python
@dataclass
class InputGuardrailResult:
    tripwire_triggered: bool  # True to block
    output_info: str | None = None  # Reason for blocking
```

### Output Guardrail Result

```python
@dataclass
class OutputGuardrailResult:
    tripwire_triggered: bool  # True to block
    output_info: str | None = None  # Reason for blocking
```

## Guardrail with Context

```python
from dataclasses import dataclass
from agents import input_guardrail, InputGuardrailResult, RunContextWrapper

@dataclass
class AppContext:
    user_tier: str
    rate_limit: int

@input_guardrail
async def rate_limit_check(
    ctx: RunContextWrapper[AppContext],
    agent,
    input_text: str
) -> InputGuardrailResult:
    """Check rate limits based on user tier."""
    if ctx.context.user_tier == "free" and ctx.context.rate_limit <= 0:
        return InputGuardrailResult(
            tripwire_triggered=True,
            output_info="Rate limit exceeded. Please upgrade."
        )
    return InputGuardrailResult(tripwire_triggered=False)
```

## LLM-Based Guardrails

Use another LLM to check content:

```python
from agents import input_guardrail, InputGuardrailResult, Agent, Runner

moderation_agent = Agent(
    name="moderator",
    instructions="Return 'SAFE' or 'UNSAFE: reason' for the given text.",
)

@input_guardrail
async def llm_moderation(ctx, agent, input_text: str) -> InputGuardrailResult:
    """Use an LLM to moderate content."""
    result = await Runner.run(moderation_agent, input_text)
    
    if result.final_output.startswith("UNSAFE"):
        return InputGuardrailResult(
            tripwire_triggered=True,
            output_info=result.final_output
        )
    
    return InputGuardrailResult(tripwire_triggered=False)
```

## Global Guardrails

Apply guardrails to all runs:

```python
from agents import Runner, RunConfig

config = RunConfig(
    input_guardrails=[check_input_length, rate_limit_check],
    output_guardrails=[check_pii],
)

result = await Runner.run(agent, user_input, run_config=config)
```

## Handling Tripwires

```python
from agents import (
    Runner,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
)

try:
    result = await Runner.run(agent, user_input)
except InputGuardrailTripwireTriggered as e:
    print(f"Input blocked: {e.guardrail_result.output_info}")
except OutputGuardrailTripwireTriggered as e:
    print(f"Output blocked: {e.guardrail_result.output_info}")
```

## Multiple Guardrails

Guardrails run in order. First tripwire stops execution:

```python
agent = Agent(
    name="multi_guard",
    instructions="...",
    input_guardrails=[
        check_length,     # Runs first
        check_language,   # Runs second
        check_content,    # Runs third
    ],
    output_guardrails=[
        check_pii,
        check_formatting,
    ],
)
```

## See Also

- [Agents](agents.md) - Creating agents
- [Running Agents](running_agents.md) - Execution
- [Tracing](tracing.md) - Debug guardrails
