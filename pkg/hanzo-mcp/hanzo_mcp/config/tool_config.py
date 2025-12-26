"""Dynamic tool configuration for Hanzo MCP.

Discovers tools from entry points instead of hardcoding.
"""

import logging
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import field, dataclass

logger = logging.getLogger(__name__)


class ToolCategory(str, Enum):
    """Categories of tools available in Hanzo AI."""

    FILESYSTEM = "filesystem"
    SHELL = "shell"
    JUPYTER = "jupyter"
    TODO = "todo"
    AGENT = "agent"
    REASONING = "reasoning"
    LSP = "lsp"
    REFACTOR = "refactor"
    DATABASE = "database"
    MEMORY = "memory"
    BROWSER = "browser"
    EDITOR = "editor"
    LLM = "llm"
    VECTOR = "vector"
    CONFIG = "config"
    MCP = "mcp"
    SYSTEM = "system"  # Built-in system tools


# Map entry point names to categories
PACKAGE_CATEGORIES = {
    "filesystem": ToolCategory.FILESYSTEM,
    "shell": ToolCategory.SHELL,
    "jupyter": ToolCategory.JUPYTER,
    "todo": ToolCategory.TODO,
    "agent": ToolCategory.AGENT,
    "reasoning": ToolCategory.REASONING,
    "lsp": ToolCategory.LSP,
    "refactor": ToolCategory.REFACTOR,
    "database": ToolCategory.DATABASE,
    "memory": ToolCategory.MEMORY,
    "browser": ToolCategory.BROWSER,
    "editor": ToolCategory.EDITOR,
    "llm": ToolCategory.LLM,
    "vector": ToolCategory.VECTOR,
    "config": ToolCategory.CONFIG,
    "mcp_tools": ToolCategory.MCP,
}


@dataclass
class ToolConfig:
    """Configuration for an individual tool."""

    name: str
    category: ToolCategory
    enabled: bool = True
    description: str = ""
    requires_permissions: bool = True
    package: str = ""  # Source package name

    def __hash__(self):
        return hash(self.name)


class DynamicToolRegistry:
    """Dynamic tool registry that discovers tools from entry points."""

    _instance: Optional["DynamicToolRegistry"] = None
    _tools: Dict[str, ToolConfig] = {}
    _initialized: bool = False

    @classmethod
    def get_instance(cls) -> "DynamicToolRegistry":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = DynamicToolRegistry()
        return cls._instance

    @classmethod
    def initialize(cls) -> None:
        """Initialize the registry by discovering tools from entry points."""
        instance = cls.get_instance()
        if instance._initialized:
            return

        try:
            from hanzo_mcp.tools.common.entrypoint_loader import EntryPointToolLoader

            loader = EntryPointToolLoader()
            loader.discover_packages()

            for pkg_name, tool_classes in loader._discovered_packages.items():
                category = PACKAGE_CATEGORIES.get(pkg_name, ToolCategory.SYSTEM)

                for tool_class in tool_classes:
                    try:
                        tool_name = cls._get_tool_name(tool_class)
                        description = cls._get_tool_description(tool_class)

                        instance._tools[tool_name] = ToolConfig(
                            name=tool_name,
                            category=category,
                            enabled=True,
                            description=str(description)[:100] if description else "",
                            package=pkg_name,
                        )
                    except Exception as e:
                        logger.debug(f"Failed to register tool from {pkg_name}: {e}")

            instance._initialized = True
            logger.info(f"Discovered {len(instance._tools)} tools from entry points")

        except Exception as e:
            logger.warning(f"Failed to initialize dynamic tool registry: {e}")

    @classmethod
    def _get_tool_name(cls, tool_class) -> str:
        """Extract tool name from class, handling @property decorators."""
        # Check if name is defined as a @property in this class or parents
        for klass in tool_class.__mro__:
            if "name" in klass.__dict__:
                if isinstance(klass.__dict__["name"], property):
                    # Need to instantiate to get the property value
                    try:
                        instance = tool_class()
                        name = getattr(instance, "name", None)
                        if isinstance(name, str):
                            return name
                    except Exception:
                        pass
                    return tool_class.__name__
                break

        # Try class-level attribute
        name = getattr(tool_class, "name", None)
        if isinstance(name, str):
            return name

        return tool_class.__name__

    @classmethod
    def _get_tool_description(cls, tool_class) -> str:
        """Extract tool description from class, handling @property decorators."""
        # Check if description is defined as a @property in this class or parents
        for klass in tool_class.__mro__:
            if "description" in klass.__dict__:
                if isinstance(klass.__dict__["description"], property):
                    try:
                        instance = tool_class()
                        desc = getattr(instance, "description", "")
                        if isinstance(desc, str):
                            return desc
                    except Exception:
                        pass
                    return ""
                break

        # Try class-level attribute
        desc = getattr(tool_class, "description", None)
        if isinstance(desc, str):
            return desc

        return ""

    @classmethod
    def get(cls, name: str) -> Optional[ToolConfig]:
        """Get a tool configuration by name."""
        cls.initialize()
        return cls.get_instance()._tools.get(name)

    @classmethod
    def list_all(cls) -> Dict[str, ToolConfig]:
        """Get all tool configurations."""
        cls.initialize()
        return cls.get_instance()._tools.copy()

    @classmethod
    def list_by_category(cls, category: ToolCategory) -> List[ToolConfig]:
        """Get all tools in a specific category."""
        cls.initialize()
        return [t for t in cls.get_instance()._tools.values() if t.category == category]

    @classmethod
    def enable(cls, name: str) -> bool:
        """Enable a tool. Returns True if successful."""
        cls.initialize()
        tool = cls.get_instance()._tools.get(name)
        if tool:
            tool.enabled = True
            return True
        return False

    @classmethod
    def disable(cls, name: str) -> bool:
        """Disable a tool. Returns True if successful."""
        cls.initialize()
        tool = cls.get_instance()._tools.get(name)
        if tool:
            tool.enabled = False
            return True
        return False

    @classmethod
    def is_enabled(cls, name: str) -> bool:
        """Check if a tool is enabled."""
        cls.initialize()
        tool = cls.get_instance()._tools.get(name)
        return tool.enabled if tool else False

    @classmethod
    def register(cls, tool_config: ToolConfig) -> None:
        """Register a new tool configuration."""
        cls.initialize()
        cls.get_instance()._tools[tool_config.name] = tool_config


# Backwards compatibility: TOOL_REGISTRY as property
class _ToolRegistryProxy:
    """Proxy object that lazily initializes the tool registry."""

    def __getitem__(self, key: str) -> ToolConfig:
        DynamicToolRegistry.initialize()
        tool = DynamicToolRegistry.get(key)
        if tool is None:
            raise KeyError(key)
        return tool

    def __contains__(self, key: str) -> bool:
        DynamicToolRegistry.initialize()
        return key in DynamicToolRegistry.get_instance()._tools

    def get(self, key: str, default=None):
        DynamicToolRegistry.initialize()
        return DynamicToolRegistry.get(key) or default

    def items(self):
        DynamicToolRegistry.initialize()
        return DynamicToolRegistry.list_all().items()

    def keys(self):
        DynamicToolRegistry.initialize()
        return DynamicToolRegistry.list_all().keys()

    def values(self):
        DynamicToolRegistry.initialize()
        return DynamicToolRegistry.list_all().values()

    def __len__(self):
        DynamicToolRegistry.initialize()
        return len(DynamicToolRegistry.get_instance()._tools)

    def __iter__(self):
        DynamicToolRegistry.initialize()
        return iter(DynamicToolRegistry.get_instance()._tools)


# Backwards compatible TOOL_REGISTRY
TOOL_REGISTRY = _ToolRegistryProxy()


def get_tools_by_category(category: ToolCategory) -> List[ToolConfig]:
    """Get all tools in a specific category."""
    return DynamicToolRegistry.list_by_category(category)


def get_enabled_tools() -> List[ToolConfig]:
    """Get all enabled tools."""
    DynamicToolRegistry.initialize()
    return [t for t in DynamicToolRegistry.get_instance()._tools.values() if t.enabled]


def get_disabled_tools() -> List[ToolConfig]:
    """Get all disabled tools."""
    DynamicToolRegistry.initialize()
    return [t for t in DynamicToolRegistry.get_instance()._tools.values() if not t.enabled]


def enable_tool(tool_name: str) -> bool:
    """Enable a specific tool. Returns True if successful."""
    return DynamicToolRegistry.enable(tool_name)


def disable_tool(tool_name: str) -> bool:
    """Disable a specific tool. Returns True if successful."""
    return DynamicToolRegistry.disable(tool_name)


def is_tool_enabled(tool_name: str) -> bool:
    """Check if a tool is enabled."""
    return DynamicToolRegistry.is_enabled(tool_name)
