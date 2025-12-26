"""Tool personality system for organizing development tools based on programmer profiles.

This module provides the core dataclasses and registry for tool personalities.
Actual personality profiles are loaded from the hanzo-persona package.
"""

import os
from typing import Set, Dict, List, Optional
from dataclasses import field, dataclass


@dataclass
class CLIToolDef:
    """Definition for a CLI tool to be created for a personality."""

    name: str
    command: str
    description: str
    timeout: int = 120


@dataclass
class ToolPersonality:
    """Represents a programmer personality with tool preferences."""

    name: str
    programmer: str
    description: str
    tools: List[str]
    environment: Optional[Dict[str, str]] = None
    philosophy: Optional[str] = None
    cli_tools: Optional[List[CLIToolDef]] = None  # Dynamic CLI tools for this mode
    # Extended fields from hanzo-persona
    category: Optional[str] = None
    ocean: Optional[Dict[str, int]] = None  # Big 5 personality traits
    behavioral_traits: Optional[Dict] = None
    cognitive_style: Optional[Dict] = None
    social_dynamics: Optional[Dict] = None
    communication_patterns: Optional[Dict] = None
    work_methodology: Optional[Dict] = None
    emotional_profile: Optional[Dict] = None

    def __post_init__(self):
        """Validate personality configuration."""
        if not self.name:
            raise ValueError("Personality name is required")
        if not self.tools:
            raise ValueError("Personality must include at least one tool")


class PersonalityRegistry:
    """Registry for tool personalities."""

    _personalities: Dict[str, ToolPersonality] = {}
    _active_personality: Optional[str] = None

    @classmethod
    def register(cls, personality: ToolPersonality) -> None:
        """Register a tool personality."""
        cls._personalities[personality.name] = personality

    @classmethod
    def get(cls, name: str) -> Optional[ToolPersonality]:
        """Get a personality by name."""
        return cls._personalities.get(name)

    @classmethod
    def list(cls) -> List[ToolPersonality]:
        """List all registered personalities."""
        return list(cls._personalities.values())

    @classmethod
    def set_active(cls, name: str) -> None:
        """Set the active personality."""
        if name not in cls._personalities:
            raise ValueError(f"Personality '{name}' not found")
        cls._active_personality = name

    @classmethod
    def get_active(cls) -> Optional[ToolPersonality]:
        """Get the active personality."""
        if cls._active_personality:
            return cls._personalities.get(cls._active_personality)
        return None

    @classmethod
    def get_active_tools(cls) -> Set[str]:
        """Get the set of tools from the active personality."""
        personality = cls.get_active()
        if personality:
            return set(personality.tools)
        return set()

    @classmethod
    def clear(cls) -> None:
        """Clear all personalities (for testing/reload)."""
        cls._personalities = {}
        cls._active_personality = None


# Essential tools that are always available in every mode
# NOTE: llm/consensus are NOT essential (heavy litellm dependency - opt-in only)
ESSENTIAL_TOOLS = [
    # File operations
    "read",
    "write",
    "edit",
    "tree",
    # Shell
    "dag",
    "zsh",
    "shell",
    "open",
    # Memory
    "memory",
    # Reasoning (lightweight)
    "think",
    "critic",
    "agent",  # Lightweight agent spawning (claude, codex, etc.)
    # Configuration
    "config",
    "mode",
    # Tool management
    "tool",
]

# Heavy tools (require large dependencies like litellm)
# These are opt-in only, not included by default
HEAVY_TOOLS = [
    "llm",  # Requires litellm (~100MB deps)
    "consensus",  # Requires litellm
]

# Common tool sets for reuse
UNIX_TOOLS = ["search", "find", "dag", "ps", "zsh"]
BUILD_TOOLS = ["dag", "npx", "uvx", "ps"]
VERSION_CONTROL = ["search", "git_search"]
AI_TOOLS = ["agent", "consensus", "critic", "think", "llm"]
SEARCH_TOOLS = ["search", "ast", "find", "git_search"]
DATABASE_TOOLS = ["sql_query", "sql_search", "graph_add", "graph_query"]
VECTOR_TOOLS = ["vector_index", "vector_search"]


def register_default_personalities() -> None:
    """Register personalities from hanzo-persona package and builtin personalities.

    Always registers builtin personalities (hanzo, minimal, fullstack, devops, security)
    and optionally loads additional personas from hanzo-persona package.
    """
    # Always register builtin personalities first
    _register_builtin_personalities()

    # Then load additional personas from hanzo-persona if available
    try:
        from hanzo_mcp.tools.common.persona_adapter import load_personas_from_package

        loaded = load_personas_from_package()
        if loaded > 0:
            import logging

            logging.getLogger(__name__).debug(f"Loaded {loaded} personas from hanzo-persona package")
    except ImportError:
        pass
    except Exception as e:
        import logging

        logging.getLogger(__name__).warning(f"Failed to load personas from package: {e}")


def _register_builtin_personalities() -> None:
    """Register minimal built-in personalities when hanzo-persona is unavailable."""
    builtin = [
        ToolPersonality(
            name="hanzo",
            programmer="Hanzo AI Default",
            description="Balanced productivity and quality",
            philosophy="The Zen of Model Context Protocol.",
            tools=list(
                set(
                    ESSENTIAL_TOOLS
                    + [
                        "agent",
                        "todo",
                        "browser",
                        "computer",
                        "search",
                        "find",
                        "ast",
                        "jupyter",
                        "refactor",
                        "lsp",
                        "iching",
                        "review",  # Agent sub-tools
                    ]
                    + BUILD_TOOLS
                )
            ),
            environment={"HANZO_MODE": "zen"},
        ),
        ToolPersonality(
            name="minimal",
            programmer="Minimalist",
            description="Just the essentials",
            philosophy="Less is more.",
            tools=list(set(ESSENTIAL_TOOLS)),
            environment={"MINIMAL_MODE": "true"},
        ),
        ToolPersonality(
            name="fullstack",
            programmer="Full Stack Developer",
            description="Every tool for every job",
            philosophy="Jack of all trades, master of... well, all trades.",
            tools=list(
                set(
                    ESSENTIAL_TOOLS
                    + AI_TOOLS
                    + SEARCH_TOOLS
                    + DATABASE_TOOLS
                    + BUILD_TOOLS
                    + UNIX_TOOLS
                    + VECTOR_TOOLS
                    + ["todo", "rules", "browser", "jupyter", "neovim_edit", "mcp", "refactor", "lsp"]
                )
            ),
            environment={"ALL_TOOLS": "enabled"},
        ),
        ToolPersonality(
            name="devops",
            programmer="DevOps Engineer",
            description="Automate everything",
            philosophy="You build it, you run it.",
            tools=list(set(ESSENTIAL_TOOLS + BUILD_TOOLS + UNIX_TOOLS + ["todo", "browser"])),
            environment={"CI_CD": "enabled"},
            cli_tools=[
                CLIToolDef("docker", "docker", "Docker container management"),
                CLIToolDef("kubectl", "kubectl", "Kubernetes CLI", timeout=60),
                CLIToolDef("terraform", "terraform", "Infrastructure as Code"),
                CLIToolDef("helm", "helm", "Kubernetes package manager"),
                CLIToolDef("aws", "aws", "AWS CLI", timeout=120),
                CLIToolDef("gcloud", "gcloud", "Google Cloud CLI", timeout=120),
            ],
        ),
        ToolPersonality(
            name="security",
            programmer="Security Researcher",
            description="Break it to secure it",
            philosophy="The only secure system is one that's powered off.",
            tools=list(set(ESSENTIAL_TOOLS + UNIX_TOOLS + ["browser", "ast"])),
            environment={"SECURITY_MODE": "paranoid"},
        ),
    ]

    for personality in builtin:
        PersonalityRegistry.register(personality)


def ensure_agent_enabled(personality: ToolPersonality) -> ToolPersonality:
    """Ensure agent tool is enabled if API keys are present."""
    api_keys_present = any(
        os.environ.get(key)
        for key in [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "GOOGLE_API_KEY",
            "HANZO_API_KEY",
            "GROQ_API_KEY",
            "TOGETHER_API_KEY",
            "MISTRAL_API_KEY",
            "PERPLEXITY_API_KEY",
        ]
    )

    if api_keys_present and "agent" not in personality.tools:
        personality.tools.append("agent")
        if "consensus" not in personality.tools:
            personality.tools.append("consensus")

    return personality
