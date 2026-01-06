# Reasoning Tools

Structured thinking and critical analysis.

→ **Full documentation: [../../tools/reasoning.md](../../tools/reasoning.md)**

## Quick Reference

### Think Tool

```python
# Structured reasoning
think(thought="""
Analyzing the authentication architecture:
1. Current: Session-based auth with cookies
2. Problem: Mobile apps need token-based auth
3. Options:
   - JWT tokens
   - OAuth 2.0
   - API keys
4. Recommendation: JWT for stateless auth
""")
```

### Critic Tool

```python
# Critical analysis
critic(analysis="""
Code Review Analysis:
- Missing error handling for network failures
- No input validation on user data
- SQL injection vulnerability in query construction
- N+1 database query problem in loop

Recommendations:
1. Add try/catch with retry logic
2. Validate all inputs at API boundary
3. Use parameterized queries
4. Batch database queries
""")
```

Use `think` for exploration, `critic` for quality assurance.
