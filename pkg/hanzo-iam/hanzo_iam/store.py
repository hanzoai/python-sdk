"""The ONE token store for Hanzo credentials.

Order of preference:

1. The OS keyring (Keychain / libsecret / Windows Credential Locker) when the
   `keyring` package is installed AND a real backend is available.
2. ``~/.hanzo/auth/token.json``, created with mode 0600 ATOMICALLY.

"Atomically" is the whole point of the fallback. The code this replaces did
``write_text()`` then ``chmod(0600)``: between those two calls the file exists
at ``0666 & ~umask`` — commonly 0644 — holding a bearer token. Any process on
the box could read it in that window. Here the bytes are written to a
private temp file that is created 0600 by `mkstemp` and never named
``token.json`` until it is already correct, then `os.replace` swaps it in.
"""

from __future__ import annotations

import json
import os
import stat
import tempfile
from pathlib import Path
from typing import Any

TOKEN_DIR = Path.home() / ".hanzo" / "auth"
TOKEN_FILE = TOKEN_DIR / "token.json"

# Keyring coordinates. <org>-<app> naming, matching IAM.
KEYRING_SERVICE = "hanzo-cli"
KEYRING_USERNAME = "default"

FILE_MODE = 0o600
DIR_MODE = 0o700


def _keyring() -> Any | None:
    """Return a usable keyring module, or None.

    Installed-but-headless is the common case on a server: `keyring` imports
    fine and then raises on first use. Probing the backend here means the file
    fallback is chosen deliberately rather than discovered mid-write.
    """
    try:
        import keyring
        from keyring.backends.fail import Keyring as FailKeyring
    except Exception:
        return None
    try:
        if isinstance(keyring.get_keyring(), FailKeyring):
            return None
    except Exception:
        return None
    return keyring


def save(data: dict[str, Any]) -> str:
    """Persist token data. Returns the backend used: "keyring" or "file"."""
    blob = json.dumps(data, indent=2, sort_keys=True)

    kr = _keyring()
    if kr is not None:
        try:
            kr.set_password(KEYRING_SERVICE, KEYRING_USERNAME, blob)
            # A stale plaintext copy is still a plaintext copy.
            _unlink_file()
            return "keyring"
        except Exception:
            pass  # fall through to the file store

    _write_private(TOKEN_FILE, blob)
    return "file"


def load() -> dict[str, Any] | None:
    """Read stored token data, or None when nothing is stored."""
    kr = _keyring()
    if kr is not None:
        try:
            blob = kr.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
            if blob:
                return json.loads(blob)
        except Exception:
            pass

    if not TOKEN_FILE.exists():
        return None
    try:
        return json.loads(TOKEN_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def clear() -> None:
    """Remove stored credentials from every backend."""
    kr = _keyring()
    if kr is not None:
        try:
            kr.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
        except Exception:
            pass
    _unlink_file()


def backend() -> str:
    """Name the backend a save would use right now — for `auth status`."""
    return "keyring" if _keyring() is not None else "file"


def file_mode() -> int | None:
    """Permission bits of the token file, or None when it does not exist."""
    try:
        return stat.S_IMODE(TOKEN_FILE.stat().st_mode)
    except FileNotFoundError:
        return None


def _unlink_file() -> None:
    try:
        TOKEN_FILE.unlink()
    except FileNotFoundError:
        pass


def _write_private(path: Path, text: str) -> None:
    """Write `text` to `path` so it is NEVER world- or group-readable.

    mkstemp creates at 0600 before any byte is written, and os.replace is
    atomic within a filesystem — a reader either sees the old file or the new
    one, never a partial or over-permissive one.
    """
    path.parent.mkdir(parents=True, exist_ok=True, mode=DIR_MODE)
    # mkdir's mode is ignored when the directory already exists, so an
    # inherited-permissive ~/.hanzo/auth is tightened here too.
    os.chmod(path.parent, DIR_MODE)

    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".token-", suffix=".tmp")
    try:
        os.fchmod(fd, FILE_MODE)  # explicit: do not inherit mkstemp's guarantee by luck
        with os.fdopen(fd, "w") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise
