"""Hanzo AI - Complete AI Infrastructure Platform SDK.

This is the main Hanzo SDK that provides:
- Router for LLM gateway (replaces litellm)
- MCP (Model Context Protocol) server and tools
- Agent runtime and orchestration
- Memory systems
- Network capabilities

CLI access is provided via the hanzo-cli package.
"""

__version__ = "0.2.3"

# Core exports
__all__ = [
    # Version
    "__version__",
    
    # Router (primary LLM interface - replaces litellm)
    "router",
    "Router",
    "completion",
    "acompletion",
    "embedding",
    "aembedding",
    
    # MCP
    "mcp",
    "MCPServer",
    "Tool",
    
    # Agents
    "Agent",
    "Network", 
    "AgentTool",
    
    # Memory
    "Memory",
    "MemoryKV",
    "MemoryVector",
    
    # Core SDK
    "Client",
    "AsyncClient",
]

# Export router as the primary LLM interface (replaces litellm)
try:
    from . import router
    from .router import Router, completion, acompletion, embedding, aembedding
    # Make router the default for LLM operations
    llm = router  # Compatibility alias
except ImportError:
    router = None
    Router = None
    completion = None
    acompletion = None
    embedding = None
    aembedding = None
    llm = None

# Export MCP capabilities
try:
    import hanzo_mcp as mcp
    from hanzo_mcp import Tool
    from hanzo_mcp.server import MCPServer
except ImportError:
    mcp = None
    Tool = None
    MCPServer = None

# Export agent components
try:
    from hanzo_agents import Agent, Network
    from hanzo_agents.core.tool import Tool as AgentTool
except ImportError:
    Agent = None
    Network = None
    AgentTool = None

# Export memory systems
try:
    from hanzo_memory import Memory, MemoryKV, MemoryVector
except ImportError:
    Memory = None
    MemoryKV = None
    MemoryVector = None

# Export main SDK client
try:
    from hanzoai import Client, AsyncClient
except ImportError:
    Client = None
    AsyncClient = None