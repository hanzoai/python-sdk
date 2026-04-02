"""Tests for session management and compaction."""

import json
import tempfile
from pathlib import Path

import pytest

from hanzoai.session import (
    Session,
    TextBlock,
    TokenUsage,
    MessageRole,
    ToolUseBlock,
    ToolResultBlock,
    CompactionConfig,
    CompactionResult,
    ConversationMessage,
    should_compact,
    compact_session,
    format_compact_summary,
    estimate_session_tokens,
)


class TestTokenUsage:
    def test_total_tokens(self):
        u = TokenUsage(input_tokens=10, output_tokens=4, cache_creation_input_tokens=2, cache_read_input_tokens=1)
        assert u.total_tokens() == 17

    def test_roundtrip(self):
        u = TokenUsage(input_tokens=5, output_tokens=3, cache_creation_input_tokens=1, cache_read_input_tokens=0)
        assert TokenUsage.from_dict(u.to_dict()) == u


class TestContentBlocks:
    def test_text_block_roundtrip(self):
        b = TextBlock(text="hello")
        d = b.to_dict()
        assert d == {"type": "text", "text": "hello"}
        assert TextBlock.from_dict(d) == b

    def test_tool_use_block_roundtrip(self):
        b = ToolUseBlock(id="t1", name="bash", input='{"command":"ls"}')
        d = b.to_dict()
        assert d["type"] == "tool_use"
        assert ToolUseBlock.from_dict(d) == b

    def test_tool_result_block_roundtrip(self):
        b = ToolResultBlock(tool_use_id="t1", tool_name="bash", output="ok", is_error=False)
        d = b.to_dict()
        assert d["type"] == "tool_result"
        assert ToolResultBlock.from_dict(d) == b


class TestConversationMessage:
    def test_user_text_factory(self):
        m = ConversationMessage.user_text("hello")
        assert m.role == MessageRole.User
        assert len(m.blocks) == 1
        assert isinstance(m.blocks[0], TextBlock)

    def test_tool_result_factory(self):
        m = ConversationMessage.tool_result("t1", "bash", "output", is_error=True)
        assert m.role == MessageRole.Tool
        assert isinstance(m.blocks[0], ToolResultBlock)
        assert m.blocks[0].is_error

    def test_assistant_with_usage(self):
        u = TokenUsage(input_tokens=10, output_tokens=4)
        m = ConversationMessage.assistant_with_usage([TextBlock(text="hi")], u)
        assert m.usage == u

    def test_roundtrip(self):
        m = ConversationMessage.user_text("test")
        assert ConversationMessage.from_dict(m.to_dict()).role == m.role


class TestSession:
    def test_empty_session(self):
        s = Session()
        assert s.version == 1
        assert s.messages == []

    def test_roundtrip_dict(self):
        s = Session()
        s.messages.append(ConversationMessage.user_text("hello"))
        s.messages.append(ConversationMessage.assistant([TextBlock(text="hi")]))
        s.messages.append(ConversationMessage.tool_result("t1", "bash", "ok", False))

        restored = Session.from_dict(s.to_dict())
        assert len(restored.messages) == 3
        assert restored.messages[0].role == MessageRole.User
        assert restored.messages[2].role == MessageRole.Tool

    def test_save_and_load(self):
        s = Session()
        s.messages.append(ConversationMessage.user_text("hello"))
        s.messages.append(
            ConversationMessage.assistant_with_usage(
                [
                    TextBlock(text="thinking"),
                    ToolUseBlock(id="t1", name="bash", input='{"cmd":"echo hi"}'),
                ],
                TokenUsage(input_tokens=10, output_tokens=4, cache_creation_input_tokens=1, cache_read_input_tokens=2),
            )
        )
        s.messages.append(ConversationMessage.tool_result("t1", "bash", "hi", False))

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        s.save(path)
        restored = Session.load(path)

        assert restored == s
        assert restored.messages[1].usage.total_tokens() == 17
        assert restored.messages[2].role == MessageRole.Tool
        Path(path).unlink()


class TestCompaction:
    def _big_session(self, n: int = 10) -> Session:
        s = Session()
        for i in range(n):
            s.messages.append(ConversationMessage.user_text("x " * 200))
            s.messages.append(ConversationMessage.assistant([TextBlock(text="y " * 200)]))
        return s

    def test_small_session_unchanged(self):
        s = Session()
        s.messages.append(ConversationMessage.user_text("hello"))
        result = compact_session(s, CompactionConfig())
        assert result.removed_message_count == 0
        assert result.compacted_session is s

    def test_compacts_old_messages(self):
        s = self._big_session(10)
        config = CompactionConfig(preserve_recent_messages=2, max_estimated_tokens=1)
        result = compact_session(s, config)

        assert result.removed_message_count == 18
        assert result.compacted_session.messages[0].role == MessageRole.System
        assert len(result.compacted_session.messages) == 3  # system + 2 preserved
        assert result.summary != ""
        assert result.formatted_summary != ""

    def test_should_compact_checks_both(self):
        s = Session()
        s.messages.append(ConversationMessage.user_text("short"))
        # Few messages, low tokens - should not compact
        assert not should_compact(s, CompactionConfig(preserve_recent_messages=0, max_estimated_tokens=100))

    def test_estimate_tokens(self):
        s = Session()
        s.messages.append(ConversationMessage.user_text("a" * 400))
        tokens = estimate_session_tokens(s)
        assert tokens == 400 // 4 + 1  # 101

    def test_compaction_reduces_tokens(self):
        s = self._big_session(10)
        config = CompactionConfig(preserve_recent_messages=2, max_estimated_tokens=1)
        result = compact_session(s, config)
        assert estimate_session_tokens(result.compacted_session) < estimate_session_tokens(s)

    def test_summary_contains_tool_names(self):
        s = Session()
        for _ in range(6):
            s.messages.append(ConversationMessage.user_text("x " * 200))
            s.messages.append(
                ConversationMessage.assistant(
                    [TextBlock(text="ok"), ToolUseBlock(id="t1", name="bash", input='{"cmd":"ls"}')]
                )
            )
            s.messages.append(ConversationMessage.tool_result("t1", "bash", "output " * 50, False))

        config = CompactionConfig(preserve_recent_messages=2, max_estimated_tokens=1)
        result = compact_session(s, config)
        assert "bash" in result.summary

    def test_summary_contains_file_candidates(self):
        s = Session()
        for _ in range(5):
            s.messages.append(ConversationMessage.user_text("Update src/main.rs and pkg/config.py next " + "x " * 200))
            s.messages.append(ConversationMessage.assistant([TextBlock(text="done " * 200)]))

        config = CompactionConfig(preserve_recent_messages=2, max_estimated_tokens=1)
        result = compact_session(s, config)
        assert "src/main.rs" in result.summary

    def test_format_compact_summary_strips_analysis(self):
        summary = "<analysis>scratch</analysis>\n<summary>Kept work</summary>"
        formatted = format_compact_summary(summary)
        assert "analysis" not in formatted
        assert "Kept work" in formatted

    def test_format_compact_summary_no_tags(self):
        formatted = format_compact_summary("plain text summary")
        assert formatted == "plain text summary"
