#!/usr/bin/env python3
"""
Example: Orchestrating Git Worktrees with Hanzo-MCP Agents

This demonstrates how to use hanzo-mcp agents to manage parallel development
across multiple git worktrees, with each agent handling a specific task.
"""

import json
import subprocess
from typing import Any, Dict, List

# This would normally use the hanzo-mcp Python client
# For demonstration, showing the conceptual flow

class WorktreeOrchestrator:
    """Orchestrates multiple agents working on git worktrees."""
    
    def __init__(self, base_branch: str = "main"):
        self.base_branch = base_branch
        self.worktrees: Dict[str, str] = {}
        
    def create_worktree_agent_prompt(self, task_id: str, task_content: str) -> str:
        """Generate agent prompt for worktree task."""
        return f"""
You are an autonomous development agent assigned to task {task_id}.

TASK: {task_content}

INSTRUCTIONS:
1. Create a git worktree for this task:
   ```bash
   git worktree add -b feature/{task_id} ../worktree-{task_id}
   cd ../worktree-{task_id}
   ```

2. Read the architecture.md file to understand the system design

3. Implement the required functionality:
   - Follow existing code patterns
   - Use appropriate error handling
   - Add necessary imports
   - Create clean, modular code

4. Write tests for your implementation:
   - Unit tests for new functions
   - Integration tests if needed
   - Ensure tests pass

5. Commit your changes:
   ```bash
   git add -A
   git commit -m "feat({task_id}): {task_content}"
   ```

6. Return a summary including:
   - Files created/modified
   - Test results
   - Any issues encountered
   - Ready for review: YES/NO

Use available tools:
- read: to read existing files
- run_command: for git and test operations  
- search: to find patterns in codebase
- grep_ast: to understand code structure
"""

    def create_critic_prompt(self, task_id: str, agent_summary: str) -> str:
        """Generate critic prompt for reviewing agent work."""
        return f"""
You are a senior code reviewer. Review the implementation in worktree-{task_id}.

AGENT SUMMARY:
{agent_summary}

REVIEW CHECKLIST:
1. Code Quality
   - [ ] Follows architecture.md patterns
   - [ ] Clean, readable code
   - [ ] Proper error handling
   - [ ] No code duplication

2. Security
   - [ ] Input validation
   - [ ] No hardcoded secrets
   - [ ] Safe data handling
   - [ ] SQL injection prevention

3. Performance  
   - [ ] Efficient algorithms
   - [ ] No unnecessary loops
   - [ ] Proper caching
   - [ ] Resource cleanup

4. Testing
   - [ ] Adequate test coverage
   - [ ] Edge cases handled
   - [ ] Tests actually pass
   - [ ] Mocks used appropriately

5. Documentation
   - [ ] Functions have docstrings
   - [ ] Complex logic explained
   - [ ] API changes documented

Read the implementation files and provide:
1. List of issues found (if any)
2. Severity of each issue (critical/major/minor)
3. Specific fix recommendations
4. Final verdict: APPROVED or NEEDS_FIXES

Be strict but fair. This code will go to production.
"""

    def execute_workflow(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute the complete worktree workflow."""
        
        results = {
            "total_tasks": len(tasks),
            "completed": [],
            "failed": [],
            "worktrees": []
        }
        
        for task in tasks:
            task_id = task["id"]
            task_content = task["content"]
            
            print(f"\n🚀 Starting task {task_id}: {task_content}")
            
            # Step 1: Agent implements the task
            agent_prompt = self.create_worktree_agent_prompt(task_id, task_content)
            
            # This would call: agent(prompt=agent_prompt)
            # For demo, showing the structure
            agent_result = {
                "task_id": task_id,
                "worktree": f"worktree-{task_id}",
                "files_modified": ["src/auth.py", "tests/test_auth.py"],
                "tests_passed": True,
                "ready_for_review": True
            }
            
            print(f"✅ Agent completed implementation")
            
            # Step 2: Critic reviews the implementation
            if agent_result["ready_for_review"]:
                critic_prompt = self.create_critic_prompt(
                    task_id, 
                    json.dumps(agent_result, indent=2)
                )
                
                # This would call: critic(analysis=critic_prompt)
                critic_result = {
                    "verdict": "APPROVED",
                    "issues": [],
                    "score": 95
                }
                
                if critic_result["verdict"] == "APPROVED":
                    print(f"✅ Critic approved implementation (score: {critic_result['score']})")
                    results["completed"].append(task_id)
                    
                    # Step 3: Prepare for merge
                    self.worktrees[task_id] = f"feature/{task_id}"
                    results["worktrees"].append({
                        "task_id": task_id,
                        "branch": f"feature/{task_id}",
                        "path": f"../worktree-{task_id}",
                        "ready_to_merge": True
                    })
                else:
                    print(f"⚠️ Critic requested fixes: {critic_result['issues']}")
                    
                    # Step 4: Agent fixes issues
                    fix_prompt = f"""
                    Fix these issues in worktree-{task_id}:
                    {json.dumps(critic_result['issues'], indent=2)}
                    """
                    
                    # Second attempt would go here
                    results["failed"].append({
                        "task_id": task_id,
                        "reason": "Needs fixes",
                        "issues": critic_result["issues"]
                    })
            
        return results

    def merge_completed_worktrees(self, results: Dict[str, Any]) -> None:
        """Merge all completed worktrees back to base branch."""
        
        print(f"\n🔀 Merging completed worktrees to {self.base_branch}")
        
        for worktree in results["worktrees"]:
            if worktree["ready_to_merge"]:
                branch = worktree["branch"]
                
                # This would execute:
                # git checkout main
                # git merge --no-ff feature/{task_id}
                # git push origin main
                
                print(f"✅ Merged {branch} to {self.base_branch}")
        
        print(f"\n🎉 Workflow complete! {len(results['completed'])}/{results['total_tasks']} tasks merged")


# Example usage
if __name__ == "__main__":
    
    # Sample tasks from todo list
    tasks = [
        {"id": "auth-1", "content": "Implement JWT token generation", "priority": "high"},
        {"id": "auth-2", "content": "Create login endpoint", "priority": "high"},
        {"id": "auth-3", "content": "Add password reset flow", "priority": "medium"},
        {"id": "auth-4", "content": "Implement rate limiting", "priority": "medium"},
    ]
    
    # Initialize orchestrator
    orchestrator = WorktreeOrchestrator(base_branch="main")
    
    # Execute parallel development workflow
    results = orchestrator.execute_workflow(tasks)
    
    # Merge successful implementations
    orchestrator.merge_completed_worktrees(results)
    
    # Output summary
    print("\n📊 Workflow Summary:")
    print(f"  Total tasks: {results['total_tasks']}")
    print(f"  Completed: {len(results['completed'])}")
    print(f"  Failed: {len(results['failed'])}")
    print(f"  Worktrees created: {len(results['worktrees'])}")
    
    # This summary could be sent to Linear or saved to a report
    with open("workflow_report.json", "w") as f:
        json.dump(results, f, indent=2)