"""Configuration system for the modular plugin architecture."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BackendConfig(BaseModel):
    """Configuration for a specific backend."""

    enabled: bool = True
    path: Optional[str] = None
    url: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)


class PluginConfig(BaseModel):
    """Configuration for the plugin system."""

    enabled_backends: List[str] = ["sqlite"]  # Default to lightweight SQLite
    backend_configs: Dict[str, BackendConfig] = Field(default_factory=dict)
    default_user_id: str = "default"
    default_project_id: str = "default"

    class Config:
        # Allow extra fields for flexibility
        extra = "allow"


def get_global_config_path() -> Path:
    """Get the global configuration file path."""
    config_dir = Path.home() / ".config" / "hanzo"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "mcp-settings.json"


def get_project_config_path() -> Optional[Path]:
    """Get the project configuration file path."""
    # Check for common project config locations
    possible_paths = [
        Path(".") / ".hanzo-mcp.json",
        Path(".") / ".hanzo" / "mcp-settings.json",
        Path(".") / "mcp-settings.json",
    ]

    for path in possible_paths:
        if path.exists():
            return path

    return None


def load_config(global_config_path: Optional[Path] = None, project_config_path: Optional[Path] = None) -> PluginConfig:
    """Load configuration from global and project files, with project overriding global."""
    global_path = global_config_path or get_global_config_path()
    project_path = project_config_path or get_project_config_path()

    # Start with default config
    config_data = {
        "enabled_backends": ["sqlite"],
        "backend_configs": {
            "sqlite": {"enabled": True, "path": str(Path.home() / ".hanzo" / "memory.db"), "settings": {}}
        },
        "default_user_id": "default",
        "default_project_id": "default",
    }

    # Load global config if it exists
    if global_path and global_path.exists():
        try:
            with open(global_path, "r") as f:
                global_data = json.load(f)
                # Update config with global settings
                for key, value in global_data.items():
                    if key in config_data:
                        if isinstance(config_data[key], dict) and isinstance(value, dict):
                            # Deep merge dictionaries
                            config_data[key].update(value)
                        else:
                            config_data[key] = value
        except Exception as e:
            print(f"Warning: Could not load global config from {global_path}: {e}")

    # Load project config if it exists (overrides global)
    if project_path and project_path.exists():
        try:
            with open(project_path, "r") as f:
                project_data = json.load(f)
                # Update config with project settings
                for key, value in project_data.items():
                    if key in config_data:
                        if isinstance(config_data[key], dict) and isinstance(value, dict):
                            # Deep merge dictionaries
                            config_data[key].update(value)
                        else:
                            config_data[key] = value
        except Exception as e:
            print(f"Warning: Could not load project config from {project_path}: {e}")

    # Create PluginConfig from the merged data
    return PluginConfig(**config_data)


def save_global_config(config: PluginConfig):
    """Save configuration to the global config file."""
    config_path = get_global_config_path()
    with open(config_path, "w") as f:
        json.dump(config.dict(), f, indent=2)


def get_default_config() -> PluginConfig:
    """Get default configuration."""
    return PluginConfig(
        enabled_backends=["sqlite"],
        backend_configs={
            "sqlite": BackendConfig(enabled=True, path=str(Path.home() / ".hanzo" / "memory.db"), settings={})
        },
    )
