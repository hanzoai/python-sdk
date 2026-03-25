"""Tests for memory service namespace, key-based retrieval, tags, ttl, and coordination."""

import asyncio
import json
import time
from datetime import datetime, timedelta, timezone

import pytest


@pytest.fixture
async def memory_service():
    """Create a PluginMemoryService with in-memory SQLite for testing."""
    from hanzo_mcp.memory_service import PluginMemoryService
    from hanzo_mcp.backends.sqlite_plugin import SQLiteBackendPlugin

    svc = PluginMemoryService()
    # Use true in-memory db — each test gets a fresh database
    plugin = SQLiteBackendPlugin(db_path=SQLiteBackendPlugin.IN_MEMORY)
    svc.registry._plugins = {"sqlite": plugin}
    svc.registry._active_plugins = ["sqlite"]
    await svc.registry.initialize_all_active()
    svc._initialized = True
    yield svc
    await svc.shutdown()


class TestNamespaceSupport:
    """Test namespace parameter on memory operations."""

    @pytest.mark.asyncio
    async def test_store_with_namespace(self, memory_service):
        mid = await memory_service.store_memory(
            content="blue agent report",
            metadata={"type": "report"},
            namespace="blue-red",
        )
        assert mid

    @pytest.mark.asyncio
    async def test_store_default_namespace(self, memory_service):
        mid = await memory_service.store_memory(
            content="plain memory",
            metadata={},
        )
        assert mid

    @pytest.mark.asyncio
    async def test_list_memories_filters_by_namespace(self, memory_service):
        await memory_service.store_memory(content="ns1", metadata={}, namespace="ns1")
        await memory_service.store_memory(content="ns2", metadata={}, namespace="ns2")
        await memory_service.store_memory(content="ns1-b", metadata={}, namespace="ns1")

        results = await memory_service.list_memories(namespace="ns1")
        assert len(results) == 2
        for r in results:
            assert r["metadata"].get("namespace") == "ns1"

    @pytest.mark.asyncio
    async def test_list_memories_no_filter(self, memory_service):
        await memory_service.store_memory(content="a", metadata={}, namespace="x")
        await memory_service.store_memory(content="b", metadata={}, namespace="y")
        results = await memory_service.list_memories()
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_namespaces_returns_counts(self, memory_service):
        await memory_service.store_memory(content="a", metadata={}, namespace="alpha")
        await memory_service.store_memory(content="b", metadata={}, namespace="alpha")
        await memory_service.store_memory(content="c", metadata={}, namespace="beta")

        ns = await memory_service.namespaces()
        assert ns["alpha"] == 2
        assert ns["beta"] == 1

    @pytest.mark.asyncio
    async def test_clear_namespace(self, memory_service):
        await memory_service.store_memory(content="a", metadata={}, namespace="temp")
        await memory_service.store_memory(content="b", metadata={}, namespace="keep")

        deleted = await memory_service.clear(namespace="temp")
        assert deleted >= 1

        results = await memory_service.list_memories()
        assert len(results) == 1
        assert results[0]["metadata"].get("namespace") == "keep"

    @pytest.mark.asyncio
    async def test_clear_all(self, memory_service):
        await memory_service.store_memory(content="a", metadata={}, namespace="x")
        await memory_service.store_memory(content="b", metadata={}, namespace="y")

        deleted = await memory_service.clear()
        assert deleted >= 2

        results = await memory_service.list_memories()
        assert len(results) == 0


class TestKeyBasedRetrieval:
    """Test key-based store and get_by_key."""

    @pytest.mark.asyncio
    async def test_store_with_key(self, memory_service):
        mid = await memory_service.store_memory(
            content="keyed content",
            metadata={"extra": "data"},
            key="my-key-1",
            namespace="test",
        )
        assert mid

    @pytest.mark.asyncio
    async def test_get_by_key_exact(self, memory_service):
        await memory_service.store_memory(
            content="target", metadata={}, key="exact-key", namespace="ns"
        )
        await memory_service.store_memory(
            content="other", metadata={}, key="other-key", namespace="ns"
        )

        result = await memory_service.get_by_key(key="exact-key", namespace="ns")
        assert result is not None
        assert result["content"] == "target"

    @pytest.mark.asyncio
    async def test_get_by_key_wildcard(self, memory_service):
        await memory_service.store_memory(
            content="report-1", metadata={}, key="blue-report-100", namespace="blue-red"
        )
        await memory_service.store_memory(
            content="report-2", metadata={}, key="blue-report-200", namespace="blue-red"
        )
        await memory_service.store_memory(
            content="other", metadata={}, key="red-report-100", namespace="blue-red"
        )

        results = await memory_service.get_by_key(
            key="blue-report-*", namespace="blue-red"
        )
        assert isinstance(results, list)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_get_by_key_not_found(self, memory_service):
        result = await memory_service.get_by_key(key="nonexistent", namespace="ns")
        assert result is None

    @pytest.mark.asyncio
    async def test_append_mode(self, memory_service):
        await memory_service.store_memory(
            content="line1", metadata={}, key="append-key", namespace="test"
        )
        await memory_service.store_memory(
            content="\nline2", metadata={}, key="append-key", namespace="test", append=True
        )

        result = await memory_service.get_by_key(key="append-key", namespace="test")
        assert "line1" in result["content"]
        assert "line2" in result["content"]


class TestTagsSupport:
    """Test tags parameter on memory operations."""

    @pytest.mark.asyncio
    async def test_store_with_tags(self, memory_service):
        mid = await memory_service.store_memory(
            content="tagged memory",
            metadata={},
            tags=["blue", "report"],
        )
        assert mid

    @pytest.mark.asyncio
    async def test_list_memories_filter_by_tag(self, memory_service):
        await memory_service.store_memory(content="a", metadata={}, tags=["blue"])
        await memory_service.store_memory(content="b", metadata={}, tags=["red"])
        await memory_service.store_memory(content="c", metadata={}, tags=["blue", "red"])

        results = await memory_service.list_memories(tag="blue")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_tag_memory(self, memory_service):
        mid = await memory_service.store_memory(content="taggable", metadata={})
        ok = await memory_service.tag_memory(mid, "new-tag")
        assert ok

        results = await memory_service.list_memories(tag="new-tag")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_untag_memory(self, memory_service):
        mid = await memory_service.store_memory(
            content="untaggable", metadata={}, tags=["remove-me"]
        )
        ok = await memory_service.untag_memory(mid, "remove-me")
        assert ok

        results = await memory_service.list_memories(tag="remove-me")
        assert len(results) == 0


class TestTTLSupport:
    """Test TTL (time-to-live) on memories."""

    @pytest.mark.asyncio
    async def test_store_with_ttl(self, memory_service):
        # TTL in the past = already expired
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        mid = await memory_service.store_memory(
            content="ephemeral", metadata={}, ttl=past
        )
        assert mid

        # Should not appear in list (expired)
        results = await memory_service.list_memories()
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_store_with_future_ttl(self, memory_service):
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        mid = await memory_service.store_memory(
            content="long-lived", metadata={}, ttl=future
        )

        results = await memory_service.list_memories()
        assert len(results) == 1


class TestStats:
    """Test stats method."""

    @pytest.mark.asyncio
    async def test_stats_empty(self, memory_service):
        s = await memory_service.stats()
        assert s["count"] == 0
        assert s["namespaces"] == {}

    @pytest.mark.asyncio
    async def test_stats_with_data(self, memory_service):
        await memory_service.store_memory(content="a", metadata={}, namespace="ns1")
        await memory_service.store_memory(content="b", metadata={}, namespace="ns1")
        await memory_service.store_memory(content="c", metadata={}, namespace="ns2")

        s = await memory_service.stats()
        assert s["count"] == 3
        assert s["namespaces"]["ns1"] == 2
        assert s["namespaces"]["ns2"] == 1


class TestHistory:
    """Test version history for a key."""

    @pytest.mark.asyncio
    async def test_history_shows_versions(self, memory_service):
        await memory_service.store_memory(
            content="v1", metadata={}, key="versioned", namespace="test"
        )
        # Store again with same key but NOT append — creates new entry
        await memory_service.store_memory(
            content="v2", metadata={}, key="versioned", namespace="test"
        )

        versions = await memory_service.history(key="versioned", namespace="test")
        assert len(versions) == 2


class TestExportImport:
    """Test export and import."""

    @pytest.mark.asyncio
    async def test_export_import_round_trip(self, memory_service):
        await memory_service.store_memory(
            content="exportable", metadata={"x": 1}, namespace="exp"
        )

        data = await memory_service.export_memories(namespace="exp")
        assert len(data) == 1
        assert data[0]["content"] == "exportable"

        # Clear and re-import
        await memory_service.clear()
        imported = await memory_service.import_memories(data)
        assert imported == 1

        results = await memory_service.list_memories(namespace="exp")
        assert len(results) == 1


class TestBackwardCompatibility:
    """Verify existing callers still work."""

    @pytest.mark.asyncio
    async def test_store_memory_original_signature(self, memory_service):
        mid = await memory_service.store_memory(
            content="old style",
            metadata={"type": "general"},
            user_id="u1",
            project_id="p1",
        )
        assert mid

    @pytest.mark.asyncio
    async def test_retrieve_memory_original_signature(self, memory_service):
        await memory_service.store_memory(
            content="findme", metadata={}, user_id="u1", project_id="p1"
        )
        results = await memory_service.retrieve_memory(
            query="findme", user_id="u1", project_id="p1"
        )
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_delete_memory_original_signature(self, memory_service):
        mid = await memory_service.store_memory(
            content="deleteme", metadata={}, user_id="u1", project_id="p1"
        )
        ok = await memory_service.delete_memory(
            memory_id=mid, user_id="u1", project_id="p1"
        )
        assert ok


class TestBlueRedChannel:
    """Test the coordination convenience class."""

    @pytest.mark.asyncio
    async def test_blue_report(self, memory_service):
        from hanzo_mcp.coordination import BlueRedChannel

        channel = BlueRedChannel(memory_service)
        key = await channel.blue_report({"analysis": "code looks good"})
        assert key.startswith("blue-report-")

    @pytest.mark.asyncio
    async def test_red_report(self, memory_service):
        from hanzo_mcp.coordination import BlueRedChannel

        channel = BlueRedChannel(memory_service)
        key = await channel.red_report({"issues": ["bug in auth"]})
        assert key.startswith("red-report-")

    @pytest.mark.asyncio
    async def test_blue_red_cycle(self, memory_service):
        from hanzo_mcp.coordination import BlueRedChannel

        channel = BlueRedChannel(memory_service)

        # Blue reports
        await channel.blue_report({"analysis": "reviewed auth module"}, scope="auth")

        # Red reads and reports findings
        blue_report = await channel.get_latest_blue_report()
        assert blue_report is not None
        assert "reviewed auth module" in blue_report["content"]

        await channel.red_report({"issues": ["SQL injection risk"]}, scope="auth")

        # Blue reads red findings
        red_findings = await channel.get_latest_red_findings()
        assert red_findings is not None
        assert "SQL injection risk" in red_findings["content"]

        # Blue responds with fixes
        await channel.blue_response({"fixes": ["added parameterized queries"]})

        # Red re-reviews
        await channel.red_rereview({"verdict": "resolved"})

        # Get full cycle
        cycle = await channel.get_full_cycle()
        assert len(cycle) == 4

    @pytest.mark.asyncio
    async def test_get_latest_blue_report_empty(self, memory_service):
        from hanzo_mcp.coordination import BlueRedChannel

        channel = BlueRedChannel(memory_service)
        result = await channel.get_latest_blue_report()
        assert result is None

    @pytest.mark.asyncio
    async def test_get_latest_red_findings_empty(self, memory_service):
        from hanzo_mcp.coordination import BlueRedChannel

        channel = BlueRedChannel(memory_service)
        result = await channel.get_latest_red_findings()
        assert result is None
