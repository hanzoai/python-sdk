"""Unified plan orchestration tool for HIP-0300 architecture.

This module provides a single unified 'plan' tool that handles orchestration:
- intent: Parse natural language → IntentIR
- route: Map IntentIR → Plan (canonical operator chain)
- compose: Plan → ExecGraph (typed DAG for execution)
- execute: Run ExecGraph with policy gates (optional, returns audit log)

Following Unix philosophy: one tool for the Orchestration axis.
Turns "permissive input" into "strict canonical chains."

Effect lattice:
- intent, route, compose: NONDETERMINISTIC (LLM-based NL understanding)
- execute: NONDETERMINISTIC (audit-friendly)
"""

import os
import json
import hashlib
import re
from datetime import datetime, timezone
from typing import Any, ClassVar, Literal
from dataclasses import dataclass, field
from enum import Enum

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core import (
    BaseTool,
    ToolError,
    InvalidParamsError,
    content_hash,
)


class EffectClass(str, Enum):
    """Effect lattice for operators."""
    PURE = "pure"
    DETERMINISTIC = "deterministic"
    NONDETERMINISTIC = "nondeterministic"


class StepStatus(str, Enum):
    """Status for plan steps (Rust parity)."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class TrackedStep:
    """A tracked plan step with status (Rust parity)."""
    step: str
    status: StepStatus = StepStatus.PENDING


@dataclass
class TrackedPlan:
    """A tracked plan with name and steps (Rust parity)."""
    name: str | None = None
    steps: list[TrackedStep] = field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class Scope(str, Enum):
    """Scope lattice for operators."""
    SPAN = "span"
    FILE = "file"
    PACKAGE = "package"
    REPO = "repo"
    WORKSPACE = "workspace"


@dataclass
class IntentIR:
    """Intermediate representation for parsed intent."""
    category: str  # navigate, edit, refactor, test, deploy, etc.
    action: str    # find, read, rename, run, etc.
    target: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    raw: str = ""


@dataclass
class PlanNode:
    """Single node in execution plan."""
    id: str
    tool: str
    action: str
    params: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    effect: EffectClass = EffectClass.PURE
    scope: Scope = Scope.FILE
    cache_key: str | None = None


@dataclass
class Plan:
    """Execution plan as typed DAG."""
    nodes: list[PlanNode] = field(default_factory=list)
    policy_gates: list[str] = field(default_factory=list)  # Nodes requiring approval
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecGraph:
    """Compiled execution graph ready for execution."""
    plan: Plan
    execution_order: list[str]  # Topologically sorted node IDs
    parallelizable: list[list[str]]  # Groups that can run in parallel
    audit_log: list[dict] = field(default_factory=list)


# Intent routing patterns
INTENT_PATTERNS = [
    # Navigation / Understanding
    (r"(where|find|locate)\s+(is\s+)?(.+)", "navigate", "find"),
    (r"(who|what)\s+(calls|uses)\s+(.+)", "navigate", "references"),
    (r"(what|explain|describe)\s+(does\s+)?(.+)\s+(do|mean)", "navigate", "explain"),
    (r"(go\s+to|jump\s+to)\s+(definition\s+of\s+)?(.+)", "navigate", "definition"),
    (r"(show|list)\s+(symbols|functions|classes)", "navigate", "symbols"),

    # Edit / Transform
    (r"(edit|change|modify|update)\s+(.+)", "edit", "transform"),
    (r"(rename|refactor)\s+(.+)\s+(to|as)\s+(.+)", "refactor", "rename"),
    (r"(add|create|insert)\s+(.+)", "edit", "create"),
    (r"(remove|delete)\s+(.+)", "edit", "delete"),
    (r"(fix|repair|correct)\s+(.+)", "edit", "fix"),

    # Test / Validate
    (r"(run|execute)\s+(tests?|specs?)", "test", "run"),
    (r"(check|verify|validate)\s+(.+)", "test", "validate"),
    (r"(lint|typecheck|format)\s+(.+)?", "test", "lint"),
    (r"(why|debug)\s+(is|are|did)\s+(.+)\s+(failing|broken|wrong)", "test", "debug"),

    # VCS
    (r"(commit|save)\s+(changes?)?", "vcs", "commit"),
    (r"(diff|compare|show\s+changes)", "vcs", "diff"),
    (r"(log|history|blame)\s*(.+)?", "vcs", "log"),

    # General
    (r"(help|how\s+do\s+i)", "meta", "help"),
]

# Canonical chains for intents
CANONICAL_CHAINS = {
    ("navigate", "find"): [
        {"tool": "fs", "action": "search"},
    ],
    ("navigate", "references"): [
        {"tool": "code", "action": "references"},
        {"tool": "code", "action": "summarize"},
    ],
    ("navigate", "definition"): [
        {"tool": "code", "action": "definition"},
        {"tool": "fs", "action": "read"},
    ],
    ("navigate", "symbols"): [
        {"tool": "code", "action": "symbols"},
    ],
    ("navigate", "explain"): [
        {"tool": "fs", "action": "read"},
        {"tool": "code", "action": "parse"},
        {"tool": "code", "action": "summarize"},
    ],
    ("edit", "transform"): [
        {"tool": "fs", "action": "read"},
        {"tool": "code", "action": "transform"},
        {"tool": "code", "action": "summarize"},  # Review patch
        {"tool": "fs", "action": "patch", "policy_gate": True},
        {"tool": "test", "action": "run"},
    ],
    ("refactor", "rename"): [
        {"tool": "code", "action": "references"},
        {"tool": "code", "action": "transform"},
        {"tool": "code", "action": "summarize"},
        {"tool": "fs", "action": "patch", "policy_gate": True},
        {"tool": "test", "action": "run"},
    ],
    ("test", "run"): [
        {"tool": "test", "action": "run"},
        {"tool": "code", "action": "summarize"},
    ],
    ("test", "debug"): [
        {"tool": "test", "action": "run"},
        {"tool": "code", "action": "summarize"},
        {"tool": "code", "action": "references"},
    ],
    ("vcs", "commit"): [
        {"tool": "vcs", "action": "diff", "params": {"staged": True}},
        {"tool": "code", "action": "summarize"},
        {"tool": "vcs", "action": "commit", "policy_gate": True},
    ],
    ("vcs", "diff"): [
        {"tool": "vcs", "action": "diff"},
        {"tool": "code", "action": "summarize"},
    ],
}


class PlanTool(BaseTool):
    """Unified plan orchestration tool (HIP-0300).

    Handles all orchestration operations:
    - intent: Parse NL → IntentIR
    - route: IntentIR → Plan
    - compose: Plan → ExecGraph
    - update: Track plan with step status (Rust parity)
    - execute: Run with audit (optional)

    This is the "permissive input → strict output" layer.
    """

    name: ClassVar[str] = "plan"
    VERSION: ClassVar[str] = "0.2.0"

    # In-memory tracked plan (matches Rust update_plan behavior)
    _tracked_plan: TrackedPlan | None = None

    def __init__(self):
        super().__init__()
        self._tracked_plan = None
        self._register_plan_actions()

    @property
    def description(self) -> str:
        return """Unified plan orchestration tool (HIP-0300).

Actions:
- update: Track plan with step status (Rust parity - name, steps with status)
- get: Get current tracked plan
- intent: Parse natural language → IntentIR
- route: Map IntentIR → Plan (canonical operator chain)
- compose: Plan → ExecGraph (execution-ready DAG)

Turns permissive natural language input into strict canonical operator chains.
"""

    def _parse_intent(self, nl: str) -> IntentIR:
        """Parse natural language to IntentIR."""
        nl_lower = nl.lower().strip()

        for pattern, category, action in INTENT_PATTERNS:
            match = re.search(pattern, nl_lower, re.IGNORECASE)
            if match:
                # Extract target from capture groups
                groups = match.groups()
                target = groups[-1] if groups else None

                return IntentIR(
                    category=category,
                    action=action,
                    target=target,
                    confidence=0.8,
                    raw=nl,
                )

        # Fallback: ambiguous
        return IntentIR(
            category="unknown",
            action="unknown",
            target=None,
            confidence=0.3,
            raw=nl,
        )

    def _build_plan(self, intent: IntentIR, policy: dict | None = None) -> Plan:
        """Build execution plan from intent."""
        chain_key = (intent.category, intent.action)
        chain = CANONICAL_CHAINS.get(chain_key, [])

        if not chain:
            # Unknown intent - return empty plan
            return Plan(
                metadata={
                    "intent": intent.category,
                    "action": intent.action,
                    "warning": "No canonical chain found",
                }
            )

        nodes = []
        policy_gates = []
        prev_id = None

        for i, step in enumerate(chain):
            node_id = f"step_{i}"
            node = PlanNode(
                id=node_id,
                tool=step["tool"],
                action=step["action"],
                params=step.get("params", {}),
                depends_on=[prev_id] if prev_id else [],
                effect=EffectClass.DETERMINISTIC if step.get("policy_gate") else EffectClass.PURE,
            )

            # Add target from intent
            if intent.target and i == 0:
                if "path" not in node.params:
                    node.params["target"] = intent.target

            nodes.append(node)

            if step.get("policy_gate"):
                policy_gates.append(node_id)

            prev_id = node_id

        return Plan(
            nodes=nodes,
            policy_gates=policy_gates,
            metadata={
                "intent": intent.category,
                "action": intent.action,
                "target": intent.target,
            }
        )

    def _compile_graph(self, plan: Plan) -> ExecGraph:
        """Compile plan into execution graph."""
        # Topological sort
        node_map = {n.id: n for n in plan.nodes}
        in_degree = {n.id: len(n.depends_on) for n in plan.nodes}
        execution_order = []
        parallelizable = []

        # Kahn's algorithm
        ready = [nid for nid, deg in in_degree.items() if deg == 0]

        while ready:
            # All ready nodes can run in parallel
            if len(ready) > 1:
                parallelizable.append(ready.copy())
            execution_order.extend(ready)

            next_ready = []
            for nid in ready:
                for node in plan.nodes:
                    if nid in node.depends_on:
                        in_degree[node.id] -= 1
                        if in_degree[node.id] == 0:
                            next_ready.append(node.id)

            ready = next_ready

        return ExecGraph(
            plan=plan,
            execution_order=execution_order,
            parallelizable=parallelizable,
        )

    def _register_plan_actions(self):
        """Register all plan actions."""

        @self.action("update", "Update tracked plan with steps and status (Rust parity)")
        async def update(
            ctx: MCPContext,
            name: str | None = None,
            plan: list[dict] | None = None,
        ) -> dict:
            """Update the tracked plan with steps and their status.

            This matches the Rust update_plan tool schema exactly.

            Args:
                name: Optional plan title (2-5 words)
                plan: List of steps, each with:
                    - step: Step description (required)
                    - status: "pending" | "in_progress" | "completed"

            Returns:
                {"message": "Plan updated", "plan": {...}}

            Example:
                plan(action="update", name="Fix auth bug", plan=[
                    {"step": "Identify the root cause", "status": "completed"},
                    {"step": "Write failing test", "status": "in_progress"},
                    {"step": "Implement fix", "status": "pending"},
                    {"step": "Verify all tests pass", "status": "pending"}
                ])
            """
            now = datetime.now(timezone.utc).isoformat()

            # Parse steps
            steps = []
            if plan:
                for item in plan:
                    step_text = item.get("step", "")
                    status_str = item.get("status", "pending")
                    try:
                        status = StepStatus(status_str)
                    except ValueError:
                        status = StepStatus.PENDING
                    steps.append(TrackedStep(step=step_text, status=status))

            # Update or create tracked plan
            if self._tracked_plan is None:
                self._tracked_plan = TrackedPlan(
                    name=name,
                    steps=steps,
                    created_at=now,
                    updated_at=now,
                )
            else:
                if name is not None:
                    self._tracked_plan.name = name
                if steps:
                    self._tracked_plan.steps = steps
                self._tracked_plan.updated_at = now

            return {
                "message": "Plan updated",
                "plan": {
                    "name": self._tracked_plan.name,
                    "steps": [
                        {"step": s.step, "status": s.status.value}
                        for s in self._tracked_plan.steps
                    ],
                    "created_at": self._tracked_plan.created_at,
                    "updated_at": self._tracked_plan.updated_at,
                },
            }

        @self.action("get", "Get current tracked plan")
        async def get(
            ctx: MCPContext,
        ) -> dict:
            """Get the current tracked plan.

            Returns:
                Current plan with name, steps, and timestamps
            """
            if self._tracked_plan is None:
                return {"plan": None, "message": "No plan currently tracked"}

            return {
                "plan": {
                    "name": self._tracked_plan.name,
                    "steps": [
                        {"step": s.step, "status": s.status.value}
                        for s in self._tracked_plan.steps
                    ],
                    "created_at": self._tracked_plan.created_at,
                    "updated_at": self._tracked_plan.updated_at,
                },
                "progress": {
                    "total": len(self._tracked_plan.steps),
                    "completed": sum(
                        1 for s in self._tracked_plan.steps
                        if s.status == StepStatus.COMPLETED
                    ),
                    "in_progress": sum(
                        1 for s in self._tracked_plan.steps
                        if s.status == StepStatus.IN_PROGRESS
                    ),
                    "pending": sum(
                        1 for s in self._tracked_plan.steps
                        if s.status == StepStatus.PENDING
                    ),
                },
            }

        @self.action("clear", "Clear tracked plan")
        async def clear(
            ctx: MCPContext,
        ) -> dict:
            """Clear the current tracked plan."""
            self._tracked_plan = None
            return {"message": "Plan cleared"}

        @self.action("intent", "Parse natural language to IntentIR")
        async def intent(
            ctx: MCPContext,
            nl: str,
        ) -> dict:
            """Parse natural language input to structured IntentIR.

            Args:
                nl: Natural language input

            Returns:
                IntentIR with category, action, target, confidence

            Effect: NONDETERMINISTIC (LLM-based, regex fallback)
            Cache: hash(nl)
            """
            parsed = self._parse_intent(nl)

            return {
                "intent_ir": {
                    "category": parsed.category,
                    "action": parsed.action,
                    "target": parsed.target,
                    "params": parsed.params,
                    "confidence": parsed.confidence,
                },
                "raw": nl,
                "hash": content_hash(nl),
            }

        @self.action("route", "Map IntentIR to Plan")
        async def route(
            ctx: MCPContext,
            intent_ir: dict | None = None,
            nl: str | None = None,
            policy: dict | None = None,
        ) -> dict:
            """Route intent to canonical operator chain.

            Args:
                intent_ir: Parsed intent (from plan.intent)
                nl: Raw NL (will parse if intent_ir not provided)
                policy: Policy constraints

            Returns:
                Plan with nodes, policy_gates, metadata

            Effect: NONDETERMINISTIC
            """
            if intent_ir:
                intent = IntentIR(
                    category=intent_ir.get("category", "unknown"),
                    action=intent_ir.get("action", "unknown"),
                    target=intent_ir.get("target"),
                    params=intent_ir.get("params", {}),
                    confidence=intent_ir.get("confidence", 1.0),
                )
            elif nl:
                intent = self._parse_intent(nl)
            else:
                raise InvalidParamsError("intent_ir or nl required")

            plan = self._build_plan(intent, policy)

            return {
                "plan": {
                    "nodes": [
                        {
                            "id": n.id,
                            "tool": n.tool,
                            "action": n.action,
                            "params": n.params,
                            "depends_on": n.depends_on,
                            "effect": n.effect.value,
                        }
                        for n in plan.nodes
                    ],
                    "policy_gates": plan.policy_gates,
                    "metadata": plan.metadata,
                },
                "chain_length": len(plan.nodes),
                "requires_approval": len(plan.policy_gates) > 0,
            }

        @self.action("compose", "Compile Plan to ExecGraph")
        async def compose(
            ctx: MCPContext,
            plan: dict,
        ) -> dict:
            """Compile plan into execution-ready graph.

            Args:
                plan: Plan dict (from plan.route)

            Returns:
                ExecGraph with execution_order, parallelizable groups

            Effect: PURE
            """
            # Reconstruct Plan
            nodes = [
                PlanNode(
                    id=n["id"],
                    tool=n["tool"],
                    action=n["action"],
                    params=n.get("params", {}),
                    depends_on=n.get("depends_on", []),
                    effect=EffectClass(n.get("effect", "pure")),
                )
                for n in plan.get("nodes", [])
            ]

            plan_obj = Plan(
                nodes=nodes,
                policy_gates=plan.get("policy_gates", []),
                metadata=plan.get("metadata", {}),
            )

            graph = self._compile_graph(plan_obj)

            return {
                "exec_graph": {
                    "execution_order": graph.execution_order,
                    "parallelizable": graph.parallelizable,
                    "policy_gates": plan_obj.policy_gates,
                    "total_steps": len(graph.execution_order),
                },
                "plan": plan,
                "ready_for_execution": True,
            }

        @self.action("chains", "List available canonical chains")
        async def chains(
            ctx: MCPContext,
            category: str | None = None,
        ) -> dict:
            """List available canonical operator chains.

            Args:
                category: Filter by category (optional)

            Returns:
                Dictionary of available chains
            """
            result = {}
            for (cat, action), chain in CANONICAL_CHAINS.items():
                if category and cat != category:
                    continue
                key = f"{cat}.{action}"
                result[key] = {
                    "steps": len(chain),
                    "tools": [s["tool"] for s in chain],
                    "has_policy_gate": any(s.get("policy_gate") for s in chain),
                }

            return {
                "chains": result,
                "total": len(result),
            }

    def register(self, mcp_server: FastMCP) -> None:
        """Register as 'plan' tool with MCP server."""
        tool_name = self.name
        tool_description = self.description

        @mcp_server.tool(name=tool_name, description=tool_description)
        async def handler(
            ctx: MCPContext,
            action: str = "help",
            **kwargs: Any,
        ) -> str:
            result = await self.call(ctx, action=action, **kwargs)
            return json.dumps(result, indent=2, default=str)


# Singleton
plan_tool = PlanTool
