# Gemini-Specific Workflow Patterns

## Overview
This document provides comprehensive patterns for working with Google's Gemini models through hanzo-mcp. It covers the Gemini model family, multimodal capabilities, and optimizations specific to Gemini's strengths.

## Gemini Model Family

### Model Tiers
```python
GEMINI_MODELS = {
    # Ultra Tier - Most capable
    "gemini-1.5-ultra": {
        "context_window": 2_097_152,  # 2M tokens
        "strengths": ["complex reasoning", "multimodal", "long context"],
        "cost_tier": "premium",
        "best_for": ["architecture design", "comprehensive analysis"]
    },
    
    # Pro Tier - Balanced performance
    "gemini-1.5-pro": {
        "context_window": 2_097_152,  # 2M tokens
        "strengths": ["reasoning", "code generation", "multimodal"],
        "cost_tier": "balanced",
        "best_for": ["general development", "code review", "documentation"]
    },
    
    "gemini-1.0-pro": {
        "context_window": 32_768,
        "strengths": ["text generation", "reasoning"],
        "cost_tier": "balanced",
        "best_for": ["standard tasks", "quick responses"]
    },
    
    # Flash Tier - Fast and efficient
    "gemini-1.5-flash": {
        "context_window": 1_048_576,  # 1M tokens
        "strengths": ["speed", "efficiency", "multimodal"],
        "cost_tier": "budget",
        "best_for": ["quick tasks", "high volume", "real-time responses"]
    },
    
    "gemini-1.5-flash-8b": {
        "context_window": 1_048_576,  # 1M tokens
        "strengths": ["ultra-fast", "low latency"],
        "cost_tier": "economy",
        "best_for": ["simple tasks", "formatting", "extraction"]
    }
}
```

### Model Selection Strategy
```python
def select_gemini_model(task_type: str, context_size: int, budget: str = "balanced"):
    """Select optimal Gemini model for task."""
    
    if context_size > 32_768:
        # Need long context support
        if budget == "premium":
            return "gemini-1.5-ultra"
        elif budget == "balanced":
            return "gemini-1.5-pro"
        else:
            return "gemini-1.5-flash"
    
    # Standard context tasks
    task_model_map = {
        "architecture": "gemini-1.5-pro",
        "code_generation": "gemini-1.5-pro",
        "code_review": "gemini-1.5-pro",
        "documentation": "gemini-1.5-flash",
        "formatting": "gemini-1.5-flash-8b",
        "extraction": "gemini-1.5-flash-8b",
        "analysis": "gemini-1.5-pro",
        "multimodal": "gemini-1.5-pro"
    }
    
    return task_model_map.get(task_type, "gemini-1.5-flash")
```

## Multimodal Capabilities

### Text + Image Analysis
```python
# Using Gemini for code screenshot analysis
result = gemini(
    prompt="""
    Analyze this code screenshot:
    - Identify the programming language
    - Explain what the code does
    - Suggest improvements
    - Find potential bugs
    """,
    images=["path/to/code_screenshot.png"],
    model="gemini-1.5-pro"
)
```

### Video Analysis
```python
# Analyze code walkthrough video
result = gemini(
    prompt="""
    Watch this code review video and:
    1. Summarize the main points
    2. List all mentioned issues
    3. Extract action items
    4. Note design decisions
    """,
    video="path/to/review_video.mp4",
    model="gemini-1.5-pro"
)
```

### Audio Processing
```python
# Transcribe and analyze meeting recording
result = gemini(
    prompt="""
    Process this technical discussion:
    1. Transcribe the conversation
    2. Extract technical decisions
    3. List action items by person
    4. Summarize architecture choices
    """,
    audio="path/to/meeting.mp3",
    model="gemini-1.5-flash"
)
```

### Combined Multimodal
```python
# Analyze multiple inputs together
result = gemini(
    prompt="""
    Based on the whiteboard image, code files, and audio explanation:
    1. Create implementation plan
    2. Identify potential issues
    3. Suggest optimizations
    4. Generate documentation
    """,
    images=["whiteboard.jpg"],
    text_files=["main.py", "config.yaml"],
    audio="explanation.mp3",
    model="gemini-1.5-ultra"
)
```

## Long Context Window Strategies

### 2M Token Context Utilization
```python
class GeminiLongContext:
    """Utilize Gemini's 2M token context window."""
    
    def __init__(self, model="gemini-1.5-pro"):
        self.model = model
        self.max_tokens = 2_097_152
    
    def analyze_entire_codebase(self, repo_path: str):
        """Analyze entire repository in single context."""
        
        # Collect all code files
        code_files = self.collect_files(repo_path)
        
        # Build massive context
        context = self.build_context(code_files)
        
        # Single comprehensive analysis
        return gemini(
            prompt=f"""
            Analyze this entire codebase:
            
            {context}
            
            Provide:
            1. Architecture overview
            2. Design patterns used
            3. Security vulnerabilities
            4. Performance bottlenecks
            5. Refactoring opportunities
            6. Missing tests
            7. Documentation gaps
            """,
            model=self.model,
            max_tokens=8000  # Large response
        )
    
    def build_context(self, files):
        """Build context from files."""
        context_parts = []
        
        for file_path, content in files.items():
            context_parts.append(f"""
            === File: {file_path} ===
            {content}
            """)
        
        return "\n\n".join(context_parts)
```

### Context Window Management
```python
def optimize_gemini_context(files: dict, max_context: int = 2_000_000):
    """Optimize context for Gemini's window."""
    
    # Priority ordering
    priority_order = [
        ".py",      # Python files first
        ".ts",      # TypeScript
        ".js",      # JavaScript
        ".md",      # Documentation
        ".yaml",    # Config
        ".json",    # Data files
    ]
    
    sorted_files = []
    for ext in priority_order:
        sorted_files.extend([
            (path, content) 
            for path, content in files.items() 
            if path.endswith(ext)
        ])
    
    # Build context up to limit
    context = []
    current_size = 0
    
    for path, content in sorted_files:
        file_size = len(content) // 4  # Rough token estimate
        if current_size + file_size > max_context:
            break
        
        context.append(f"File: {path}\n{content}")
        current_size += file_size
    
    return "\n\n".join(context)
```

## Code Generation Optimizations

### Gemini Code Generation Patterns
```python
# Optimized code generation prompt
code_result = gemini(
    prompt="""
    Generate Python implementation for user authentication:
    
    Requirements:
    - JWT tokens with RS256
    - Redis session storage
    - Rate limiting per IP
    - Password complexity validation
    - 2FA support
    
    Style Guidelines:
    - Use type hints
    - Add comprehensive docstrings
    - Include error handling
    - Follow PEP 8
    
    Include:
    1. Main implementation
    2. Unit tests
    3. Integration tests
    4. Usage examples
    """,
    model="gemini-1.5-pro",
    temperature=0.4,  # Focused generation
    response_mime_type="text/x-python"  # Gemini-specific
)
```

### Multi-File Generation
```python
def generate_module_with_gemini(module_name: str, requirements: str):
    """Generate complete module with Gemini."""
    
    result = gemini(
        prompt=f"""
        Create a complete Python module '{module_name}' with these requirements:
        {requirements}
        
        Generate these files:
        1. __init__.py - Package initialization
        2. models.py - Data models
        3. services.py - Business logic
        4. api.py - API endpoints
        5. utils.py - Helper functions
        6. tests/test_{module_name}.py - Tests
        7. README.md - Documentation
        
        Use markdown code blocks with filenames:
        ```python:filename.py
        code here
        ```
        """,
        model="gemini-1.5-pro",
        temperature=0.3
    )
    
    # Parse and save files
    files = parse_gemini_multifile_response(result)
    return files
```

## Integration with Google Cloud Services

### Vertex AI Integration
```python
from google.cloud import aiplatform
from hanzoai import Hanzo

class GeminiVertex:
    """Gemini through Vertex AI."""
    
    def __init__(self, project_id: str, location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
        aiplatform.init(project=project_id, location=location)
        
        # Also use through Hanzo
        self.hanzo = Hanzo(
            api_key=os.getenv("HANZO_API_KEY")
        )
    
    async def generate(self, prompt: str, model: str = "gemini-1.5-pro"):
        """Generate using Vertex AI or Hanzo."""
        
        try:
            # Try Vertex AI first (better quotas)
            response = await self.vertex_generate(prompt, model)
        except Exception:
            # Fallback to Hanzo
            response = await self.hanzo.chat.completions.create(
                model=f"vertex/{model}",
                messages=[{"role": "user", "content": prompt}]
            )
        
        return response
```

### Google Cloud Storage Integration
```python
def analyze_gcs_codebase(bucket_name: str, prefix: str = ""):
    """Analyze code directly from GCS."""
    
    # List all files in bucket
    files = list_gcs_files(bucket_name, prefix)
    
    # Build GCS URLs
    file_urls = [
        f"gs://{bucket_name}/{file}"
        for file in files
    ]
    
    # Gemini can read GCS directly
    result = gemini(
        prompt="""
        Analyze this codebase from Google Cloud Storage.
        Provide comprehensive architecture review.
        """,
        files=file_urls,  # GCS URLs
        model="gemini-1.5-pro"
    )
    
    return result
```

## Cost-Performance Tradeoffs

### Cost Optimization Strategy
```python
class GeminiCostOptimizer:
    """Optimize Gemini usage costs."""
    
    def __init__(self):
        self.cost_per_1k_tokens = {
            "gemini-1.5-ultra": {"input": 0.007, "output": 0.021},
            "gemini-1.5-pro": {"input": 0.0035, "output": 0.0105},
            "gemini-1.5-flash": {"input": 0.00035, "output": 0.00105},
            "gemini-1.5-flash-8b": {"input": 0.0001, "output": 0.0003}
        }
    
    def select_by_budget(self, task: str, max_cost: float):
        """Select model within budget."""
        
        estimated_tokens = self.estimate_tokens(task)
        
        for model, costs in self.cost_per_1k_tokens.items():
            estimated_cost = (
                (estimated_tokens["input"] / 1000) * costs["input"] +
                (estimated_tokens["output"] / 1000) * costs["output"]
            )
            
            if estimated_cost <= max_cost:
                return model
        
        return "gemini-1.5-flash-8b"  # Cheapest fallback
    
    def batch_optimize(self, tasks: list):
        """Optimize batch processing."""
        
        # Group by complexity
        simple_tasks = [t for t in tasks if t["complexity"] == "simple"]
        complex_tasks = [t for t in tasks if t["complexity"] == "complex"]
        
        # Use Flash for simple tasks
        if simple_tasks:
            gemini(
                prompt=self.batch_prompt(simple_tasks),
                model="gemini-1.5-flash-8b"
            )
        
        # Use Pro for complex tasks
        if complex_tasks:
            gemini(
                prompt=self.batch_prompt(complex_tasks),
                model="gemini-1.5-pro"
            )
```

## Gemini-Specific Prompt Formats

### Structured Prompts
```python
def create_gemini_prompt(
    instruction: str,
    context: str = None,
    examples: list = None,
    constraints: list = None,
    output_format: str = None
):
    """Create optimized Gemini prompt."""
    
    prompt_parts = []
    
    # Gemini responds well to clear sections
    prompt_parts.append(f"## Instruction\n{instruction}")
    
    if context:
        prompt_parts.append(f"## Context\n{context}")
    
    if examples:
        prompt_parts.append("## Examples")
        for i, example in enumerate(examples, 1):
            prompt_parts.append(f"### Example {i}")
            prompt_parts.append(f"Input: {example['input']}")
            prompt_parts.append(f"Output: {example['output']}")
    
    if constraints:
        prompt_parts.append("## Constraints")
        for constraint in constraints:
            prompt_parts.append(f"- {constraint}")
    
    if output_format:
        prompt_parts.append(f"## Output Format\n{output_format}")
    
    return "\n\n".join(prompt_parts)
```

### Chain of Thought Prompting
```python
# Gemini excels at step-by-step reasoning
cot_result = gemini(
    prompt="""
    Solve this algorithm problem step by step:
    
    Problem: [problem description]
    
    Think through this methodically:
    1. Understand the problem
    2. Identify the algorithm type
    3. Consider edge cases
    4. Design the solution
    5. Implement in Python
    6. Analyze time complexity
    7. Optimize if possible
    
    Show your reasoning for each step.
    """,
    model="gemini-1.5-pro",
    temperature=0.2
)
```

## Function Calling Patterns

### Gemini Function Calling
```python
# Define functions for Gemini
functions = [
    {
        "name": "execute_code",
        "description": "Execute Python code and return results",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute"
                }
            },
            "required": ["code"]
        }
    },
    {
        "name": "search_documentation",
        "description": "Search project documentation",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "file_pattern": {
                    "type": "string",
                    "description": "File pattern to search"
                }
            },
            "required": ["query"]
        }
    }
]

# Use with function calling
result = gemini(
    prompt="Find and fix the authentication bug",
    model="gemini-1.5-pro",
    functions=functions,
    function_call="auto"  # Let Gemini decide when to call
)
```

### Tool Use Patterns
```python
def gemini_with_tools(task: str):
    """Use Gemini with tool access."""
    
    return gemini(
        prompt=f"""
        Task: {task}
        
        You have access to these tools:
        - search: Search codebase
        - read: Read files
        - execute: Run code
        - test: Run tests
        
        Use tools as needed to complete the task.
        Call tools using: TOOL[tool_name](arguments)
        """,
        model="gemini-1.5-pro",
        enable_tool_use=True
    )
```

## Safety Settings and Content Filtering

### Configure Safety Settings
```python
SAFETY_SETTINGS = {
    "harassment": "BLOCK_NONE",
    "hate_speech": "BLOCK_NONE",
    "sexually_explicit": "BLOCK_NONE",
    "dangerous_content": "BLOCK_ONLY_HIGH"
}

# Apply safety settings
result = gemini(
    prompt="Analyze security vulnerabilities",
    model="gemini-1.5-pro",
    safety_settings=SAFETY_SETTINGS
)
```

### Content Filtering for Code
```python
def gemini_code_review(code: str):
    """Review code with appropriate filters."""
    
    # Disable filters for code review
    # Code might contain security examples
    return gemini(
        prompt=f"""
        Review this code for security issues:
        ```python
        {code}
        ```
        
        Include:
        - SQL injection vulnerabilities
        - XSS possibilities
        - Authentication bypasses
        - Cryptographic weaknesses
        """,
        model="gemini-1.5-pro",
        safety_settings={
            "dangerous_content": "BLOCK_NONE"  # Allow security discussion
        }
    )
```

## Best Practices for Gemini

### 1. Model Selection
```python
# Choose model based on task requirements
if needs_multimodal:
    model = "gemini-1.5-pro"
elif needs_long_context:
    model = "gemini-1.5-pro" if budget else "gemini-1.5-flash"
elif needs_speed:
    model = "gemini-1.5-flash-8b"
else:
    model = "gemini-1.5-flash"
```

### 2. Prompt Optimization
- Use clear section headers
- Provide structured examples
- Leverage chain-of-thought for complex reasoning
- Include explicit output format specifications

### 3. Context Management
- Utilize full 2M token window when beneficial
- Prioritize relevant files in context
- Use file references for large codebases

### 4. Cost Optimization
- Use Flash models for simple tasks
- Batch similar requests
- Cache frequently used responses
- Monitor token usage

### 5. Error Handling
```python
try:
    result = gemini(prompt=prompt, model=model)
except GoogleAPIError as e:
    if "quota_exceeded" in str(e):
        # Switch to different model
        result = gemini(prompt=prompt, model="gemini-1.5-flash")
    elif "safety_filter" in str(e):
        # Adjust safety settings
        result = gemini(
            prompt=prompt,
            model=model,
            safety_settings=relaxed_settings
        )
    else:
        raise
```

## Integration with Hanzo MCP

### Using Gemini CLI Tool
```bash
# Direct Gemini invocation
gemini "Analyze this Python module for improvements"

# With specific model
gemini --model gemini-1.5-ultra "Design system architecture"

# With multimodal inputs
gemini --image diagram.png "Explain this architecture diagram"
```

### Using LLM Tool with Gemini
```bash
# Single Gemini query
llm --action query \
    --model gemini-1.5-pro \
    --prompt "Generate comprehensive test suite"

# Gemini in consensus
llm --action consensus \
    --models '["gemini-1.5-pro", "claude-3-opus", "gpt-4"]' \
    --prompt "Design decision: microservices vs monolith"
```

### Gemini in Agent Workflows
```python
# Use Gemini for specific agent tasks
agent(
    prompt="Implement feature with tests",
    model="gemini-1.5-pro",  # Specify Gemini
    tools=["read", "write", "test"]
)

# Gemini in swarm
swarm(
    agents=[
        {"role": "architect", "model": "gemini-1.5-ultra"},
        {"role": "coder", "model": "gemini-1.5-pro"},
        {"role": "tester", "model": "gemini-1.5-flash"}
    ]
)
```

This comprehensive guide enables effective use of Gemini models for development workflows in the Hanzo Python SDK project.