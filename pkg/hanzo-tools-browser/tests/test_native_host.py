import json
import sys

import pytest

from hanzo_tools.browser import native_host


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(sys, "platform", "linux")
    exe = tmp_path / ".local" / "bin" / "hanzo-zap-host"
    exe.parent.mkdir(parents=True)
    exe.write_text("")
    monkeypatch.setattr(native_host, "_executable", lambda: str(exe))
    return tmp_path


def test_every_installed_engine_gets_its_own_manifest(home):
    (home / ".config" / "chromium").mkdir(parents=True)
    (home / ".mozilla").mkdir()
    written = native_host.install()
    chromium = json.loads((home / ".config/chromium/NativeMessagingHosts/ai.hanzo.zap.json").read_text())
    firefox = json.loads((home / ".mozilla/native-messaging-hosts/ai.hanzo.zap.json").read_text())
    assert chromium["allowed_origins"] == ["chrome-extension://biingenefmanpecedoafkfajbnlgdmbl/"]
    assert "allowed_extensions" not in chromium
    assert firefox["allowed_extensions"] == ["hanzo-ai@hanzo.ai"]
    assert "allowed_origins" not in firefox
    assert len(written) == 2
    assert native_host.install() == []  # idempotent


def test_an_engine_that_is_not_installed_is_left_alone(home):
    assert native_host.install() == []
    assert not (home / ".mozilla").exists()
