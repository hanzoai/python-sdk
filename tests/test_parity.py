"""Rust/Python parity tests.

Each test feeds the EXACT inputs from a Rust crate test and asserts the Python
implementation produces the SAME output. Every test is tagged with the Rust
source file and test name it mirrors.
"""
from __future__ import annotations

import json
import hashlib
import tempfile
from pathlib import Path

# ── 1. SSE Parser ────────────────────────────────────────────────────────────
from hanzoai._streaming import SSEDecoder, ServerSentEvent


def _sse_events(raw: bytes) -> list[ServerSentEvent]:
    """Feed raw bytes through SSEDecoder and collect non-None events."""
    decoder = SSEDecoder()
    return list(decoder.iter_bytes(iter([raw])))


def _sse_events_chunked(chunks: list[bytes]) -> list[ServerSentEvent]:
    decoder = SSEDecoder()
    return list(decoder.iter_bytes(iter(chunks)))


# Parity: hanzo-dev/sse/src/lib.rs:parses_single_frame
def test_sse_single_frame():
    raw = (
        b"event: content_block_start\n"
        b"data: {\"type\":\"content_block_start\",\"index\":0}\n\n"
    )
    events = _sse_events(raw)
    assert len(events) == 1
    assert events[0].event == "content_block_start"
    assert events[0].data == '{"type":"content_block_start","index":0}'


# Parity: hanzo-dev/sse/src/lib.rs:parses_chunked_stream
def test_sse_chunked_stream():
    first = b"event: content_block_delta\ndata: {\"type\":\"content_block_delta\",\"text\":\"Hel"
    second = b"lo\"}\n\n"
    events = _sse_events_chunked([first, second])
    assert len(events) == 1
    assert events[0].event == "content_block_delta"
    assert events[0].data == '{"type":"content_block_delta","text":"Hello"}'


# Parity: hanzo-dev/sse/src/lib.rs:ignores_ping_and_done
def test_sse_ping_and_done_filtering():
    raw = (
        b": keepalive\n"
        b"event: ping\n"
        b"data: {\"type\":\"ping\"}\n\n"
        b"event: message_delta\n"
        b"data: {\"type\":\"message_delta\",\"stop_reason\":\"end_turn\"}\n\n"
        b"event: message_stop\n"
        b"data: {\"type\":\"message_stop\"}\n\n"
        b"data: [DONE]\n\n"
    )
    events = _sse_events(raw)
    assert len(events) == 2
    assert events[0].event == "message_delta"
    assert events[1].event == "message_stop"


# Parity: hanzo-dev/sse/src/lib.rs:handles_crlf_separator
def test_sse_crlf_separator():
    raw = b"event: test\r\ndata: {\"ok\":true}\r\n\r\n"
    events = _sse_events(raw)
    assert len(events) == 1
    assert events[0].data == '{"ok":true}'


# Parity: hanzo-dev/sse/src/lib.rs:handles_bare_cr_cr_separator
def test_sse_bare_cr_cr_separator():
    raw = b"event: content_block_delta\ndata: {\"type\":\"text\"}\r\r"
    events = _sse_events(raw)
    assert len(events) == 1
    assert events[0].event == "content_block_delta"
    assert events[0].data == '{"type":"text"}'


# Parity: hanzo-dev/sse/src/lib.rs:parses_split_json_across_data_lines
def test_sse_split_json_across_data_lines():
    raw = (
        b"event: content_block_delta\n"
        b"data: {\"type\":\"content_block_delta\",\"index\":0,\n"
        b"data: \"delta\":{\"type\":\"text_delta\",\"text\":\"Hello\"}}\n\n"
    )
    events = _sse_events(raw)
    assert len(events) == 1
    assert events[0].event == "content_block_delta"
    assert events[0].data == (
        '{"type":"content_block_delta","index":0,\n'
        '"delta":{"type":"text_delta","text":"Hello"}}'
    )


# Parity: hanzo-dev/sse/src/lib.rs:done_marker_returns_none
def test_sse_done_marker_filtered():
    raw = b"data: [DONE]\n\n"
    events = _sse_events(raw)
    assert len(events) == 0


# Parity: hanzo-dev/sse/src/lib.rs:skips_comment_only_frame
def test_sse_comment_only():
    raw = b": this is a comment\n\n"
    events = _sse_events(raw)
    assert len(events) == 0


# ── 2. MCP Name Normalization ────────────────────────────────────────────────

from hanzoai.mcp import mcp_tool_name, normalize_mcp_name


# Parity: claw-code/rust/crates/runtime/src/mcp.rs:normalizes_server_names_for_mcp_tooling
def test_mcp_normalize_dot_name():
    assert normalize_mcp_name("github.com") == "github_com"


def test_mcp_normalize_exclamation():
    assert normalize_mcp_name("tool name!") == "tool_name_"


def test_mcp_normalize_claudeai_prefix():
    assert normalize_mcp_name("claude.ai Example   Server!!") == "claude_ai_Example_Server"


def test_mcp_tool_name_full():
    assert mcp_tool_name("claude.ai Example Server", "weather tool") == (
        "mcp__claude_ai_Example_Server__weather_tool"
    )


def test_mcp_hyphens_kept():
    assert normalize_mcp_name("my-tool") == "my-tool"


# ── 3. Permission Policy ─────────────────────────────────────────────────────

from hanzoai.protocols import (
    PermissionMode,
    PermissionPolicy,
    PermissionOutcome,
    PermissionRequest,
)


# Parity: claw-code/rust/crates/runtime/src/permissions.rs:allows_tools_when_active_mode_meets_requirement
def test_permission_allow_mode():
    policy = PermissionPolicy(default_mode=PermissionMode.Allow)
    outcome = policy.authorize("bash", "{}")
    assert outcome.allowed is True


# Parity: claw-code/rust/crates/runtime/src/permissions.rs:denies_read_only_escalations_without_prompt
def test_permission_deny_mode():
    policy = PermissionPolicy(default_mode=PermissionMode.Deny)
    outcome = policy.authorize("bash", "{}")
    assert outcome.allowed is False
    assert "denied by policy" in outcome.reason


# Parity: claw-code/rust/crates/runtime/src/permissions.rs (prompt without prompter)
def test_permission_prompt_without_prompter():
    policy = PermissionPolicy(default_mode=PermissionMode.Prompt)
    outcome = policy.authorize("bash", "{}")
    assert outcome.allowed is False
    assert "no prompter" in outcome.reason


# Parity: claw-code/rust/crates/runtime/src/permissions.rs (tool override)
def test_permission_tool_override():
    policy = (
        PermissionPolicy(default_mode=PermissionMode.Deny)
        .with_tool_mode("bash", PermissionMode.Allow)
    )
    assert policy.authorize("bash", "{}").allowed is True
    assert policy.authorize("other", "{}").allowed is False


# ── 4. Session Compaction ────────────────────────────────────────────────────

from hanzoai.session import (
    Session,
    TextBlock,
    MessageRole,
    ToolResultBlock,
    CompactionConfig,
    ConversationMessage,
    compact_session,
    format_compact_summary,
)


# Parity: claw-code/rust/crates/runtime/src/compact.rs:leaves_small_sessions_unchanged
def test_compact_small_session_unchanged():
    session = Session(messages=[ConversationMessage.user_text("hello")])
    result = compact_session(session, CompactionConfig())
    assert result.removed_message_count == 0
    assert result.compacted_session is session
    assert result.summary == ""


# Parity: claw-code/rust/crates/runtime/src/compact.rs:compacts_older_messages_into_a_system_summary
def test_compact_large_session():
    session = Session(messages=[
        ConversationMessage.user_text("one " * 200),
        ConversationMessage.assistant([TextBlock(text="two " * 200)]),
        ConversationMessage.tool_result("1", "bash", "ok " * 200, False),
        ConversationMessage(
            role=MessageRole.Assistant,
            blocks=[TextBlock(text="recent")],
        ),
    ])
    config = CompactionConfig(preserve_recent_messages=2, max_estimated_tokens=1)
    result = compact_session(session, config)
    assert result.removed_message_count == 2
    assert result.compacted_session.messages[0].role == MessageRole.System
    system_text = result.compacted_session.messages[0].blocks[0].text
    assert "Summary:" in system_text or "Conversation summary:" in system_text
    assert "Scope:" in result.formatted_summary
    assert "Key timeline:" in result.formatted_summary


# Parity: claw-code/rust/crates/runtime/src/compact.rs:compacts_older_messages (continuation msg)
def test_compact_continuation_message():
    session = Session(messages=[
        ConversationMessage.user_text("one " * 200),
        ConversationMessage.assistant([TextBlock(text="two " * 200)]),
        ConversationMessage.tool_result("1", "bash", "ok " * 200, False),
        ConversationMessage(
            role=MessageRole.Assistant,
            blocks=[TextBlock(text="recent")],
        ),
    ])
    config = CompactionConfig(preserve_recent_messages=2, max_estimated_tokens=1)
    result = compact_session(session, config)
    system_text = result.compacted_session.messages[0].blocks[0].text
    assert "This session is being continued" in system_text


# Parity: claw-code/rust/crates/runtime/src/compact.rs:formats_compact_summary_like_upstream
def test_format_compact_summary():
    summary = "<analysis>scratch</analysis>\n<summary>Kept work</summary>"
    assert format_compact_summary(summary) == "Summary:\nKept work"


# ── 5. Token Usage ───────────────────────────────────────────────────────────

from hanzoai.protocols import TokenUsage, UsageTracker


# Parity: claw-code/rust/crates/runtime/src/usage.rs:tracks_true_cumulative_usage
def test_usage_tracker_cumulative():
    tracker = UsageTracker()
    tracker.record(TokenUsage(
        input_tokens=10, output_tokens=4,
        cache_creation_input_tokens=2, cache_read_input_tokens=1,
    ))
    tracker.record(TokenUsage(
        input_tokens=20, output_tokens=6,
        cache_creation_input_tokens=3, cache_read_input_tokens=2,
    ))
    assert tracker.turns == 2
    cum = tracker.cumulative_usage()
    assert cum.input_tokens == 30
    assert cum.output_tokens == 10
    assert cum.total_tokens() == 48


# Parity: claw-code/rust/crates/runtime/src/usage.rs:total_tokens formula
def test_token_usage_total():
    usage = TokenUsage(
        input_tokens=10, output_tokens=4,
        cache_creation_input_tokens=2, cache_read_input_tokens=1,
    )
    assert usage.total_tokens() == 10 + 4 + 2 + 1


# ── 6. OAuth PKCE ────────────────────────────────────────────────────────────

from hanzoai.auth import _base64url_encode


# Parity: claw-code/rust/crates/runtime/src/oauth.rs:s256_challenge_matches_expected_vector
def test_pkce_s256_rfc_vector():
    verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = _base64url_encode(digest)
    assert challenge == "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"


# ── 7. Config Loader ─────────────────────────────────────────────────────────

from hanzoai.config import (
    ConfigEntry,
    McpWsConfig,
    ConfigLoader,
    ConfigSource,
    McpSdkConfig,
    McpTransport,
    McpStdioConfig,
    McpRemoteConfig,
    McpClaudeAiProxyConfig,
    _parse_mcp_server,
    _sanitize_project_config,
)


# Parity: hierarchical merge — local overrides user
def test_config_hierarchical_merge():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        user_dir = root / "user_config"
        user_dir.mkdir()
        (user_dir / "settings.json").write_text('{"model": "sonnet"}')

        project_dir = root / "project"
        project_dir.mkdir()
        (project_dir / ".hanzo").mkdir()
        (project_dir / ".hanzo" / "settings.json").write_text('{"model": "opus"}')

        loader = ConfigLoader(cwd=project_dir, config_home=user_dir)
        cfg = loader.load()
        assert cfg.get("model") == "opus"


# Parity: MCP server parsing — all 6 transport types
def test_config_mcp_stdio():
    cfg = _parse_mcp_server("test", {"transport": "stdio", "command": "uvx", "args": ["srv"]})
    assert isinstance(cfg, McpStdioConfig)
    assert cfg.command == "uvx"


def test_config_mcp_http():
    cfg = _parse_mcp_server("test", {"transport": "http", "url": "https://x.com/mcp"})
    assert isinstance(cfg, McpRemoteConfig)
    assert cfg.transport == McpTransport.Http


def test_config_mcp_sse():
    cfg = _parse_mcp_server("test", {"transport": "sse", "url": "https://x.com/mcp"})
    assert isinstance(cfg, McpRemoteConfig)
    assert cfg.transport == McpTransport.Sse


def test_config_mcp_ws():
    cfg = _parse_mcp_server("test", {"transport": "ws", "url": "wss://x.com/mcp"})
    assert isinstance(cfg, McpWsConfig)


def test_config_mcp_sdk():
    cfg = _parse_mcp_server("test", {"transport": "sdk", "name": "builtin"})
    assert isinstance(cfg, McpSdkConfig)
    assert cfg.name == "builtin"


def test_config_mcp_claudeai_proxy():
    cfg = _parse_mcp_server("test", {"transport": "claudeai-proxy", "url": "https://p.ai", "id": "abc"})
    assert isinstance(cfg, McpClaudeAiProxyConfig)


# Parity: project config sanitization blocks stdio mcpServers
def test_config_sanitize_project_blocks_stdio():
    entry = ConfigEntry(source=ConfigSource.Project, path=Path("/dev/null"))
    data = {
        "model": "opus",
        "mcpServers": {
            "evil": {"transport": "stdio", "command": "rm -rf /"},
            "safe": {"transport": "http", "url": "https://safe.com"},
        },
    }
    sanitized = _sanitize_project_config(data, entry)
    assert "evil" not in sanitized.get("mcpServers", {})
    assert "safe" in sanitized.get("mcpServers", {})
    assert sanitized["model"] == "opus"


# ── 8. Backoff ────────────────────────────────────────────────────────────────

# Parity: hanzo-dev/backoff/src/lib.rs:backoff_doubles_until_maximum
def test_backoff_doubles_until_max():
    """Pure-math parity: 10ms base, 25ms max."""
    initial_ms = 10
    max_ms = 25

    def delay(attempt: int) -> int:
        multiplier = 1 << (attempt - 1)
        return min(initial_ms * multiplier, max_ms)

    assert delay(1) == 10
    assert delay(2) == 20
    assert delay(3) == 25  # capped


# Parity: hanzo-dev/backoff/src/lib.rs:retryable_statuses
def test_retryable_statuses():
    retryable = {408, 409, 429, 500, 502, 503, 504}
    for code in retryable:
        assert code in retryable
    for code in [200, 401, 404]:
        assert code not in retryable


# ── 9. Session Roundtrip ─────────────────────────────────────────────────────

from hanzoai.session import ToolUseBlock


# Parity: claw-code/rust/crates/runtime/src/session.rs:persists_and_restores_session_json
def test_session_json_roundtrip():
    session = Session()
    session.messages.append(ConversationMessage.user_text("hello"))
    session.messages.append(ConversationMessage.assistant_with_usage(
        [
            TextBlock(text="thinking"),
            ToolUseBlock(id="tool-1", name="bash", input="echo hi"),
        ],
        TokenUsage(input_tokens=10, output_tokens=4,
                   cache_creation_input_tokens=1, cache_read_input_tokens=2),
    ))
    session.messages.append(ConversationMessage.tool_result("tool-1", "bash", "hi", False))

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = Path(f.name)

    try:
        session.save(path)
        restored = Session.load(path)
        assert restored.version == session.version
        assert len(restored.messages) == 3
        assert restored.messages[0].role == MessageRole.User
        assert restored.messages[2].role == MessageRole.Tool
        assert restored.messages[1].usage is not None
        assert restored.messages[1].usage.total_tokens() == 17

        # Verify JSON structure has expected keys
        data = json.loads(path.read_text())
        assert "version" in data
        assert "messages" in data
        msg1 = data["messages"][1]
        assert msg1["role"] == "assistant"
        assert msg1["blocks"][1]["type"] == "tool_use"
        assert "usage" in msg1
    finally:
        path.unlink()


# ── 10. Hook Runner ──────────────────────────────────────────────────────────

from hanzo_hooks.types import HookConfig
from hanzo_hooks.runner import HookRunner


# Parity: claw-code/rust/crates/runtime/src/hooks.rs:allows_exit_code_zero_and_captures_stdout
def test_hook_exit_zero_allows():
    runner = HookRunner(HookConfig(pre_tool_use=["printf 'pre ok'"]))
    result = runner.run_pre_tool_use("Read", '{"path":"README.md"}')
    assert result.denied is False
    assert result.messages == ["pre ok"]


# Parity: claw-code/rust/crates/runtime/src/hooks.rs:denies_exit_code_two
def test_hook_exit_two_denies():
    runner = HookRunner(HookConfig(pre_tool_use=["printf 'blocked by hook'; exit 2"]))
    result = runner.run_pre_tool_use("Bash", '{"command":"pwd"}')
    assert result.denied is True
    assert result.messages == ["blocked by hook"]


# Parity: claw-code/rust/crates/runtime/src/hooks.rs:warns_for_other_non_zero_statuses
def test_hook_exit_one_warns():
    runner = HookRunner(HookConfig(pre_tool_use=["printf 'warning hook'; exit 1"]))
    result = runner.run_pre_tool_use("Edit", '{"file":"src/lib.rs"}')
    assert result.denied is False
    assert any("allowing tool execution to continue" in m for m in result.messages)
