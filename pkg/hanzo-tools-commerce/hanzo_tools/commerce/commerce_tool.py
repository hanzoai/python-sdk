"""MCP tool for Hanzo Commerce -- orders, products, collections, stores.

Wraps the Hanzo Commerce API at api.hanzo.ai/api/v1/.
Auth: Uses HanzoSession from hanzo-tools-auth for bearer tokens.
"""

from __future__ import annotations

import os
import json
import logging
from typing import Any, Annotated, final

from pydantic import Field
from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext

from hanzo_tools.core.base import BaseTool

logger = logging.getLogger(__name__)

DESCRIPTION = """Hanzo Commerce -- orders, products, collections, stores, and discounts.

Requires authentication via `hanzo login` (stored at ~/.hanzo/auth/token.json).

Actions:
- orders: List orders (optional query param for filtering)
- order: Get order by ID (order_id required)
- products: List products
- product: Get product by ID (product_id required)
- collections: List product collections
- search_users: Search users (query required)
- search_orders: Search orders (query required)
- stores: List stores
- discounts: List discount codes
- webhooks: List configured webhooks
"""

API_BASE = "https://api.hanzo.ai/api/v1"


def _get_session():
    """Get HanzoSession singleton."""
    from hanzo_tools.auth.session import HanzoSession
    return HanzoSession.get()


def _api_base() -> str:
    """Get commerce API base URL (overridable via env)."""
    return os.getenv("HANZO_COMMERCE_API_URL", API_BASE).rstrip("/")


def _request(method: str, path: str, token: str, **kwargs: Any) -> Any:
    """Make an authenticated HTTP request to the commerce API."""
    import httpx

    url = f"{_api_base()}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "hanzo-mcp/0.1",
    }

    with httpx.Client(timeout=30.0) as client:
        resp = client.request(method, url, headers=headers, **kwargs)
        if resp.status_code >= 400:
            try:
                err = resp.json()
                msg = err.get("error", err.get("message", resp.text))
            except Exception:
                msg = resp.text
            raise RuntimeError(f"Commerce API error {resp.status_code}: {msg}")
        if not resp.content or resp.status_code == 204:
            return {}
        return resp.json()


def _get(path: str, token: str, params: dict[str, str] | None = None) -> Any:
    return _request("GET", path, token, params=params)


@final
class CommerceTool(BaseTool):
    """MCP tool for Hanzo commerce operations."""

    @property
    def name(self) -> str:
        return "commerce"

    @property
    def description(self) -> str:
        return DESCRIPTION

    def _get_token(self) -> str:
        """Get auth token or raise."""
        session = _get_session()
        token = session.get_iam_token()
        if not token:
            raise RuntimeError("Not authenticated. Run 'hanzo login' first.")
        return token

    async def call(
        self,
        ctx: MCPContext,
        action: str = "orders",
        order_id: str | None = None,
        product_id: str | None = None,
        query: str | None = None,
        **kwargs: Any,
    ) -> str:
        try:
            if action == "orders":
                return await self._orders(query)
            elif action == "order":
                return await self._order(order_id)
            elif action == "products":
                return await self._products(query)
            elif action == "product":
                return await self._product(product_id)
            elif action == "collections":
                return await self._collections()
            elif action == "search_users":
                return await self._search_users(query)
            elif action == "search_orders":
                return await self._search_orders(query)
            elif action == "stores":
                return await self._stores()
            elif action == "discounts":
                return await self._discounts()
            elif action == "webhooks":
                return await self._webhooks()
            else:
                return json.dumps({
                    "error": f"Unknown action: {action}",
                    "available": [
                        "orders", "order", "products", "product", "collections",
                        "search_users", "search_orders", "stores", "discounts", "webhooks",
                    ],
                })
        except RuntimeError as e:
            return json.dumps({"error": str(e)})
        except Exception as e:
            logger.exception(f"Commerce tool error: {e}")
            return json.dumps({"error": f"Commerce error: {e}"})

    # -- Actions -------------------------------------------------------------

    async def _orders(self, query: str | None) -> str:
        token = self._get_token()
        params = {"q": query} if query else None
        data = _get("/orders", token, params=params)
        return json.dumps(data, indent=2)

    async def _order(self, order_id: str | None) -> str:
        if not order_id:
            return json.dumps({"error": "Required: order_id"})
        token = self._get_token()
        data = _get(f"/orders/{order_id}", token)
        return json.dumps(data, indent=2)

    async def _products(self, query: str | None) -> str:
        token = self._get_token()
        params = {"q": query} if query else None
        data = _get("/products", token, params=params)
        return json.dumps(data, indent=2)

    async def _product(self, product_id: str | None) -> str:
        if not product_id:
            return json.dumps({"error": "Required: product_id"})
        token = self._get_token()
        data = _get(f"/products/{product_id}", token)
        return json.dumps(data, indent=2)

    async def _collections(self) -> str:
        token = self._get_token()
        data = _get("/collections", token)
        return json.dumps(data, indent=2)

    async def _search_users(self, query: str | None) -> str:
        if not query:
            return json.dumps({"error": "Required: query (search term)"})
        token = self._get_token()
        data = _get("/users", token, params={"q": query})
        return json.dumps(data, indent=2)

    async def _search_orders(self, query: str | None) -> str:
        if not query:
            return json.dumps({"error": "Required: query (search term)"})
        token = self._get_token()
        data = _get("/orders", token, params={"q": query})
        return json.dumps(data, indent=2)

    async def _stores(self) -> str:
        token = self._get_token()
        data = _get("/stores", token)
        return json.dumps(data, indent=2)

    async def _discounts(self) -> str:
        token = self._get_token()
        data = _get("/discounts", token)
        return json.dumps(data, indent=2)

    async def _webhooks(self) -> str:
        token = self._get_token()
        data = _get("/webhooks", token)
        return json.dumps(data, indent=2)

    # -- Registration --------------------------------------------------------

    def register(self, mcp_server: FastMCP) -> None:
        """Register commerce tool with explicit parameters."""
        tool_instance = self

        @mcp_server.tool(
            name="commerce",
            description=DESCRIPTION,
        )
        async def commerce(
            action: Annotated[
                str,
                Field(
                    description=(
                        "Action to perform. "
                        "orders, order, products, product, collections, "
                        "search_users, search_orders, stores, discounts, webhooks."
                    ),
                ),
            ] = "orders",
            order_id: Annotated[
                str | None,
                Field(description="Order ID (for order action)"),
            ] = None,
            product_id: Annotated[
                str | None,
                Field(description="Product ID (for product action)"),
            ] = None,
            query: Annotated[
                str | None,
                Field(description="Search query (for search_users, search_orders, or filtering orders/products)"),
            ] = None,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_instance.call(
                ctx,
                action=action,
                order_id=order_id,
                product_id=product_id,
                query=query,
            )
