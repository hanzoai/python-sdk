"""MCP client configuration types."""
from pydantic import BaseModel, Field


class MCPSSEServerConfig(BaseModel):
    """Configuration for a single MCP SSE server.

    Attributes:
        url: The server URL
        api_key: Optional API key for authentication
    """

    url: str
    api_key: str | None = None


class MCPSHTTPServerConfig(BaseModel):
    """Configuration for a MCP HTTP server.
    
    Attributes:
        url: The server URL
        api_key: Optional API key for authentication
    """
    
    url: str
    api_key: str | None = None


class MCPStdioServerConfig(BaseModel):
    """Configuration for a MCP server that uses stdio.

    Attributes:
        name: The name of the server
        command: The command to run the server
        args: The arguments to pass to the server
        env: The environment variables to set for the server
    """

    name: str
    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)