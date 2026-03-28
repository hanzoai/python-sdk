"""Hanzo UI Registry — cached component server and client.

Server: pre-fetches all component data from hanzoai/ui on GitHub,
serves cached responses via FastAPI. Deploy at ui.hanzo.ai.

Client: fetches from the registry server instead of hitting GitHub
directly. Used by the UI tool as a middle-tier between local and GitHub.
"""

from .client import RegistryClient

__all__ = ["RegistryClient"]

# Server imports are deferred to avoid requiring fastapi at import time.
# Use: from hanzo_tools.ui.registry.server import app
