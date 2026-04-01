"""Session management with compaction for Hanzo AI SDK.

Ported from claw-code's session.rs and compact.rs. Provides conversation
message types, session persistence, and context window compaction.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Union


# ---------------------------------------------------------------------------
# Message primitives
# ---------------------------------------------------------------------------

class MessageRole(Enum):
    System = "system"
    User = "user"
    Assistant = "assistant"
    Tool = "tool"


@dataclass
class TextBlock:
    text: str

    def to_dict(self) -> dict[str, Any]:
        return {"type": "text", "text": self.text}

    @staticmethod
    def from_dict(d: dict[str, Any]) -> TextBlock:
        return TextBlock(text=d["text"])


@dataclass
class ToolUseBlock:
    id: str
    name: str
    input: str  # Raw JSON string, matching Rust's String type

    def to_dict(self) -> dict[str, Any]:
        return {"type": "tool_use", "id": self.id, "name": self.name, "input": self.input}

    @staticmethod
    def from_dict(d: dict[str, Any]) -> ToolUseBlock:
        raw = d["input"]
        # Backwards compat: accept dict from old serialized data, convert to JSON string
        if isinstance(raw, dict):
            raw = json.dumps(raw, separators=(",", ":"))
        return ToolUseBlock(id=d["id"], name=d["name"], input=raw)


@dataclass
class ToolResultBlock:
    tool_use_id: str
    tool_name: str
    output: str
    is_error: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "tool_result",
            "tool_use_id": self.tool_use_id,
            "tool_name": self.tool_name,
            "output": self.output,
            "is_error": self.is_error,
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> ToolResultBlock:
        return ToolResultBlock(
            tool_use_id=d["tool_use_id"],
            tool_name=d["tool_name"],
            output=d["output"],
            is_error=d.get("is_error", False),
        )


ContentBlock = Union[TextBlock, ToolUseBlock, ToolResultBlock]

_BLOCK_PARSERS = {
    "text": TextBlock.from_dict,
    "tool_use": ToolUseBlock.from_dict,
    "tool_result": ToolResultBlock.from_dict,
}


def _block_from_dict(d: dict[str, Any]) -> ContentBlock:
    parser = _BLOCK_PARSERS.get(d["type"])
    if parser is None:
        raise ValueError(f"unknown block type: {d['type']}")
    return parser(d)


# ---------------------------------------------------------------------------
# Token usage — canonical definition lives in protocols.py
# ---------------------------------------------------------------------------

from hanzoai.protocols import TokenUsage


# ---------------------------------------------------------------------------
# ConversationMessage
# ---------------------------------------------------------------------------

@dataclass
class ConversationMessage:
    role: MessageRole
    blocks: list[ContentBlock]
    usage: TokenUsage | None = None

    # -- Factory methods --

    @staticmethod
    def user_text(text: str) -> ConversationMessage:
        return ConversationMessage(role=MessageRole.User, blocks=[TextBlock(text=text)])

    @staticmethod
    def assistant(blocks: list[ContentBlock]) -> ConversationMessage:
        return ConversationMessage(role=MessageRole.Assistant, blocks=blocks)

    @staticmethod
    def assistant_with_usage(blocks: list[ContentBlock], usage: TokenUsage) -> ConversationMessage:
        return ConversationMessage(role=MessageRole.Assistant, blocks=blocks, usage=usage)

    @staticmethod
    def tool_result(tool_use_id: str, tool_name: str, output: str, is_error: bool = False) -> ConversationMessage:
        block = ToolResultBlock(tool_use_id=tool_use_id, tool_name=tool_name, output=output, is_error=is_error)
        return ConversationMessage(role=MessageRole.Tool, blocks=[block])

    # -- Serialization --

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "role": self.role.value,
            "blocks": [b.to_dict() for b in self.blocks],
        }
        if self.usage is not None:
            d["usage"] = self.usage.to_dict()
        return d

    @staticmethod
    def from_dict(d: dict[str, Any]) -> ConversationMessage:
        return ConversationMessage(
            role=MessageRole(d["role"]),
            blocks=[_block_from_dict(b) for b in d["blocks"]],
            usage=TokenUsage.from_dict(d["usage"]) if "usage" in d else None,
        )


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

@dataclass
class Session:
    version: int = 1
    messages: list[ConversationMessage] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "messages": [m.to_dict() for m in self.messages],
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> Session:
        return Session(
            version=d.get("version", 1),
            messages=[ConversationMessage.from_dict(m) for m in d.get("messages", [])],
        )

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @staticmethod
    def load(path: str | Path) -> Session:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return Session.from_dict(data)


# ---------------------------------------------------------------------------
# Compaction
# ---------------------------------------------------------------------------

@dataclass
class CompactionConfig:
    preserve_recent_messages: int = 4
    max_estimated_tokens: int = 10_000


@dataclass
class CompactionResult:
    summary: str
    formatted_summary: str
    compacted_session: Session
    removed_message_count: int


_FILE_EXTENSIONS = frozenset({
    ".py", ".rs", ".go", ".ts", ".tsx", ".js", ".jsx", ".json", ".yaml", ".yml",
    ".toml", ".md", ".sh", ".sql", ".html", ".css", ".c", ".h", ".cpp", ".hpp",
})

_PENDING_KEYWORDS = frozenset({"todo", "next", "pending", "follow up", "remaining"})


def estimate_session_tokens(session: Session) -> int:
    """Estimate token count: len(text)/4 + 1 per block."""
    total = 0
    for msg in session.messages:
        for block in msg.blocks:
            if isinstance(block, TextBlock):
                total += len(block.text) // 4 + 1
            elif isinstance(block, ToolUseBlock):
                total += len(block.input) // 4 + 1
            elif isinstance(block, ToolResultBlock):
                total += len(block.output) // 4 + 1
    return total


def should_compact(session: Session, config: CompactionConfig) -> bool:
    return (
        len(session.messages) > config.preserve_recent_messages
        and estimate_session_tokens(session) >= config.max_estimated_tokens
    )


def compact_session(session: Session, config: CompactionConfig) -> CompactionResult:
    """Compact a session by summarizing old messages and keeping recent ones."""
    if not should_compact(session, config):
        return CompactionResult(
            summary="",
            formatted_summary="",
            compacted_session=session,
            removed_message_count=0,
        )

    msgs = session.messages
    keep_count = min(config.preserve_recent_messages, len(msgs))
    split = len(msgs) - keep_count
    removed = msgs[:split]
    kept = msgs[split:]

    summary = _build_summary(removed)
    formatted = format_compact_summary(summary)

    continuation_text = (
        "This session is being continued from a previous conversation that ran "
        "out of context. The summary below covers the earlier portion of the "
        "conversation.\n\n"
        f"{formatted}\n\n"
        "Recent messages are preserved verbatim.\n"
        "Continue the conversation from where it left off without asking the "
        "user any further questions. Resume directly \u2014 do not acknowledge the "
        "summary, do not recap what was happening, and do not preface with "
        "continuation text."
    )

    system_msg = ConversationMessage(
        role=MessageRole.System,
        blocks=[TextBlock(text=continuation_text)],
    )

    compacted = Session(
        version=session.version,
        messages=[system_msg] + kept,
    )

    return CompactionResult(
        summary=summary,
        formatted_summary=formatted,
        compacted_session=compacted,
        removed_message_count=len(removed),
    )


def _build_summary(messages: list[ConversationMessage]) -> str:
    """Build a structured summary of removed messages, matching Rust summarize_messages()."""
    role_counts: dict[str, int] = {}
    tool_names: list[str] = []
    user_texts: list[str] = []
    pending_items: list[str] = []
    file_candidates: set[str] = set()
    last_text = ""
    timeline: list[tuple[str, str]] = []  # (role, block_summary)

    for msg in messages:
        role_counts[msg.role.value] = role_counts.get(msg.role.value, 0) + 1

        block_parts: list[str] = []
        for block in msg.blocks:
            if isinstance(block, ToolUseBlock):
                if block.name not in tool_names:
                    tool_names.append(block.name)
                block_parts.append(f"[tool_use: {block.name}]")
            elif isinstance(block, ToolResultBlock):
                if block.tool_name not in tool_names:
                    tool_names.append(block.tool_name)
                status = "error" if block.is_error else "ok"
                block_parts.append(f"[tool_result: {block.tool_name} ({status})]")

            if isinstance(block, TextBlock):
                if msg.role == MessageRole.User:
                    user_texts.append(block.text)
                last_text = block.text

                text_lower = block.text.lower()
                for kw in _PENDING_KEYWORDS:
                    if kw in text_lower:
                        for line in block.text.splitlines():
                            if kw in line.lower():
                                pending_items.append(line.strip())
                                break
                        break

                for token in block.text.split():
                    if "/" in token and _has_interesting_extension(token):
                        cleaned = token.strip("(),;:\"'`")
                        if "/" in cleaned:
                            file_candidates.add(cleaned)

                truncated = block.text[:80] + "..." if len(block.text) > 80 else block.text
                block_parts.append(truncated.replace("\n", " "))

        if block_parts:
            timeline.append((msg.role.value, "; ".join(block_parts)))

    recent_requests = user_texts[-3:] if user_texts else []

    u = role_counts.get("user", 0)
    a = role_counts.get("assistant", 0)
    t = role_counts.get("tool", 0)
    tools_str = ", ".join(tool_names) if tool_names else "none"
    files_str = ", ".join(sorted(file_candidates)[:20]) if file_candidates else "none"
    last_text_truncated = last_text[:100].replace("\n", " ") if last_text else "n/a"

    lines: list[str] = ["<summary>", "Conversation summary:"]
    lines.append(f"- Scope: {len(messages)} earlier messages compacted (user={u}, assistant={a}, tool={t}).")
    lines.append(f"- Tools mentioned: {tools_str}.")

    if recent_requests:
        lines.append("- Recent user requests:")
        for req in recent_requests:
            truncated = req[:200] + "..." if len(req) > 200 else req
            lines.append(f"  - {truncated}")

    if pending_items:
        lines.append("- Pending work:")
        for item in pending_items[:5]:
            lines.append(f"  - {item}")

    lines.append(f"- Key files referenced: {files_str}.")
    lines.append(f"- Current work: {last_text_truncated}")
    lines.append("- Key timeline:")
    for role, block_summary in timeline[-10:]:
        lines.append(f"  - {role}: {block_summary}")
    lines.append("</summary>")

    return "\n".join(lines)


def _has_interesting_extension(token: str) -> bool:
    """Check if a token looks like a file path with a known extension."""
    for ext in _FILE_EXTENSIONS:
        if token.endswith(ext):
            return True
    return False


def format_compact_summary(summary: str) -> str:
    """Strip analysis tags, extract summary content, collapse blank lines.

    Matches Rust's format_compact_summary:
    - Strip <analysis>...</analysis> block
    - Replace <summary>content</summary> with "Summary:\\ncontent"
    - Collapse consecutive blank lines
    """
    # Strip <analysis>...</analysis> block
    result = re.sub(r"<analysis>.*?</analysis>\s*", "", summary, flags=re.DOTALL)
    # Replace <summary>content</summary> with "Summary:\ncontent"
    result = re.sub(
        r"<summary>(.*?)</summary>",
        lambda m: "Summary:\n" + m.group(1).strip(),
        result,
        flags=re.DOTALL,
    )
    # Collapse consecutive blank lines
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()
