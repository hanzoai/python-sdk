# Linear MCP Integration Guide

## Installation & Setup

### 1. Install Linear MCP Server
```bash
# Install the Linear MCP server
npm install -g @modelcontextprotocol/server-linear

# Or add to package.json
npm install @modelcontextprotocol/server-linear
```

### 2. Get Linear API Key
1. Go to Linear Settings → API → Personal API keys
2. Create a new key with scopes:
   - `read` - Read access to all resources
   - `write` - Write access (create/update issues)
   - `admin` - Admin access (optional, for team management)

### 3. Configure Claude Desktop
```json
{
  "mcpServers": {
    "linear": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-linear"],
      "env": {
        "LINEAR_API_KEY": "lin_api_YOUR_KEY_HERE"
      }
    }
  }
}
```

## Available Linear MCP Tools

Once configured, these tools become available:

### Issue Management
- `linear_create_issue` - Create new issues
- `linear_update_issue` - Update existing issues  
- `linear_get_issue` - Get issue details
- `linear_search_issues` - Search issues

### Project Management
- `linear_create_project` - Create projects
- `linear_get_project` - Get project details
- `linear_update_project` - Update projects

### Team & User
- `linear_get_teams` - List teams
- `linear_get_users` - List users
- `linear_assign_issue` - Assign issues to users

## Workflow Integration

### Automated Task Creation from Architecture

```python
# After generating architecture and tasks
agent_prompt = """
Using Linear MCP tools:

1. Create a new project called 'OAuth Implementation'
   
2. Read the tasks from our todo list and for each:
   - Create a Linear issue with:
     - Title: [todo content]
     - Description: Implementation details from architecture.md
     - Priority: Map (high→urgent, medium→high, low→medium)
     - Labels: ['backend', 'feature', 'oauth']
   
3. Set up dependencies:
   - JWT service blocks login endpoint
   - Login endpoint blocks password reset
   
4. Create a roadmap project to track overall progress

Return: Project ID and all issue IDs created
"""

# Execute with agent
result = agent(prompt=agent_prompt)
```

### Link Git Branches to Linear Issues

```python
# When creating worktrees, link to Linear
agent_prompt = f"""
1. Get Linear issue {issue_id} details
2. Create git worktree: feature/{issue_id}
3. Implement the feature
4. Update Linear issue:
   - Add branch link: feature/{issue_id}  
   - Set status: In Progress
   - Add comment: "Implementation started"
5. After completion:
   - Set status: In Review
   - Add PR link
"""
```

### Sync Todo List with Linear

```python
# Bidirectional sync between todo and Linear
sync_prompt = """
1. Get all pending todos from todo list
2. For each todo without a Linear issue:
   - Create Linear issue
   - Store Linear ID in todo metadata
3. For each Linear issue in project:
   - If not in todo list, add it
   - Sync status changes
4. Return sync summary
"""

agent(prompt=sync_prompt)
```

## Complete Example: End-to-End Flow

```python
# PHASE 1: Setup Linear Project
setup_result = agent(prompt="""
Using Linear MCP tools:
1. Create project 'User Authentication System'
2. Create epic 'OAuth2 Implementation'
3. Set project lead and dates
Return project and epic IDs
""")

# PHASE 2: Generate and Link Tasks
tasks_result = agent(prompt=f"""
Read architecture.md and create Linear issues for each component:
- OAuth2 service → Priority 1
- JWT handler → Priority 1  
- Login endpoint → Priority 2
- Password reset → Priority 3
- Rate limiting → Priority 2

Link all to epic {setup_result.epic_id}
Set proper dependencies
Return all issue IDs
""")

# PHASE 3: Development Workflow
for issue_id in tasks_result.issue_ids:
    # Update Linear status
    agent(prompt=f"Update Linear issue {issue_id} status to 'In Progress'")
    
    # Create worktree and implement
    impl_result = agent(prompt=f"""
    1. Get Linear issue {issue_id} details
    2. Create worktree for issue
    3. Implement based on issue description
    4. Run tests
    5. Commit with Linear issue reference
    """)
    
    # Update Linear with progress
    agent(prompt=f"""
    Update Linear issue {issue_id}:
    - Add comment with implementation summary
    - Link branch and commit
    - Update status to 'In Review'
    """)
    
    # After critic approval
    if critic_approved:
        agent(prompt=f"""
        Update Linear issue {issue_id}:
        - Status: Done
        - Add completion comment
        - Link merged PR
        """)

# PHASE 4: Project Reporting
report = agent(prompt=f"""
Generate Linear project report:
1. Get project {setup_result.project_id} stats
2. List completed vs remaining issues
3. Calculate velocity
4. Identify blockers
5. Export as markdown report
""")
```

## Advanced Linear Patterns

### 1. Automated Sprint Planning
```python
agent(prompt="""
Using Linear:
1. Create new sprint cycle (2 weeks)
2. Auto-assign issues based on:
   - Priority and dependencies
   - Team capacity
   - Current velocity
3. Balance workload across team
4. Set sprint goals
""")
```

### 2. PR-to-Issue Automation
```python
agent(prompt=f"""
When PR is created:
1. Parse PR title for Linear issue ID
2. Update Linear issue:
   - Link PR URL
   - Status → In Review
   - Add PR description as comment
3. When PR merged:
   - Status → Done
   - Add merge commit
""")
```

### 3. Daily Standup Generation
```python
agent(prompt="""
Generate standup from Linear:
1. Get all In Progress issues
2. For each assignee:
   - Yesterday: completed issues
   - Today: in progress issues
   - Blockers: blocked issues
3. Format as standup report
""")
```

### 4. Dependency Visualization
```python
agent(prompt="""
Analyze Linear project dependencies:
1. Get all issues with dependencies
2. Identify critical path
3. Find potential bottlenecks
4. Suggest parallelization opportunities
5. Create Gantt chart data
""")
```

## Tips for Effective Linear Integration

### 1. Issue Templates
Create consistent issue structures:
```python
template = {
    "title": "[Component] Feature description",
    "description": """
    ## Objective
    [What we're building]
    
    ## Requirements
    - [ ] Requirement 1
    - [ ] Requirement 2
    
    ## Technical Details
    [Architecture reference]
    
    ## Acceptance Criteria
    - [ ] Tests pass
    - [ ] Code reviewed
    - [ ] Documentation updated
    """,
    "labels": ["feature", "backend"],
    "priority": 2
}
```

### 2. Smart Labeling
Use labels for automation:
- `needs-review` - Triggers review request
- `blocked` - Escalates to team lead
- `ready-to-deploy` - Adds to release queue

### 3. Cycle Management
```python
# Automatic cycle progression
agent(prompt="""
At end of cycle:
1. Move incomplete issues to next cycle
2. Archive completed issues
3. Generate cycle retrospective
4. Create next cycle with learnings
""")
```

### 4. Cross-Project Dependencies
```python
# Handle dependencies across projects
agent(prompt="""
For issue with external dependency:
1. Create placeholder issue in other project
2. Link bidirectionally
3. Set up notifications
4. Track in dependency matrix
""")
```

## Troubleshooting

### Linear API Key Issues
```bash
# Test Linear connection
curl -H "Authorization: lin_api_YOUR_KEY" \
  https://api.linear.app/graphql \
  -d '{"query":"{ viewer { id name } }"}'
```

### MCP Server Not Found
```bash
# Verify installation
npm list -g @modelcontextprotocol/server-linear

# Run directly to test
LINEAR_API_KEY=lin_api_YOUR_KEY npx @modelcontextprotocol/server-linear
```

### Permission Errors
Ensure API key has required scopes:
- Read for viewing issues
- Write for creating/updating
- Admin for team management

## Integration Checklist

- [ ] Linear API key obtained
- [ ] MCP server installed
- [ ] Claude Desktop configured
- [ ] Test connection with simple query
- [ ] Create test issue via agent
- [ ] Verify bidirectional sync
- [ ] Set up team workflows
- [ ] Document team conventions

This integration enables seamless project management where Linear becomes the persistent backing store for the in-memory todo system, providing team visibility and long-term tracking while maintaining the speed of local operation.