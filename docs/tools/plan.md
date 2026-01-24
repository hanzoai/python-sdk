# Plan Tool

Orchestration and intent routing for agentic workflows (HIP-0300 operator).

## Installation

```bash
pip install hanzo-tools-plan
```

## Overview

The `plan` tool routes natural language intents to canonical operator chains:

| Action | Signature | Effect |
|--------|-----------|--------|
| `intent` | `NL → IntentIR` | PURE |
| `route` | `(IntentIR, Policy?) → Plan` | PURE |
| `compose` | `Plan → ExecGraph` | PURE |

## Actions

### intent

Parse natural language into structured intent representation.

```python
plan(action="intent", nl="find where user authentication happens")
# Returns: {
#   category: "navigate",
#   action: "find",
#   target: "user authentication",
#   confidence: 0.92
# }

plan(action="intent", nl="rename authenticate to verify_user")
# Returns: {
#   category: "refactor",
#   action: "rename",
#   target: "authenticate",
#   params: {new_name: "verify_user"},
#   confidence: 0.95
# }
```

**Intent Categories:**
- `navigate` - Finding code/files (find, search, locate)
- `explain` - Understanding code (what, why, how)
- `modify` - Changing code (rename, extract, fix)
- `validate` - Testing/checking (test, verify, check)
- `debug` - Troubleshooting (trace, why fails)
- `create` - Adding new code (add, create, implement)

### route

Map IntentIR to a canonical operator chain.

```python
intent_ir = {"category": "refactor", "action": "rename", "target": "foo"}
plan(action="route", intent_ir=intent_ir)
# Returns: {
#   nodes: [
#     {tool: "code", action: "references", params: {symbol: "foo"}},
#     {tool: "code", action: "transform", params: {kind: "rename"}},
#     {tool: "code", action: "summarize"},
#     {tool: "fs", action: "patch", policy_gate: True},
#     {tool: "test", action: "run"}
#   ],
#   policy_gates: [3],
#   estimated_steps: 5
# }
```

**Parameters:**
- `intent_ir` (dict, optional): Structured intent from `intent` action
- `nl` (str, optional): Natural language (will call intent internally)
- `policy` (dict, optional): Custom policy overrides

### compose

Compile Plan into an execution graph with dependencies.

```python
plan(action="compose", plan=plan_result)
# Returns: {
#   graph: {
#     nodes: [...],
#     edges: [(0,1), (1,2), (2,3), (3,4)],
#     entry: 0,
#     exit: 4
#   },
#   execution_order: [0, 1, 2, 3, 4],
#   parallelizable: [[0], [1], [2], [3, 4]],  # Groups that can run in parallel
#   estimated_complexity: "medium"
# }
```

## Canonical Chains

Common intent → operator chain mappings:

| Intent Pattern | Canonical Chain |
|---------------|-----------------|
| "find X" | `fs.search(X)` |
| "what is X" | `fs.search(X) → code.summarize` |
| "rename X to Y" | `code.references(X) → code.transform(rename) → [policy] → fs.patch → test.run` |
| "fix bug in X" | `fs.read(X) → code.parse → code.transform(fix) → [policy] → fs.patch → test.run` |
| "add tests for X" | `code.symbols(X) → code.transform(add_tests) → fs.write → test.run` |
| "why does X fail" | `test.run(X) → vcs.log → code.summarize` |
| "refactor X" | `code.references(X) → code.transform → [policy] → fs.patch → test.run` |

## Policy Gates

High-risk operations require explicit approval:

```python
# In the plan output, policy_gate: True indicates approval needed
{
  "nodes": [
    {"tool": "code", "action": "transform", "params": {...}},
    {"tool": "fs", "action": "patch", "policy_gate": True}  # <-- requires approval
  ]
}
```

Configurable policy rules:
- File modifications (`fs.patch`, `fs.write`)
- Process execution with shell (`proc.run` with shell=True)
- Version control commits (`vcs.commit`, `vcs.push`)

## Example Workflow

```python
# 1. Parse user intent
intent = plan(action="intent", nl="rename the authenticate function to verify_credentials")

# 2. Route to operator chain
workflow = plan(action="route", intent_ir=intent["data"])

# 3. Compile to execution graph
graph = plan(action="compose", plan=workflow["data"])

# 4. Execute with policy gates
for step in graph["data"]["execution_order"]:
    node = graph["data"]["nodes"][step]

    if node.get("policy_gate"):
        # Request user approval
        approved = await request_approval(node)
        if not approved:
            break

    # Execute the step
    result = await dispatch(node["tool"], node["action"], node["params"])
```

## Custom Routing

Override default routing with custom rules:

```python
plan(action="route", nl="add caching to API",
     policy={"prefer_tools": ["code", "test"], "require_tests": True})
```

## See Also

- [HIP-0300](../hip/HIP-0300.md) - Unified Tools Architecture
- [Agent Tool](agent.md) - Multi-agent orchestration
- [Code Tool](code.md) - Symbol and structure operations
- [Test Tool](test.md) - Validation operations
