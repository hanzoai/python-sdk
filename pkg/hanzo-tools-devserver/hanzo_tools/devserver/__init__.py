"""Dev server tools for Hanzo AI.

Tools:
- devserver: find running dev servers (Next, Vite, Nuxt, Remix, React Router,
  Astro, SvelteKit), call their built-in MCP tools, read current errors.

``discover()`` returns the servers as plain ``DevServer`` records.
"""

from .discovery import DevServer, discover
from .devserver_tool import DevserverTool

TOOLS = [DevserverTool]

__all__ = ["TOOLS", "DevserverTool", "DevServer", "discover"]
