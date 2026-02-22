"""Parse hanzo.toml deployment manifests into PaaS container payloads.

The hanzo.toml file is the project-level deployment manifest for Hanzo PaaS.
It maps cleanly to the PaaS container API:

    [app]
    name = "my-app"
    type = "deployment"
    dockerfile = "Dockerfile"

    [env]
    NODE_ENV = "production"

    [networking]
    port = 3000
    ingress = true
    force_https = true

    [resources]
    cpu = "2000m"      # millicores or "2" for cores
    memory = "2048Mi"  # mebibytes or "2Gi" for gibibytes

    [storage]
    enabled = true
    mount = "/data"
    size = "1Gi"

    [deploy]
    replicas = 1
    strategy = "RollingUpdate"
    command = "node index.js"

    [probes.readiness]
    path = "/health"
    port = 3000
    period = 30
    timeout = 10

    [probes.liveness]
    path = "/health"
    port = 3000
    period = 30
    timeout = 10
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Python 3.11+ has tomllib in stdlib; older versions need tomli.
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError as exc:
        raise ImportError(
            "hanzo.toml support requires the 'tomli' package on Python <3.11. "
            "Install it with: pip install tomli"
        ) from exc

DEFAULT_CONFIG_FILENAME = "hanzo.toml"


def find_config(path: str | Path | None = None) -> Path | None:
    """Locate hanzo.toml — explicit path or CWD search."""
    if path:
        p = Path(path)
        if p.is_file():
            return p
        return None
    cwd = Path.cwd()
    candidate = cwd / DEFAULT_CONFIG_FILENAME
    return candidate if candidate.is_file() else None


def load_config(path: str | Path) -> dict[str, Any]:
    """Read and parse a hanzo.toml file."""
    with open(path, "rb") as f:
        return tomllib.load(f)


def _parse_cpu(raw: str | int) -> tuple[int, str]:
    """Parse CPU value like '2000m' or '2' into (value, type)."""
    s = str(raw).strip()
    if s.endswith("m"):
        return int(s[:-1]), "millicores"
    return int(float(s) * 1000), "millicores"


def _parse_memory(raw: str | int) -> tuple[int, str]:
    """Parse memory value like '2048Mi' or '2Gi' into (value, type)."""
    s = str(raw).strip()
    if s.endswith("Gi"):
        return int(s[:-2]), "gibibyte"
    if s.endswith("Mi"):
        return int(s[:-2]), "mebibyte"
    # Plain number = mebibytes
    return int(s), "mebibyte"


def _parse_storage_size(raw: str | int) -> tuple[int, str]:
    """Parse storage size like '1Gi' or '500Mi'."""
    s = str(raw).strip()
    if s.endswith("Gi"):
        return int(s[:-2]), "gibibyte"
    if s.endswith("Mi"):
        return int(s[:-2]), "mebibyte"
    return int(s), "gibibyte"


def _build_probe(cfg: dict[str, Any], port_default: int) -> dict[str, Any]:
    """Convert a [probes.*] section into PaaS probe config."""
    return {
        "enabled": True,
        "checkMechanism": "httpGet",
        "httpPath": cfg.get("path", "/health"),
        "httpPort": cfg.get("port", port_default),
        "initialDelaySeconds": cfg.get("initial_delay", 30),
        "periodSeconds": cfg.get("period", 30),
        "timeoutSeconds": cfg.get("timeout", 10),
        "failureThreshold": cfg.get("failure_threshold", 3),
    }


def config_to_payload(cfg: dict[str, Any]) -> dict[str, Any]:
    """Convert a parsed hanzo.toml dict into a PaaS container creation payload."""
    app = cfg.get("app", {})
    env = cfg.get("env", {})
    networking = cfg.get("networking", {})
    resources = cfg.get("resources", {})
    storage = cfg.get("storage", {})
    deploy = cfg.get("deploy", {})
    probes_cfg = cfg.get("probes", {})

    name = app.get("name", "app")
    deploy_type = app.get("type", "deployment")
    port = networking.get("port", 3000)

    # Resources
    cpu_val, cpu_type = _parse_cpu(resources.get("cpu", "200m"))
    mem_val, mem_type = _parse_memory(resources.get("memory", "256Mi"))

    payload: dict[str, Any] = {
        "name": name,
        "type": deploy_type,
        "networking": {
            "containerPort": port,
            "ingress": {"enabled": networking.get("ingress", False)},
            "customDomain": {"enabled": False},
            "tcpProxy": {"enabled": False},
        },
        "podConfig": {
            "restartPolicy": "Always",
            "cpuRequest": cpu_val // 2,
            "cpuRequestType": cpu_type,
            "cpuLimit": cpu_val,
            "cpuLimitType": cpu_type,
            "memoryRequest": mem_val // 2,
            "memoryRequestType": mem_type,
            "memoryLimit": mem_val,
            "memoryLimitType": mem_type,
        },
        "storageConfig": {
            "enabled": storage.get("enabled", False),
        },
        "probes": {
            "startup": {"enabled": False},
            "readiness": {"enabled": False},
            "liveness": {"enabled": False},
        },
    }

    # Storage
    if storage.get("enabled", False):
        size_val, size_type = _parse_storage_size(storage.get("size", "1Gi"))
        payload["storageConfig"] = {
            "enabled": True,
            "mountPath": storage.get("mount", "/data"),
            "size": size_val,
            "sizeType": size_type,
            "accessModes": ["ReadWriteOnce"],
        }

    # Probes
    for probe_name in ("readiness", "liveness", "startup"):
        if probe_name in probes_cfg:
            payload["probes"][probe_name] = _build_probe(probes_cfg[probe_name], port)

    # Deployment config
    if deploy_type == "deployment":
        payload["deploymentConfig"] = {
            "desiredReplicas": deploy.get("replicas", 1),
            "strategy": deploy.get("strategy", "RollingUpdate"),
            "rollingUpdate": {
                "maxSurge": 30,
                "maxSurgeType": "percentage",
                "maxUnavailable": 0,
                "maxUnavailableType": "number",
            },
            "revisionHistoryLimit": 10,
            "cpuMetric": {"enabled": False},
            "memoryMetric": {"enabled": False},
        }

    # Environment variables
    if env:
        payload["variables"] = [
            {"name": k, "value": str(v)} for k, v in env.items()
        ]

    # Source — always repo (Dockerfile-based) for hanzo.toml
    dockerfile = app.get("dockerfile", "Dockerfile")
    payload["repoOrRegistry"] = "repo"
    payload["repo"] = {
        "dockerfile": dockerfile,
    }

    return payload
