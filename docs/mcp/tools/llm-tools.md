# LLM Tools

Unified LLM interface via LiteLLM.

→ **Full documentation: [../../tools/llm-tools.md](../../tools/llm-tools.md)**

## Quick Reference

```python
# Call any LLM
llm(model="gpt-4", prompt="Explain quantum computing")

# With system prompt
llm(model="claude-3-5-sonnet", prompt="...", system="You are a helpful assistant")

# Multi-model consensus
consensus(
    prompt="Best database for this use case?",
    models=["gpt-4", "claude-3-5-sonnet", "gemini-pro"]
)
```

Supports: OpenAI, Anthropic, Google, Together, Groq, Mistral, Ollama, and 100+ more.
