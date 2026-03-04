"""Hanzo Ingress Tools -- Traefik inspection and PaaS domain management via MCP."""

from .ingress_tool import IngressTool

TOOLS = [IngressTool]

__all__ = ["IngressTool", "TOOLS"]
