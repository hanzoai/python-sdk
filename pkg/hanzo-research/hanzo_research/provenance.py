"""What a filed measurement must carry to be believed or repeated: the harness commit, the model
and its weights, the machine, the device, the software, the date.

`capture()` reads all of it from the environment; `Provenance.apply(run)` folds it into a
run: `commit`, `system`, `version` (`<model>@<weights sha256>`), `by`, and a sentence in
`notes` ending in the SHA-256 of the whole record (RFC 8785), so the record can be filed
beside the run as an artifact and checked against it. Best-effort throughout: a missing
tool or a directory outside git yields an empty field, never an error.

The functions the experiment handle uses (`git_state`, `commit_narrative`, `lib_versions`,
`host`, `find_repo`, `caller_doc`) are the crate's `provenance.rs`, record for record.
"""

from __future__ import annotations

import os
import re
import sys
import socket
import hashlib
import inspect
import platform
import subprocess
import dataclasses
from typing import Any
from importlib import metadata
from dataclasses import field, dataclass

from . import canonical
from .wire import Run, now

__all__ = [
    "Provenance",
    "capture",
    "digest_file",
    "digest_tree",
    "weights",
    "git_state",
    "commit_narrative",
    "lib_versions",
    "host",
    "find_repo",
    "caller_doc",
]

PACKAGES = ("hanzo-research", "numpy", "torch", "transformers", "datasets", "vllm", "jax", "hanzo-kai")
_HEX = re.compile(r"^[0-9a-fA-F]{1,64}$")
_SHA = re.compile(r"^(sha256:)?([0-9a-f]{64})$")


def _run(*args: str, cwd: str | None = None) -> str:
    try:
        out = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=cwd)
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def _git(repo: str, *args: str) -> str:
    return _run("git", "-C", repo, *args)


def git_state(repo: str) -> dict[str, Any]:
    """The producing repo's commit sha, branch, and whether the tree was dirty."""
    return {
        "git_sha": _git(repo, "rev-parse", "HEAD"),
        "git_branch": _git(repo, "rev-parse", "--abbrev-ref", "HEAD"),
        "git_dirty": bool(_git(repo, "status", "--porcelain")),
    }


def commit_narrative(repo: str, since_sha: str = "", window: int = 10) -> list[str]:
    """Commit subjects since the last recorded run's sha (`<since>..HEAD`), else the last `window`.

    `since_sha` can come from a server answer, so only a git object id (hex) is used; anything
    else, which could read as a flag or a path, falls back to the window.
    """
    if since_sha and _HEX.match(since_sha):
        raw = _git(repo, "log", f"{since_sha}..HEAD", "--format=%s")
    else:
        raw = _git(repo, "log", f"-{int(window)}", "--format=%s")
    return [ln.strip() for ln in raw.splitlines() if ln.strip()]


def lib_versions(names: Any) -> dict[str, str]:
    """{distribution: installed version} for the named ones that are installed."""
    out = {}
    for n in names or []:
        try:
            out[n] = metadata.version(n)
        except metadata.PackageNotFoundError:
            pass
    return out


def host() -> dict[str, str]:
    """The box the run executed on: hostname and OS name."""
    return {"hostname": socket.gethostname(), "platform": platform.system() or os.name}


def find_repo(start: str | None = None) -> str:
    """The git toplevel the caller runs in, else the directory itself."""
    start = start or os.getcwd()
    return _git(start, "rev-parse", "--show-toplevel") or start


def caller_doc() -> str:
    """The module docstring of the first frame outside this package: what the experiment is."""
    for fr in inspect.stack():
        if not str(fr.frame.f_globals.get("__name__", "")).startswith("hanzo_research"):
            return (fr.frame.f_globals.get("__doc__") or "").strip()
    return ""


# ── digests ─────────────────────────────────────────────────────────────────────


def digest_file(path: str) -> str:
    """`sha256:<hex>` of a file's bytes, read in 1 MiB blocks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return "sha256:" + h.hexdigest()


def digest_tree(path: str) -> str:
    """`sha256:<hex>` of a directory: of its SHA256SUMS when it holds one, else of the
    `sha256sum` listing of every file under it, sorted by path, written as that file would be.
    """
    sums = os.path.join(path, "SHA256SUMS")
    if os.path.isfile(sums):
        return digest_file(sums)
    lines = []
    for root, dirs, files in os.walk(path):
        dirs.sort()
        for name in sorted(files):
            full = os.path.join(root, name)
            rel = os.path.relpath(full, path).replace(os.sep, "/")
            lines.append(f"{digest_file(full)[7:]}  {rel}\n")
    return "sha256:" + hashlib.sha256("".join(sorted(lines, key=lambda s: s[66:])).encode()).hexdigest()


def weights(value: str) -> str:
    """Weights as `sha256:<hex>`: a file or a directory hashed, or a digest given as one."""
    if os.path.isdir(value):
        return digest_tree(value)
    if os.path.isfile(value):
        return digest_file(value)
    m = _SHA.match(value.strip().lower())
    if not m:
        raise ValueError(f"weights {value!r} is neither a path nor a sha256")
    return "sha256:" + m.group(2)


# ── the record ──────────────────────────────────────────────────────────────────


@dataclass
class Provenance:
    """Where a number came from: harness commit, model and weights, machine, device, software, date."""

    repo: str = ""
    remote: str = ""
    commit: str = ""
    branch: str = ""
    dirty: bool = False
    diff: str = ""
    model: str = ""
    weights: str = ""
    host: str = ""
    os: str = ""
    machine: str = ""
    cpu: str = ""
    cores: int = 0
    gpu: str = ""
    device: str = ""
    dtype: str = ""
    python: str = ""
    packages: dict[str, str] = field(default_factory=dict)
    date: str = ""

    def dump(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    def digest(self) -> str:
        """`sha256:<hex>` of the record's RFC 8785 bytes: the address of the record filed as an artifact."""
        return "sha256:" + canonical.digest(self.dump())

    def note(self) -> str:
        """The record as one sentence for a run's notes, ending in its digest."""
        parts = []
        if self.commit:
            where = self.remote or self.repo
            tree = f", dirty (diff {self.diff})" if self.dirty else ""
            parts.append(f"harness {where} at {self.commit}{tree}")
        if self.model:
            parts.append(f"model {self.model}" + (f", weights {self.weights}" if self.weights else ""))
        box = ", ".join(
            x
            for x in (
                self.os,
                self.machine,
                self.cpu and f"CPU {self.cpu}",
                self.cores and f"{self.cores} cores",
                self.gpu and f"GPU {self.gpu}",
            )
            if x
        )
        if self.host:
            parts.append(f"host {self.host}" + (f" ({box})" if box else ""))
        if self.device or self.dtype:
            parts.append(
                " ".join(
                    x
                    for x in (
                        f"device {self.device}" if self.device else "",
                        f"dtype {self.dtype}" if self.dtype else "",
                    )
                    if x
                )
            )
        soft = ", ".join(f"{k} {v}" for k, v in sorted(self.packages.items()))
        parts.append(f"python {self.python}" + (f" with {soft}" if soft else ""))
        if self.date:
            parts.append(f"captured {self.date}")
        return "Provenance: " + "; ".join(parts) + f". Record {self.digest()}."

    def apply(self, run: Run | dict[str, Any]) -> Run | dict[str, Any]:
        """Fold the record into a run, filling what the run leaves empty and appending `note()`."""
        version = f"{self.model}@{self.weights.removeprefix('sha256:')}" if self.model and self.weights else self.model
        fill = {"commit": self.commit, "system": self.model, "version": version, "by": self.host}
        get = run.get if isinstance(run, dict) else lambda k, d=None: getattr(run, k, d)
        for key, value in fill.items():
            if value and not get(key):
                _set(run, key, value)
        notes = str(get("notes") or "")
        _set(run, "notes", (notes.rstrip() + " " if notes.strip() else "") + self.note())
        return run

    def environment(self) -> Any:
        """The record as the crate's `EnvironmentV1`, whose digest a Rust harness computes alike."""
        from .lineage import EnvironmentV1

        return EnvironmentV1(
            git_sha=self.commit,
            git_branch=self.branch,
            git_dirty=self.dirty,
            host=self.host,
            os=self.os,
            kernel_version=platform.release(),
            cargo_lock_hash="",
            image_digest="",
            precision_config=self.dtype,
            determinism_config="",
            compiler_version=f"python {self.python}",
            lib_versions=dict(self.packages),
        )


def _set(run: Any, key: str, value: Any) -> None:
    if isinstance(run, dict):
        run[key] = value
    else:
        setattr(run, key, value)


def capture(
    repo: str | None = None,
    model: str = "",
    weights: str | None = None,
    device: str = "",
    dtype: str = "",
    packages: Any = None,
    gpu: bool = True,
) -> Provenance:
    """Read the provenance of a measurement made now.

    `repo` is the harness checkout (default: the git toplevel of the working directory);
    `weights` a file, a directory (its SHA256SUMS, else every file) or a sha256 given as a
    value; `packages` the distributions whose versions pin the result (default: the
    common ML stack, those installed). A dirty tree is recorded with the SHA-256 of
    `git diff HEAD`, so the uncommitted state the number came from is pinned too.
    """
    top = find_repo(repo) if repo is None or os.path.isdir(repo) else repo
    state = git_state(top)
    diff = ""
    if state["git_dirty"]:
        listing = _git(top, "diff", "HEAD", "--binary") + "\n" + _git(top, "ls-files", "--others", "--exclude-standard")
        diff = "sha256:" + hashlib.sha256(listing.encode()).hexdigest()
    names = list(packages) if packages is not None else list(PACKAGES)
    return Provenance(
        repo=top,
        remote=_remote(top),
        commit=state["git_sha"],
        branch=state["git_branch"],
        dirty=state["git_dirty"],
        diff=diff,
        model=model,
        weights=_weights(weights) if weights else "",
        host=socket.gethostname(),
        os=f"{platform.system()} {platform.release()}".strip(),
        machine=platform.machine(),
        cpu=_cpu(),
        cores=os.cpu_count() or 0,
        gpu=_gpu() if gpu else "",
        device=device,
        dtype=dtype,
        python=platform.python_version(),
        packages=lib_versions(names),
        date=now(),
    )


_weights = weights  # capture() takes a parameter of that name


def _remote(repo: str) -> str:
    url = _git(repo, "remote", "get-url", "origin")
    # never a credential: https://user:token@host/... keeps only the host and path
    return re.sub(r"^(\w+://)[^@/]+@", r"\1", url)


def _cpu() -> str:
    if sys.platform == "darwin":
        return _run("sysctl", "-n", "machdep.cpu.brand_string")
    try:
        with open("/proc/cpuinfo") as f:
            text = f.read()
    except OSError:
        return platform.processor()
    for key in ("model name", "Model", "Hardware"):
        m = re.search(rf"^{key}\s*:\s*(.+)$", text, re.M)
        if m:
            return m.group(1).strip()
    lscpu = _run("lscpu")
    m = re.search(r"^Model name:\s*(.+)$", lscpu, re.M)
    return m.group(1).strip() if m else platform.processor()


def _gpu() -> str:
    nv = _run("nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader")
    if nv:
        rows = [r.split(",") for r in nv.splitlines() if r.strip()]
        return "; ".join(f"{r[0].strip()} (driver {r[1].strip()})" if len(r) > 1 else r[0].strip() for r in rows)
    info = _run("rocminfo")
    if info:
        names = re.findall(r"Marketing Name:\s*(.+)", info)
        gfx = [
            n.strip()
            for n, kind in zip(names, re.findall(r"Device Type:\s*(\w+)", info), strict=False)
            if kind == "GPU"
        ]
        return "; ".join(gfx)
    return ""
