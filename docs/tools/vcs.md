# VCS Tool

Version control operations: status, diff, commit, log (HIP-0300 operator).

## Installation

```bash
pip install hanzo-tools-vcs
```

## Overview

The `vcs` tool handles all version control operations:

| Action | Signature | Effect |
|--------|-----------|--------|
| `status` | `() → {staged, unstaged, untracked}` | DETERMINISTIC |
| `diff` | `(ref1?, ref2?, paths?) → Diff` | DETERMINISTIC |
| `commit` | `(message, files?) → {sha, message}` | DETERMINISTIC |
| `log` | `(n?, since?, path?) → [Commit]` | DETERMINISTIC |
| `branch` | `(name?, action?) → {current, branches}` | DETERMINISTIC |
| `stash` | `(action, message?) → {ok}` | DETERMINISTIC |
| `apply` | `(patch) → {ok, files_changed}` | DETERMINISTIC |
| `checkout` | `(ref, paths?) → {ok}` | DETERMINISTIC |

## Actions

### status

Get working tree status.

```python
vcs(action="status")
# Returns: {
#   staged: [
#     {path: "src/main.py", status: "modified"},
#     {path: "src/utils.py", status: "added"}
#   ],
#   unstaged: [
#     {path: "src/config.py", status: "modified"}
#   ],
#   untracked: ["temp.txt", "notes.md"],
#   branch: "feature/auth",
#   ahead: 2,
#   behind: 0
# }
```

### diff

Show differences between commits, branches, or working tree.

```python
# Working tree diff (unstaged)
vcs(action="diff")
# Returns: {
#   diff: "diff --git a/src/main.py b/src/main.py\n...",
#   files: ["src/main.py"],
#   additions: 15,
#   deletions: 3
# }

# Staged diff
vcs(action="diff", staged=True)

# Between commits
vcs(action="diff", ref1="HEAD~3", ref2="HEAD")

# Specific files
vcs(action="diff", paths=["src/auth.py", "src/users.py"])

# Between branches
vcs(action="diff", ref1="main", ref2="feature/auth")
```

### commit

Create a commit.

```python
vcs(action="commit", message="Add user authentication")
# Returns: {
#   sha: "abc123def456",
#   message: "Add user authentication",
#   files_changed: 3
# }

# Commit specific files
vcs(action="commit", message="Fix bug in auth", files=["src/auth.py"])

# Amend last commit
vcs(action="commit", message="Updated message", amend=True)
```

### log

View commit history.

```python
vcs(action="log")
# Returns: {
#   commits: [
#     {sha: "abc123", message: "Add auth", author: "...", date: "..."},
#     {sha: "def456", message: "Fix bug", author: "...", date: "..."}
#   ]
# }

# Limit results
vcs(action="log", n=10)

# Filter by date
vcs(action="log", since="2024-01-01", until="2024-01-31")

# Filter by path
vcs(action="log", path="src/auth.py")

# Show full diff with each commit
vcs(action="log", n=5, show_diff=True)
```

### branch

Branch operations.

```python
# List branches
vcs(action="branch")
# Returns: {
#   current: "feature/auth",
#   local: ["main", "feature/auth", "bugfix/login"],
#   remote: ["origin/main", "origin/develop"]
# }

# Create branch
vcs(action="branch", name="feature/new-feature", create=True)

# Delete branch
vcs(action="branch", name="old-branch", delete=True)
```

### stash

Stash operations.

```python
# Save stash
vcs(action="stash", push=True, message="WIP: auth changes")
# Returns: {ok: True, stash: "stash@{0}"}

# List stashes
vcs(action="stash", list=True)
# Returns: {stashes: [{ref: "stash@{0}", message: "..."}]}

# Apply stash
vcs(action="stash", apply=True)

# Pop stash (apply and remove)
vcs(action="stash", pop=True)
```

### apply

Apply a patch (unified diff format).

```python
patch = """
diff --git a/src/main.py b/src/main.py
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
+# New header comment
 def main():
     pass
"""

vcs(action="apply", patch=patch)
# Returns: {ok: True, files_changed: ["src/main.py"]}
```

### checkout

Switch branches or restore files.

```python
# Switch branch
vcs(action="checkout", ref="main")
# Returns: {ok: True, branch: "main"}

# Create and switch
vcs(action="checkout", ref="feature/new", create=True)

# Restore specific files
vcs(action="checkout", ref="HEAD", paths=["src/main.py"])
```

## Usage Examples

### Safe Commit Workflow

```python
# 1. Check status
status = vcs(action="status")

# 2. Review diff
if status["data"]["unstaged"]:
    diff = vcs(action="diff")
    print(diff["data"]["diff"])

# 3. Stage and commit
vcs(action="commit", message="Implement user authentication",
    files=["src/auth.py", "tests/test_auth.py"])
```

### Code Review Workflow

```python
# 1. Get diff between branches
diff = vcs(action="diff", ref1="main", ref2="feature/auth")

# 2. Summarize with code tool
from hanzo_tools.code import code_tool
summary = code_tool(action="summarize", diff=diff["data"]["diff"])

print(f"Changes: +{diff['data']['additions']} -{diff['data']['deletions']}")
print(f"Summary: {summary['data']['summary']}")
```

### History Analysis

```python
# Get recent changes to a file
commits = vcs(action="log", path="src/api.py", n=10, show_diff=True)

for commit in commits["data"]["commits"]:
    print(f"{commit['sha'][:7]} {commit['message']}")
```

## Integration with fs.patch

VCS diffs integrate with `fs.patch` for applying changes:

```python
# Generate diff
diff = vcs(action="diff", ref1="main", ref2="feature/fix")

# Apply to another location
fs(action="patch", path="/other/project/src/main.py",
   patch=diff["data"]["diff"])
```

## See Also

- [HIP-0300](../hip/HIP-0300.md) - Unified Tools Architecture
- [Filesystem Tool](fs.md) - For `fs.patch` to apply diffs
- [Code Tool](code.md) - For `code.summarize` on diffs
- [Test Tool](test.md) - For validation after commits
