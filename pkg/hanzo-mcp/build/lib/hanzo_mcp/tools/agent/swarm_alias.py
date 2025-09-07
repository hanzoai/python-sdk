"""Swarm tool as an alias to Network tool for backward compatibility.

This module makes swarm an alias to the network tool, as network is the
evolution of swarm with better distributed execution capabilities.
"""

from hanzo_mcp.tools.agent.network_tool import NetworkTool
from hanzo_mcp.tools.common.permissions import PermissionManager


class SwarmTool(NetworkTool):
    """Swarm tool - alias to Network tool for backward compatibility.

    The swarm tool is now an alias to the network tool, which provides
    all the same functionality plus additional distributed execution modes.
    Use 'network' for new code, 'swarm' is maintained for compatibility.
    """

    @property
    def name(self) -> str:
        """Get the tool name."""
        return "swarm"

    @property
    def description(self) -> str:
        """Get the tool description."""
        return """Execute a network of AI agents (alias to 'network' tool).

The 'swarm' tool is now an alias to the 'network' tool for backward compatibility.
All swarm functionality is available through network, which additionally provides:

- Local-first execution with privacy preservation
- Distributed compute across devices  
- Hybrid mode with cloud fallback
- Integration with hanzo-network for MCP-connected agents

Examples:
```python
# These are equivalent:
swarm(task="Analyze code", agents=["analyzer", "reviewer"])
network(task="Analyze code", agents=["analyzer", "reviewer"])

# Network adds new modes:
network(task="Process data", mode="local")  # Privacy-first
network(task="Large analysis", mode="distributed")  # Scale out
```

For new code, prefer using 'network' directly."""

    def __init__(
        self,
        permission_manager: PermissionManager,
        default_mode: str = "hybrid",
        **kwargs,
    ):
        """Initialize swarm as an alias to network.

        Args:
            permission_manager: Permission manager
            default_mode: Default execution mode (hybrid/local/distributed)
            **kwargs: Additional arguments passed to NetworkTool
        """
        # Just pass through to NetworkTool
        super().__init__(
            permission_manager=permission_manager, default_mode=default_mode, **kwargs
        )

    async def call(self, **kwargs) -> str:
        """Execute swarm via network tool.

        All parameters are passed through to the network tool.
        """
        # For backward compatibility, rename some parameters if needed
        if "config" in kwargs and "agents" not in kwargs:
            # Old swarm used 'config' for agent definitions
            config = kwargs.pop("config")
            if isinstance(config, dict) and "agents" in config:
                kwargs["agents"] = config["agents"]
                if "topology" in config:
                    kwargs["routing"] = config["topology"]

        # Pass through to network tool
        return await super().call(**kwargs)


# For backward compatibility exports
__all__ = ["SwarmTool"]
