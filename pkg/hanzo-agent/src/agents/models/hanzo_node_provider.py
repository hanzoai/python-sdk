"""
Hanzo Node Model Provider for direct integration with hanzod at port 3690.
"""

import os
from typing import Optional

from openai import AsyncOpenAI

from ..models.interface import Model, ModelProvider
from ..models.openai_chatcompletions import OpenAIChatCompletionsModel


class HanzoNodeProvider(ModelProvider):
    """
    Model provider that connects directly to Hanzo Node (hanzod) at port 3690.

    This provider enables direct integration with the local Hanzo node for:
    - Local LLM inference
    - Embeddings generation
    - Vector search capabilities
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        port: int = 3690,
    ):
        """
        Initialize Hanzo Node provider.

        Args:
            base_url: Override base URL (defaults to localhost with port)
            api_key: API key for authentication (optional for local node)
            port: Port number for hanzod (default: 3690)
        """
        # Use provided base_url or construct from port
        if base_url is None:
            base_url = f"http://localhost:{port}/v1"

        # Use provided api_key or default for local node
        if api_key is None:
            api_key = os.getenv("HANZO_NODE_API_KEY", "sk-local-node")

        self.base_url = base_url
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        print(f"Configured Hanzo Node at: {base_url}")

    def get_model(self, model_name: Optional[str] = None) -> Model:
        """
        Get a model instance for the specified model name.

        Args:
            model_name: Name of the model (defaults to gpt-oss:20b for local inference)

        Returns:
            Model instance configured for Hanzo Node
        """
        # Default to local OSS model if not specified
        model = model_name or "gpt-oss:20b"
        print(f"Using Hanzo Node model: {model}")

        return OpenAIChatCompletionsModel(
            model=model,
            openai_client=self.client
        )

    @property
    def is_local(self) -> bool:
        """Check if this is a local node connection."""
        return "localhost" in self.base_url or "127.0.0.1" in self.base_url

    async def health_check(self) -> bool:
        """
        Check if the Hanzo node is healthy and responding.

        Returns:
            True if node is healthy, False otherwise
        """
        try:
            # Try to list models as a health check
            await self.client.models.list()
            return True
        except Exception as e:
            print(f"Health check failed: {e}")
            return False


# Convenience function to create a Hanzo Node provider
def create_hanzo_node_provider(
    port: int = 3690,
    api_key: Optional[str] = None
) -> HanzoNodeProvider:
    """
    Create a Hanzo Node provider with default settings.

    Args:
        port: Port number for hanzod (default: 3690)
        api_key: Optional API key

    Returns:
        Configured HanzoNodeProvider instance
    """
    return HanzoNodeProvider(port=port, api_key=api_key)