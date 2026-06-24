"""S3Tool test suite — action routing, validation, client wiring."""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from hanzo_tools.s3.s3_tool import S3Tool


@pytest.fixture
def tool():
    return S3Tool()


@pytest.fixture
def ctx():
    return MagicMock()


def _patch_client(client):
    return patch("hanzo_tools.s3.s3_tool._get_client", return_value=client)


class TestProperties:
    def test_name(self, tool):
        assert tool.name == "s3"

    def test_description_sections(self, tool):
        for section in ("Bucket actions", "Object actions"):
            assert section in tool.description


class TestActionRouting:
    @pytest.mark.asyncio
    async def test_unknown_action_returns_error(self, tool, ctx):
        result = json.loads(await tool.call(ctx, action="bogus"))
        assert "Unknown action" in result["error"]

    @pytest.mark.asyncio
    async def test_unknown_action_lists_available(self, tool, ctx):
        result = json.loads(await tool.call(ctx, action="bogus"))
        assert set(result["available"]) == {
            "buckets", "make_bucket", "remove_bucket",
            "objects", "stat", "remove_object", "presign",
        }


class TestBuckets:
    @pytest.mark.asyncio
    async def test_buckets(self, tool, ctx):
        client = MagicMock()
        bucket = MagicMock(name="hanzo-space", creation_date=datetime(2026, 1, 1))
        bucket.name = "hanzo-space"
        client.list_buckets.return_value = [bucket]
        with _patch_client(client):
            result = json.loads(await tool.call(ctx, action="buckets"))
        assert result["count"] == 1
        assert result["buckets"][0]["name"] == "hanzo-space"

    @pytest.mark.asyncio
    async def test_make_bucket_requires_name(self, tool, ctx):
        result = json.loads(await tool.call(ctx, action="make_bucket"))
        assert "Required" in result["error"]

    @pytest.mark.asyncio
    async def test_make_bucket(self, tool, ctx):
        client = MagicMock()
        with _patch_client(client):
            result = json.loads(await tool.call(ctx, action="make_bucket", bucket="b1"))
        client.make_bucket.assert_called_once_with("b1")
        assert result["action"] == "created"

    @pytest.mark.asyncio
    async def test_remove_bucket(self, tool, ctx):
        client = MagicMock()
        with _patch_client(client):
            result = json.loads(await tool.call(ctx, action="remove_bucket", bucket="b1"))
        client.remove_bucket.assert_called_once_with("b1")
        assert result["action"] == "removed"


class TestObjects:
    @pytest.mark.asyncio
    async def test_objects_requires_bucket(self, tool, ctx):
        result = json.loads(await tool.call(ctx, action="objects"))
        assert "Required" in result["error"]

    @pytest.mark.asyncio
    async def test_objects(self, tool, ctx):
        client = MagicMock()
        obj = MagicMock(object_name="a.txt", size=12, is_dir=False,
                        last_modified=datetime(2026, 1, 1))
        client.list_objects.return_value = [obj]
        with _patch_client(client):
            result = json.loads(await tool.call(ctx, action="objects", bucket="b1", prefix="a"))
        assert result["count"] == 1
        assert result["objects"][0]["key"] == "a.txt"
        client.list_objects.assert_called_once_with("b1", prefix="a", recursive=False)

    @pytest.mark.asyncio
    async def test_stat(self, tool, ctx):
        client = MagicMock()
        client.stat_object.return_value = MagicMock(
            size=99, etag="abc", content_type="text/plain",
            last_modified=datetime(2026, 1, 1),
        )
        with _patch_client(client):
            result = json.loads(await tool.call(ctx, action="stat", bucket="b1", object_name="a.txt"))
        assert result["size"] == 99
        assert result["etag"] == "abc"

    @pytest.mark.asyncio
    async def test_remove_object(self, tool, ctx):
        client = MagicMock()
        with _patch_client(client):
            result = json.loads(await tool.call(ctx, action="remove_object", bucket="b1", object_name="a.txt"))
        client.remove_object.assert_called_once_with("b1", "a.txt")
        assert result["action"] == "removed"

    @pytest.mark.asyncio
    async def test_presign(self, tool, ctx):
        client = MagicMock()
        client.presigned_get_object.return_value = "https://s3.hanzo.ai/b1/a.txt?sig=x"
        with _patch_client(client):
            result = json.loads(await tool.call(ctx, action="presign", bucket="b1", object_name="a.txt"))
        assert result["url"].startswith("https://s3.hanzo.ai/")


class TestCredentials:
    @pytest.mark.asyncio
    async def test_missing_creds_errors(self, tool, ctx, monkeypatch):
        for var in ("HANZO_S3_ACCESS_KEY", "HANZO_S3_SECRET_KEY",
                    "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"):
            monkeypatch.delenv(var, raising=False)
        result = json.loads(await tool.call(ctx, action="buckets"))
        assert "credentials" in result["error"].lower()
