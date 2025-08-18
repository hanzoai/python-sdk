# GPT-5/Codex Orchestration Guide

## Overview

Hanzo Dev supports using GPT-5, GPT-4, Codex, and other advanced models as orchestrators for AI-powered code review, development, and system improvements.

## Available Orchestrator Models

| Model | Best For | Context Window | Cost |
|-------|----------|----------------|------|
| `gpt-5` | Complex reasoning, architecture | 128K | High |
| `gpt-4o` | Code review, optimization | 128K | Medium |
| `gpt-4-turbo` | Fast iterations | 128K | Medium |
| `gpt-4` | General development | 32K | Medium |
| `codex` | Code generation, completion | 8K | Low |
| `o3` | Advanced reasoning | 200K | High |
| `claude-3-5-sonnet` | Long context, analysis | 200K | Medium |
| `local:llama3.2` | Simple tasks (free!) | 8K | Free |

## Quick Start

### 1. Basic GPT-5 Orchestration

```bash
# Use GPT-5 as the main orchestrator
hanzo dev --orchestrator gpt-5
```

### 2. GPT-4o for Code Review

```bash
# Optimized GPT-4 for code review
hanzo dev --orchestrator gpt-4o --instances 3 --critic-instances 2
```

### 3. Cost-Optimized Hybrid Mode

```bash
# GPT-5 orchestrator + local workers (90% cost reduction)
hanzo dev --orchestrator gpt-5 --use-hanzo-net
```

This configuration:
- Uses GPT-5 only for high-level orchestration
- Deploys local models for simple tasks
- Routes complex tasks to API models when needed
- Reduces costs by 90%

## Advanced Usage

### Comprehensive Code Review

```bash
hanzo dev --orchestrator gpt-4o \
          --instances 3 \
          --critic-instances 2 \
          --enable-guardrails \
          --workspace /path/to/project
```

Then provide review instructions:
```
Please review the codebase for:
1. Security vulnerabilities
2. Performance bottlenecks
3. Architecture issues
4. Code quality problems
5. Best practice violations

Generate a detailed report with fixes.
```

### Multi-Model Orchestration

You can combine different models for specialized tasks:

```python
# In your Python code
from hanzo.dev import HanzoDevOrchestrator

orchestrator = HanzoDevOrchestrator(
    orchestrator_model="gpt-5",      # High-level planning
    worker_models=[
        "gpt-4o",                     # Code generation
        "codex",                      # Code completion
        "local:llama3.2"              # Simple tasks
    ],
    critic_models=[
        "claude-3-5-sonnet",          # Deep analysis
        "gpt-4-turbo"                 # Fast validation
    ]
)
```

## Cost Optimization Strategies

### 1. Tiered Routing

The system automatically routes tasks based on complexity:

| Task Type | Routed To | Examples |
|-----------|-----------|----------|
| Simple | Local models | Formatting, linting, simple checks |
| Medium | GPT-4-turbo | Refactoring, documentation |
| Complex | GPT-4o/GPT-5 | Architecture, security analysis |
| Critical | GPT-5/O3 | System design, complex debugging |

### 2. Batch Processing

Group related tasks for efficient processing:

```bash
# Process multiple files in parallel
hanzo dev --orchestrator gpt-4o \
          --batch-mode \
          --files "src/**/*.py"
```

### 3. Caching and Reuse

The system caches:
- Common code patterns
- Previous review results
- Frequent queries

## Model-Specific Features

### GPT-5 Features
- Advanced reasoning chains
- Multi-step planning
- Cross-codebase analysis
- Architectural recommendations

### GPT-4o Features
- Optimized for code tasks
- Fast response times
- Excellent at refactoring
- Strong type inference

### Codex Features
- Code completion
- Docstring generation
- Test generation
- Code translation

### O3 Features
- Complex problem solving
- Mathematical proofs
- Algorithm optimization
- Security analysis

## Integration with MCP Tools

All orchestrators can use MCP tools:

```bash
# Enable all MCP tools for the orchestrator
hanzo dev --orchestrator gpt-5 --mcp-tools
```

Available tools:
- File operations
- Code search
- Git operations
- Browser automation
- Database queries
- API calls

## Monitoring and Debugging

### View Orchestrator Decisions

```bash
# Enable verbose logging
hanzo dev --orchestrator gpt-4o --verbose

# Monitor in real-time
hanzo dev --orchestrator gpt-5 --monitor
```

### Performance Metrics

The system tracks:
- Token usage per model
- Response times
- Task success rates
- Cost per operation

View metrics:
```bash
hanzo metrics --orchestrator gpt-5
```

## Best Practices

1. **Start with GPT-4o**: Good balance of performance and cost
2. **Use local models for simple tasks**: Free and fast
3. **Reserve GPT-5 for complex problems**: Maximum capability when needed
4. **Enable critic agents**: Catch issues early
5. **Use guardrails**: Prevent code degradation
6. **Monitor costs**: Track usage with `hanzo metrics`

## Example Workflows

### Security Audit

```bash
hanzo dev --orchestrator gpt-5 \
          --focus security \
          --workspace . \
          --output security-report.md
```

### Performance Optimization

```bash
hanzo dev --orchestrator gpt-4o \
          --focus performance \
          --profile \
          --suggest-optimizations
```

### Architecture Review

```bash
hanzo dev --orchestrator o3 \
          --focus architecture \
          --generate-diagrams \
          --suggest-patterns
```

## Environment Variables

```bash
# Required for OpenAI models
export OPENAI_API_KEY=sk-...

# Optional: Custom endpoints
export OPENAI_API_BASE=https://api.openai.com/v1
export GPT5_ENDPOINT=https://api.openai.com/v1  # When available

# Cost limits
export HANZO_DAILY_LIMIT=100  # USD
export HANZO_HOURLY_LIMIT=10  # USD
```

## Troubleshooting

### Model Not Available

If GPT-5 is not yet available:
```bash
# Fallback to GPT-4o
hanzo dev --orchestrator gpt-4o
```

### Rate Limits

Handle rate limits with:
```bash
# Add retry logic and backoff
hanzo dev --orchestrator gpt-4o \
          --retry-on-rate-limit \
          --max-retries 3
```

### High Costs

Reduce costs with:
```bash
# Use local models for most tasks
hanzo dev --orchestrator gpt-4o \
          --use-hanzo-net \
          --prefer-local
```

## Future Features

- **GPT-5 Vision**: Code review from screenshots
- **Voice Control**: Natural language commands
- **Auto-fix**: Automatic issue resolution
- **Continuous Monitoring**: 24/7 code quality checks
- **Team Collaboration**: Multiple orchestrators working together

## Support

For issues or questions:
- GitHub: https://github.com/hanzoai/python-sdk
- Discord: https://discord.gg/hanzoai
- Email: support@hanzo.ai