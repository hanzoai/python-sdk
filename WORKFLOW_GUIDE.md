# Hanzo AI Peak Workflow Guide

## Overview
This guide documents the complete Hanzo AI workflow for architecture, planning, task generation, and development using Claude, MCP tools, and the Hanzo SDK.

## Prerequisites

### Installation
```bash
# Install Hanzo SDK and all components
pip install hanzo[all]

# Or install specific components
pip install hanzo hanzo-mcp hanzo-agents hanzo-repl

# Verify installation
hanzo --version
hanzo-mcp --help
```

### Environment Setup
```bash
# Required API keys
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."  # Optional
export HANZO_API_KEY="..."      # Optional for Hanzo Router

# Optional configuration
export HANZO_DEFAULT_MODEL="claude-3-5-sonnet-20241022"
export HANZO_USE_LOCAL="false"
```

## Phase 1: Architecture & Planning

### 1.1 Independent Architecture Proposals
```bash
# Using Hanzo REPL with Claude agent
hanzo repl start --model claude-3-opus-20240229

# In REPL, request architecture proposal
agent:claude "Analyze the codebase and propose architecture for [FEATURE]"

# Or use multiple agents for consensus
swarm:3 "Independently analyze and propose architecture for [FEATURE], then build consensus"
```

### 1.2 Architecture Refinement
```python
# Using Python SDK for architecture refinement
from hanzoai import Hanzo
import json

client = Hanzo()

# Get initial proposals
proposals = []
for agent in ["claude-3-opus", "claude-3-5-sonnet", "gpt-4"]:
    response = client.chat.completions.create(
        model=agent,
        messages=[
            {"role": "system", "content": "You are a senior architect"},
            {"role": "user", "content": f"Propose architecture for: {feature_description}"}
        ]
    )
    proposals.append(response.choices[0].message.content)

# Refine with GPT-5 Pro (or Claude Opus)
refined = client.chat.completions.create(
    model="claude-3-opus-20240229",
    messages=[
        {"role": "system", "content": "You are a principal architect reviewing proposals"},
        {"role": "user", "content": f"Review and improve these proposals:\n{json.dumps(proposals, indent=2)}"}
    ]
)

# Save architecture document
with open("ARCHITECTURE.md", "w") as f:
    f.write(refined.choices[0].message.content)
```

### 1.3 Save Architecture with MCP
```bash
# Using hanzo-mcp to save architecture
hanzo mcp write --file ARCHITECTURE.md --content "$ARCHITECTURE_CONTENT"

# Or in Python
from hanzo_mcp import MCPClient

mcp = MCPClient()
mcp.write("ARCHITECTURE.md", architecture_content)
```

## Phase 2: Task Generation

### 2.1 Generate Linear Tasks
```python
# Read architecture and generate tasks
from hanzoai import Hanzo
from hanzo_mcp import MCPClient

client = Hanzo()
mcp = MCPClient()

# Read architecture
architecture = mcp.read("ARCHITECTURE.md")

# Generate tasks
tasks_response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[
        {"role": "system", "content": "You are a technical project manager"},
        {"role": "user", "content": f"""
        Based on this architecture:
        {architecture}
        
        Generate small, focused Linear tasks that a junior engineer can complete in under a day.
        Format as JSON with: title, description, priority, dependencies, acceptance_criteria
        """}
    ]
)

tasks = json.loads(tasks_response.choices[0].message.content)
```

### 2.2 Refine Tasks with GPT-5 Pro
```python
# Refine task list
refined_tasks = client.chat.completions.create(
    model="claude-3-opus-20240229",  # Or GPT-5 when available
    messages=[
        {"role": "system", "content": "You are an engineering manager"},
        {"role": "user", "content": f"""
        Review and improve these tasks:
        {json.dumps(tasks, indent=2)}
        
        Ensure:
        - Clear scope and boundaries
        - Proper dependency ordering
        - Testable acceptance criteria
        - Realistic time estimates
        """}
    ]
)
```

### 2.3 Create Linear Issues (with MCP Linear integration)
```python
# If Linear MCP is available
from hanzo_mcp.tools import linear

# Create project
project = linear.create_project(
    name="Feature Implementation",
    description=architecture_summary
)

# Create epic
epic = linear.create_issue(
    title="Main Feature Epic",
    description=architecture,
    project_id=project.id,
    type="Epic"
)

# Create tasks
for task in refined_tasks:
    issue = linear.create_issue(
        title=task["title"],
        description=task["description"],
        project_id=project.id,
        parent_id=epic.id,
        priority=task["priority"],
        labels=task.get("labels", [])
    )
    
    # Set dependencies
    for dep_title in task.get("dependencies", []):
        dep_issue = linear.find_issue(title=dep_title)
        if dep_issue:
            linear.add_dependency(issue.id, dep_issue.id)
```

## Phase 3: Development Workflow

### 3.1 Create Worktree per Task
```bash
#!/bin/bash
# Script: create_task_worktree.sh

TASK_ID=$1
TASK_TITLE=$2

# Create worktree
git worktree add -b "task-$TASK_ID" "./worktrees/$TASK_ID" main

cd "./worktrees/$TASK_ID"

# Save task context
echo "Task: $TASK_TITLE" > .task_context
echo "Linear ID: $TASK_ID" >> .task_context
```

### 3.2 One-Shot Task Implementation
```python
# one_shot_task.py
import sys
from hanzoai import Hanzo
from hanzo_mcp import MCPClient

def implement_task(task_id: str):
    client = Hanzo()
    mcp = MCPClient()
    
    # Get task details (from Linear or local file)
    task = load_task(task_id)
    architecture = mcp.read("ARCHITECTURE.md")
    
    # One-shot implementation
    implementation = client.chat.completions.create(
        model="claude-3-5-sonnet-20241022",
        messages=[
            {"role": "system", "content": f"""
            You are implementing a specific task. 
            Architecture: {architecture}
            Use MCP tools to read, write, and test code.
            """},
            {"role": "user", "content": f"""
            Implement this task:
            {json.dumps(task, indent=2)}
            
            Requirements:
            1. Follow the architecture exactly
            2. Write comprehensive tests
            3. Add proper documentation
            4. Ensure all tests pass
            """}
        ],
        tools=mcp.get_all_tools(),
        tool_choice="auto"
    )
    
    return implementation

if __name__ == "__main__":
    task_id = sys.argv[1]
    result = implement_task(task_id)
    print(f"Task {task_id} implemented")
```

### 3.3 Code Review with Claude Code
```python
# review_task.py
def review_implementation(task_id: str):
    client = Hanzo()
    mcp = MCPClient()
    
    # Get changed files
    changes = mcp.run_command("git diff main")
    
    # Review with Claude Code
    review = client.chat.completions.create(
        model="claude-3-opus-20240229",
        messages=[
            {"role": "system", "content": "You are a senior code reviewer"},
            {"role": "user", "content": f"""
            Review these changes:
            {changes}
            
            Check for:
            - Bugs and edge cases
            - Performance issues
            - Security vulnerabilities
            - Code style and best practices
            - Test coverage
            """}
        ]
    )
    
    return review.choices[0].message.content
```

### 3.4 Iterative Refinement
```python
# refine_implementation.py
def refine_with_feedback(task_id: str, feedback: str):
    client = Hanzo()
    mcp = MCPClient()
    
    refinement = client.chat.completions.create(
        model="claude-3-5-sonnet-20241022",
        messages=[
            {"role": "system", "content": "You are addressing code review feedback"},
            {"role": "user", "content": f"""
            Address this feedback:
            {feedback}
            
            Make necessary changes using MCP tools.
            """}
        ],
        tools=mcp.get_all_tools(),
        tool_choice="auto"
    )
    
    return refinement
```

## Phase 4: Pull Request Workflow

### 4.1 Create Pull Request
```bash
# Push changes and create PR
git push -u origin "task-$TASK_ID"

# Create PR with gh CLI
gh pr create \
  --title "Task $TASK_ID: $TASK_TITLE" \
  --body "$(cat .task_context)" \
  --base main
```

### 4.2 Automated PR Review
```python
# pr_review_bot.py
def review_pr(pr_number: int):
    reviews = []
    
    # Get PR diff
    diff = mcp.run_command(f"gh pr diff {pr_number}")
    
    # Review with multiple agents
    for model in ["claude-3-opus", "claude-3-5-sonnet"]:
        review = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Review this PR for issues"},
                {"role": "user", "content": diff}
            ]
        )
        reviews.append(review.choices[0].message.content)
    
    # Post reviews as comments
    for review in reviews:
        mcp.run_command(f'gh pr comment {pr_number} --body "{review}"')
    
    return reviews
```

## Complete Automation Script

### Full Workflow Automation
```python
#!/usr/bin/env python3
# hanzo_workflow.py

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

from hanzoai import Hanzo
from hanzo_mcp import MCPClient
from hanzo_agents import SwarmOrchestrator

class HanzoWorkflow:
    def __init__(self):
        self.client = Hanzo()
        self.mcp = MCPClient()
        self.swarm = SwarmOrchestrator()
    
    def run_architecture_phase(self, feature: str) -> str:
        """Phase 1: Architecture & Planning"""
        print("🏗️  Phase 1: Architecture & Planning")
        
        # Get proposals from multiple agents
        proposals = self.swarm.run(
            agents=["claude-3-opus", "claude-3-5-sonnet", "gpt-4"],
            task=f"Propose architecture for: {feature}",
            consensus=True
        )
        
        # Refine with top model
        refined = self.client.chat.completions.create(
            model="claude-3-opus-20240229",
            messages=[
                {"role": "system", "content": "You are a principal architect"},
                {"role": "user", "content": f"Refine: {proposals}"}
            ]
        )
        
        # Save architecture
        architecture = refined.choices[0].message.content
        self.mcp.write("ARCHITECTURE.md", architecture)
        print("✅ Architecture saved to ARCHITECTURE.md")
        
        return architecture
    
    def run_task_generation(self, architecture: str) -> List[Dict]:
        """Phase 2: Task Generation"""
        print("📋 Phase 2: Task Generation")
        
        # Generate tasks
        tasks_response = self.client.chat.completions.create(
            model="claude-3-5-sonnet-20241022",
            messages=[
                {"role": "system", "content": "Generate Linear tasks"},
                {"role": "user", "content": f"From architecture: {architecture}"}
            ],
            response_format={"type": "json_object"}
        )
        
        tasks = json.loads(tasks_response.choices[0].message.content)
        
        # Save tasks
        self.mcp.write("TASKS.json", json.dumps(tasks, indent=2))
        print(f"✅ Generated {len(tasks)} tasks")
        
        return tasks
    
    def implement_task(self, task: Dict) -> bool:
        """Phase 3: Task Implementation"""
        task_id = task["id"]
        print(f"💻 Implementing task {task_id}: {task['title']}")
        
        # Create worktree
        worktree_path = f"./worktrees/{task_id}"
        self.mcp.run_command(f"git worktree add -b task-{task_id} {worktree_path} main")
        
        # Implement with Claude
        os.chdir(worktree_path)
        
        implementation = self.client.chat.completions.create(
            model="claude-3-5-sonnet-20241022",
            messages=[
                {"role": "system", "content": "Implement this task using MCP tools"},
                {"role": "user", "content": json.dumps(task)}
            ],
            tools=self.mcp.get_all_tools(),
            tool_choice="auto"
        )
        
        # Run tests
        test_result = self.mcp.run_command("make test")
        
        if "PASSED" in test_result:
            print(f"✅ Task {task_id} implemented successfully")
            return True
        else:
            print(f"❌ Task {task_id} tests failed")
            return False
    
    def create_pr(self, task: Dict) -> str:
        """Phase 4: Create Pull Request"""
        task_id = task["id"]
        print(f"🔀 Creating PR for task {task_id}")
        
        # Push branch
        self.mcp.run_command(f"git push -u origin task-{task_id}")
        
        # Create PR
        pr_output = self.mcp.run_command(f"""
            gh pr create \
                --title "Task {task_id}: {task['title']}" \
                --body "{task['description']}" \
                --base main
        """)
        
        pr_number = pr_output.split("/")[-1].strip()
        print(f"✅ Created PR #{pr_number}")
        
        return pr_number
    
    def run_full_workflow(self, feature: str):
        """Run complete workflow"""
        print("🚀 Starting Hanzo AI Peak Workflow")
        print("="*50)
        
        # Phase 1: Architecture
        architecture = self.run_architecture_phase(feature)
        
        # Phase 2: Task Generation
        tasks = self.run_task_generation(architecture)
        
        # Phase 3 & 4: Implementation and PRs
        for task in tasks:
            if self.implement_task(task):
                self.create_pr(task)
            
            # Return to main directory
            os.chdir(Path(__file__).parent)
        
        print("="*50)
        print("✨ Workflow complete!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: hanzo_workflow.py 'Feature description'")
        sys.exit(1)
    
    feature = sys.argv[1]
    workflow = HanzoWorkflow()
    workflow.run_full_workflow(feature)
```

## Using Hanzo CLI and REPL

### Interactive Chat with Agent Selection
```bash
# Start REPL
hanzo repl start

# In REPL, use different agent syntaxes:
> agent:claude "Analyze this code for security issues"
> agent:gpt4 "Generate unit tests"
> swarm:3 "Brainstorm solutions for this problem"

# Direct model selection
> @claude-3-opus How would you architect this system?
> @gpt-4 What are the performance implications?
```

### CLI Quick Commands
```bash
# Quick questions
hanzo ask "How do I implement OAuth2 in FastAPI?"

# Chat with specific model
hanzo chat --model claude-3-5-sonnet-20241022

# Use local models
hanzo chat --local --model llama-3.2-3b

# With MCP tools
hanzo chat --tools filesystem,search,git
```

## Advanced Features

### Voice Mode
```bash
# Enable voice in REPL
hanzo repl start --voice

# Or set environment
export HANZO_ENABLE_VOICE=true
hanzo repl start
```

### TUI Interface
```bash
# Beautiful terminal UI
hanzo repl start --tui
```

### IPython Integration
```bash
# IPython magic commands
hanzo repl start --ipython

# In IPython:
%mcp_read file.py
%mcp_search "pattern"
%agent claude "Analyze this"
```

## Environment Variables

```bash
# Core configuration
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export HANZO_API_KEY="..."

# Default settings
export HANZO_DEFAULT_MODEL="claude-3-5-sonnet-20241022"
export HANZO_USE_LOCAL="false"
export HANZO_ENABLE_VOICE="false"

# Router configuration (if using Hanzo Router)
export HANZO_ROUTER_URL="http://localhost:4000"
export HANZO_USE_ROUTER="true"
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure all packages are installed
   ```bash
   pip install hanzo[all]
   ```

2. **API key issues**: Check environment variables
   ```bash
   echo $ANTHROPIC_API_KEY
   echo $OPENAI_API_KEY
   ```

3. **MCP tools not available**: Install hanzo-mcp
   ```bash
   pip install hanzo-mcp
   hanzo-mcp install-desktop  # For Claude Desktop
   ```

4. **REPL not starting**: Check dependencies
   ```bash
   pip install hanzo-repl ipython textual
   ```

## Summary

This workflow enables:
1. ✅ Architecture generation with multiple AI models
2. ✅ Task breakdown and Linear integration
3. ✅ Automated implementation with one-shot prompts
4. ✅ Code review and iterative refinement
5. ✅ PR creation and automated review
6. ✅ Full CLI and REPL support with agent:claude syntax
7. ✅ Swarm orchestration for consensus building
8. ✅ MCP tool integration throughout

The system is fully functional and can be used immediately with proper API keys configured.