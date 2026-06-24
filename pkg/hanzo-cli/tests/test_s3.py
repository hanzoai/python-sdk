"""Unit tests for the `hanzo s3` CLI group (mocked S3 client)."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from hanzo_cli.s3.commands import s3


def _patch_client(client):
    return patch("hanzo_cli.s3.commands._get_s3_client", return_value=client)


def test_s3_group_help():
    result = CliRunner().invoke(s3, ["--help"])
    assert result.exit_code == 0
    for cmd in ("buckets", "mb", "rb", "ls", "stat", "rm", "presign"):
        assert cmd in result.output


def test_buckets_lists():
    client = MagicMock()
    b = MagicMock(creation_date=datetime(2026, 1, 1))
    b.name = "hanzo-space"
    client.list_buckets.return_value = [b]
    with _patch_client(client):
        result = CliRunner().invoke(s3, ["buckets"])
    assert result.exit_code == 0
    assert "hanzo-space" in result.output


def test_make_bucket():
    client = MagicMock()
    with _patch_client(client):
        result = CliRunner().invoke(s3, ["mb", "b1"])
    assert result.exit_code == 0
    client.make_bucket.assert_called_once_with("b1")


def test_ls_objects():
    client = MagicMock()
    obj = MagicMock(object_name="a.txt", size=12, is_dir=False,
                    last_modified=datetime(2026, 1, 1))
    client.list_objects.return_value = [obj]
    with _patch_client(client):
        result = CliRunner().invoke(s3, ["ls", "b1", "--prefix", "a"])
    assert result.exit_code == 0
    assert "a.txt" in result.output


def test_presign_outputs_url():
    client = MagicMock()
    client.presigned_get_object.return_value = "https://s3.hanzo.ai/b1/a.txt?sig=x"
    with _patch_client(client):
        result = CliRunner().invoke(s3, ["presign", "b1", "a.txt"])
    assert result.exit_code == 0
    assert "https://s3.hanzo.ai/" in result.output


def test_rm_confirms(monkeypatch):
    client = MagicMock()
    with _patch_client(client):
        # Decline confirmation → aborts, client not called.
        result = CliRunner().invoke(s3, ["rm", "b1", "a.txt"], input="n\n")
    assert result.exit_code != 0
    client.remove_object.assert_not_called()


def test_missing_credentials():
    runner = CliRunner()
    with patch.dict("os.environ", {}, clear=True):
        result = runner.invoke(s3, ["buckets"])
    assert result.exit_code != 0
    assert "credentials" in result.output.lower()
