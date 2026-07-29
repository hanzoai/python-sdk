"""Tests for hanzo_iam.store — the token store.

`test_token_file_is_never_world_readable_mid_write` is the regression: the code
this replaces did `write_text()` then `chmod(0600)`, so with a default umask of
022 the file existed at 0644 — holding a bearer token — between the two calls.
That test FAILS against write-then-chmod and passes against create-private-then-
rename.
"""

from __future__ import annotations

import json
import os
import stat

import pytest

from hanzo_iam import store

TOKEN = {"access_token": "header.payload.signature", "refresh_token": "r"}


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    """Point the store at a scratch HOME and disable the keyring, so these
    tests exercise the FILE backend — the one with the permissions hazard."""
    monkeypatch.setattr(store, "TOKEN_DIR", tmp_path / ".hanzo" / "auth")
    monkeypatch.setattr(store, "TOKEN_FILE", tmp_path / ".hanzo" / "auth" / "token.json")
    monkeypatch.setattr(store, "_keyring", lambda: None)
    return tmp_path


def test_roundtrip():
    assert store.save(TOKEN) == "file"
    assert store.load() == TOKEN


def test_load_returns_none_when_nothing_stored():
    assert store.load() is None


def test_clear_removes_the_file():
    store.save(TOKEN)
    store.clear()
    assert store.load() is None
    assert not store.TOKEN_FILE.exists()


def test_token_file_is_0600():
    store.save(TOKEN)
    assert store.file_mode() == 0o600


def test_token_dir_is_0700():
    store.save(TOKEN)
    assert stat.S_IMODE(store.TOKEN_DIR.stat().st_mode) == 0o700


def test_permissive_umask_cannot_widen_the_token_file():
    """A 0000 umask is the worst case: anything created without an explicit
    mode lands at 0666. The store must not care."""
    old = os.umask(0o000)
    try:
        store.save(TOKEN)
    finally:
        os.umask(old)
    assert store.file_mode() == 0o600


def test_token_file_is_never_world_readable_mid_write(monkeypatch):
    """THE regression test. Watch every mode the token file ever has.

    write-then-chmod publishes the path at 0644 first and tightens it after;
    this asserts the file is never observable at anything but 0600, which is
    only true when it is created private and renamed into place.
    """
    seen: list[int] = []
    real_replace = os.replace

    def watching_replace(src, dst):
        # The instant before the name exists, and the instant after.
        seen.append(stat.S_IMODE(os.stat(src).st_mode))
        real_replace(src, dst)
        seen.append(stat.S_IMODE(os.stat(dst).st_mode))

    monkeypatch.setattr(os, "replace", watching_replace)
    old = os.umask(0o000)
    try:
        store.save(TOKEN)
    finally:
        os.umask(old)

    assert seen, "the store must publish the token by rename, not by writing in place"
    assert all(m == 0o600 for m in seen), f"token was observable at {[oct(m) for m in seen]}"


def test_no_leftover_temp_files():
    store.save(TOKEN)
    leftovers = [p.name for p in store.TOKEN_DIR.iterdir() if p.name != "token.json"]
    assert leftovers == []


def test_failed_write_leaves_no_temp_file_and_no_partial_token(monkeypatch):
    store.save(TOKEN)
    original = store.load()

    def boom(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError):
        store.save({"access_token": "new"})

    assert store.load() == original  # the old token survived intact
    assert [p.name for p in store.TOKEN_DIR.iterdir()] == ["token.json"]


def test_save_overwrites_rather_than_appends():
    store.save(TOKEN)
    store.save({"access_token": "second"})
    assert store.load() == {"access_token": "second"}
    assert json.loads(store.TOKEN_FILE.read_text()) == {"access_token": "second"}


def test_corrupt_file_reads_as_absent_not_as_a_credential():
    store.TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    store.TOKEN_FILE.write_text("{not json")
    assert store.load() is None


def test_keyring_backend_removes_any_plaintext_copy(monkeypatch):
    """Promoting to the keyring must delete the file — a stale plaintext token
    on disk is exactly what the keyring is there to avoid."""
    store.save(TOKEN)
    assert store.TOKEN_FILE.exists()

    vault: dict[tuple[str, str], str] = {}

    class FakeKeyring:
        @staticmethod
        def set_password(service, user, value):
            vault[(service, user)] = value

        @staticmethod
        def get_password(service, user):
            return vault.get((service, user))

        @staticmethod
        def delete_password(service, user):
            vault.pop((service, user), None)

    monkeypatch.setattr(store, "_keyring", lambda: FakeKeyring)
    assert store.save(TOKEN) == "keyring"
    assert not store.TOKEN_FILE.exists()
    assert store.load() == TOKEN
    assert store.backend() == "keyring"


def test_falls_back_to_file_when_keyring_raises(monkeypatch):
    class BrokenKeyring:
        @staticmethod
        def set_password(*a):
            raise RuntimeError("no backend")

        @staticmethod
        def get_password(*a):
            raise RuntimeError("no backend")

    monkeypatch.setattr(store, "_keyring", lambda: BrokenKeyring)
    assert store.save(TOKEN) == "file"
    assert store.file_mode() == 0o600
    assert store.load() == TOKEN


def test_existing_permissive_directory_is_tightened(isolated_home):
    d = store.TOKEN_DIR
    d.mkdir(parents=True)
    os.chmod(d, 0o777)
    store.save(TOKEN)
    assert stat.S_IMODE(d.stat().st_mode) == 0o700


def test_write_private_is_reusable_for_other_credentials(tmp_path):
    """The PaaS session cache uses this too; it must be private there as well."""
    target = tmp_path / "nested" / "session.json"
    store._write_private(target, '{"at":"x"}')
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert target.read_text() == '{"at":"x"}'
