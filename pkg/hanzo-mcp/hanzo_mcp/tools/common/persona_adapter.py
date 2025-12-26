"""Adapter to load personalities from hanzo-persona package.

This module bridges the hanzo-persona package (which has rich persona profiles)
with the hanzo-mcp tool personality system.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from hanzo_mcp.tools.common.personality import (
    AI_TOOLS,
    UNIX_TOOLS,
    BUILD_TOOLS,
    SEARCH_TOOLS,
    VECTOR_TOOLS,
    DATABASE_TOOLS,
    ESSENTIAL_TOOLS,
    CLIToolDef,
    ToolPersonality,
    PersonalityRegistry,
)

logger = logging.getLogger(__name__)


# Tool mappings for persona categories
CATEGORY_TOOL_MAPPINGS = {
    "programmer": ESSENTIAL_TOOLS + ["symbols", "multi_edit"] + SEARCH_TOOLS + BUILD_TOOLS,
    "scientist": ESSENTIAL_TOOLS + ["jupyter", "critic"] + AI_TOOLS + VECTOR_TOOLS,
    "philosopher": ESSENTIAL_TOOLS + ["critic", "think", "search"],
    "artist": ESSENTIAL_TOOLS + ["watch", "jupyter"] + AI_TOOLS,
    "leader": ESSENTIAL_TOOLS + ["todo", "rules", "agent"] + AI_TOOLS,
    "writer": ESSENTIAL_TOOLS + ["search", "critic", "todo"],
    "mathematician": ESSENTIAL_TOOLS + ["jupyter", "symbols", "critic"],
    "musician": ESSENTIAL_TOOLS + ["watch", "todo"],
    "athlete": ESSENTIAL_TOOLS + ["todo", "watch", "process"],
    "entrepreneur": ESSENTIAL_TOOLS + ["todo", "agent", "consensus"] + BUILD_TOOLS + DATABASE_TOOLS,
    "activist": ESSENTIAL_TOOLS + ["search", "todo", "rules"],
    "religious_leader": ESSENTIAL_TOOLS + ["search", "critic", "think"],
    "military_leader": ESSENTIAL_TOOLS + ["todo", "process", "critic"] + UNIX_TOOLS,
    "explorer": ESSENTIAL_TOOLS + ["search", "watch", "todo"],
    "comedian": ESSENTIAL_TOOLS + ["todo", "watch", "critic"],
    "default": ESSENTIAL_TOOLS + AI_TOOLS,
}


def persona_to_tool_personality(persona: Dict[str, Any]) -> Optional[ToolPersonality]:
    """Convert a hanzo-persona profile to a ToolPersonality.

    Args:
        persona: Raw persona dict from hanzo-persona package

    Returns:
        ToolPersonality instance or None if invalid
    """
    try:
        # Get name - could be 'id' or 'name' field
        name = persona.get("id") or persona.get("name", "").lower().replace(" ", "_")
        if not name:
            return None

        # Get programmer name (display name)
        programmer = persona.get("programmer") or persona.get("name", name)

        # Get description
        description = persona.get("description", "")

        # Get philosophy
        philosophy = persona.get("philosophy", "")

        # Determine tools based on category and persona's tool preferences
        category = persona.get("category", "default")
        base_tools = CATEGORY_TOOL_MAPPINGS.get(category, CATEGORY_TOOL_MAPPINGS["default"])

        # Add tools from persona's tool preferences
        tools_config = persona.get("tools", {})
        if isinstance(tools_config, dict):
            essential = tools_config.get("essential", [])
            preferred = tools_config.get("preferred", [])
            all_tools = list(set(base_tools + essential + preferred))
        elif isinstance(tools_config, list):
            all_tools = list(set(base_tools + tools_config))
        else:
            all_tools = list(base_tools)

        # Map common tool names to hanzo-mcp tool names
        tool_name_map = {
            "python": "uvx",
            "formatter": "edit",
            "testing": "bash",
            "documentation": "rules",
            "pytest": "bash",
        }
        all_tools = [tool_name_map.get(t, t) for t in all_tools]
        all_tools = list(set(all_tools))  # Dedupe

        # Get environment variables
        environment = persona.get("environment", {})

        # Extract extended fields
        ocean = persona.get("ocean")
        behavioral_traits = persona.get("behavioral_traits")
        cognitive_style = persona.get("cognitive_style")
        social_dynamics = persona.get("social_dynamics")
        communication_patterns = persona.get("communication_patterns")
        work_methodology = persona.get("work_methodology")
        emotional_profile = persona.get("emotional_profile")

        return ToolPersonality(
            name=name,
            programmer=programmer,
            description=description,
            tools=all_tools,
            environment=environment if environment else None,
            philosophy=philosophy if philosophy else None,
            category=category,
            ocean=ocean,
            behavioral_traits=behavioral_traits,
            cognitive_style=cognitive_style,
            social_dynamics=social_dynamics,
            communication_patterns=communication_patterns,
            work_methodology=work_methodology,
            emotional_profile=emotional_profile,
        )
    except Exception as e:
        logger.warning(f"Failed to convert persona: {e}")
        return None


def load_personas_from_package() -> int:
    """Load all personas from hanzo-persona package.

    Returns:
        Number of personas loaded
    """
    loaded_count = 0

    try:
        # Try to import hanzo-persona package
        from personalities.personality_loader import PERSONA_DIR, PersonalityLoader

        # Load from all_personalities.json if exists
        all_personalities_file = PERSONA_DIR / "all_personalities.json"
        if all_personalities_file.exists():
            loader = PersonalityLoader(all_personalities_file)
            for persona in loader.get_all():
                tp = persona_to_tool_personality(persona)
                if tp:
                    PersonalityRegistry.register(tp)
                    loaded_count += 1
            logger.info(f"Loaded {loaded_count} personas from all_personalities.json")
            return loaded_count
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"Could not load from personalities module: {e}")

    # Try loading from profiles directory
    try:
        profiles_dir = _find_profiles_dir()
        if profiles_dir and profiles_dir.exists():
            loaded_count = _load_from_profiles_dir(profiles_dir)
            logger.info(f"Loaded {loaded_count} personas from profiles directory")
            return loaded_count
    except Exception as e:
        logger.debug(f"Could not load from profiles dir: {e}")

    return loaded_count


def _find_profiles_dir() -> Optional[Path]:
    """Find the hanzo-persona profiles directory."""
    # Check common locations
    search_paths = [
        Path.home() / "work" / "hanzo" / "experiments" / "persona" / "profiles",
        Path.home() / "work" / "hanzo" / "persona" / "profiles",
        Path("/opt/hanzo/persona/profiles"),
    ]

    # Check HANZO_PERSONA_DIR environment variable
    import os

    env_path = os.environ.get("HANZO_PERSONA_DIR")
    if env_path:
        search_paths.insert(0, Path(env_path) / "profiles")

    for path in search_paths:
        if path.exists():
            return path

    return None


def _load_from_profiles_dir(profiles_dir: Path) -> int:
    """Load personas from individual JSON files in profiles directory."""
    loaded_count = 0

    for json_file in profiles_dir.glob("*.json"):
        if json_file.name in ["index.json", "categories.json"]:
            continue

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                persona = json.load(f)

            tp = persona_to_tool_personality(persona)
            if tp:
                PersonalityRegistry.register(tp)
                loaded_count += 1
        except Exception as e:
            logger.debug(f"Failed to load {json_file}: {e}")

    return loaded_count


def get_persona_categories() -> List[str]:
    """Get list of available persona categories."""
    return list(CATEGORY_TOOL_MAPPINGS.keys())


def get_personas_by_category(category: str) -> List[ToolPersonality]:
    """Get all personas in a specific category."""
    return [p for p in PersonalityRegistry.list() if p.category == category]
