"""Linux sandbox isolation via unshare -- ported from claw-code sandbox.rs."""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class FilesystemIsolationMode(Enum):
    OFF = "off"
    WORKSPACE_ONLY = "workspace-only"
    ALLOW_LIST = "allow-list"


@dataclass
class SandboxConfig:
    enabled: bool | None = None
    namespace_restrictions: bool | None = None
    network_isolation: bool | None = None
    filesystem_mode: FilesystemIsolationMode | None = None
    allowed_mounts: list[str] = field(default_factory=list)

    def resolve_request(
        self,
        enabled_override: bool | None = None,
        namespace_override: bool | None = None,
        network_override: bool | None = None,
        filesystem_mode_override: FilesystemIsolationMode | None = None,
        allowed_mounts_override: list[str] | None = None,
    ) -> SandboxRequest:
        enabled = enabled_override if enabled_override is not None else (self.enabled if self.enabled is not None else True)
        ns = namespace_override if namespace_override is not None else (self.namespace_restrictions if self.namespace_restrictions is not None else True)
        net = network_override if network_override is not None else (self.network_isolation if self.network_isolation is not None else False)
        fs_mode = filesystem_mode_override or self.filesystem_mode or FilesystemIsolationMode.WORKSPACE_ONLY
        mounts = allowed_mounts_override if allowed_mounts_override is not None else list(self.allowed_mounts)
        return SandboxRequest(
            enabled=enabled,
            namespace_restrictions=ns,
            network_isolation=net,
            filesystem_mode=fs_mode,
            allowed_mounts=mounts,
        )


@dataclass
class SandboxRequest:
    enabled: bool = True
    namespace_restrictions: bool = True
    network_isolation: bool = False
    filesystem_mode: FilesystemIsolationMode = FilesystemIsolationMode.WORKSPACE_ONLY
    allowed_mounts: list[str] = field(default_factory=list)


@dataclass
class ContainerEnvironment:
    in_container: bool = False
    markers: list[str] = field(default_factory=list)


@dataclass
class SandboxDetectionInputs:
    env_pairs: list[tuple[str, str]] = field(default_factory=list)
    dockerenv_exists: bool = False
    containerenv_exists: bool = False
    proc_1_cgroup: str | None = None


@dataclass
class SandboxStatus:
    enabled: bool = False
    requested: SandboxRequest = field(default_factory=SandboxRequest)
    supported: bool = False
    active: bool = False
    namespace_supported: bool = False
    namespace_active: bool = False
    network_supported: bool = False
    network_active: bool = False
    filesystem_mode: FilesystemIsolationMode = FilesystemIsolationMode.WORKSPACE_ONLY
    filesystem_active: bool = False
    allowed_mounts: list[str] = field(default_factory=list)
    in_container: bool = False
    container_markers: list[str] = field(default_factory=list)
    fallback_reason: str | None = None


@dataclass
class LinuxSandboxCommand:
    program: str = ""
    args: list[str] = field(default_factory=list)
    env: list[tuple[str, str]] = field(default_factory=list)


_CONTAINER_ENV_KEYS = frozenset({"container", "docker", "podman", "kubernetes_service_host"})
_CGROUP_NEEDLES = ("docker", "containerd", "kubepods", "podman", "libpod")


def detect_container_environment() -> ContainerEnvironment:
    proc_1_cgroup: str | None = None
    try:
        proc_1_cgroup = Path("/proc/1/cgroup").read_text()
    except OSError:
        pass
    return detect_container_environment_from(SandboxDetectionInputs(
        env_pairs=list(os.environ.items()),
        dockerenv_exists=Path("/.dockerenv").exists(),
        containerenv_exists=Path("/run/.containerenv").exists(),
        proc_1_cgroup=proc_1_cgroup,
    ))


def detect_container_environment_from(inputs: SandboxDetectionInputs) -> ContainerEnvironment:
    markers: list[str] = []
    if inputs.dockerenv_exists:
        markers.append("/.dockerenv")
    if inputs.containerenv_exists:
        markers.append("/run/.containerenv")
    for key, value in inputs.env_pairs:
        if key.lower() in _CONTAINER_ENV_KEYS and value:
            markers.append(f"env:{key}={value}")
    if inputs.proc_1_cgroup is not None:
        for needle in _CGROUP_NEEDLES:
            if needle in inputs.proc_1_cgroup:
                markers.append(f"/proc/1/cgroup:{needle}")
    markers = sorted(set(markers))
    return ContainerEnvironment(in_container=bool(markers), markers=markers)


def _command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def _is_linux() -> bool:
    return sys.platform == "linux"


def _normalize_mounts(mounts: list[str], cwd: Path) -> list[str]:
    result: list[str] = []
    for mount in mounts:
        p = Path(mount)
        result.append(str(p if p.is_absolute() else cwd / p))
    return result


def resolve_sandbox_status(config: SandboxConfig, cwd: Path) -> SandboxStatus:
    request = config.resolve_request()
    return resolve_sandbox_status_for_request(request, cwd)


def resolve_sandbox_status_for_request(request: SandboxRequest, cwd: Path) -> SandboxStatus:
    container = detect_container_environment()
    namespace_supported = _is_linux() and _command_exists("unshare")
    network_supported = namespace_supported
    filesystem_active = request.enabled and request.filesystem_mode != FilesystemIsolationMode.OFF
    fallback_reasons: list[str] = []

    if request.enabled and request.namespace_restrictions and not namespace_supported:
        fallback_reasons.append("namespace isolation unavailable (requires Linux with `unshare`)")
    if request.enabled and request.network_isolation and not network_supported:
        fallback_reasons.append("network isolation unavailable (requires Linux with `unshare`)")
    if request.enabled and request.filesystem_mode == FilesystemIsolationMode.ALLOW_LIST and not request.allowed_mounts:
        fallback_reasons.append("filesystem allow-list requested without configured mounts")

    active = request.enabled and (not request.namespace_restrictions or namespace_supported) and (not request.network_isolation or network_supported)
    allowed_mounts = _normalize_mounts(request.allowed_mounts, cwd)

    return SandboxStatus(
        enabled=request.enabled,
        requested=request,
        supported=namespace_supported,
        active=active,
        namespace_supported=namespace_supported,
        namespace_active=request.enabled and request.namespace_restrictions and namespace_supported,
        network_supported=network_supported,
        network_active=request.enabled and request.network_isolation and network_supported,
        filesystem_mode=request.filesystem_mode,
        filesystem_active=filesystem_active,
        allowed_mounts=allowed_mounts,
        in_container=container.in_container,
        container_markers=container.markers,
        fallback_reason="; ".join(fallback_reasons) if fallback_reasons else None,
    )


def build_linux_sandbox_command(command: str, cwd: Path, status: SandboxStatus) -> LinuxSandboxCommand | None:
    if not _is_linux() or not status.enabled or (not status.namespace_active and not status.network_active):
        return None

    args = ["--user", "--map-root-user", "--mount", "--ipc", "--pid", "--uts", "--fork"]
    if status.network_active:
        args.append("--net")
    args.extend(["sh", "-lc", command])

    sandbox_home = str(cwd / ".sandbox-home")
    sandbox_tmp = str(cwd / ".sandbox-tmp")
    env: list[tuple[str, str]] = [
        ("HOME", sandbox_home),
        ("TMPDIR", sandbox_tmp),
        ("SANDBOX_FILESYSTEM_MODE", status.filesystem_mode.value),
        ("SANDBOX_ALLOWED_MOUNTS", ":".join(status.allowed_mounts)),
    ]
    path = os.environ.get("PATH")
    if path is not None:
        env.append(("PATH", path))

    return LinuxSandboxCommand(program="unshare", args=args, env=env)
