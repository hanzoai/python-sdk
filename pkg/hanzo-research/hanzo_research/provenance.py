"""Zero-config provenance auto-capture — like OpenTelemetry auto-instrument, for
experiments. The caller supplies nothing; the SDK reads the run's environment: git
sha/branch/dirty, the recent COMMIT MESSAGES (the narrative of what changed), the
installed lib versions, and the host. Import and go.
"""
import inspect
import os
import socket
import subprocess
from importlib import metadata


def _git(repo, *args):
    try:
        return subprocess.check_output(["git", "-C", repo, *args], stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return ""


def git_state(repo):
    """The producing repo's commit sha, branch, and whether the tree was dirty."""
    return {
        "git_sha": _git(repo, "rev-parse", "HEAD"),
        "git_branch": _git(repo, "rev-parse", "--abbrev-ref", "HEAD"),
        "git_dirty": bool(_git(repo, "status", "--porcelain")),
    }


def commit_narrative(repo, since_sha="", window=10):
    """The commit-message narrative — the 'what changed + why' story. Commit subjects
    SINCE the last recorded run's sha when known (`<since>..HEAD`), else the last
    `window` commits. Research self-documents as a side effect of running."""
    rng = f"{since_sha}..HEAD" if since_sha else f"-n{window}"
    raw = _git(repo, "log", rng, "--format=%s") if since_sha else _git(repo, "log", f"-{window}", "--format=%s")
    return [ln for ln in raw.splitlines() if ln.strip()]


def lib_versions(names):
    """{lib: installed version} for the relevant libs, skipping any not installed."""
    out = {}
    for n in names or []:
        try:
            out[n] = metadata.version(n)
        except Exception:
            pass
    return out


def host():
    """The box the run executed on — enough to correlate a result to hardware."""
    return {"hostname": socket.gethostname(), "platform": os.uname().sysname if hasattr(os, "uname") else os.name}


def find_repo(start=None):
    """The git repo the caller runs in (the toplevel), auto-detected from the CWD."""
    start = start or os.getcwd()
    top = _git(start, "rev-parse", "--show-toplevel")
    return top or start


def caller_doc():
    """The docstring of the first caller frame OUTSIDE this SDK — 'what this experiment
    is', captured zero-config from the researcher's normal module docstring. Together
    with the commit narrative and an optional note, the project self-documents as a side
    effect of running: write a normal docstring + commit normally, nothing extra."""
    for fr in inspect.stack():
        mod = fr.frame.f_globals.get("__name__", "")
        if not mod.startswith("hanzo_research"):
            return (fr.frame.f_globals.get("__doc__") or "").strip()
    return ""
