# hanzo-tools-reasoning

Reasoning and analysis tools for Hanzo MCP.

## Installation

```bash
pip install hanzo-tools-reasoning
```

## Tools

### think - Structured Reasoning
Record thoughts for complex reasoning or brainstorming.

```python
think(thought="Analyzing the architecture: The codebase uses...")
```

**Use cases:**
- Bug exploration and fix brainstorming
- Test failure analysis
- Complex refactoring planning
- Feature design decisions
- Issue investigation

### critic - Critical Analysis
Play devil's advocate and ensure high standards.

```python
critic(analysis="Review this implementation for bugs and edge cases...")
```

**What it checks:**
- Potential bugs and edge cases
- Error handling gaps
- Test coverage issues
- Performance problems
- Security vulnerabilities
- Code quality and design

**Example output:**
```
Code Review Analysis:
- Implementation Issues:
  * No error handling for network failures
  * Race condition in concurrent updates
  
- Test Coverage Gaps:
  * No tests for error scenarios
  * Missing edge case: empty input
  
- Recommendations:
  1. Add retry logic with exponential backoff
  2. Use database transactions
```

## License

MIT
