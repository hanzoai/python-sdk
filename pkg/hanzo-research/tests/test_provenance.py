"""capture() reads the harness, the weights and the machine; apply() folds them into a run."""

from __future__ import annotations

import os
import hashlib
import subprocess

import pytest
from hanzo_research import Run, canonical, provenance
from hanzo_research.lineage import EnvironmentV1


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "harness"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    git(r, "config", "user.email", "t@example.com")
    git(r, "config", "user.name", "t")
    git(r, "remote", "add", "origin", "https://user:secret@github.com/hanzoai/harness.git")
    (r / "bench.py").write_text("print(1)\n")
    git(r, "add", ".")
    git(r, "commit", "-q", "-m", "first")
    (r / "bench.py").write_text("print(2)\n")
    git(r, "commit", "-qam", "second")
    return r


def test_capture_reads_the_harness_and_the_machine(repo):
    p = provenance.capture(
        repo=str(repo),
        model="kai-1.3",
        weights="sha256:" + "a" * 64,
        device="cpu",
        dtype="f32",
        packages=["hanzo-research-not-installed"],
        gpu=False,
    )
    assert p.commit == git(repo, "rev-parse", "HEAD") and p.branch == "main" and not p.dirty and p.diff == ""
    assert p.remote == "https://github.com/hanzoai/harness.git"
    assert p.weights == "sha256:" + "a" * 64 and p.device == "cpu" and p.dtype == "f32"
    assert p.host and p.python and p.cores > 0 and p.date.endswith("Z") and p.packages == {}
    (repo / "bench.py").write_text("print(3)\n")
    d = provenance.capture(repo=str(repo), gpu=False)
    assert d.dirty and d.diff.startswith("sha256:")
    (repo / "new.py").write_text("x")
    assert provenance.capture(repo=str(repo), gpu=False).diff != d.diff


def test_weights_are_hashed_by_content(tmp_path):
    f = tmp_path / "model.safetensors"
    f.write_bytes(b"w" * 3_000_000)
    assert provenance.weights(str(f)) == "sha256:" + hashlib.sha256(b"w" * 3_000_000).hexdigest()
    d = tmp_path / "folder"
    (d / "sub").mkdir(parents=True)
    (d / "kai.json").write_text("{}")
    (d / "sub" / "b.bin").write_bytes(b"b")
    listing = "".join(f"{hashlib.sha256(x).hexdigest()}  {n}\n" for n, x in (("kai.json", b"{}"), ("sub/b.bin", b"b")))
    assert provenance.weights(str(d)) == "sha256:" + hashlib.sha256(listing.encode()).hexdigest()
    (d / "SHA256SUMS").write_text(listing)
    assert provenance.weights(str(d)) == "sha256:" + hashlib.sha256(listing.encode()).hexdigest()
    assert provenance.weights("E45DD919" * 8) == "sha256:" + "e45dd919" * 8
    with pytest.raises(ValueError):
        provenance.weights("not-a-path-or-digest")


def test_apply_fills_what_the_run_leaves_empty(repo):
    p = provenance.capture(
        repo=str(repo), model="kai-1.3", weights="sha256:" + "b" * 64, device="cuda", dtype="bf16", gpu=False
    )
    r = p.apply(Run(id="x", benchmark="b", notes="Read once."))
    assert r.commit == p.commit and r.system == "kai-1.3" and r.version == "kai-1.3@" + "b" * 64 and r.by == p.host
    assert r.notes.startswith("Read once. Provenance: harness https://github.com/hanzoai/harness.git at ")
    assert f"Record {p.digest()}." in r.notes and "device cuda dtype bf16" in r.notes
    assert p.digest() == "sha256:" + canonical.digest(p.dump())
    kept = p.apply({"id": "y", "system": "kai", "version": "kai-1.3@cafe", "commit": "abc"})
    assert (kept["system"], kept["version"], kept["commit"]) == ("kai", "kai-1.3@cafe", "abc")
    assert kept["notes"].startswith("Provenance: ")


def test_environment_is_the_crates_record(repo):
    env = provenance.capture(repo=str(repo), dtype="bf16", gpu=False).environment()
    assert (
        isinstance(env, EnvironmentV1) and env.precision_config == "bf16" and env.compiler_version.startswith("python ")
    )
    assert len(env.digest()) == 64


def test_the_narrative_takes_only_an_object_id(repo):
    first = git(repo, "rev-list", "--max-parents=0", "HEAD")
    assert provenance.commit_narrative(str(repo), since_sha=first) == ["second"]
    assert provenance.commit_narrative(str(repo), since_sha="--output=/tmp/pwned") == ["second", "first"]
    assert provenance.git_state(str(repo))["git_branch"] == "main"
    assert provenance.find_repo(str(repo / ".")) == os.path.realpath(repo)
    assert provenance.host()["hostname"]


def test_the_dirty_digest_pins_untracked_contents(repo):
    (repo / "eval.yaml").write_text("split: test\n")
    a = provenance.capture(repo=str(repo), gpu=False).diff
    (repo / "eval.yaml").write_text("split: train\n")
    b = provenance.capture(repo=str(repo), gpu=False).diff
    assert a.startswith("sha256:") and a != b
    (repo / "bench.py").write_bytes(b"print(\xff\xfe)\n")  # not UTF-8
    assert provenance.capture(repo=str(repo), gpu=False).dirty


def test_a_git_that_fails_is_never_clean(repo, monkeypatch):
    monkeypatch.setattr(provenance, "_bytes", lambda *a: None)
    p = provenance.capture(repo=str(repo), gpu=False)
    assert p.dirty and p.diff == "unknown"


def test_a_folder_is_checked_against_its_sha256sums(tmp_path):
    d = tmp_path / "release"
    d.mkdir()
    (d / "model.safetensors").write_bytes(b"weights")
    (d / "kai.json").write_text("{}")
    sums = "".join(
        f"{hashlib.sha256(x).hexdigest()}  {n}\n" for n, x in (("kai.json", b"{}"), ("model.safetensors", b"weights"))
    )
    (d / "SHA256SUMS").write_text(sums)
    assert provenance.weights(str(d)) == "sha256:" + hashlib.sha256(sums.encode()).hexdigest()
    (d / "model.safetensors").write_bytes(b"other weights")
    with pytest.raises(ValueError, match="model.safetensors does not match"):
        provenance.weights(str(d))
    (d / "model.safetensors").write_bytes(b"weights")
    (d / "extra.bin").write_bytes(b"x")
    with pytest.raises(ValueError, match="extra.bin is not listed"):
        provenance.weights(str(d))


def test_a_name_cannot_forge_a_listing(tmp_path):
    one, two = tmp_path / "one", tmp_path / "two"
    one.mkdir()
    two.mkdir()
    z = hashlib.sha256(b"Z").hexdigest()
    (one / f"a\n{z}  b").write_bytes(b"X")
    (two / "a").write_bytes(b"X")
    (two / "b").write_bytes(b"Z")
    assert provenance.weights(str(one)) != provenance.weights(str(two))
    (two / "linked").symlink_to(one, target_is_directory=True)
    with pytest.raises(ValueError, match="directory symlink"):
        provenance.weights(str(two))


def test_no_credential_survives_in_a_remote(monkeypatch):
    # git's own insteadOf rewrites differ by machine, so the url is given, not configured
    for url, want in (
        ("https://user:secret@github.com/hanzoai/x.git", "https://github.com/hanzoai/x.git"),
        ("https://user:tok/en@github.com/hanzoai/x.git", "https://github.com/hanzoai/x.git"),
        ("https://user:p@ss@github.com/hanzoai/x.git", "https://github.com/hanzoai/x.git"),
        ("git@github.com:hanzoai/x.git", "git@github.com:hanzoai/x.git"),
    ):
        monkeypatch.setattr(provenance, "_git", lambda repo, *args, u=url: u)
        assert provenance._remote("repo") == want
