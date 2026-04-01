"""Tests for hanzo_hooks."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from hanzo_hooks import HookConfig, HookEvent, HookRunner, HookRunResult


class TestHookEvent:
    def test_values(self):
        assert HookEvent.PreToolUse.value == "PreToolUse"
        assert HookEvent.PostToolUse.value == "PostToolUse"


class TestHookRunResult:
    def test_allow(self):
        r = HookRunResult.allow()
        assert not r.denied
        assert r.messages == []

    def test_allow_with_messages(self):
        r = HookRunResult.allow(["msg1", "msg2"])
        assert not r.denied
        assert r.messages == ["msg1", "msg2"]

    def test_denied(self):
        r = HookRunResult(denied=True, messages=["blocked"])
        assert r.denied
        assert r.messages == ["blocked"]

    def test_to_permission_outcome_allow(self):
        r = HookRunResult.allow()
        outcome = r.to_permission_outcome()
        assert outcome.allowed is True

    def test_to_permission_outcome_deny(self):
        r = HookRunResult(denied=True, messages=["reason A", "reason B"])
        outcome = r.to_permission_outcome()
        assert outcome.allowed is False
        assert "reason A" in outcome.reason
        assert "reason B" in outcome.reason


class TestHookConfig:
    def test_from_dict(self):
        cfg = HookConfig.from_dict({
            "pre_tool_use": ["echo pre"],
            "post_tool_use": ["echo post"],
        })
        assert cfg.pre_tool_use == ["echo pre"]
        assert cfg.post_tool_use == ["echo post"]

    def test_from_dict_camel_case(self):
        cfg = HookConfig.from_dict({
            "PreToolUse": ["echo pre"],
            "PostToolUse": ["echo post"],
        })
        assert cfg.pre_tool_use == ["echo pre"]
        assert cfg.post_tool_use == ["echo post"]

    def test_from_dict_empty(self):
        cfg = HookConfig.from_dict({})
        assert cfg.pre_tool_use == []
        assert cfg.post_tool_use == []

    def test_from_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"hooks": {"pre_tool_use": ["echo hi"]}}, f)
            f.flush()
            cfg = HookConfig.from_json(f.name)
        assert cfg.pre_tool_use == ["echo hi"]
        assert cfg.post_tool_use == []
        Path(f.name).unlink()


class TestHookRunner:
    def test_no_commands_returns_allow(self):
        runner = HookRunner(HookConfig())
        result = runner.run_pre_tool_use("Read", '{"path":"README.md"}')
        assert not result.denied
        assert result.messages == []

    def test_exit_zero_captures_stdout(self):
        runner = HookRunner(HookConfig(pre_tool_use=["printf 'pre ok'"]))
        result = runner.run_pre_tool_use("Read", '{"path":"README.md"}')
        assert not result.denied
        assert result.messages == ["pre ok"]

    def test_exit_two_denies(self):
        runner = HookRunner(HookConfig(pre_tool_use=["printf 'blocked'; exit 2"]))
        result = runner.run_pre_tool_use("Bash", '{"command":"pwd"}')
        assert result.denied
        assert result.messages == ["blocked"]

    def test_exit_two_without_stdout_uses_default_message(self):
        runner = HookRunner(HookConfig(pre_tool_use=["exit 2"]))
        result = runner.run_pre_tool_use("Bash", '{"command":"pwd"}')
        assert result.denied
        assert "denied" in result.messages[0]
        assert "Bash" in result.messages[0]

    def test_other_exit_code_warns_but_allows(self):
        runner = HookRunner(HookConfig(pre_tool_use=["printf 'oops'; exit 1"]))
        result = runner.run_pre_tool_use("Edit", '{"file":"lib.py"}')
        assert not result.denied
        assert len(result.messages) == 1
        assert "allowing tool execution to continue" in result.messages[0]

    def test_short_circuit_on_deny(self):
        runner = HookRunner(HookConfig(pre_tool_use=[
            "printf 'first ok'",
            "printf 'deny'; exit 2",
            "printf 'never reached'",
        ]))
        result = runner.run_pre_tool_use("Bash", '{}')
        assert result.denied
        assert result.messages == ["first ok", "deny"]

    def test_post_tool_use(self):
        runner = HookRunner(HookConfig(post_tool_use=["printf 'post ok'"]))
        result = runner.run_post_tool_use("Read", '{}', "file contents", is_error=False)
        assert not result.denied
        assert result.messages == ["post ok"]

    def test_env_vars_passed(self):
        runner = HookRunner(HookConfig(pre_tool_use=[
            'printf "%s %s" "$HOOK_EVENT" "$HOOK_TOOL_NAME"'
        ]))
        result = runner.run_pre_tool_use("Bash", '{"command":"ls"}')
        assert not result.denied
        assert result.messages == ["PreToolUse Bash"]

    def test_stdin_payload(self):
        runner = HookRunner(HookConfig(pre_tool_use=[
            """python3 -c "import sys, json; d=json.load(sys.stdin); print(d['tool_name'])" """
        ]))
        result = runner.run_pre_tool_use("Grep", '{"pattern":"foo"}')
        assert not result.denied
        assert result.messages == ["Grep"]

    def test_multiple_commands_collect_messages(self):
        runner = HookRunner(HookConfig(pre_tool_use=[
            "printf 'msg1'",
            "printf 'msg2'",
        ]))
        result = runner.run_pre_tool_use("Read", '{}')
        assert not result.denied
        assert result.messages == ["msg1", "msg2"]

    def test_from_settings(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"hooks": {"pre_tool_use": ["printf 'from settings'"]}}, f)
            f.flush()
            runner = HookRunner.from_settings(f.name)
        result = runner.run_pre_tool_use("Bash", '{}')
        assert not result.denied
        assert result.messages == ["from settings"]
        Path(f.name).unlink()
