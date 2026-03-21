"""Playground client and types test suite.

Covers type construction, serialization, PlaygroundClient instantiation,
and URL/header configuration.
"""

import json
from dataclasses import asdict

import pytest
import httpx

from hanzo_zap import (
    PlaygroundClient,
    AgentEvent,
    AgentInfo,
    CommitInfo,
    EventMsg,
    FileChange,
    RealtimeAudioFrame,
    Submission,
)


# -- Playground types --------------------------------------------------------


class TestSubmission:
    def test_fields(self):
        s = Submission(id="sub-1", op={"type": "inject", "message": "hi"})
        assert s.id == "sub-1"
        assert s.op["type"] == "inject"
        assert s.trace is None

    def test_with_trace(self):
        s = Submission(
            id="sub-2",
            op={"type": "broadcast"},
            trace={"request_id": "abc"},
        )
        assert s.trace["request_id"] == "abc"

    def test_serializes(self):
        s = Submission(id="sub-3", op={"type": "noop"})
        d = asdict(s)
        assert d == {"id": "sub-3", "op": {"type": "noop"}, "trace": None}


class TestEventMsg:
    def test_defaults(self):
        e = EventMsg(type="turn_started")
        assert e.type == "turn_started"
        assert e.data == {}
        assert e.raw is None

    def test_with_data(self):
        e = EventMsg(type="agent_message", data={"text": "hello"})
        assert e.data["text"] == "hello"

    def test_with_raw(self):
        e = EventMsg(type="binary", raw=b"\x00\x01")
        assert e.raw == b"\x00\x01"

    def test_serializes(self):
        e = EventMsg(type="turn_completed", data={"tokens": 42})
        d = asdict(e)
        assert d["type"] == "turn_completed"
        assert d["data"]["tokens"] == 42


class TestAgentEvent:
    def test_required_fields(self):
        ae = AgentEvent(type="message", space_id="sp-1", agent_id="ag-1")
        assert ae.type == "message"
        assert ae.space_id == "sp-1"
        assert ae.agent_id == "ag-1"
        assert ae.agent_name == ""
        assert ae.timestamp == ""
        assert ae.data == {}

    def test_full(self):
        ae = AgentEvent(
            type="tool_call",
            space_id="sp-1",
            agent_id="ag-2",
            agent_name="coder",
            timestamp="2026-03-19T00:00:00Z",
            data={"tool": "read_file", "path": "/tmp/x"},
        )
        assert ae.agent_name == "coder"
        assert ae.data["tool"] == "read_file"


class TestAgentInfo:
    def test_defaults(self):
        ai = AgentInfo(agent_id="ag-1")
        assert ai.agent_id == "ag-1"
        assert ai.did == ""
        assert ai.status == "offline"
        assert ai.capabilities == []
        assert ai.model == ""

    def test_full(self):
        ai = AgentInfo(
            agent_id="ag-2",
            did="did:key:abc",
            space_id="sp-1",
            display_name="Coder",
            status="online",
            capabilities=[{"name": "code"}],
            model="zen-405b",
        )
        assert ai.display_name == "Coder"
        assert ai.status == "online"
        assert len(ai.capabilities) == 1

    def test_serializes(self):
        ai = AgentInfo(agent_id="ag-3", model="zen-32b")
        d = asdict(ai)
        assert d["agent_id"] == "ag-3"
        assert d["model"] == "zen-32b"


class TestRealtimeAudioFrame:
    def test_defaults(self):
        f = RealtimeAudioFrame(data="AAAA")
        assert f.data == "AAAA"
        assert f.sample_rate == 16000
        assert f.num_channels == 1

    def test_custom(self):
        f = RealtimeAudioFrame(data="base64data", sample_rate=44100, num_channels=2)
        assert f.sample_rate == 44100
        assert f.num_channels == 2


class TestFileChange:
    def test_fields(self):
        fc = FileChange(path="src/main.py", status="modified")
        assert fc.path == "src/main.py"
        assert fc.status == "modified"


class TestCommitInfo:
    def test_fields(self):
        ci = CommitInfo(
            hash="abc123",
            message="fix: resolve issue",
            author="Test",
            email="test@example.com",
            timestamp="2026-03-19T00:00:00Z",
        )
        assert ci.hash == "abc123"
        assert ci.message == "fix: resolve issue"
        assert ci.author == "Test"
        assert ci.email == "test@example.com"

    def test_serializes(self):
        ci = CommitInfo(
            hash="def456",
            message="feat: add playground",
            author="Dev",
            email="dev@hanzo.ai",
            timestamp="2026-03-19T12:00:00Z",
        )
        d = asdict(ci)
        assert d["hash"] == "def456"
        assert d["author"] == "Dev"


# -- PlaygroundClient --------------------------------------------------------


class TestPlaygroundClient:
    def test_default_url(self):
        pc = PlaygroundClient()
        assert pc.base_url == "http://localhost:8080"

    def test_custom_url(self):
        pc = PlaygroundClient(base_url="https://playground.hanzo.ai/")
        assert pc.base_url == "https://playground.hanzo.ai"

    def test_trailing_slash_stripped(self):
        pc = PlaygroundClient(base_url="http://localhost:9090/")
        assert pc.base_url == "http://localhost:9090"

    def test_no_auth_header_without_token(self):
        pc = PlaygroundClient()
        assert "Authorization" not in pc._client.headers

    def test_auth_header_with_token(self):
        pc = PlaygroundClient(token="test-token-123")
        assert pc._client.headers["Authorization"] == "Bearer test-token-123"

    def test_timeout(self):
        pc = PlaygroundClient()
        assert pc._client.timeout.connect == 30.0

    @pytest.mark.asyncio
    async def test_context_manager(self):
        async with PlaygroundClient() as pc:
            assert pc.base_url == "http://localhost:8080"
        # client should be closed after exit
        assert pc._client.is_closed


# -- Import sanity -----------------------------------------------------------


class TestImports:
    """Verify all new symbols are importable from hanzo_zap top-level."""

    def test_playground_client(self):
        from hanzo_zap import PlaygroundClient
        assert PlaygroundClient is not None

    def test_all_types(self):
        from hanzo_zap import (
            Submission,
            EventMsg,
            AgentEvent,
            AgentInfo,
            RealtimeAudioFrame,
            FileChange,
            CommitInfo,
        )
        # All should be callable dataclasses
        assert callable(Submission)
        assert callable(EventMsg)
        assert callable(AgentEvent)
        assert callable(AgentInfo)
        assert callable(RealtimeAudioFrame)
        assert callable(FileChange)
        assert callable(CommitInfo)

    def test_existing_exports_still_work(self):
        from hanzo_zap import (
            ZapClient,
            ZapServer,
            ApprovalPolicy,
            SandboxPolicy,
            MessageType,
            Tool,
            ToolCall,
            ToolResult,
            ServerInfo,
            ClientInfo,
        )
        assert ZapClient is not None
        assert ZapServer is not None

    def test_version_bumped(self):
        import hanzo_zap
        assert hanzo_zap.__version__ == "0.7.0"
