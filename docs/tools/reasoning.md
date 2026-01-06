# hanzo-tools-reasoning

Structured thinking and critical analysis tools for AI agents. Provides the `think` and `critic` tools for deliberate reasoning.

## Installation

```bash
pip install hanzo-tools-reasoning
```

Or as part of the full toolkit:

```bash
pip install hanzo-mcp[tools-all]
```

## Overview

`hanzo-tools-reasoning` provides:

- **think** - Structured reasoning and brainstorming
- **critic** - Critical analysis and devil's advocate

## think

Use the think tool for deliberate reasoning without taking action.

### When to Use

1. **Exploring solutions** - Brainstorm approaches before implementing
2. **Debugging** - Organize hypotheses about failures
3. **Planning** - Think through architecture decisions
4. **Complex problems** - Break down multi-step solutions

### Usage

```python
think(thought="""
Feature Implementation Planning
- New code search feature requirements:
  * Search for code patterns across multiple files
  * Identify function usages and references
  * Analyze import relationships
  * Generate summary of matching patterns

- Implementation considerations:
  * Need to leverage existing search mechanisms
  * Should use regex for pattern matching
  * Results need consistent format
  * Must handle large codebases efficiently

- Design approach:
  1. Create new CodeSearcher class
  2. Implement core pattern matching
  3. Add result formatting
  4. Integrate with file traversal
  5. Add caching for performance

- Testing strategy:
  * Unit tests for search accuracy
  * Integration tests with existing components
  * Performance tests with large codebases
""")
```

### Best Practices

- **Be specific**: Include concrete details and constraints
- **Structure thoughts**: Use lists, sections, and hierarchies
- **Consider alternatives**: List multiple approaches
- **Note tradeoffs**: Document pros/cons of each option

### Examples

#### Bug Investigation

```python
think(thought="""
Bug Analysis: API returning 500 errors

Symptoms:
- Intermittent 500 errors on /api/users endpoint
- Happens under high load
- Error logs show connection pool exhausted

Hypotheses:
1. Connection pool too small
   - Check: current pool size vs concurrent requests
   - Fix: increase pool size or add connection recycling

2. Slow queries blocking connections
   - Check: query execution times
   - Fix: add indexes, optimize queries

3. Connection leak in error paths
   - Check: connection release in exception handlers
   - Fix: ensure connections released in finally blocks

Investigation order:
1. Check connection pool metrics
2. Review slow query logs
3. Audit connection handling code
""")
```

#### Architecture Decision

```python
think(thought="""
Architecture Decision: State Management

Options:
1. Redux
   + Predictable state updates
   + Great devtools
   - Boilerplate heavy
   - Overkill for simple apps

2. Zustand
   + Minimal API
   + No providers needed
   + TypeScript friendly
   - Less ecosystem

3. React Context + useReducer
   + Built-in, no dependencies
   + Familiar patterns
   - Performance concerns at scale
   - Manual optimization needed

Recommendation: Zustand
- Our app is medium complexity
- Team prefers minimal boilerplate
- TypeScript is priority
- Performance is acceptable for our scale
""")
```

## critic

Use the critic tool for critical analysis and quality assurance.

### When to Use

1. **Code review** - Analyze implementations for issues
2. **Before finalizing** - Ensure quality standards met
3. **Testing** - Question if tests are comprehensive
4. **Design review** - Challenge assumptions

### Usage

```python
critic(analysis="""
Code Review Analysis:

Implementation Issues:
- No error handling for network failures in API calls
- Missing validation for user input boundaries
- Race condition possible in concurrent updates
- Memory leak potential in event listener registration

Test Coverage Gaps:
- No tests for error scenarios
- Missing edge case: empty array input
- No performance benchmarks for large datasets
- Integration tests don't cover auth failures

Security Concerns:
- SQL injection vulnerability in query construction
- Missing rate limiting on public endpoints
- Sensitive data logged in debug mode

Performance Issues:
- O(n²) algorithm where O(n log n) is possible
- Database queries in a loop (N+1 problem)
- No caching for expensive computations

Code Quality:
- Functions too long and doing multiple things
- Inconsistent naming conventions
- Missing type annotations
- No documentation for complex algorithms

Design Flaws:
- Tight coupling between modules
- Hard-coded configuration values
- No abstraction for external dependencies
- Violates single responsibility principle

Recommendations:
1. Add comprehensive error handling
2. Implement input validation
3. Use database transactions for race conditions
4. Parameterize SQL queries
5. Implement rate limiting
6. Refactor to smaller functions
7. Add missing type annotations
8. Batch database queries
""")
```

### The Inner Critic Mindset

The critic tool forces critical thinking that:

- **Questions assumptions** - "Is this really necessary?"
- **Looks for bugs** - "What could go wrong?"
- **Checks edge cases** - "What about empty input?"
- **Verifies security** - "Can this be exploited?"
- **Reviews performance** - "Will this scale?"
- **Ensures quality** - "Is this maintainable?"

### Examples

#### Feature Review

```python
critic(analysis="""
Review: User Authentication Feature

Positive aspects:
- Clean API design
- Good separation of concerns
- Follows existing patterns

Issues found:
1. Token expiry not handled
   - Tokens never expire
   - No refresh token mechanism
   - Risk: Stolen tokens valid forever

2. Password handling
   - Using MD5 (insecure)
   - No salt
   - Should use bcrypt/argon2

3. Rate limiting missing
   - No limit on login attempts
   - Vulnerable to brute force

4. Error messages too specific
   - "Invalid password" reveals user exists
   - Should use generic "Invalid credentials"

5. Session management
   - No logout invalidation
   - Can't revoke sessions
   - No concurrent session limit

Required before merge:
- Switch to bcrypt
- Add rate limiting
- Implement token refresh
- Generic error messages
""")
```

#### Test Review

```python
critic(analysis="""
Test Suite Analysis:

Coverage gaps:
- No tests for boundary conditions
- Error paths untested
- Async behavior not verified
- No integration tests with real DB

Test quality issues:
- Tests too coupled to implementation
- Magic numbers without explanation
- No test documentation
- Flaky tests due to timing

Missing test categories:
- Performance/load tests
- Security tests
- Accessibility tests
- Cross-browser tests

Recommendations:
1. Add boundary condition tests
2. Test all error scenarios
3. Use proper test fixtures
4. Add integration test suite
5. Document test intentions
""")
```

## Combining Think and Critic

Use both tools together for thorough analysis:

```python
# First, think through the problem
think(thought="""
Planning: Implement caching layer
- Need to cache API responses
- Options: Redis, in-memory, file-based
- Must handle invalidation
- Need TTL support
""")

# Then, critically analyze the plan
critic(analysis="""
Cache Implementation Review:

Potential issues:
- Cache invalidation strategy unclear
- No handling for cache stampede
- Memory limits not considered
- No monitoring/metrics planned

Missing considerations:
- What happens when cache is full?
- How to warm cache on startup?
- How to handle partial failures?
- What's the fallback if Redis down?

Recommendations:
1. Define explicit invalidation triggers
2. Add circuit breaker for cache failures
3. Implement cache warming strategy
4. Add memory limits with eviction
5. Include cache hit/miss metrics
""")
```
