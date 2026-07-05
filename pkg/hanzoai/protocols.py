"""Protocol abstractions for pluggable tool execution, permissions, and conversation runtime.

Ported from claw-code's trait-based architecture to enable dependency injection
and testing without network calls.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Protocol, runtime_checkable


# ---------------------------------------------------------------------------
# Tool execution
# ---------------------------------------------------------------------------

@runtime_checkable
class ToolExecutor(Protocol):
    """Execute a named tool with a JSON-encoded input string."""

    def execute(self, tool_name: str, input: str) -> str: ...


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------

class PermissionMode(Enum):
    Allow = auto()
    Deny = auto()
    Prompt = auto()


@dataclass(frozen=True, slots=True)
class PermissionRequest:
    tool_name: str
    input: str


@dataclass(frozen=True, slots=True)
class PermissionOutcome:
    allowed: bool
    reason: str = ""

    @classmethod
    def allow(cls) -> PermissionOutcome:
        return cls(allowed=True)

    @classmethod
    def deny(cls, reason: str) -> PermissionOutcome:
        return cls(allowed=False, reason=reason)


# Named constructors matching Rust enum variants.
PERMISSION_ALLOW = PermissionOutcome(allowed=True)


@runtime_checkable
class PermissionPrompter(Protocol):
    """Interactively decide whether a tool invocation is allowed."""

    def decide(self, request: PermissionRequest) -> PermissionOutcome: ...


class PermissionPolicy:
    """Default-mode + per-tool override permission policy.

    Mirrors the Rust ``PermissionPolicy`` struct: a default mode with an
    ordered map of per-tool overrides.
    """

    __slots__ = ("default_mode", "_tool_modes")

    def __init__(
        self,
        default_mode: PermissionMode = PermissionMode.Prompt,
        tool_modes: dict[str, PermissionMode] | None = None,
    ) -> None:
        self.default_mode = default_mode
        # Sorted dict to match Rust BTreeMap ordering.
        self._tool_modes: dict[str, PermissionMode] = dict(
            sorted((tool_modes or {}).items())
        )

    def with_tool_mode(self, name: str, mode: PermissionMode) -> PermissionPolicy:
        """Fluent builder: set a per-tool override and return self for chaining."""
        self._tool_modes[name] = mode
        self._tool_modes = dict(sorted(self._tool_modes.items()))
        return self

    def mode_for(self, tool_name: str) -> PermissionMode:
        return self._tool_modes.get(tool_name, self.default_mode)

    def authorize(
        self,
        tool_name: str,
        input: str,
        prompter: PermissionPrompter | None = None,
    ) -> PermissionOutcome:
        mode = self.mode_for(tool_name)
        if mode is PermissionMode.Allow:
            return PermissionOutcome.allow()
        if mode is PermissionMode.Deny:
            return PermissionOutcome.deny(f"tool '{tool_name}' denied by policy")
        # Prompt
        if prompter is None:
            return PermissionOutcome.deny("no prompter available for interactive decision")
        return prompter.decide(PermissionRequest(tool_name=tool_name, input=input))


# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0

    def __iadd__(self, other: TokenUsage) -> TokenUsage:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.cache_creation_input_tokens += other.cache_creation_input_tokens
        self.cache_read_input_tokens += other.cache_read_input_tokens
        return self

    def total_tokens(self) -> int:
        return (
            self.input_tokens
            + self.output_tokens
            + self.cache_creation_input_tokens
            + self.cache_read_input_tokens
        )

    def to_dict(self) -> dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_creation_input_tokens": self.cache_creation_input_tokens,
            "cache_read_input_tokens": self.cache_read_input_tokens,
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> TokenUsage:
        return TokenUsage(
            input_tokens=d.get("input_tokens", 0),
            output_tokens=d.get("output_tokens", 0),
            cache_creation_input_tokens=d.get("cache_creation_input_tokens", 0),
            cache_read_input_tokens=d.get("cache_read_input_tokens", 0),
        )


@dataclass(frozen=True, slots=True)
class ModelPricing:
    """Per-token prices in USD."""
    input_price_per_token: float
    output_price_per_token: float
    cache_creation_price_per_token: float = 0.0
    cache_read_price_per_token: float = 0.0

    def cost(self, usage: TokenUsage) -> float:
        return (
            usage.input_tokens * self.input_price_per_token
            + usage.output_tokens * self.output_price_per_token
            + usage.cache_creation_input_tokens * self.cache_creation_price_per_token
            + usage.cache_read_input_tokens * self.cache_read_price_per_token
        )


class UsageTracker:
    """Accumulates per-turn and cumulative token usage."""

    __slots__ = ("_turns",)

    def __init__(self) -> None:
        self._turns: list[TokenUsage] = []

    def record(self, usage: TokenUsage) -> None:
        self._turns.append(usage)

    @property
    def turns(self) -> int:
        """Number of recorded turns. Matches Rust ``pub fn turns(&self) -> u32``."""
        return len(self._turns)

    def turns_list(self) -> list[TokenUsage]:
        """Return a copy of per-turn usage records."""
        return list(self._turns)

    def cumulative_usage(self) -> TokenUsage:
        total = TokenUsage()
        for t in self._turns:
            total += t
        return total

    def cost(self, pricing: ModelPricing) -> float:
        return pricing.cost(self.cumulative_usage())


# ---------------------------------------------------------------------------
# API transport types
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class AssistantEvent:
    """Event from the assistant stream.

    ``kind`` uses string values matching Rust enum variant names:
    ``"text_delta"``, ``"tool_use"``, ``"usage"``, ``"message_stop"``.
    """
    kind: str
    text: str = ""
    tool_use_id: str = ""
    tool_name: str = ""
    tool_input: str = ""
    usage: TokenUsage | None = None


@dataclass(slots=True)
class ApiRequest:
    system_prompt: list[str]
    messages: list[dict]


@runtime_checkable
class ApiClient(Protocol):
    """Send a conversation request and receive a stream of events."""

    def stream(self, request: ApiRequest) -> list[AssistantEvent]: ...


# ---------------------------------------------------------------------------
# Turn summary
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class TurnSummary:
    assistant_messages: list[dict] = field(default_factory=list)
    tool_results: list[dict] = field(default_factory=list)
    usage: TokenUsage = field(default_factory=TokenUsage)
    iterations: int = 0


# ---------------------------------------------------------------------------
# Static tool executor (test helper)
# ---------------------------------------------------------------------------

class StaticToolExecutor:
    """Register handlers by name.  Useful for testing."""

    __slots__ = ("_handlers",)

    def __init__(self) -> None:
        self._handlers: dict[str, Callable[[str], str]] = {}

    def register(self, name: str, handler: Callable[[str], str]) -> None:
        self._handlers[name] = handler

    def execute(self, tool_name: str, input: str) -> str:
        handler = self._handlers.get(tool_name)
        if handler is None:
            raise KeyError(f"no handler registered for tool '{tool_name}'")
        return handler(input)


# ---------------------------------------------------------------------------
# Conversation runtime
# ---------------------------------------------------------------------------

_DEFAULT_MAX_ITERATIONS = 16


class ConversationRuntime:
    """Orchestrate turn execution over an API client and tool executor.

    Generic over any ``ApiClient`` and ``ToolExecutor`` implementations,
    mirroring the Rust ``ConversationRuntime<A, T>`` generic struct.
    """

    __slots__ = (
        "session",
        "api_client",
        "tool_executor",
        "permission_policy",
        "system_prompt",
        "max_iterations",
        "usage_tracker",
    )

    def __init__(
        self,
        *,
        session: list[dict],
        api_client: ApiClient,
        tool_executor: ToolExecutor,
        permission_policy: PermissionPolicy,
        system_prompt: list[str] | None = None,
        max_iterations: int = _DEFAULT_MAX_ITERATIONS,
    ) -> None:
        self.session = session
        self.api_client = api_client
        self.tool_executor = tool_executor
        self.permission_policy = permission_policy
        self.system_prompt = system_prompt or []
        self.max_iterations = max_iterations
        self.usage_tracker = UsageTracker()

    # ---- public API -------------------------------------------------------

    def run_turn(
        self,
        user_input: str,
        prompter: PermissionPrompter | None = None,
    ) -> TurnSummary:
        """Execute one conversational turn, looping on tool use.

        Appends the user message, then repeatedly:
          1. Build ``ApiRequest`` with system_prompt + messages.
          2. Call ``api_client.stream()`` to get assistant events.
          3. Assemble the assistant message from events.
          4. If no tool_use blocks are present, break.
          5. For each tool_use, authorize via permission_policy then execute.
          6. Append results to session.
          7. Guard against ``max_iterations``.
        """
        self.session.append({"role": "user", "content": user_input})

        summary = TurnSummary()

        for iteration in range(1, self.max_iterations + 1):
            summary.iterations = iteration

            request = ApiRequest(
                system_prompt=self.system_prompt,
                messages=list(self.session),
            )
            events = self.api_client.stream(request)
            assistant_msg, tool_uses, turn_usage = _build_assistant_message(events)

            self.session.append(assistant_msg)
            summary.assistant_messages.append(assistant_msg)
            summary.usage += turn_usage
            self.usage_tracker.record(turn_usage)

            if not tool_uses:
                break

            for tu in tool_uses:
                outcome = self.permission_policy.authorize(
                    tu.tool_name, tu.tool_input, prompter,
                )

                if outcome.allowed:
                    try:
                        output = self.tool_executor.execute(tu.tool_name, tu.tool_input)
                        is_error = False
                    except Exception as exc:
                        output = str(exc)
                        is_error = True
                else:
                    output = outcome.reason
                    is_error = True

                result_msg = {
                    "role": "tool",
                    "tool_use_id": tu.tool_use_id,
                    "tool_name": tu.tool_name,
                    "output": output,
                    "is_error": is_error,
                }
                self.session.append(result_msg)
                summary.tool_results.append(result_msg)

        return summary


def _build_assistant_message(
    events: list[AssistantEvent],
) -> tuple[dict, list[AssistantEvent], TokenUsage]:
    """Parse stream events into an assistant message dict, tool uses, and usage."""
    text_parts: list[str] = []
    tool_uses: list[AssistantEvent] = []
    usage = TokenUsage()
    blocks: list[dict] = []

    for event in events:
        if event.kind == "text_delta":
            text_parts.append(event.text)
        elif event.kind == "tool_use":
            # Flush accumulated text
            if text_parts:
                blocks.append({"type": "text", "text": "".join(text_parts)})
                text_parts.clear()
            blocks.append({
                "type": "tool_use",
                "id": event.tool_use_id,
                "name": event.tool_name,
                "input": event.tool_input,
            })
            tool_uses.append(event)
        elif event.kind == "usage" and event.usage is not None:
            usage += event.usage

    if text_parts:
        blocks.append({"type": "text", "text": "".join(text_parts)})

    msg = {"role": "assistant", "blocks": blocks}
    return msg, tool_uses, usage


__all__ = [
    # Tool execution
    "ToolExecutor",
    "StaticToolExecutor",
    # Permissions
    "PermissionMode",
    "PermissionRequest",
    "PermissionOutcome",
    "PermissionPrompter",
    "PermissionPolicy",
    # API client
    "ApiClient",
    "ApiRequest",
    "AssistantEvent",
    # (AssistantEvent uses string 'kind' values, no separate enum)
    # Usage
    "TokenUsage",
    "ModelPricing",
    "UsageTracker",
    # Conversation
    "ConversationRuntime",
    "TurnSummary",
]
