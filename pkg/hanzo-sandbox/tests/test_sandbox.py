"""Tests ported from claw-code sandbox.rs test suite."""

from pathlib import Path

from hanzo_sandbox import (
    ContainerEnvironment,
    FilesystemIsolationMode,
    SandboxConfig,
    SandboxDetectionInputs,
    SandboxRequest,
    build_linux_sandbox_command,
    detect_container_environment_from,
    resolve_sandbox_status_for_request,
)


def test_detects_container_markers_from_multiple_sources():
    detected = detect_container_environment_from(SandboxDetectionInputs(
        env_pairs=[("container", "docker")],
        dockerenv_exists=True,
        containerenv_exists=False,
        proc_1_cgroup="12:memory:/docker/abc",
    ))
    assert detected.in_container
    assert "/.dockerenv" in detected.markers
    assert "env:container=docker" in detected.markers
    assert "/proc/1/cgroup:docker" in detected.markers


def test_no_container_when_no_markers():
    detected = detect_container_environment_from(SandboxDetectionInputs(
        env_pairs=[],
        dockerenv_exists=False,
        containerenv_exists=False,
        proc_1_cgroup=None,
    ))
    assert not detected.in_container
    assert detected.markers == []


def test_containerenv_marker():
    detected = detect_container_environment_from(SandboxDetectionInputs(
        env_pairs=[],
        dockerenv_exists=False,
        containerenv_exists=True,
        proc_1_cgroup=None,
    ))
    assert detected.in_container
    assert "/run/.containerenv" in detected.markers


def test_kubernetes_env_detected():
    detected = detect_container_environment_from(SandboxDetectionInputs(
        env_pairs=[("KUBERNETES_SERVICE_HOST", "10.0.0.1")],
        dockerenv_exists=False,
        containerenv_exists=False,
        proc_1_cgroup=None,
    ))
    assert detected.in_container
    assert "env:KUBERNETES_SERVICE_HOST=10.0.0.1" in detected.markers


def test_empty_env_value_ignored():
    detected = detect_container_environment_from(SandboxDetectionInputs(
        env_pairs=[("DOCKER", "")],
        dockerenv_exists=False,
        containerenv_exists=False,
        proc_1_cgroup=None,
    ))
    assert not detected.in_container


def test_cgroup_multiple_needles():
    detected = detect_container_environment_from(SandboxDetectionInputs(
        env_pairs=[],
        dockerenv_exists=False,
        containerenv_exists=False,
        proc_1_cgroup="1:name=systemd:/kubepods/burstable/containerd/abc",
    ))
    assert detected.in_container
    assert "/proc/1/cgroup:kubepods" in detected.markers
    assert "/proc/1/cgroup:containerd" in detected.markers


def test_markers_sorted_and_deduped():
    detected = detect_container_environment_from(SandboxDetectionInputs(
        env_pairs=[("DOCKER", "1"), ("container", "docker")],
        dockerenv_exists=True,
        containerenv_exists=True,
        proc_1_cgroup="12:memory:/docker/abc",
    ))
    assert detected.markers == sorted(set(detected.markers))


def test_resolves_request_defaults():
    config = SandboxConfig()
    request = config.resolve_request()
    assert request.enabled is True
    assert request.namespace_restrictions is True
    assert request.network_isolation is False
    assert request.filesystem_mode == FilesystemIsolationMode.WORKSPACE_ONLY
    assert request.allowed_mounts == []


def test_resolves_request_with_overrides():
    config = SandboxConfig(
        enabled=True,
        namespace_restrictions=True,
        network_isolation=False,
        filesystem_mode=FilesystemIsolationMode.WORKSPACE_ONLY,
        allowed_mounts=["logs"],
    )
    request = config.resolve_request(
        enabled_override=True,
        namespace_override=False,
        network_override=True,
        filesystem_mode_override=FilesystemIsolationMode.ALLOW_LIST,
        allowed_mounts_override=["tmp"],
    )
    assert request.enabled is True
    assert request.namespace_restrictions is False
    assert request.network_isolation is True
    assert request.filesystem_mode == FilesystemIsolationMode.ALLOW_LIST
    assert request.allowed_mounts == ["tmp"]


def test_config_values_used_when_no_overrides():
    config = SandboxConfig(
        enabled=False,
        namespace_restrictions=False,
        network_isolation=True,
        filesystem_mode=FilesystemIsolationMode.OFF,
        allowed_mounts=["/data"],
    )
    request = config.resolve_request()
    assert request.enabled is False
    assert request.namespace_restrictions is False
    assert request.network_isolation is True
    assert request.filesystem_mode == FilesystemIsolationMode.OFF
    assert request.allowed_mounts == ["/data"]


def test_sandbox_status_unsupported_on_non_linux():
    import sys
    request = SandboxRequest(enabled=True, namespace_restrictions=True, network_isolation=True)
    status = resolve_sandbox_status_for_request(request, Path("/workspace"))
    if sys.platform != "linux":
        assert not status.supported
        assert not status.active
        assert not status.namespace_active
        assert not status.network_active
        assert status.fallback_reason is not None
        assert "unshare" in status.fallback_reason


def test_sandbox_disabled_means_not_active():
    request = SandboxRequest(enabled=False)
    status = resolve_sandbox_status_for_request(request, Path("/workspace"))
    assert not status.active
    assert not status.namespace_active
    assert not status.network_active
    assert not status.filesystem_active


def test_filesystem_active_unless_off():
    request = SandboxRequest(enabled=True, filesystem_mode=FilesystemIsolationMode.WORKSPACE_ONLY)
    status = resolve_sandbox_status_for_request(request, Path("/workspace"))
    assert status.filesystem_active

    request_off = SandboxRequest(enabled=True, filesystem_mode=FilesystemIsolationMode.OFF)
    status_off = resolve_sandbox_status_for_request(request_off, Path("/workspace"))
    assert not status_off.filesystem_active


def test_allowlist_without_mounts_warns():
    request = SandboxRequest(
        enabled=True,
        filesystem_mode=FilesystemIsolationMode.ALLOW_LIST,
        allowed_mounts=[],
    )
    status = resolve_sandbox_status_for_request(request, Path("/workspace"))
    assert status.fallback_reason is not None
    assert "allow-list" in status.fallback_reason


def test_normalize_mounts_relative_resolved():
    request = SandboxRequest(enabled=True, allowed_mounts=["logs", "/absolute/path"])
    status = resolve_sandbox_status_for_request(request, Path("/workspace"))
    assert "/workspace/logs" in status.allowed_mounts
    assert "/absolute/path" in status.allowed_mounts


def test_build_returns_none_on_non_linux():
    import sys
    if sys.platform != "linux":
        from hanzo_sandbox import SandboxStatus
        status = SandboxStatus(
            enabled=True,
            namespace_active=True,
            network_active=True,
            filesystem_mode=FilesystemIsolationMode.WORKSPACE_ONLY,
        )
        result = build_linux_sandbox_command("echo hi", Path("/workspace"), status)
        assert result is None


def test_build_returns_none_when_disabled():
    from hanzo_sandbox import SandboxStatus
    status = SandboxStatus(enabled=False)
    result = build_linux_sandbox_command("echo hi", Path("/workspace"), status)
    assert result is None


def test_enum_values():
    assert FilesystemIsolationMode.OFF.value == "off"
    assert FilesystemIsolationMode.WORKSPACE_ONLY.value == "workspace-only"
    assert FilesystemIsolationMode.ALLOW_LIST.value == "allow-list"
