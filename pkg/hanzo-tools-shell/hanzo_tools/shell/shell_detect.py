"""Shell detection for hanzo-mcp.

Detects the user's active shell and login shell to expose only
the relevant shell tool via MCP. On Mac with Homebrew, this will
detect and use /opt/homebrew/bin/zsh if that's what the user has
configured.

Environment variables for override:
- HANZO_MCP_SHELL: Force a specific shell (e.g., "zsh", "bash")
- HANZO_MCP_FORCE_SHELL: Force a specific shell path (e.g., "/opt/homebrew/bin/zsh")
"""

from __future__ import annotations

import os
import shlex
import shutil
import platform
import subprocess
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Common shells (names you might see from `ps -o comm=`) and typical full paths.
KNOWN_SHELL_NAMES = {
    "zsh",
    "bash",
    "fish",
    "sh",
    "ksh",
    "tcsh",
    "csh",
    "dash",
    "nu",
    "xonsh",
    "pwsh",
    "powershell",
}
KNOWN_SHELL_PATH_BASENAMES = KNOWN_SHELL_NAMES | {"busybox"}  # sometimes sh is busybox

# Shells we support with dedicated tools
SUPPORTED_SHELLS = {"zsh", "bash", "fish", "dash", "ksh", "tcsh", "csh"}


@dataclass(frozen=True)
class ShellInfo:
    """Information about detected shells."""

    # "Login shell" as configured on the user account (what ssh/login uses).
    login_shell: Optional[str]
    # The shell that appears to have invoked this process (best-effort).
    invoking_shell: Optional[str]
    # $SHELL (often, but not always, matches login shell)
    env_shell: Optional[str]
    # Debug evidence for logging / telemetry.
    evidence: Dict[str, str]


def _run(cmd: List[str]) -> Tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    try:
        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except Exception as e:
        return 127, "", f"{type(e).__name__}: {e}"


def _which(cmd: str) -> Optional[str]:
    """Find command in PATH."""
    paths = os.environ.get("PATH", "").split(os.pathsep)
    for d in paths:
        p = os.path.join(d, cmd)
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None


def _parse_passwd_line(line: str) -> Optional[str]:
    """Parse passwd format: name:pw:uid:gid:gecos:dir:shell"""
    parts = line.split(":")
    if len(parts) >= 7:
        shell = parts[6].strip()
        return shell or None
    return None


def get_login_shell() -> Tuple[Optional[str], Dict[str, str]]:
    """
    Tries multiple sources to determine the *account login shell*.
    Order of preference:
      1) Python's pwd database (POSIX)
      2) macOS: `id -P user` (NSS/passwd view)
      3) Linux: `getent passwd user`
    """
    evidence: Dict[str, str] = {}
    user = os.environ.get("USER") or os.environ.get("LOGNAME") or ""

    # POSIX: pwd module uses NSS; on macOS it generally reflects Directory Services.
    if os.name == "posix":
        try:
            import pwd

            if user:
                shell = pwd.getpwnam(user).pw_shell
                evidence["pwd.getpwnam"] = shell
                if shell:
                    return shell, evidence
        except Exception as e:
            evidence["pwd.getpwnam_error"] = f"{type(e).__name__}: {e}"

    system = platform.system().lower()

    # macOS: `id -P user` prints passwd-style record.
    if system == "darwin" and user:
        rc, out, err = _run(["id", "-P", user])
        evidence["id_-P_rc"] = str(rc)
        if err:
            evidence["id_-P_err"] = err
        if rc == 0 and out:
            evidence["id_-P_out"] = out
            # id -P output is colon-separated, shell is the last field.
            shell = out.split(":")[-1].strip() or None
            if shell:
                return shell, evidence

    # Linux/BSD: getent is the most robust CLI view into NSS.
    if user and _which("getent"):
        rc, out, err = _run(["getent", "passwd", user])
        evidence["getent_rc"] = str(rc)
        if err:
            evidence["getent_err"] = err
        if rc == 0 and out:
            evidence["getent_out"] = out
            shell = _parse_passwd_line(out)
            if shell:
                return shell, evidence

    # As a last resort: $SHELL (not authoritative for login shell)
    env_shell = os.environ.get("SHELL")
    if env_shell:
        evidence["fallback_env_SHELL"] = env_shell
    return env_shell, evidence


def _ps_comm(pid: int) -> Optional[str]:
    """Get executable name for a process."""
    rc, out, _ = _run(["ps", "-p", str(pid), "-o", "comm="])
    if rc == 0 and out:
        return out.strip()
    return None


def _ps_args(pid: int) -> Optional[str]:
    """Get full command line for a process."""
    rc, out, _ = _run(["ps", "-p", str(pid), "-o", "args="])
    if rc == 0 and out:
        return out.strip()
    return None


def get_invoking_shell(max_hops: int = 12) -> Tuple[Optional[str], Dict[str, str]]:
    """
    Best-effort guess of the *shell that invoked this process* by walking parent PIDs.
    This is useful if hanzo-mcp is launched from a user's interactive shell.
    If your process is daemonized / launched by a service manager, this may return None.
    """
    evidence: Dict[str, str] = {}
    if os.name != "posix":
        return None, {"note": "invoking shell detection is POSIX-only"}

    pid = os.getpid()
    ppid = os.getppid()
    evidence["self_pid"] = str(pid)
    evidence["self_ppid"] = str(ppid)

    # Walk parent chain looking for a known shell.
    cur = ppid
    for hop in range(max_hops):
        comm = _ps_comm(cur) or ""
        args = _ps_args(cur) or ""
        evidence[f"hop_{hop}_pid"] = str(cur)
        if comm:
            evidence[f"hop_{hop}_comm"] = comm
        if args:
            evidence[f"hop_{hop}_args"] = args

        base = os.path.basename(comm).strip()
        if base in KNOWN_SHELL_PATH_BASENAMES:
            # Try to return a plausible full path if args contains one.
            if os.path.isabs(comm):
                return comm, evidence
            # Pull first token from args if it looks like a path to shell.
            try:
                argv0 = shlex.split(args)[0]
            except Exception:
                argv0 = ""
            if argv0 and (os.path.isabs(argv0) or os.path.basename(argv0) in KNOWN_SHELL_NAMES):
                return argv0, evidence
            return comm, evidence

        # Next parent: use `ps -o ppid=` to get parent of parent.
        rc, out, _ = _run(["ps", "-p", str(cur), "-o", "ppid="])
        if rc != 0 or not out.strip():
            break
        next_ppid = int(out.strip())
        if next_ppid <= 1 or next_ppid == cur:
            break
        cur = next_ppid

    return None, evidence


def normalize_shell(shell: Optional[str]) -> Optional[str]:
    """Normalize shell path - return as-is if valid."""
    if not shell:
        return None
    shell = shell.strip()
    return shell or None


def shell_basename(shell: Optional[str]) -> Optional[str]:
    """Get the basename of a shell path (e.g., '/opt/homebrew/bin/zsh' -> 'zsh')."""
    if not shell:
        return None
    return os.path.basename(shell).strip() or None


def choose_default_shell(info: ShellInfo) -> str:
    """
    Policy: prefer invoking shell if detected; else login shell; else $SHELL; else /bin/sh.
    """
    for candidate in (info.invoking_shell, info.login_shell, info.env_shell):
        c = normalize_shell(candidate)
        if c:
            return c
    # Very conservative fallback
    return "C:\\Windows\\System32\\cmd.exe" if os.name == "nt" else "/bin/sh"


def detect_shells() -> ShellInfo:
    """Detect all shell information."""
    login_shell, login_ev = get_login_shell()
    invoking_shell, inv_ev = get_invoking_shell()
    env_shell = os.environ.get("SHELL")

    evidence: Dict[str, str] = {}
    evidence.update({f"login.{k}": v for k, v in login_ev.items()})
    evidence.update({f"invoking.{k}": v for k, v in inv_ev.items()})
    if env_shell:
        evidence["env.SHELL"] = env_shell

    return ShellInfo(
        login_shell=normalize_shell(login_shell),
        invoking_shell=normalize_shell(invoking_shell),
        env_shell=normalize_shell(env_shell),
        evidence=evidence,
    )


def resolve_shell_path(shell_name: str) -> Optional[str]:
    """
    Resolve a shell name to its full path, preferring Homebrew on macOS.

    Args:
        shell_name: Shell name (e.g., 'zsh', 'bash')

    Returns:
        Full path to shell or None if not found
    """
    # Check environment override first
    force_shell = os.environ.get("HANZO_MCP_FORCE_SHELL")
    if force_shell:
        if os.path.isfile(force_shell) and os.access(force_shell, os.X_OK):
            return force_shell

    # Priority paths - Homebrew first on macOS
    search_paths = [
        f"/opt/homebrew/bin/{shell_name}",  # Apple Silicon Homebrew
        f"/usr/local/bin/{shell_name}",  # Intel Homebrew
        f"/bin/{shell_name}",  # System
        f"/usr/bin/{shell_name}",  # System alternative
    ]

    for path in search_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    # Fallback to which
    return shutil.which(shell_name)


def get_active_shell() -> Tuple[str, str]:
    """
    Get the user's active shell name and path.

    Respects environment overrides:
    - HANZO_MCP_SHELL: Force shell name (e.g., "zsh")
    - HANZO_MCP_FORCE_SHELL: Force shell path (e.g., "/opt/homebrew/bin/zsh")

    Returns:
        Tuple of (shell_name, shell_path)
        e.g., ("zsh", "/opt/homebrew/bin/zsh")
    """
    # Check for explicit override
    override_shell = os.environ.get("HANZO_MCP_SHELL")
    if override_shell:
        override_shell = override_shell.strip().lower()
        if override_shell in SUPPORTED_SHELLS:
            path = resolve_shell_path(override_shell)
            if path:
                return override_shell, path

    # Check for explicit path override
    force_path = os.environ.get("HANZO_MCP_FORCE_SHELL")
    if force_path and os.path.isfile(force_path) and os.access(force_path, os.X_OK):
        name = shell_basename(force_path)
        if name and name in SUPPORTED_SHELLS:
            return name, force_path
        # If it's an unknown shell, still use it but expose as "shell"
        return name or "shell", force_path

    # Detect from environment
    info = detect_shells()
    chosen_path = choose_default_shell(info)
    chosen_name = shell_basename(chosen_path)

    # Map to supported shell name
    if chosen_name in SUPPORTED_SHELLS:
        # Resolve to best available path (prefer Homebrew)
        best_path = resolve_shell_path(chosen_name)
        return chosen_name, best_path or chosen_path

    # Fallback: if detected shell isn't supported, default to zsh
    for fallback in ["zsh", "bash", "fish", "dash"]:
        path = resolve_shell_path(fallback)
        if path:
            return fallback, path

    # Ultimate fallback
    return "sh", "/bin/sh"


def get_shell_tool_class(shell_name: str):
    """
    Get the appropriate shell tool class for the given shell name.

    Args:
        shell_name: Shell name (e.g., 'zsh', 'bash')

    Returns:
        Shell tool class or None if not supported
    """
    # Import here to avoid circular imports
    from hanzo_tools.shell.shell_tools import CshTool, KshTool, ZshTool, BashTool, DashTool, FishTool, TcshTool

    shell_map = {
        "zsh": ZshTool,
        "bash": BashTool,
        "fish": FishTool,
        "dash": DashTool,
        "ksh": KshTool,
        "ksh93": KshTool,  # Alias
        "pdksh": KshTool,  # Alias
        "mksh": KshTool,  # Alias
        "tcsh": TcshTool,
        "csh": CshTool,
    }

    return shell_map.get(shell_name.lower())


# Cache for shell detection (avoid repeated subprocess calls)
_cached_shell: Optional[Tuple[str, str]] = None


def get_cached_active_shell() -> Tuple[str, str]:
    """Get cached active shell info (detects once per process)."""
    global _cached_shell
    if _cached_shell is None:
        _cached_shell = get_active_shell()
    return _cached_shell


def clear_shell_cache():
    """Clear the shell detection cache (useful for testing)."""
    global _cached_shell
    _cached_shell = None


if __name__ == "__main__":
    info = detect_shells()
    shell_name, shell_path = get_active_shell()

    print("=== Shell Detection ===")
    print(f"login_shell   : {info.login_shell}")
    print(f"invoking_shell: {info.invoking_shell}")
    print(f"env_shell     : {info.env_shell}")
    print(f"")
    print(f"=== Active Shell ===")
    print(f"name          : {shell_name}")
    print(f"path          : {shell_path}")
    print(f"")
    print(f"=== Environment ===")
    print(f"HANZO_MCP_SHELL      : {os.environ.get('HANZO_MCP_SHELL', '(not set)')}")
    print(f"HANZO_MCP_FORCE_SHELL: {os.environ.get('HANZO_MCP_FORCE_SHELL', '(not set)')}")
