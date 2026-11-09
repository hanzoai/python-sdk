"""The order a credential is resolved in, the identities, and what never leaves the module."""

from __future__ import annotations

import json
import time

import pytest
import hanzo_login as login
from conftest import jwt

LOGIN = jwt(
    {
        "owner": "hanzo",
        "name": "z",
        "displayName": "Zach",
        "email": "z@hanzo.ai",
        "orgs": [{"org": "hanzo", "role": "admin"}, {"org": "lux", "role": "member"}],
        "exp": int(time.time()) + 3600,
    }
)
OTHER = jwt({"owner": "lux", "name": "ops", "email": "ops@lux.network", "exp": int(time.time()) + 3600})
ROWS = json.dumps(
    [
        {"key": "hanzo/z", "owner": "hanzo", "subject": "z@hanzo.ai", "expiry": 1893456000, "active": True},
        {"key": "lux/ops", "owner": "lux", "subject": "ops@lux.network", "active": False, "token": "leak"},
    ]
)


# -- the order ----------------------------------------------------------------


def test_the_key_in_the_environment_beats_the_login_and_the_stored_key(machine, monkeypatch):
    machine.hanzo({"auth token": (0, LOGIN + "\n", "")})
    machine.config("sk-stale")
    monkeypatch.setenv("HANZO_API_KEY", " sk-env ")
    cred = login.credential()
    assert (cred.source, cred.secret) == ("env", "sk-env")
    assert machine.runs() == []


def test_the_login_beats_the_stored_key(machine):
    machine.hanzo({"auth token": (0, LOGIN + "\n", "")})
    machine.config("sk-stale")
    cred = login.credential()
    assert (cred.source, cred.secret, cred.refused) == ("login", LOGIN, None)
    assert machine.runs() == ["auth token"]


def test_a_login_that_fails_falls_through_to_the_stored_key_and_says_why(machine):
    machine.hanzo({"auth token": (1, "", "not signed in: run `hanzo auth login`\nsecond line\n")})
    machine.config("sk-legacy")
    cred = login.credential()
    assert (cred.source, cred.secret) == ("stored", "sk-legacy")
    assert cred.refused == "not signed in: run `hanzo auth login`"


def test_nothing_answering_is_a_credential_with_no_source(machine):
    cred = login.credential()
    assert cred.source is None and cred.secret == ""
    assert "not installed" in cred.refused


def test_a_key_in_the_environment_and_an_identity_asks_the_login(machine, monkeypatch):
    machine.hanzo({"auth token --as lux/ops": (0, OTHER + "\n", "")})
    monkeypatch.setenv("HANZO_API_KEY", "sk-env")
    cred = login.credential("lux/ops")
    assert (cred.source, cred.secret, cred.identity) == ("login", OTHER, "lux/ops")
    assert machine.runs() == ["auth token --as lux/ops"]


def test_a_named_identity_the_login_refuses_is_an_error_not_another_account(machine, monkeypatch):
    machine.hanzo({"auth token --as lux/nobody": (1, "", "no identity lux/nobody\n")})
    machine.config("sk-legacy")
    monkeypatch.setenv("HANZO_API_KEY", "sk-env")
    with pytest.raises(login.LoginError, match="no identity lux/nobody"):
        login.credential("lux/nobody")


def test_the_cli_is_never_found_on_path(machine, monkeypatch, tmp_path):
    decoy = tmp_path / "path"
    decoy.mkdir()
    ran = tmp_path / "decoy-ran"
    (decoy / "hanzo").write_text(f"#!/bin/sh\ntouch {ran}\necho decoy\n")
    (decoy / "hanzo").chmod(0o755)
    monkeypatch.setenv("PATH", f"{decoy}:/usr/bin:/bin")
    assert login.credential().source is None
    assert not ran.exists()


def test_the_cli_lives_in_the_installers_bin_under_home(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert login.cli() == tmp_path / ".local" / "bin" / "hanzo"


def test_output_that_is_not_one_token_is_no_login(machine):
    machine.hanzo({"auth token": (0, "opening a window\n", "")})
    assert login.credential().refused == "hanzo auth token did not print one token"


# -- identities named by a person ---------------------------------------------


@pytest.mark.parametrize("bad", ["--help", "-x", "a b", "../x", "a/b/c", "a\nb", "a;b", "x" * 129, "é/x"])
def test_an_identity_that_could_be_argv_is_refused_before_it_reaches_argv(machine, bad):
    machine.hanzo({})
    for call in (login.token, login.credential, login.use, login.switch):
        with pytest.raises(login.LoginError):
            call(bad)
    with pytest.raises(login.LoginError):
        login.switch("")
    assert machine.runs() == []


@pytest.mark.parametrize("good", ["hanzo", "hanzo/z", "lux/ops@lux.network", "a+b_c.d-e/f", "x" * 128])
def test_an_identity_that_is_a_name_passes(good):
    assert login.valid(good) == good


@pytest.mark.parametrize("bad", ["", "a/b", "a b", "x\r\nHost: evil", "--org", "x" * 129])
def test_an_org_that_could_split_a_header_is_refused(bad):
    with pytest.raises(login.LoginError):
        login.valid_org(bad)


def test_an_org_that_is_a_name_passes():
    assert login.valid_org("hanzo") == "hanzo" and login.valid_org("lux-2.0") == "lux-2.0"


def test_a_refused_identity_is_not_echoed():
    with pytest.raises(login.LoginError) as raised:
        login.valid("eyJhbGciOi secret")
    assert "eyJ" not in str(raised.value)


def test_use_asks_the_login_for_the_identity_and_holds_it_for_this_process(machine):
    machine.hanzo({"auth token --as lux/ops": (0, OTHER + "\n", ""), "auth token": (0, LOGIN + "\n", "")})
    login.use("lux/ops")
    assert login.using() == "lux/ops"
    assert machine.runs() == ["auth token --as lux/ops"]
    assert login.credential().secret == OTHER
    login.use(None)
    assert login.using() is None and login.credential().secret == LOGIN


def test_use_checks_the_login_again_even_when_it_just_answered(machine):
    machine.hanzo({"auth token --as lux/ops": (0, OTHER + "\n", "")})
    login.token("lux/ops")
    login.use("lux/ops")
    assert machine.runs() == ["auth token --as lux/ops"] * 2


def test_use_of_an_identity_the_login_does_not_hold_changes_nothing(machine):
    machine.hanzo({"auth token --as lux/ops": (0, OTHER + "\n", ""), "auth token --as x/y": (1, "", "no identity x/y")})
    login.use("lux/ops")
    with pytest.raises(login.LoginError, match="no identity x/y"):
        login.use("x/y")
    assert login.using() == "lux/ops"


def test_use_names_an_identity_even_when_a_key_is_set(machine, monkeypatch):
    machine.hanzo({"auth token --as lux/ops": (0, OTHER + "\n", "")})
    monkeypatch.setenv("HANZO_API_KEY", "sk-env")
    login.use("lux/ops")
    assert login.credential().secret == OTHER
    assert login.credential("lux/ops").secret == OTHER


def test_switch_makes_it_the_clis_active_identity_and_forgets_what_was_kept(machine):
    machine.hanzo({"auth token": (0, LOGIN + "\n", ""), "auth switch lux/ops": (0, "", "")})
    login.token()
    login.switch("lux/ops")
    login.token()
    assert machine.runs() == ["auth token", "auth switch lux/ops", "auth token"]


def test_switch_to_an_identity_the_cli_does_not_hold_says_why(machine):
    machine.hanzo({"auth switch x/y": (1, "", "no identity x/y\n")})
    with pytest.raises(login.LoginError, match="no identity x/y"):
        login.switch("x/y")


def test_identities_are_the_rows_of_auth_list_without_anything_else(machine):
    machine.hanzo({"auth list -o json": (0, ROWS, "")})
    rows = login.identities()
    assert [r["key"] for r in rows] == ["hanzo/z", "lux/ops"]
    assert rows[0]["active"] is True and rows[0]["expiry"] == 1893456000
    assert "token" not in rows[1]


def test_identities_from_a_cli_that_prints_no_json_say_so(machine):
    machine.hanzo({"auth list -o json": (0, "table\n", "")})
    with pytest.raises(login.LoginError, match="did not print JSON"):
        login.identities()


# -- the kept token -----------------------------------------------------------


def test_a_token_is_kept_300_seconds_per_identity(machine, monkeypatch):
    machine.hanzo({"auth token": (0, LOGIN + "\n", ""), "auth token --as lux/ops": (0, OTHER + "\n", "")})
    clock = [1000.0]
    monkeypatch.setattr(login, "_now", lambda: clock[0])
    login.token()
    login.token()
    login.token("lux/ops")
    login.token("lux/ops")
    assert machine.runs() == ["auth token", "auth token --as lux/ops"]
    clock[0] += 299
    login.token()
    assert len(machine.runs()) == 2
    clock[0] += 2
    login.token()
    login.token("lux/ops")
    assert machine.runs() == ["auth token", "auth token --as lux/ops"] * 2


def test_a_token_about_to_expire_is_not_kept(machine):
    soon = jwt({"owner": "hanzo", "exp": int(time.time()) + 10})
    machine.hanzo({"auth token": (0, soon + "\n", "")})
    login.token()
    login.token()
    assert machine.runs() == ["auth token"] * 2


def test_not_signed_in_is_remembered_briefly_so_a_new_login_is_seen(machine, monkeypatch):
    machine.hanzo({"auth token": (1, "", "not signed in")})
    clock = [0.0]
    monkeypatch.setattr(login, "_now", lambda: clock[0])
    for _ in range(3):
        with pytest.raises(login.LoginError):
            login.token()
    assert machine.runs() == ["auth token"]
    clock[0] += login.REFUSAL_TTL + 1
    with pytest.raises(login.LoginError):
        login.token()
    assert len(machine.runs()) == 2


def test_forget_makes_the_next_call_ask_again(machine):
    machine.hanzo({"auth token": (0, LOGIN + "\n", "")})
    login.token()
    login.forget()
    login.token()
    assert machine.runs() == ["auth token"] * 2


# -- what is said about whoever answered --------------------------------------


def test_describe_a_login_names_the_active_identity_from_the_clis_rows(machine):
    machine.hanzo({"auth token": (0, LOGIN + "\n", ""), "auth list -o json": (0, ROWS, "")})
    out = login.describe()
    assert out == {
        "source": "login",
        "using": None,
        "identity": "hanzo/z",
        "email": "z@hanzo.ai",
        "name": "Zach",
        "org": "hanzo",
        "orgs": [{"org": "hanzo", "role": "admin"}, {"org": "lux", "role": "member"}],
    }
    assert LOGIN not in json.dumps(out)


def test_describe_a_login_falls_back_to_the_claims_when_the_cli_lists_nothing(machine):
    machine.hanzo({"auth token": (0, LOGIN + "\n", "")})
    assert login.describe()["identity"] == "hanzo/z"


def test_describe_an_identity_that_was_named(machine):
    machine.hanzo({"auth token --as lux/ops": (0, OTHER + "\n", "")})
    login.use("lux/ops")
    out = login.describe()
    assert (out["identity"], out["using"], out["name"], out["org"], out["orgs"]) == (
        "lux/ops",
        "lux/ops",
        "ops",
        "lux",
        [],
    )


def test_describe_a_key_is_its_prefix_only(machine, monkeypatch):
    monkeypatch.setenv("HANZO_API_KEY", "sk-0123456789abcdef")
    out = login.describe()
    assert out == {"source": "env", "using": None, "key": "sk-…"}
    assert "0123" not in json.dumps(out)


def test_describe_a_stored_key_and_why_the_login_did_not_answer(machine):
    machine.hanzo({"auth token": (1, "", "not signed in")})
    machine.config("pk-ABCDEF")
    out = login.describe()
    assert out == {"source": "stored", "using": None, "key": "pk-…", "login": "not signed in"}


def test_describe_a_key_with_no_known_prefix_says_nothing_of_it(machine, monkeypatch):
    monkeypatch.setenv("HANZO_API_KEY", "0123456789")
    assert login.describe()["key"] == "…"


def test_a_credential_does_not_print_its_secret(machine, monkeypatch):
    monkeypatch.setenv("HANZO_API_KEY", "sk-secret-value")
    cred = login.credential()
    assert "secret-value" not in repr(cred) and "secret-value" not in str(cred)


# -- a fresh machine ----------------------------------------------------------


def test_a_fresh_machine_with_only_the_cli_signs_in_through_it(machine):
    assert list(machine.home.iterdir()) == []
    machine.hanzo({"auth token": (0, LOGIN + "\n", ""), "auth list -o json": (0, ROWS, "")})
    cred = login.credential()
    assert (cred.source, cred.secret) == ("login", LOGIN)
    assert list(machine.home.iterdir()) == []
