"""MCP tool for Hanzo Billing -- balance, usage, plans, subscriptions, invoices.

Wraps the Hanzo Commerce billing API at api.hanzo.ai/api/v1/billing/.
Auth: Uses HanzoSession from hanzo-tools-auth for bearer tokens.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Annotated, Any, final

from mcp.server import FastMCP
from mcp.server.fastmcp import Context as MCPContext
from pydantic import Field

from hanzo_tools.core.base import BaseTool

logger = logging.getLogger(__name__)

DESCRIPTION = """Hanzo Billing -- account balance, usage, plans, subscriptions, and invoices.

Requires authentication via `hanzo login` (stored at ~/.hanzo/auth/token.json).

Actions:
- balance: Get current billing balance
- usage: Get usage summary (period param: current, previous, or YYYY-MM)
- plans: List available plans
- subscriptions: List all subscriptions
- subscription: Get subscription by ID (subscription_id required)
- invoices: List invoices
- invoice: Get invoice by ID (invoice_id required)
- payment_methods: List payment methods on file
- spend_alerts: List configured spend alerts
- credit_balance: Get credit/promotional balance
- meters: List usage meters
- deposit: Add a deposit (amount required)
- credit: Grant starter credit to account
"""

API_BASE = "https://api.hanzo.ai/api/v1/billing"


def _get_session():
    """Get HanzoSession singleton."""
    from hanzo_tools.auth.session import HanzoSession
    return HanzoSession.get()


def _api_base() -> str:
    """Get billing API base URL (overridable via env)."""
    return os.getenv("HANZO_BILLING_API_URL", API_BASE).rstrip("/")


def _request(method: str, path: str, token: str, **kwargs: Any) -> Any:
    """Make an authenticated HTTP request to the billing API."""
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
            raise RuntimeError(f"Billing API error {resp.status_code}: {msg}")
        if not resp.content or resp.status_code == 204:
            return {}
        return resp.json()


def _get(path: str, token: str) -> Any:
    return _request("GET", path, token)


def _post(path: str, token: str, **kwargs: Any) -> Any:
    return _request("POST", path, token, **kwargs)


@final
class BillingTool(BaseTool):
    """MCP tool for Hanzo billing operations."""

    @property
    def name(self) -> str:
        return "billing"

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
        action: str = "balance",
        user: str | None = None,
        subscription_id: str | None = None,
        invoice_id: str | None = None,
        period: str | None = None,
        amount: float | None = None,
        **kwargs: Any,
    ) -> str:
        try:
            if action == "balance":
                return await self._balance(user)
            elif action == "usage":
                return await self._usage(user, period)
            elif action == "plans":
                return await self._plans()
            elif action == "subscriptions":
                return await self._subscriptions(user)
            elif action == "subscription":
                return await self._subscription(subscription_id)
            elif action == "invoices":
                return await self._invoices(user)
            elif action == "invoice":
                return await self._invoice(invoice_id)
            elif action == "payment_methods":
                return await self._payment_methods(user)
            elif action == "spend_alerts":
                return await self._spend_alerts(user)
            elif action == "credit_balance":
                return await self._credit_balance(user)
            elif action == "meters":
                return await self._meters(user)
            elif action == "deposit":
                return await self._deposit(user, amount)
            elif action == "credit":
                return await self._credit(user)
            else:
                return json.dumps({
                    "error": f"Unknown action: {action}",
                    "available": [
                        "balance", "usage", "plans", "subscriptions", "subscription",
                        "invoices", "invoice", "payment_methods", "spend_alerts",
                        "credit_balance", "meters", "deposit", "credit",
                    ],
                })
        except RuntimeError as e:
            return json.dumps({"error": str(e)})
        except Exception as e:
            logger.exception(f"Billing tool error: {e}")
            return json.dumps({"error": f"Billing error: {e}"})

    # -- Actions -------------------------------------------------------------

    async def _balance(self, user: str | None) -> str:
        token = self._get_token()
        params = f"?user={user}" if user else ""
        data = _get(f"/balance{params}", token)
        return json.dumps(data, indent=2)

    async def _usage(self, user: str | None, period: str | None) -> str:
        token = self._get_token()
        parts = []
        if user:
            parts.append(f"user={user}")
        if period:
            parts.append(f"period={period}")
        qs = f"?{'&'.join(parts)}" if parts else ""
        data = _get(f"/usage{qs}", token)
        return json.dumps(data, indent=2)

    async def _plans(self) -> str:
        token = self._get_token()
        data = _get("/plans", token)
        return json.dumps(data, indent=2)

    async def _subscriptions(self, user: str | None) -> str:
        token = self._get_token()
        params = f"?user={user}" if user else ""
        data = _get(f"/subscriptions{params}", token)
        return json.dumps(data, indent=2)

    async def _subscription(self, subscription_id: str | None) -> str:
        if not subscription_id:
            return json.dumps({"error": "Required: subscription_id"})
        token = self._get_token()
        data = _get(f"/subscriptions/{subscription_id}", token)
        return json.dumps(data, indent=2)

    async def _invoices(self, user: str | None) -> str:
        token = self._get_token()
        params = f"?user={user}" if user else ""
        data = _get(f"/invoices{params}", token)
        return json.dumps(data, indent=2)

    async def _invoice(self, invoice_id: str | None) -> str:
        if not invoice_id:
            return json.dumps({"error": "Required: invoice_id"})
        token = self._get_token()
        data = _get(f"/invoices/{invoice_id}", token)
        return json.dumps(data, indent=2)

    async def _payment_methods(self, user: str | None) -> str:
        token = self._get_token()
        params = f"?user={user}" if user else ""
        data = _get(f"/payment-methods{params}", token)
        return json.dumps(data, indent=2)

    async def _spend_alerts(self, user: str | None) -> str:
        token = self._get_token()
        params = f"?user={user}" if user else ""
        data = _get(f"/spend-alerts{params}", token)
        return json.dumps(data, indent=2)

    async def _credit_balance(self, user: str | None) -> str:
        token = self._get_token()
        params = f"?user={user}" if user else ""
        data = _get(f"/credits{params}", token)
        return json.dumps(data, indent=2)

    async def _meters(self, user: str | None) -> str:
        token = self._get_token()
        params = f"?user={user}" if user else ""
        data = _get(f"/meters{params}", token)
        return json.dumps(data, indent=2)

    async def _deposit(self, user: str | None, amount: float | None) -> str:
        if not amount or amount <= 0:
            return json.dumps({"error": "Required: amount (positive number)"})
        token = self._get_token()
        body: dict[str, Any] = {"amount": amount}
        if user:
            body["user"] = user
        data = _post("/deposit", token, json=body)
        return json.dumps(data, indent=2)

    async def _credit(self, user: str | None) -> str:
        token = self._get_token()
        body: dict[str, Any] = {}
        if user:
            body["user"] = user
        data = _post("/credit", token, json=body)
        return json.dumps(data, indent=2)

    # -- Registration --------------------------------------------------------

    def register(self, mcp_server: FastMCP) -> None:
        """Register billing tool with explicit parameters."""
        tool_instance = self

        @mcp_server.tool(
            name="billing",
            description=DESCRIPTION,
        )
        async def billing(
            action: Annotated[
                str,
                Field(
                    description=(
                        "Action to perform. "
                        "balance, usage, plans, subscriptions, subscription, "
                        "invoices, invoice, payment_methods, spend_alerts, "
                        "credit_balance, meters, deposit, credit."
                    ),
                ),
            ] = "balance",
            user: Annotated[
                str | None,
                Field(description="User identifier (org/username) to scope queries"),
            ] = None,
            subscription_id: Annotated[
                str | None,
                Field(description="Subscription ID (for subscription action)"),
            ] = None,
            invoice_id: Annotated[
                str | None,
                Field(description="Invoice ID (for invoice action)"),
            ] = None,
            period: Annotated[
                str | None,
                Field(description="Usage period: current, previous, or YYYY-MM (for usage action)"),
            ] = None,
            amount: Annotated[
                float | None,
                Field(description="Deposit amount in USD (for deposit action)"),
            ] = None,
            ctx: MCPContext = None,
        ) -> str:
            return await tool_instance.call(
                ctx,
                action=action,
                user=user,
                subscription_id=subscription_id,
                invoice_id=invoice_id,
                period=period,
                amount=amount,
            )
