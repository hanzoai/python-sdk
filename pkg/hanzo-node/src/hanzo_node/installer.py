"""Cross-platform binary installer for hanzo-node."""

import os
import sys
import stat
import shutil
import tarfile
import zipfile
import platform
import tempfile
from pathlib import Path

import httpx

# GitHub release info
GITHUB_REPO = "hanzoai/node"
BINARY_NAME = "hanzo-node"

# Platform detection
PLATFORM_MAP = {
    ("Darwin", "arm64"): "darwin-arm64",
    ("Darwin", "x86_64"): "darwin-x64",
    ("Linux", "x86_64"): "linux-x64",
    ("Linux", "aarch64"): "linux-arm64",
    ("Windows", "AMD64"): "windows-x64",
    ("Windows", "x86_64"): "windows-x64",
}

# Asset name patterns for each platform
ASSET_PATTERNS = {
    "darwin-arm64": ["darwin", "arm64", "macos", "apple"],
    "darwin-x64": ["darwin", "x64", "amd64", "macos"],
    "linux-x64": ["linux", "x64", "amd64"],
    "linux-arm64": ["linux", "arm64", "aarch64"],
    "windows-x64": ["windows", "x64", "amd64", "win"],
}


def get_install_dir() -> Path:
    """Get the installation directory for the binary."""
    if os.name == "nt":  # Windows
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "hanzo" / "bin"
    else:  # Unix-like
        return Path(os.environ.get("HANZO_INSTALL_DIR", Path.home() / ".local" / "bin"))


def get_binary_path() -> Path:
    """Get the full path to the hanzo-node binary."""
    binary = BINARY_NAME
    if os.name == "nt":
        binary += ".exe"
    return get_install_dir() / binary


def is_installed() -> bool:
    """Check if hanzo-node is installed."""
    return get_binary_path().exists()


def get_installed_version() -> str | None:
    """Get the version of the installed binary."""
    import subprocess

    binary = get_binary_path()
    if not binary.exists():
        return None

    try:
        result = subprocess.run(
            [str(binary), "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            # Parse version from output like "hanzo-node 0.1.0"
            parts = result.stdout.strip().split()
            if len(parts) >= 2:
                return parts[1]
        return None
    except Exception:
        return None


def detect_platform() -> str:
    """Detect the current platform."""
    system = platform.system()
    machine = platform.machine()

    key = (system, machine)
    if key not in PLATFORM_MAP:
        raise RuntimeError(f"Unsupported platform: {system}-{machine}")

    return PLATFORM_MAP[key]


def get_latest_release() -> dict:
    """Get the latest release info from GitHub."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

    with httpx.Client(follow_redirects=True, timeout=30) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.json()


def find_asset_url(release: dict, plat: str) -> str | None:
    """Find the download URL for the current platform."""
    patterns = ASSET_PATTERNS.get(plat, [])

    for asset in release.get("assets", []):
        name = asset.get("name", "").lower()

        # Check if asset matches platform patterns
        matches = sum(1 for p in patterns if p in name)
        if matches >= 2:  # Need at least 2 pattern matches
            return asset.get("browser_download_url")

    return None


def download_and_extract(url: str, dest: Path) -> None:
    """Download and extract the binary."""
    dest.parent.mkdir(parents=True, exist_ok=True)

    with httpx.Client(follow_redirects=True, timeout=120) as client:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)

            # Download with progress
            with client.stream("GET", url) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get("content-length", 0))
                downloaded = 0

                for chunk in resp.iter_bytes(chunk_size=8192):
                    tmp.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = (downloaded / total) * 100
                        print(f"\r  downloading... {pct:.0f}%", end="", flush=True)

                print()  # newline after progress

    # Extract based on file type
    try:
        if url.endswith(".tar.gz") or url.endswith(".tgz"):
            _extract_tarball(tmp_path, dest)
        elif url.endswith(".zip"):
            _extract_zip(tmp_path, dest)
        else:
            # Assume raw binary
            shutil.copy2(tmp_path, dest)
    finally:
        tmp_path.unlink(missing_ok=True)

    # Make executable
    if os.name != "nt":
        dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _extract_tarball(archive: Path, dest: Path) -> None:
    """Extract binary from tarball."""
    binary_name = BINARY_NAME

    with tarfile.open(archive, "r:gz") as tar:
        # Find the binary in the archive
        for member in tar.getmembers():
            if member.name.endswith(binary_name) or member.name == binary_name:
                # Extract to temp location then move
                with tempfile.TemporaryDirectory() as tmpdir:
                    tar.extract(member, tmpdir)
                    extracted = Path(tmpdir) / member.name
                    shutil.copy2(extracted, dest)
                    return

        # If not found by name, try extracting all and finding it
        with tempfile.TemporaryDirectory() as tmpdir:
            tar.extractall(tmpdir)  # noqa: S202
            for f in Path(tmpdir).rglob(binary_name):
                if f.is_file():
                    shutil.copy2(f, dest)
                    return

    raise RuntimeError(f"Could not find {binary_name} in archive")


def _extract_zip(archive: Path, dest: Path) -> None:
    """Extract binary from zip."""
    binary_name = BINARY_NAME
    if os.name == "nt":
        binary_name += ".exe"

    with zipfile.ZipFile(archive, "r") as zf:
        # Find the binary in the archive
        for name in zf.namelist():
            if name.endswith(binary_name) or os.path.basename(name) == binary_name:
                with tempfile.TemporaryDirectory() as tmpdir:
                    zf.extract(name, tmpdir)
                    extracted = Path(tmpdir) / name
                    shutil.copy2(extracted, dest)
                    return

        # If not found, extract all and search
        with tempfile.TemporaryDirectory() as tmpdir:
            zf.extractall(tmpdir)  # noqa: S202
            for f in Path(tmpdir).rglob(binary_name):
                if f.is_file():
                    shutil.copy2(f, dest)
                    return

    raise RuntimeError(f"Could not find {binary_name} in archive")


def install(force: bool = False, version: str | None = None) -> Path:
    """
    Install hanzo-node binary.

    Args:
        force: Force reinstall even if already installed
        version: Specific version to install (default: latest)

    Returns:
        Path to installed binary
    """
    binary_path = get_binary_path()

    if binary_path.exists() and not force:
        installed_ver = get_installed_version()
        print(f"  hanzo-node {installed_ver or '?'} already installed at {binary_path}")
        return binary_path

    plat = detect_platform()
    print(f"  platform: {plat}")

    # Get release info
    print("  fetching release info...")
    if version:
        # TODO: fetch specific version
        release = get_latest_release()
    else:
        release = get_latest_release()

    release_version = release.get("tag_name", "unknown")
    print(f"  version: {release_version}")

    # Find asset URL
    asset_url = find_asset_url(release, plat)
    if not asset_url:
        raise RuntimeError(f"No binary available for {plat}")

    print(f"  url: {asset_url}")

    # Download and install
    download_and_extract(asset_url, binary_path)

    print(f"  ✓ installed to {binary_path}")

    # Check if in PATH
    install_dir = str(get_install_dir())
    if install_dir not in os.environ.get("PATH", ""):
        print(f'\n  add to PATH: export PATH="{install_dir}:$PATH"')

    return binary_path


def uninstall() -> bool:
    """
    Uninstall hanzo-node binary.

    Returns:
        True if uninstalled, False if wasn't installed
    """
    binary_path = get_binary_path()

    if not binary_path.exists():
        print("  hanzo-node is not installed")
        return False

    binary_path.unlink()
    print(f"  ✓ removed {binary_path}")
    return True
