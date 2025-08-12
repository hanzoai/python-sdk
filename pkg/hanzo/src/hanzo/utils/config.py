"""Configuration utilities for Hanzo CLI."""

import os
import json
from typing import Any, Dict, Optional
from pathlib import Path

import yaml


def get_config_paths() -> Dict[str, Path]:
    """Get configuration file paths."""
    paths = {}

    # System config
    if os.name == "nt":  # Windows
        paths["system"] = (
            Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData"))
            / "hanzo"
            / "config.yaml"
        )
    else:  # Unix-like
        paths["system"] = Path("/etc/hanzo/config.yaml")

    # Global config (user)
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    paths["global"] = config_home / "hanzo" / "config.yaml"

    # Local config (project)
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        config_file = parent / ".hanzo" / "config.yaml"
        if config_file.exists():
            paths["local"] = config_file
            break
    else:
        # Default local path even if it doesn't exist
        paths["local"] = cwd / ".hanzo" / "config.yaml"

    return paths


def load_config(path: Path) -> Dict[str, Any]:
    """Load configuration from file."""
    if not path.exists():
        return {}

    try:
        with open(path, "r") as f:
            if path.suffix == ".json":
                return json.load(f)
            else:
                return yaml.safe_load(f) or {}
    except Exception:
        return {}


def save_config(path: Path, config: Dict[str, Any]):
    """Save configuration to file."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        if path.suffix == ".json":
            json.dump(config, f, indent=2)
        else:
            yaml.dump(config, f, default_flow_style=False)


def get_config_value(key: str, default: Any = None, scope: Optional[str] = None) -> Any:
    """Get configuration value from merged configs."""
    paths = get_config_paths()

    # Load configs in priority order (local > global > system)
    configs = []

    if scope == "system" or scope is None:
        if paths["system"].exists():
            configs.append(load_config(paths["system"]))

    if scope == "global" or scope is None:
        if paths["global"].exists():
            configs.append(load_config(paths["global"]))

    if scope == "local" or scope is None:
        if paths.get("local") and paths["local"].exists():
            configs.append(load_config(paths["local"]))

    # Merge configs (later ones override earlier)
    merged = {}
    for config in configs:
        merged.update(config)

    # Get nested key
    keys = key.split(".")
    current = merged

    try:
        for k in keys:
            current = current[k]
        return current
    except (KeyError, TypeError):
        return default


def set_config_value(key: str, value: Any, scope: str = "global"):
    """Set configuration value."""
    paths = get_config_paths()
    path = paths.get(scope, paths["global"])

    config = load_config(path) if path.exists() else {}

    # Set nested key
    keys = key.split(".")
    current = config

    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]

    current[keys[-1]] = value

    save_config(path, config)


def init_config() -> Dict[str, Path]:
    """Initialize configuration structure."""
    paths = get_config_paths()

    # Create global config if it doesn't exist
    if not paths["global"].exists():
        default_config = {
            "default_model": "llama-3.2-3b",
            "default_provider": "local",
            "mcp": {"allowed_paths": [str(Path.home())], "enable_all_tools": True},
            "cluster": {"default_name": "hanzo-local", "default_port": 8000},
        }
        save_config(paths["global"], default_config)

    return paths


def get_default_model() -> str:
    """Get default model from config or environment."""
    return os.environ.get("HANZO_DEFAULT_MODEL") or get_config_value(
        "default_model", "llama-3.2-3b"
    )


def get_api_key(provider: str) -> Optional[str]:
    """Get API key for provider."""
    # Check environment first
    env_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "hanzo": "HANZO_API_KEY",
        "groq": "GROQ_API_KEY",
    }

    if env_key := env_map.get(provider.lower()):
        if key := os.environ.get(env_key):
            return key

    # Check config
    return get_config_value(f"api_keys.{provider}")


def is_local_preferred() -> bool:
    """Check if local execution is preferred."""
    return os.environ.get("HANZO_USE_LOCAL", "").lower() == "true" or get_config_value(
        "prefer_local", False
    )
