# Claude-Specific Workflow Patterns

## Overview
This document provides comprehensive patterns for working with Anthropic's Claude models through hanzo-mcp. It covers the Claude model family, Constitutional AI principles, and optimizations specific to Claude's strengths.

## Claude Model Family

### Model Tiers
```python
CLAUDE_MODELS = {
    # Opus - Most capable, slowest
    "claude-3-opus-20240229": {
        "context_window": 200_000,
        "strengths": ["deep reasoning", "complex analysis", "nuanced understanding"],
        "cost_tier": "premium",
        "best_for": ["architecture design", "code review", "security analysis"],
        "speed": "slow",
        "intelligence": "highest"
    },
    
    # Sonnet - Balanced performance
    "claude-3-5-sonnet-20241022": {
        "context_window": 200_000,
        "strengths": ["code generation", "balanced speed/quality", "tool use"],
        "cost_tier": "balanced",
        "best_for": ["implementation", "refactoring", "general development"],
        "speed": "medium",
        "intelligence": "high"
    },
    
    "claude-3-sonnet-20240229": {
        "context_window": 200_000,
        "strengths": ["reasoning", "code understanding"],
        "cost_tier": "balanced",
        "best_for": ["analysis", "documentation"],
        "speed": "medium",
        "intelligence": "high"
    },
    
    # Haiku - Fast and efficient
    "claude-3-haiku-20240307": {
        "context_window": 200_000,
        "strengths": ["speed", "efficiency", "simple tasks"],
        "cost_tier": "budget",
        "best_for": ["formatting", "simple edits", "quick answers"],
        "speed": "fast",
        "intelligence": "good"
    },
    
    # Legacy
    "claude-2.1": {
        "context_window": 200_000,
        "strengths": ["long context", "stability"],
        "cost_tier": "legacy",
        "best_for": ["backward compatibility"],
        "speed": "medium",
        "intelligence": "good"
    }
}
```

### Model Selection Strategy
```python
def select_claude_model(task_type: str, quality_requirement: str = "balanced"):
    """Select optimal Claude model for task."""
    
    task_model_map = {
        # High complexity tasks
        "architecture": "claude-3-opus-20240229",
        "security_audit": "claude-3-opus-20240229",
        "complex_debugging": "claude-3-opus-20240229",
        
        # Code generation tasks
        "implementation": "claude-3-5-sonnet-20241022",
        "refactoring": "claude-3-5-sonnet-20241022",
        "test_generation": "claude-3-5-sonnet-20241022",
        
        # Analysis tasks
        "code_review": "claude-3-sonnet-20240229",
        "documentation": "claude-3-sonnet-20240229",
        
        # Simple tasks
        "formatting": "claude-3-haiku-20240307",
        "simple_edits": "claude-3-haiku-20240307",
        "quick_questions": "claude-3-haiku-20240307"
    }
    
    model = task_model_map.get(task_type, "claude-3-5-sonnet-20241022")
    
    # Adjust for quality requirements
    if quality_requirement == "maximum":
        return "claude-3-opus-20240229"
    elif quality_requirement == "fast":
        return "claude-3-haiku-20240307"
    
    return model
```

## Repository Overview

This is the Hanzo Python SDK monorepo containing the official Python client library for the Hanzo AI platform and related packages. The SDK provides unified access to 100+ LLM providers through a single OpenAI-compatible API interface, with enterprise features like cost tracking, rate limiting, and observability.

## Project Structure

This is a monorepo managed with `rye` containing multiple interconnected packages:

### Main Package
- **`pkg/hanzoai/`** - Core SDK for Hanzo AI platform
  - OpenAI-compatible API client
  - Support for 100+ LLM providers
  - Cost tracking and rate limiting
  - Team and organization management
  - File operations and fine-tuning

### Sub-Packages (in `pkg/` directory)
- **`hanzo/`** - CLI and orchestration tools
- **`hanzo-mcp/`** - Model Context Protocol implementation
- **`hanzo-agents/`** - Agent framework and swarm orchestration
- **`hanzo-memory/`** - Memory and knowledge base management
- **`hanzo-network/`** - Distributed network capabilities
- **`hanzo-repl/`** - Interactive REPL for AI chat
- **`hanzo-aci/`** - AI code intelligence and editing tools

## Development Commands

### Setup and Installation
```bash
# Install Python via uv (required)
make install-python

# Complete setup (venv + dependencies)
make setup

# Install specific package for development
uv pip install -e .
uv pip install -e ./pkg/hanzo-agents
```

### Testing
```bash
# Run all tests
make test
./scripts/test

# Run specific test file
uv run pytest tests/api_resources/test_chat.py -v

# Run tests with specific pattern
uv run pytest -k "pattern" -v

# Run tests with coverage
uv run pytest --cov=hanzoai tests/

# Run tests for specific package
make test-agents  # Test hanzo-agents
make test-mcp     # Test hanzo-mcp
```

### Code Quality
```bash
# Format code
make format
ruff format pkg/

# Run linting
make lint
ruff check . --fix

# Type checking
make check-types
uv run mypy pkg/hanzoai --ignore-missing-imports
uv run pyright
```

### Building and Publishing
```bash
# Build all packages
make build

# Build specific package
uv build .
cd pkg/hanzo-mcp && uv build

# Check packages before publishing
make publish-check
```

## Architecture and Code Organization

### Client Architecture
The SDK uses a code-generated client architecture (via Stainless):
- **Base Client** (`_base_client.py`) - HTTP client with retry logic
- **Main Client** (`_client.py`) - `Hanzo` and `AsyncHanzo` classes
- **Resources** (`resources/`) - API endpoint implementations
  - Each resource follows a consistent pattern with sync/async support
  - Resources are organized by API domain (chat, files, models, etc.)
- **Types** (`types/`) - Pydantic models for request/response types

### Key Patterns

#### Resource Pattern
All API resources follow this structure:
```python
class ResourceWithRawResponse:
    def __init__(self, resource: Resource) -> None:
        self._resource = resource
        # Expose methods with raw response wrapper

class AsyncResourceWithRawResponse:
    # Async version of the above
```

#### Testing Pattern
Tests use `respx` for HTTP mocking (no external dependencies):
```python
@pytest.mark.respx(base_url=base_url)
def test_method(client: Hanzo, respx_mock: MockRouter) -> None:
    respx_mock.get("/endpoint").mock(return_value=Response(200, json={}))
    # Test implementation
```

### Important Implementation Details

1. **Environment Variables**:
   - `HANZO_API_KEY` - API authentication
   - `HANZO_BASE_URL` - API base URL (default: https://api.hanzo.ai)
   - `HANZO_LOG` - Logging level (debug/info/warning/error)

2. **Dependency Management**:
   - Uses `rye` for workspace management
   - `uv` for fast Python package operations
   - Separate lock files for production and dev dependencies

3. **Test Infrastructure**:
   - All tests use mocked responses (no external API calls)
   - 100% test coverage requirement
   - Tests organized by resource in `tests/api_resources/`

4. **Code Generation**:
   - Many files are auto-generated from OpenAPI spec
   - Look for "File generated from our OpenAPI spec" header
   - Manual changes to generated files will be overwritten

## Package-Specific Notes

### hanzo-mcp
- Implements Model Context Protocol for tool capabilities
- Includes filesystem, search, and agent delegation tools
- Can be installed to Claude Desktop with `make install-desktop`

### hanzo-agents
- Provides agent swarm orchestration
- Supports both hierarchical and peer network architectures
- Includes MCP tool integration for recursive agent calls

### hanzo CLI
- Main entry point: `hanzo.cli:main`
- Subcommands for auth, chat, mcp, network operations
- Supports local AI orchestration with `hanzo dev`

## Common Tasks

### Adding New API Endpoints
1. Update OpenAPI spec if using code generation
2. Add resource class in `resources/` directory
3. Add types in `types/` directory
4. Add tests in `tests/api_resources/`
5. Update `__init__.py` exports

### Running Local Development Server
```bash
# Start mock server for testing
python run_mock_server.py

# Run hanzo dev with local orchestration
hanzo dev --orchestrator local:llama-3.2-3b
```

### Debugging Tests
```bash
# Run with verbose output
uv run pytest -vv tests/

# Run with print statements visible
uv run pytest -s tests/

# Run specific test with debugging
uv run pytest tests/test_client.py::TestClient::test_method -vv
```

## CI/CD Pipeline

The repository uses GitHub Actions for CI:
- **Linting** - Runs on every push/PR with `ruff`
- **Testing** - Full test suite with coverage reporting
- **Type Checking** - Both `mypy` and `pyright`
- **Package Testing** - Separate CI for each sub-package

## Important Conventions

1. **No Print Statements**: Use logging instead, except in CLI tools
2. **Type Hints Required**: All functions must have type annotations
3. **Async Support**: All API methods have both sync and async versions
4. **Error Handling**: Use specific exception classes from `_exceptions.py`
5. **Documentation**: Docstrings for public APIs, examples in `/examples`

## Constitutional AI Principles

### Implementing Constitutional AI in Practice
```python
def apply_constitutional_ai(prompt: str, response: str) -> str:
    """Apply Constitutional AI principles to Claude's responses."""
    
    constitutional_check = claude(
        prompt=f"""
        Original request: {prompt}
        Initial response: {response}
        
        Review this response against these principles:
        1. Helpful: Does it genuinely help the user?
        2. Harmless: Could it cause any harm?
        3. Honest: Is it accurate and truthful?
        
        If any issues, provide a revised response.
        Otherwise, return "APPROVED".
        """,
        model="claude-3-opus-20240229"
    )
    
    if constitutional_check != "APPROVED":
        return constitutional_check
    return response
```

### Ethical Code Generation
```python
# Claude excels at considering ethical implications
ethical_result = claude(
    prompt="""
    Implement user data deletion feature.
    
    Consider:
    - GDPR compliance
    - User privacy rights
    - Data retention requirements
    - Audit trail needs
    - Cascading deletions
    
    Explain ethical tradeoffs in your implementation.
    """,
    model="claude-3-opus-20240229"
)
```

## XML Tag Usage for Structured Thinking

### Structured Analysis Pattern
```python
# Claude responds well to XML-style structure
analysis_result = claude(
    prompt="""
    Analyze this codebase for refactoring opportunities.
    
    <analysis_structure>
        <code_smells>
            Identify problematic patterns
        </code_smells>
        
        <architecture_issues>
            Find architectural problems
        </architecture_issues>
        
        <performance_bottlenecks>
            Locate performance issues
        </performance_bottlenecks>
        
        <security_vulnerabilities>
            Identify security risks
        </security_vulnerabilities>
        
        <recommendations>
            Provide prioritized fixes
        </recommendations>
    </analysis_structure>
    
    Use the XML tags in your response.
    """,
    model="claude-3-opus-20240229"
)
```

### Thinking Tags Pattern
```python
# Use thinking tags for complex reasoning
reasoning_result = claude(
    prompt="""
    Design a distributed caching strategy.
    
    <thinking>
    Consider these aspects step by step:
    - Cache invalidation strategies
    - Consistency guarantees
    - Network partition handling
    - Performance implications
    </thinking>
    
    <solution>
    Provide your recommended approach
    </solution>
    
    <implementation>
    Show code examples
    </implementation>
    """,
    model="claude-3-opus-20240229"
)
```

## Long Context Handling (200k tokens)

### Context Window Utilization
```python
class ClaudeLongContext:
    """Utilize Claude's 200k token context window."""
    
    def __init__(self, model="claude-3-opus-20240229"):
        self.model = model
        self.max_tokens = 200_000
    
    def analyze_large_pr(self, pr_files: dict):
        """Analyze large PR with many files."""
        
        # Build comprehensive context
        context = self.build_pr_context(pr_files)
        
        return claude(
            prompt=f"""
            Review this pull request:
            
            {context}
            
            Provide:
            1. Overall assessment
            2. Security concerns
            3. Performance implications
            4. Breaking changes
            5. Test coverage gaps
            6. Specific file-by-file feedback
            """,
            model=self.model,
            max_tokens=4000
        )
    
    def build_pr_context(self, files):
        """Build context from PR files."""
        context_parts = []
        
        for filepath, changes in files.items():
            context_parts.append(f"""
            <file path="{filepath}">
            {changes}
            </file>
            """)
        
        return "\n".join(context_parts)
```

### Conversation Memory Management
```python
class ClaudeConversationManager:
    """Manage long conversations with Claude."""
    
    def __init__(self):
        self.conversation_history = []
        self.max_context = 190_000  # Leave room for response
    
    def add_turn(self, user_msg: str, assistant_msg: str):
        """Add conversation turn."""
        self.conversation_history.append({
            "user": user_msg,
            "assistant": assistant_msg,
            "timestamp": time.time()
        })
    
    def get_relevant_context(self, new_query: str):
        """Get relevant conversation context."""
        
        # Claude can handle full context
        full_context = self.format_history()
        
        if self.estimate_tokens(full_context) < self.max_context:
            return full_context
        
        # Smart truncation if needed
        return self.smart_truncate(full_context, new_query)
    
    def smart_truncate(self, context: str, query: str):
        """Intelligently truncate context."""
        
        # Keep most relevant parts
        return claude(
            prompt=f"""
            <context>
            {context}
            </context>
            
            <new_query>
            {query}
            </new_query>
            
            Extract the most relevant parts of the context
            for answering the new query. Keep under 180k tokens.
            """,
            model="claude-3-haiku-20240307"  # Use fast model
        )
```

## Code Generation with Claude

### Claude's Code Generation Strengths
```python
# Claude excels at generating well-structured, documented code
code_result = claude(
    prompt="""
    Implement a rate limiter with these requirements:
    - Token bucket algorithm
    - Redis backend
    - Async Python
    - Per-user and per-IP limits
    - Graceful degradation
    
    Include:
    1. Full implementation
    2. Comprehensive docstrings
    3. Type hints
    4. Unit tests
    5. Integration tests
    6. Usage examples
    """,
    model="claude-3-5-sonnet-20241022",
    temperature=0.3  # Lower for code generation
)
```

### Test Generation Pattern
```python
def generate_tests_with_claude(code: str):
    """Generate comprehensive tests with Claude."""
    
    return claude(
        prompt=f"""
        Generate comprehensive tests for this code:
        
        ```python
        {code}
        ```
        
        Include:
        <unit_tests>
        - Test each function/method
        - Edge cases
        - Error conditions
        - Mocking external dependencies
        </unit_tests>
        
        <integration_tests>
        - End-to-end scenarios
        - Real dependency tests
        </integration_tests>
        
        <property_tests>
        - Property-based tests using hypothesis
        </property_tests>
        
        Use pytest framework with fixtures.
        """,
        model="claude-3-5-sonnet-20241022"
    )
```

## Artifact Generation Patterns

### Documentation Artifacts
```python
# Claude can generate structured artifacts
docs_result = claude(
    prompt="""
    Create comprehensive documentation for this module.
    
    Generate these artifacts:
    1. README.md - Overview and quickstart
    2. API.md - Full API reference
    3. EXAMPLES.md - Usage examples
    4. CONTRIBUTING.md - Contribution guide
    
    Format as separate markdown sections.
    """,
    model="claude-3-sonnet-20240229"
)
```

### Configuration Generation
```python
# Generate complex configurations
config_result = claude(
    prompt="""
    Generate production-ready configurations:
    
    1. docker-compose.yml - Full stack setup
    2. .github/workflows/ci.yml - CI/CD pipeline
    3. kubernetes/deployment.yaml - K8s deployment
    4. terraform/main.tf - Infrastructure as code
    
    Include security best practices and comments.
    """,
    model="claude-3-opus-20240229"
)
```

## Multi-Turn Conversation Management

### Stateful Conversations
```python
class ClaudeStatefulChat:
    """Manage stateful conversations with Claude."""
    
    def __init__(self, model="claude-3-5-sonnet-20241022"):
        self.model = model
        self.messages = []
        self.system_prompt = None
    
    def set_system(self, prompt: str):
        """Set system prompt for conversation."""
        self.system_prompt = prompt
    
    def add_message(self, role: str, content: str):
        """Add message to conversation."""
        self.messages.append({"role": role, "content": content})
    
    def chat(self, user_input: str):
        """Continue conversation."""
        self.add_message("user", user_input)
        
        response = claude(
            messages=self.messages,
            system=self.system_prompt,
            model=self.model
        )
        
        self.add_message("assistant", response)
        return response
    
    def reset_context(self, keep_system=True):
        """Reset conversation context."""
        self.messages = []
        if not keep_system:
            self.system_prompt = None
```

## Analysis and Reasoning Capabilities

### Deep Code Analysis
```python
# Claude's superior reasoning for complex analysis
analysis = claude(
    prompt="""
    Perform deep analysis of this codebase:
    
    <reasoning_steps>
    1. Identify architectural patterns
    2. Find hidden dependencies
    3. Detect potential race conditions
    4. Analyze error propagation
    5. Evaluate test effectiveness
    </reasoning_steps>
    
    <provide>
    - Detailed findings for each step
    - Risk assessment
    - Prioritized recommendations
    </provide>
    
    Think step by step, showing your reasoning.
    """,
    model="claude-3-opus-20240229"
)
```

### Comparative Analysis
```python
# Claude excels at nuanced comparisons
comparison = claude(
    prompt="""
    Compare these two implementation approaches:
    
    <approach_1>
    {code_1}
    </approach_1>
    
    <approach_2>
    {code_2}
    </approach_2>
    
    Analyze:
    - Performance characteristics
    - Maintainability
    - Scalability
    - Error handling
    - Testing complexity
    
    Provide a balanced recommendation.
    """,
    model="claude-3-opus-20240229"
)
```

## Integration with Claude Desktop and MCP

### Claude Desktop Configuration
```json
{
  "mcpServers": {
    "hanzo-mcp": {
      "command": "hanzo-mcp",
      "args": ["serve"],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "DEFAULT_CLAUDE_MODEL": "claude-3-5-sonnet-20241022"
      }
    }
  }
}
```

### MCP Tool Usage Patterns
```python
# Claude with MCP tools
result = claude(
    prompt="""
    Using available MCP tools:
    1. Search for authentication patterns
    2. Read the main auth module
    3. Suggest improvements
    4. Generate updated implementation
    """,
    enable_tools=True,
    tools=["search", "read", "write"]
)
```

## Claude CLI Tool Usage

### Basic CLI Usage
```bash
# Direct Claude invocation
claude "Analyze this Python module for improvements"

# With specific model
claude --model claude-3-opus-20240229 "Design system architecture"

# With system prompt
claude --system "You are a security expert" "Audit this code for vulnerabilities"
```

### Advanced CLI Patterns
```bash
# Multi-file analysis
claude --files "*.py" "Review all Python files for consistency"

# Interactive mode
claude --interactive --model claude-3-5-sonnet-20241022

# With context from previous conversation
claude --continue-from session-123 "What about the error handling?"
```

## Best Practices for Claude

### 1. Model Selection
```python
# Choose based on task requirements
if needs_deep_reasoning:
    model = "claude-3-opus-20240229"
elif needs_code_generation:
    model = "claude-3-5-sonnet-20241022"
elif needs_speed:
    model = "claude-3-haiku-20240307"
else:
    model = "claude-3-sonnet-20240229"
```

### 2. Prompt Engineering
- Use XML tags for structure
- Include thinking steps for complex reasoning
- Provide clear output format specifications
- Use Constitutional AI principles

### 3. Context Management
- Leverage full 200k context when beneficial
- Use conversation history effectively
- Implement smart truncation when needed

### 4. Error Handling
```python
try:
    result = claude(prompt=prompt, model=model)
except AnthropicError as e:
    if "rate_limit" in str(e):
        # Wait and retry
        time.sleep(60)
        result = claude(prompt=prompt, model="claude-3-haiku-20240307")
    elif "context_length" in str(e):
        # Truncate and retry
        truncated_prompt = prompt[:50000]
        result = claude(prompt=truncated_prompt, model=model)
    else:
        raise
```

### 5. Cost Optimization
- Use Haiku for simple tasks
- Cache frequently used responses
- Batch similar requests
- Monitor token usage

## Integration with Hanzo SDK

### Using Claude through Hanzo
```python
from hanzoai import Hanzo

client = Hanzo(api_key="your-key")

# Use Claude through unified interface
response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[
        {"role": "user", "content": "Your prompt"}
    ],
    max_tokens=4000,
    temperature=0.7
)
```

### Claude-Specific Features
```python
# System prompts (Claude-specific)
response = client.chat.completions.create(
    model="claude-3-opus-20240229",
    system="You are an expert code reviewer",
    messages=[{"role": "user", "content": "Review this code"}]
)

# Streaming responses
stream = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Generate code"}],
    stream=True
)

for chunk in stream:
    print(chunk.choices[0].delta.content, end="")
```

This comprehensive guide enables effective use of Claude models for development workflows in the Hanzo Python SDK project.