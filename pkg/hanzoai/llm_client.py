"""
Simple LLM Client for Hanzo AI

This provides a simpler interface for common LLM operations,
complementing the full-featured auto-generated client.
"""

import os
from typing import Optional

# We can import and use litellm as a dependency
try:
    import litellm

    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    litellm = None

from ._client import Hanzo

# Hanzo AI specific configuration
HANZO_API_BASE = "https://api.hanzo.ai/v1"
HANZO_IAM_BASE = "https://iam.hanzo.ai"

# Check for Hanzo API key
HANZO_API_KEY = os.getenv("HANZO_API_KEY")


class SimpleLLMClient:
    """
    Simple LLM client for Hanzo AI with litellm compatibility.

    This provides a simpler interface that's compatible with the
    patterns from the llm/hanzoai package, while using the
    full-featured client under the hood.

    Example:
        >>> from hanzoai.llm_client import SimpleLLMClient
        >>> client = SimpleLLMClient(api_key="your-api-key")
        >>> response = client.completion(model="gpt-4", messages=[{"role": "user", "content": "Hello!"}])
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        iam_token: Optional[str] = None,
        auto_login: bool = False,
    ):
        """
        Initialize Simple LLM client.

        Args:
            api_key: Hanzo API key. If not provided, uses HANZO_API_KEY env var
            api_base: API base URL. Defaults to https://api.hanzo.ai/v1
            iam_token: IAM token for authentication
            auto_login: Automatically login with IAM if no API key provided
        """
        self.api_key = api_key or HANZO_API_KEY
        self.api_base = api_base or HANZO_API_BASE
        self.iam_token = iam_token

        # Handle IAM token authentication
        if self.iam_token:
            # Format IAM token for proxy server
            self.api_key = f"Bearer iam_{self.iam_token}"
        elif not self.api_key and auto_login:
            # No API key, attempt IAM login
            self._iam_login()

        # Create the underlying Hanzo client
        self._client = Hanzo(api_key=self.api_key, base_url=self.api_base)

        # Configure litellm if available
        if LITELLM_AVAILABLE and litellm:
            litellm.api_base = self.api_base
            litellm.drop_params = True  # Be permissive with params
            if self.api_key:
                litellm.api_key = self.api_key
                os.environ["OPENAI_API_KEY"] = self.api_key  # For OpenAI compatibility

    def _iam_login(self):
        """Login using IAM (Casdoor) authentication."""
        try:
            import webbrowser
            from urllib.parse import urlencode

            # IAM OAuth2 flow
            client_id = os.getenv("HANZO_CLIENT_ID", "hanzoai-sdk")
            redirect_uri = "http://localhost:8080/callback"

            # Build authorization URL
            auth_params = {
                "client_id": client_id,
                "response_type": "code",
                "redirect_uri": redirect_uri,
                "scope": "openid profile email",
                "state": "hanzoai-login",
            }
            auth_url = (
                f"{HANZO_IAM_BASE}/login/oauth/authorize?{urlencode(auth_params)}"
            )

            print(f"Opening browser for Hanzo AI login...")
            print(f"If browser doesn't open, visit: {auth_url}")
            webbrowser.open(auth_url)

            # TODO: Implement local server to catch callback
            # For now, prompt for manual token entry
            print("\nAfter logging in, copy your API key from the dashboard.")
            self.api_key = input("Enter your Hanzo API key: ").strip()

            if self.api_key:
                # Save to environment for future use
                os.environ["HANZO_API_KEY"] = self.api_key
                print("✅ Authentication successful!")

                # Update the client
                self._client = Hanzo(api_key=self.api_key, base_url=self.api_base)

        except Exception as e:
            print(f"IAM login failed: {e}")
            print(
                "Please set HANZO_API_KEY environment variable or pass api_key parameter"
            )

    def completion(self, **kwargs):
        """
        Create a completion using Hanzo AI.

        If litellm is available, uses litellm for compatibility.
        Otherwise uses the native client.
        """
        if LITELLM_AVAILABLE and litellm:
            # Use litellm for maximum compatibility
            kwargs.setdefault("api_base", self.api_base)
            if self.iam_token:
                kwargs.setdefault("api_key", f"Bearer iam_{self.iam_token}")
            elif self.api_key:
                kwargs.setdefault("api_key", self.api_key)
            return litellm.completion(**kwargs)
        else:
            # Use native client
            return self._client.chat.completions.create(**kwargs)

    def embedding(self, **kwargs):
        """Create embeddings using Hanzo AI."""
        if LITELLM_AVAILABLE and litellm:
            kwargs.setdefault("api_base", self.api_base)
            if self.api_key:
                kwargs.setdefault("api_key", self.api_key)
            return litellm.embedding(**kwargs)
        else:
            return self._client.embeddings.create(**kwargs)

    def image_generation(self, **kwargs):
        """Generate images using Hanzo AI."""
        if LITELLM_AVAILABLE and litellm:
            kwargs.setdefault("api_base", self.api_base)
            if self.api_key:
                kwargs.setdefault("api_key", self.api_key)
            return litellm.image_generation(**kwargs)
        else:
            return self._client.images.generations.create(**kwargs)

    def list_models(self):
        """List available models on Hanzo AI."""
        return self._client.models.list()

    def list_mcp_tools(self):
        """List available MCP tools on Hanzo AI."""
        # This might need a custom endpoint
        import requests

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        response = requests.get(f"{self.api_base}/mcp/tools/list", headers=headers)
        return response.json()


# For OpenAI drop-in compatibility
class OpenAICompatibleClient:
    """OpenAI-compatible client that uses Hanzo AI."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or HANZO_API_KEY
        self.base_url = base_url or HANZO_API_BASE
        self._client = SimpleLLMClient(api_key=self.api_key, api_base=self.base_url)

    @property
    def chat(self):
        return self

    @property
    def completions(self):
        return self

    def create(self, **kwargs):
        """OpenAI-compatible completion."""
        return self._client.completion(**kwargs)


# Convenience functions
def completion(**kwargs):
    """
    Quick completion using Hanzo AI with automatic authentication.

    Example:
        >>> from hanzoai.llm_client import completion
        >>> response = completion(model="gpt-4", messages=[{"role": "user", "content": "Hello!"}])
    """
    # Use Hanzo API base by default
    kwargs.setdefault("api_base", HANZO_API_BASE)

    # Use Hanzo API key if available
    if HANZO_API_KEY:
        kwargs.setdefault("api_key", HANZO_API_KEY)

    if LITELLM_AVAILABLE and litellm:
        return litellm.completion(**kwargs)
    else:
        client = SimpleLLMClient()
        return client.completion(**kwargs)


def set_api_key(api_key: str):
    """Set the Hanzo API key globally."""
    global HANZO_API_KEY
    HANZO_API_KEY = api_key
    os.environ["HANZO_API_KEY"] = api_key
    if LITELLM_AVAILABLE and litellm:
        litellm.api_key = api_key
    os.environ["OPENAI_API_KEY"] = api_key


# Initialize default client if API key is available
default_client = None
if HANZO_API_KEY:
    default_client = SimpleLLMClient()
