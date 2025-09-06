"""Configuration settings for Hanzo Memory Service."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="HANZO_",
        case_sensitive=False,
    )

    # API Settings
    api_key: str | None = Field(None, description="Hanzo API key for authentication")
    disable_auth: bool = Field(
        False, description="Disable authentication for local development"
    )

    # Server Settings
    host: str = Field("0.0.0.0", description="Server host")
    port: int = Field(4000, description="Server port")

    # Database Backend Settings
    db_backend: str = Field(
        "lancedb",  # LanceDB works on all platforms
        description="Database backend to use (lancedb, infinity)",
    )

    # InfinityDB Settings
    infinity_db_path: Path = Field(
        Path("data/infinity_db"), description="Path to InfinityDB data directory"
    )

    # LanceDB Settings
    lancedb_path: Path = Field(
        Path("data/lancedb"), description="Path to LanceDB data directory"
    )

    # LLM Settings (LiteLLM compatible)
    llm_model: str = Field(
        "gpt-4o-mini", description="LLM model to use (LiteLLM format)"
    )
    llm_api_base: str | None = Field(
        None, description="API base URL for local models"
    )
    llm_api_key: str | None = Field(None, description="API key for LLM provider")
    llm_temperature: float = Field(0.7, description="Default temperature for LLM")
    llm_max_tokens: int = Field(1000, description="Default max tokens for LLM")

    # Legacy API keys (for backwards compatibility)
    openai_api_key: str | None = Field(None, description="OpenAI API key")
    anthropic_api_key: str | None = Field(None, description="Anthropic API key")

    # Embedding Settings
    embedding_model: str = Field(
        "BAAI/bge-small-en-v1.5", description="FastEmbed model to use"
    )
    embedding_dimensions: int = Field(384, description="Embedding vector dimensions")

    # Memory Settings
    max_memories_per_user: int = Field(10000, description="Maximum memories per user")
    memory_retrieval_limit: int = Field(
        50, description="Default memory retrieval limit"
    )

    # Knowledge Base Settings
    max_knowledge_bases_per_user: int = Field(
        100, description="Maximum knowledge bases per user"
    )
    max_facts_per_base: int = Field(
        100000, description="Maximum facts per knowledge base"
    )

    # Cache Settings
    redis_url: str | None = Field(None, description="Redis URL for caching")
    cache_ttl: int = Field(3600, description="Cache TTL in seconds")

    # Logging Settings
    log_level: str = Field("INFO", description="Logging level")
    log_format: str = Field("json", description="Log format (json or text)")

    # MCP Settings
    mcp_server_name: str = Field("hanzo-memory", description="MCP server name")
    mcp_server_version: str = Field("1.0.0", description="MCP server version")

    @property
    def infinity_db_str(self) -> str:
        """Get InfinityDB path as string."""
        return str(self.infinity_db_path.absolute())

    def ensure_paths(self) -> None:
        """Ensure required paths exist."""
        self.infinity_db_path.mkdir(parents=True, exist_ok=True)
        self.lancedb_path.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings(
    api_key=None,
    disable_auth=False,
    host="0.0.0.0",
    port=4000,
    db_backend="lancedb",
    infinity_db_path=Path("data/infinity_db"),
    lancedb_path=Path("data/lancedb"),
    llm_model="gpt-4o-mini",
    llm_api_base=None,
    llm_api_key=None,
    llm_temperature=0.7,
    llm_max_tokens=1000,
    openai_api_key=None,
    anthropic_api_key=None,
    embedding_model="BAAI/bge-small-en-v1.5",
    embedding_dimensions=384,
    max_memories_per_user=10000,
    memory_retrieval_limit=50,
    max_knowledge_bases_per_user=100,
    max_facts_per_base=100000,
    redis_url=None,
    cache_ttl=3600,
    log_level="INFO",
    log_format="json",
    mcp_server_name="hanzo-memory",
    mcp_server_version="1.0.0",
)
