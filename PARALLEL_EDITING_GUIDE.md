# Parallel Editing with Hanzo-MCP Batch Tool

## Overview
This guide demonstrates how to use hanzo-mcp's batch tool to edit multiple files in parallel, delegating to different AI CLI tools (claude, codex, gemini, grok) for simultaneous execution.

## Available Tools in Batch Mode

### Tools That Work in Batch
```python
BATCH_AVAILABLE_TOOLS = [
    "dispatch_agent",  # Delegate to sub-agents
    "read",           # Read files
    "directory_tree", # Explore structure
    "grep",          # Search patterns
    "grep_ast",      # AST search
    "run_command",   # Execute commands
    "notebook_read", # Read notebooks
]
```

### CLI Agent Tools (Via Agent Invocation)
- `claude` - Claude CLI agent
- `codex` - OpenAI Codex/GPT-4 agent
- `gemini` - Google Gemini agent
- `grok` - xAI Grok agent

## Parallel File Editing Pattern

### Step 1: Read All Files in Parallel
```python
# Read all documentation files simultaneously
read_batch = {
    "description": "Read AI documentation files",
    "invocations": [
        {
            "tool_name": "read",
            "input": {"file_path": "/Users/z/work/hanzo/python-sdk/LLM.md"}
        },
        {
            "tool_name": "read",
            "input": {"file_path": "/Users/z/work/hanzo/python-sdk/AGENTS.md"}
        },
        {
            "tool_name": "read",
            "input": {"file_path": "/Users/z/work/hanzo/python-sdk/GEMINI.md"}
        },
        {
            "tool_name": "read",
            "input": {"file_path": "/Users/z/work/hanzo/python-sdk/CLAUDE.md"}
        }
    ]
}

# Execute batch
results = batch(**read_batch)
```

### Step 2: Delegate Edits to Different Agents
Since direct CLI tools aren't available in batch, use the agent tool to delegate:

```python
# Parallel agent delegation for editing
edit_batch = {
    "description": "Edit docs with specialized agents",
    "invocations": [
        {
            "tool_name": "dispatch_agent",
            "input": {
                "prompt": """
                You are Claude. Read and enhance CLAUDE.md at /Users/z/work/hanzo/python-sdk/CLAUDE.md with:
                1. Add section on computer use capabilities
                2. Include vision capabilities for code screenshots
                3. Add prompt caching patterns
                4. Include Artifacts 2.0 features
                
                Use the read tool to get current content, then provide the complete enhanced version.
                Focus on Claude-specific strengths.
                """
            }
        },
        {
            "tool_name": "dispatch_agent",
            "input": {
                "prompt": """
                You are GPT-4. Read and enhance LLM.md at /Users/z/work/hanzo/python-sdk/LLM.md with:
                1. Add GPT-4 Turbo with Vision patterns
                2. Include Assistants API v2 integration
                3. Add batch API for cost optimization
                4. Include fine-tuning workflows
                
                Use the read tool to get current content, then provide the complete enhanced version.
                Focus on OpenAI-specific features.
                """
            }
        },
        {
            "tool_name": "dispatch_agent",
            "input": {
                "prompt": """
                You are Gemini. Read and enhance GEMINI.md at /Users/z/work/hanzo/python-sdk/GEMINI.md with:
                1. Add Gemini 1.5 Flash latest improvements
                2. Include Code Interpreter capabilities
                3. Add grounding with Google Search
                4. Include extensions and plugins
                
                Use the read tool to get current content, then provide the complete enhanced version.
                Focus on Google-specific integrations.
                """
            }
        },
        {
            "tool_name": "dispatch_agent",
            "input": {
                "prompt": """
                You are an expert in agent systems. Read and enhance AGENTS.md at /Users/z/work/hanzo/python-sdk/AGENTS.md with:
                1. Add multi-agent reinforcement learning
                2. Include agent marketplace patterns
                3. Add federated learning strategies
                4. Include agent versioning and rollback
                
                Use the read tool to get current content, then provide the complete enhanced version.
                Focus on advanced orchestration patterns.
                """
            }
        }
    ]
}

# Execute parallel edits
edit_results = batch(**edit_batch)
```

## Advanced Parallel Patterns

### Pattern 1: Divide and Conquer
Each agent handles a specific section of the same file:

```python
section_batch = {
    "description": "Edit different sections in parallel",
    "invocations": [
        {
            "tool_name": "dispatch_agent",
            "input": {
                "prompt": """
                Read AGENTS.md and enhance ONLY the 'Swarm Coordination Patterns' section.
                Add emergent behavior patterns and load balancing strategies.
                Return just the enhanced section.
                """
            }
        },
        {
            "tool_name": "dispatch_agent",
            "input": {
                "prompt": """
                Read AGENTS.md and enhance ONLY the 'Git Worktree Management' section.
                Add CI/CD integration and automated PR generation.
                Return just the enhanced section.
                """
            }
        },
        {
            "tool_name": "dispatch_agent",
            "input": {
                "prompt": """
                Read AGENTS.md and enhance ONLY the 'Error Handling' section.
                Add circuit breakers and graceful degradation patterns.
                Return just the enhanced section.
                """
            }
        }
    ]
}
```

### Pattern 2: Multi-Stage Pipeline
Sequential stages with parallel execution within each stage:

```python
# Stage 1: Parallel Analysis
analysis_batch = {
    "description": "Analyze all files for improvements",
    "invocations": [
        {
            "tool_name": "dispatch_agent",
            "input": {
                "prompt": "Analyze LLM.md for missing topics and outdated patterns. List improvements needed."
            }
        },
        {
            "tool_name": "dispatch_agent",
            "input": {
                "prompt": "Analyze CLAUDE.md for missing features and API updates. List improvements needed."
            }
        },
        {
            "tool_name": "dispatch_agent",
            "input": {
                "prompt": "Analyze GEMINI.md for missing capabilities. List improvements needed."
            }
        }
    ]
}

analysis_results = batch(**analysis_batch)

# Stage 2: Parallel Implementation based on analysis
implementation_batch = {
    "description": "Implement identified improvements",
    "invocations": [
        # Use analysis results to guide edits
        {
            "tool_name": "dispatch_agent",
            "input": {
                "prompt": f"""
                Based on this analysis: {analysis_results[0]}
                Implement the improvements for LLM.md
                """
            }
        },
        # ... similar for other files
    ]
}
```

### Pattern 3: Consensus Editing
Multiple agents edit the same content, then merge:

```python
consensus_batch = {
    "description": "Multiple agents propose edits",
    "invocations": [
        {
            "tool_name": "dispatch_agent",
            "input": {
                "prompt": """
                As Claude, propose a new 'Best Practices' section for AGENTS.md.
                Focus on reliability and safety.
                """
            }
        },
        {
            "tool_name": "dispatch_agent",
            "input": {
                "prompt": """
                As GPT-4, propose a new 'Best Practices' section for AGENTS.md.
                Focus on performance and scalability.
                """
            }
        },
        {
            "tool_name": "dispatch_agent",
            "input": {
                "prompt": """
                As Gemini, propose a new 'Best Practices' section for AGENTS.md.
                Focus on maintainability and testing.
                """
            }
        }
    ]
}

proposals = batch(**consensus_batch)

# Merge proposals
merge_batch = {
    "description": "Merge all proposals",
    "invocations": [
        {
            "tool_name": "dispatch_agent",
            "input": {
                "prompt": f"""
                Merge these three proposals into a unified 'Best Practices' section:
                
                Claude's proposal: {proposals[0]}
                GPT-4's proposal: {proposals[1]}
                Gemini's proposal: {proposals[2]}
                
                Create a comprehensive section combining the best of each.
                """
            }
        }
    ]
}
```

### Pattern 4: Cross-Validation
Agents review each other's work in parallel:

```python
review_batch = {
    "description": "Cross-review edits",
    "invocations": [
        {
            "tool_name": "dispatch_agent",
            "input": {
                "prompt": f"""
                Review the GPT-4 edits to LLM.md: {gpt4_edits}
                Check for technical accuracy and consistency.
                Provide feedback and improvements.
                """
            }
        },
        {
            "tool_name": "dispatch_agent",
            "input": {
                "prompt": f"""
                Review the Claude edits to CLAUDE.md: {claude_edits}
                Check for implementation feasibility.
                Provide feedback and improvements.
                """
            }
        },
        {
            "tool_name": "dispatch_agent",
            "input": {
                "prompt": f"""
                Review the Gemini edits to GEMINI.md: {gemini_edits}
                Check for completeness and clarity.
                Provide feedback and improvements.
                """
            }
        }
    ]
}
```

## Complete Workflow Example

```python
async def parallel_documentation_update():
    """Complete workflow for parallel documentation updates."""
    
    # Phase 1: Read all files in parallel
    read_results = await batch(
        description="Read all documentation",
        invocations=[
            {"tool_name": "read", "input": {"file_path": f"{path}/{file}"}}
            for file in ["LLM.md", "AGENTS.md", "GEMINI.md", "CLAUDE.md"]
        ]
    )
    
    # Phase 2: Analyze gaps in parallel
    analysis = await batch(
        description="Analyze documentation gaps",
        invocations=[
            {
                "tool_name": "dispatch_agent",
                "input": {
                    "prompt": f"Analyze this content and identify missing topics: {content}"
                }
            }
            for content in read_results
        ]
    )
    
    # Phase 3: Generate improvements in parallel
    improvements = await batch(
        description="Generate improvements",
        invocations=[
            {
                "tool_name": "dispatch_agent",
                "input": {
                    "prompt": f"""
                    Based on analysis: {gap_analysis}
                    Current content: {current_content}
                    Generate improved version with all gaps filled.
                    """
                }
            }
            for gap_analysis, current_content in zip(analysis, read_results)
        ]
    )
    
    # Phase 4: Cross-review in parallel
    reviews = await batch(
        description="Cross-review improvements",
        invocations=[
            {
                "tool_name": "dispatch_agent",
                "input": {
                    "prompt": f"Review and validate: {improvement}"
                }
            }
            for improvement in improvements
        ]
    )
    
    # Phase 5: Write all files in parallel (using individual writes after batch)
    for file, content in zip(files, final_contents):
        await write(file_path=file, content=content)
    
    return "All documentation updated in parallel"
```

## Practical CLI Usage

### Using batch with hanzo-mcp CLI:
```bash
# Execute parallel reads
hanzo-mcp batch --description "Read docs" \
  --invocations '[
    {"tool_name": "read", "input": {"file_path": "LLM.md"}},
    {"tool_name": "read", "input": {"file_path": "AGENTS.md"}}
  ]'

# Execute parallel agent tasks
hanzo-mcp batch --description "Enhance docs" \
  --invocations '[
    {
      "tool_name": "dispatch_agent",
      "input": {
        "prompt": "Enhance LLM.md with latest OpenAI features"
      }
    },
    {
      "tool_name": "dispatch_agent",
      "input": {
        "prompt": "Enhance CLAUDE.md with latest Anthropic features"
      }
    }
  ]'
```

### In Python with hanzo-mcp:
```python
from hanzo_mcp import batch, dispatch_agent

# Parallel execution
results = await batch(
    description="Update all AI docs",
    invocations=[
        {
            "tool_name": "dispatch_agent",
            "input": {"prompt": f"Update {doc} with latest features"}
        }
        for doc in ["LLM.md", "CLAUDE.md", "GEMINI.md", "AGENTS.md"]
    ]
)
```

## Performance Considerations

### Optimal Batch Sizes
- **Reading**: Up to 20 files in parallel
- **Agent tasks**: 3-5 complex tasks in parallel
- **Simple operations**: Up to 10 in parallel

### Resource Management
```python
# Monitor batch execution
batch_config = {
    "max_concurrent": 4,  # Limit concurrent executions
    "timeout": 300,       # 5 minute timeout per task
    "retry_on_failure": True,
    "fallback_strategy": "sequential"  # If parallel fails
}
```

## Error Handling

### Partial Failure Handling
```python
try:
    results = await batch(**batch_invocations)
    
    # Check for partial failures
    failures = [r for r in results if r.get("error")]
    if failures:
        # Retry failed tasks sequentially
        for failed in failures:
            retry_result = await dispatch_agent(
                prompt=failed["original_prompt"]
            )
except BatchExecutionError as e:
    # Handle complete batch failure
    print(f"Batch failed: {e}")
    # Fall back to sequential execution
```

## Best Practices

1. **Group Similar Operations**: Batch similar tasks together for efficiency
2. **Balance Load**: Don't overload with too many complex tasks
3. **Use Appropriate Agents**: Match agent expertise to task type
4. **Implement Checkpoints**: Save progress between batch phases
5. **Monitor Progress**: Use batch status to track execution
6. **Handle Failures Gracefully**: Have fallback strategies ready

## Limitations

### Tools NOT Available in Batch
- `write` - File writing (must be done individually after batch)
- `edit` - File editing (must be done individually)
- `think` - Thinking tool (sequential only)
- `critic` - Critic tool (sequential only)

### Workarounds
For tools not available in batch, use dispatch_agent to delegate:
```python
# Instead of direct write in batch
dispatch_agent(
    prompt="Generate content for NEW_FILE.md with these specifications..."
)
# Then write the generated content after batch completes
```

This guide enables efficient parallel editing of multiple files using hanzo-mcp's batch capabilities with different AI agents working simultaneously.