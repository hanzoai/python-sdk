"""The browser's way onto this machine's ZAP router: Chrome native messaging.

A browser extension cannot open a unix socket, so Chrome starts this helper for
it (host ``ai.hanzo.zap``, allowed for the Hanzo extension's id only) and talks
to it over stdio. The helper relays ZAP router envelopes both ways between that
stdio and the router's unix socket. No port and no pairing: Chrome's origin
check and the socket's 0600 owner are the trust.

The helper stands for the router like every other ZAP process
(``zapd.embed()``), so a browser with no other Hanzo process running still
has one.

Native messaging frames are a u32 native-endian length and UTF-8 JSON; each
envelope rides base64 in ``{"z": ...}``. Envelopes on the socket carry their
own little-endian u32 length.
"""

from __future__ import annotations

import base64
import json
import os
import socket
import struct
import sys
import threading
import time
from pathlib import Path

NAME = "ai.hanzo.zap"
EXTENSIONS = ("biingenefmanpecedoafkfajbnlgdmbl",)

# Where each Chromium-family browser looks for a user-level host manifest.
_LINUX = (
    "~/.config/google-chrome",
    "~/.config/google-chrome-beta",
    "~/.config/google-chrome-unstable",
    "~/.config/chromium",
    "~/.config/BraveSoftware/Brave-Browser",
    "~/.config/microsoft-edge",
    "~/.config/vivaldi",
)
_DARWIN = (
    "~/Library/Application Support/Google/Chrome",
    "~/Library/Application Support/Google/Chrome Beta",
    "~/Library/Application Support/Chromium",
    "~/Library/Application Support/BraveSoftware/Brave-Browser",
    "~/Library/Application Support/Microsoft Edge",
    "~/Library/Application Support/Vivaldi",
)


def _executable() -> str | None:
    """The installed ``hanzo-zap-host`` beside this interpreter's scripts."""
    for d in (Path(sys.executable).parent, Path.home() / ".local" / "bin"):
        p = d / "hanzo-zap-host"
        if p.exists():
            return str(p)
    return None


def install() -> list[str]:
    """Register the host with every browser installed for this user.

    Idempotent and silent: a browser that is not installed is skipped, and a
    manifest already naming this executable is left as it is.
    """
    exe = _executable()
    if not exe:
        return []
    manifest = {
        "name": NAME,
        "description": "Hanzo ZAP: the browser's seat on this machine's router",
        "path": exe,
        "type": "stdio",
        "allowed_origins": [f"chrome-extension://{e}/" for e in EXTENSIONS],
    }
    body = json.dumps(manifest, indent=2) + "\n"
    roots = _DARWIN if sys.platform == "darwin" else _LINUX
    written = []
    for root in roots:
        base = Path(root).expanduser()
        if not base.is_dir():
            continue
        target = base / "NativeMessagingHosts" / f"{NAME}.json"
        try:
            if target.exists() and target.read_text() == body:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body)
            written.append(str(target))
        except OSError:
            continue
    return written


def _read(stream) -> dict | None:
    head = stream.read(4)
    if len(head) < 4:
        return None
    (n,) = struct.unpack("=I", head)
    data = stream.read(n)
    if len(data) < n:
        return None
    return json.loads(data)


def _dial(path: str, deadline: float) -> socket.socket:
    """The router's socket, waiting out an election in progress."""
    while True:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            s.connect(path)
            return s
        except OSError:
            s.close()
            if time.monotonic() > deadline:
                raise
            time.sleep(0.05)


def main() -> None:
    # stdout is the native messaging channel: keep a private handle on it and
    # point fd 1 at stderr, so nothing else this process prints can corrupt it.
    out = os.fdopen(os.dup(1), "wb", buffering=0)
    os.dup2(2, 1)
    sys.stdout = sys.stderr

    import zapd

    zapd.embed()
    sock = _dial(zapd.socket_path(), time.monotonic() + 10)
    lock = threading.Lock()

    def up() -> None:
        """Router → browser: split the socket into envelopes, one message each."""
        buf = b""
        while True:
            chunk = sock.recv(1 << 16)
            if not chunk:
                os._exit(0)
            buf += chunk
            while len(buf) >= 4:
                (n,) = struct.unpack("<I", buf[:4])
                if len(buf) < 4 + n:
                    break
                frame, buf = buf[: 4 + n], buf[4 + n :]
                msg = json.dumps({"z": base64.b64encode(frame).decode()}, separators=(",", ":")).encode()
                with lock:
                    out.write(struct.pack("=I", len(msg)) + msg)

    threading.Thread(target=up, daemon=True).start()

    stdin = sys.stdin.buffer
    while True:
        m = _read(stdin)
        if m is None:
            os._exit(0)
        z = m.get("z")
        if isinstance(z, str):
            sock.sendall(base64.b64decode(z))


if __name__ == "__main__":
    main()
