# Hanzo AI SDK

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options

__all__ = ["BillingResource", "AsyncBillingResource"]


class BillingResource(SyncAPIResource):
    """Billing and subscription management via Commerce API."""

    @cached_property
    def with_raw_response(self) -> BillingResourceWithRawResponse:
        return BillingResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> BillingResourceWithStreamingResponse:
        return BillingResourceWithStreamingResponse(self)

    # ------------------------------------------------------------------
    # Balance
    # ------------------------------------------------------------------

    def get_balance(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get current account balance."""
        return self._get(
            "/billing/balance",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------
    # Usage
    # ------------------------------------------------------------------

    def get_usage(
        self,
        *,
        start_date: str,
        end_date: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get usage for a date range."""
        return self._get(
            "/billing/usage",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={
                    "startDate": start_date,
                    "endDate": end_date,
                },
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------
    # Meters
    # ------------------------------------------------------------------

    def list_meters(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all billing meters."""
        return self._get(
            "/billing/meters",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def get_meter(
        self,
        *,
        meter_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific billing meter."""
        return self._get(
            f"/billing/meters/{meter_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------
    # Credit Grants
    # ------------------------------------------------------------------

    def list_credit_grants(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all credit grants."""
        return self._get(
            "/billing/credit-grants",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def create_credit_grant(
        self,
        *,
        amount: float,
        description: str,
        expires_at: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a credit grant."""
        return self._post(
            "/billing/credit-grants",
            body={
                "amount": amount,
                "description": description,
                "expires_at": expires_at,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------
    # Invoices
    # ------------------------------------------------------------------

    def list_invoices(
        self,
        *,
        limit: int | NotGiven = NOT_GIVEN,
        offset: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List invoices."""
        return self._get(
            "/billing/invoices",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={
                    "limit": limit,
                    "offset": offset,
                },
            ),
            cast_to=object,
        )

    def get_invoice(
        self,
        *,
        invoice_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific invoice."""
        return self._get(
            f"/billing/invoices/{invoice_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------
    # Subscriptions
    # ------------------------------------------------------------------

    def list_subscriptions(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all subscriptions."""
        return self._get(
            "/billing/subscriptions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def get_subscription(
        self,
        *,
        subscription_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific subscription."""
        return self._get(
            f"/billing/subscriptions/{subscription_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def create_subscription(
        self,
        *,
        plan_id: str,
        metadata: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a subscription."""
        return self._post(
            "/billing/subscriptions",
            body={
                "plan_id": plan_id,
                "metadata": metadata,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def cancel_subscription(
        self,
        *,
        subscription_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Cancel a subscription."""
        return self._delete(
            f"/billing/subscriptions/{subscription_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------
    # Payment Intents
    # ------------------------------------------------------------------

    def list_payment_intents(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all payment intents."""
        return self._get(
            "/billing/payment-intents",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def create_payment_intent(
        self,
        *,
        amount: float,
        currency: str,
        metadata: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a payment intent."""
        return self._post(
            "/billing/payment-intents",
            body={
                "amount": amount,
                "currency": currency,
                "metadata": metadata,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------
    # Payment Methods
    # ------------------------------------------------------------------

    def list_payment_methods(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all payment methods."""
        return self._get(
            "/billing/payment-methods",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def add_payment_method(
        self,
        *,
        type: str,
        token: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a payment method."""
        return self._post(
            "/billing/payment-methods",
            body={
                "type": type,
                "token": token,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def remove_payment_method(
        self,
        *,
        payment_method_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Remove a payment method."""
        return self._delete(
            f"/billing/payment-methods/{payment_method_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------
    # Plans
    # ------------------------------------------------------------------

    def list_plans(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all available plans."""
        return self._get(
            "/billing/plans",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def get_plan(
        self,
        *,
        plan_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific plan."""
        return self._get(
            f"/billing/plans/{plan_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------
    # Spend Alerts
    # ------------------------------------------------------------------

    def list_spend_alerts(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all spend alerts."""
        return self._get(
            "/billing/spend-alerts",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def create_spend_alert(
        self,
        *,
        threshold: float,
        notification_channels: List[str],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a spend alert."""
        return self._post(
            "/billing/spend-alerts",
            body={
                "threshold": threshold,
                "notification_channels": notification_channels,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    def delete_spend_alert(
        self,
        *,
        alert_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a spend alert."""
        return self._delete(
            f"/billing/spend-alerts/{alert_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------
    # Portal
    # ------------------------------------------------------------------

    def get_portal_url(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get customer billing portal URL."""
        return self._post(
            "/billing/portal",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class AsyncBillingResource(AsyncAPIResource):
    """Billing and subscription management via Commerce API."""

    @cached_property
    def with_raw_response(self) -> AsyncBillingResourceWithRawResponse:
        return AsyncBillingResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncBillingResourceWithStreamingResponse:
        return AsyncBillingResourceWithStreamingResponse(self)

    # ------------------------------------------------------------------
    # Balance
    # ------------------------------------------------------------------

    async def get_balance(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get current account balance."""
        return await self._get(
            "/billing/balance",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------
    # Usage
    # ------------------------------------------------------------------

    async def get_usage(
        self,
        *,
        start_date: str,
        end_date: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get usage for a date range."""
        return await self._get(
            "/billing/usage",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={
                    "startDate": start_date,
                    "endDate": end_date,
                },
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------
    # Meters
    # ------------------------------------------------------------------

    async def list_meters(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all billing meters."""
        return await self._get(
            "/billing/meters",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def get_meter(
        self,
        *,
        meter_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific billing meter."""
        return await self._get(
            f"/billing/meters/{meter_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------
    # Credit Grants
    # ------------------------------------------------------------------

    async def list_credit_grants(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all credit grants."""
        return await self._get(
            "/billing/credit-grants",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def create_credit_grant(
        self,
        *,
        amount: float,
        description: str,
        expires_at: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a credit grant."""
        return await self._post(
            "/billing/credit-grants",
            body={
                "amount": amount,
                "description": description,
                "expires_at": expires_at,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------
    # Invoices
    # ------------------------------------------------------------------

    async def list_invoices(
        self,
        *,
        limit: int | NotGiven = NOT_GIVEN,
        offset: int | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List invoices."""
        return await self._get(
            "/billing/invoices",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query={
                    "limit": limit,
                    "offset": offset,
                },
            ),
            cast_to=object,
        )

    async def get_invoice(
        self,
        *,
        invoice_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific invoice."""
        return await self._get(
            f"/billing/invoices/{invoice_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------
    # Subscriptions
    # ------------------------------------------------------------------

    async def list_subscriptions(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all subscriptions."""
        return await self._get(
            "/billing/subscriptions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def get_subscription(
        self,
        *,
        subscription_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific subscription."""
        return await self._get(
            f"/billing/subscriptions/{subscription_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def create_subscription(
        self,
        *,
        plan_id: str,
        metadata: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a subscription."""
        return await self._post(
            "/billing/subscriptions",
            body={
                "plan_id": plan_id,
                "metadata": metadata,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def cancel_subscription(
        self,
        *,
        subscription_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Cancel a subscription."""
        return await self._delete(
            f"/billing/subscriptions/{subscription_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------
    # Payment Intents
    # ------------------------------------------------------------------

    async def list_payment_intents(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all payment intents."""
        return await self._get(
            "/billing/payment-intents",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def create_payment_intent(
        self,
        *,
        amount: float,
        currency: str,
        metadata: Dict[str, Any] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a payment intent."""
        return await self._post(
            "/billing/payment-intents",
            body={
                "amount": amount,
                "currency": currency,
                "metadata": metadata,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------
    # Payment Methods
    # ------------------------------------------------------------------

    async def list_payment_methods(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all payment methods."""
        return await self._get(
            "/billing/payment-methods",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def add_payment_method(
        self,
        *,
        type: str,
        token: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Add a payment method."""
        return await self._post(
            "/billing/payment-methods",
            body={
                "type": type,
                "token": token,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def remove_payment_method(
        self,
        *,
        payment_method_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Remove a payment method."""
        return await self._delete(
            f"/billing/payment-methods/{payment_method_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------
    # Plans
    # ------------------------------------------------------------------

    async def list_plans(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all available plans."""
        return await self._get(
            "/billing/plans",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def get_plan(
        self,
        *,
        plan_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get a specific plan."""
        return await self._get(
            f"/billing/plans/{plan_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------
    # Spend Alerts
    # ------------------------------------------------------------------

    async def list_spend_alerts(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """List all spend alerts."""
        return await self._get(
            "/billing/spend-alerts",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def create_spend_alert(
        self,
        *,
        threshold: float,
        notification_channels: List[str],
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Create a spend alert."""
        return await self._post(
            "/billing/spend-alerts",
            body={
                "threshold": threshold,
                "notification_channels": notification_channels,
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    async def delete_spend_alert(
        self,
        *,
        alert_id: str,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Delete a spend alert."""
        return await self._delete(
            f"/billing/spend-alerts/{alert_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )

    # ------------------------------------------------------------------
    # Portal
    # ------------------------------------------------------------------

    async def get_portal_url(
        self,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> object:
        """Get customer billing portal URL."""
        return await self._post(
            "/billing/portal",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=object,
        )


class BillingResourceWithRawResponse:
    def __init__(self, billing: BillingResource) -> None:
        self._billing = billing

        self.get_balance = to_raw_response_wrapper(
            billing.get_balance,
        )
        self.get_usage = to_raw_response_wrapper(
            billing.get_usage,
        )
        self.list_meters = to_raw_response_wrapper(
            billing.list_meters,
        )
        self.get_meter = to_raw_response_wrapper(
            billing.get_meter,
        )
        self.list_credit_grants = to_raw_response_wrapper(
            billing.list_credit_grants,
        )
        self.create_credit_grant = to_raw_response_wrapper(
            billing.create_credit_grant,
        )
        self.list_invoices = to_raw_response_wrapper(
            billing.list_invoices,
        )
        self.get_invoice = to_raw_response_wrapper(
            billing.get_invoice,
        )
        self.list_subscriptions = to_raw_response_wrapper(
            billing.list_subscriptions,
        )
        self.get_subscription = to_raw_response_wrapper(
            billing.get_subscription,
        )
        self.create_subscription = to_raw_response_wrapper(
            billing.create_subscription,
        )
        self.cancel_subscription = to_raw_response_wrapper(
            billing.cancel_subscription,
        )
        self.list_payment_intents = to_raw_response_wrapper(
            billing.list_payment_intents,
        )
        self.create_payment_intent = to_raw_response_wrapper(
            billing.create_payment_intent,
        )
        self.list_payment_methods = to_raw_response_wrapper(
            billing.list_payment_methods,
        )
        self.add_payment_method = to_raw_response_wrapper(
            billing.add_payment_method,
        )
        self.remove_payment_method = to_raw_response_wrapper(
            billing.remove_payment_method,
        )
        self.list_plans = to_raw_response_wrapper(
            billing.list_plans,
        )
        self.get_plan = to_raw_response_wrapper(
            billing.get_plan,
        )
        self.list_spend_alerts = to_raw_response_wrapper(
            billing.list_spend_alerts,
        )
        self.create_spend_alert = to_raw_response_wrapper(
            billing.create_spend_alert,
        )
        self.delete_spend_alert = to_raw_response_wrapper(
            billing.delete_spend_alert,
        )
        self.get_portal_url = to_raw_response_wrapper(
            billing.get_portal_url,
        )


class AsyncBillingResourceWithRawResponse:
    def __init__(self, billing: AsyncBillingResource) -> None:
        self._billing = billing

        self.get_balance = async_to_raw_response_wrapper(
            billing.get_balance,
        )
        self.get_usage = async_to_raw_response_wrapper(
            billing.get_usage,
        )
        self.list_meters = async_to_raw_response_wrapper(
            billing.list_meters,
        )
        self.get_meter = async_to_raw_response_wrapper(
            billing.get_meter,
        )
        self.list_credit_grants = async_to_raw_response_wrapper(
            billing.list_credit_grants,
        )
        self.create_credit_grant = async_to_raw_response_wrapper(
            billing.create_credit_grant,
        )
        self.list_invoices = async_to_raw_response_wrapper(
            billing.list_invoices,
        )
        self.get_invoice = async_to_raw_response_wrapper(
            billing.get_invoice,
        )
        self.list_subscriptions = async_to_raw_response_wrapper(
            billing.list_subscriptions,
        )
        self.get_subscription = async_to_raw_response_wrapper(
            billing.get_subscription,
        )
        self.create_subscription = async_to_raw_response_wrapper(
            billing.create_subscription,
        )
        self.cancel_subscription = async_to_raw_response_wrapper(
            billing.cancel_subscription,
        )
        self.list_payment_intents = async_to_raw_response_wrapper(
            billing.list_payment_intents,
        )
        self.create_payment_intent = async_to_raw_response_wrapper(
            billing.create_payment_intent,
        )
        self.list_payment_methods = async_to_raw_response_wrapper(
            billing.list_payment_methods,
        )
        self.add_payment_method = async_to_raw_response_wrapper(
            billing.add_payment_method,
        )
        self.remove_payment_method = async_to_raw_response_wrapper(
            billing.remove_payment_method,
        )
        self.list_plans = async_to_raw_response_wrapper(
            billing.list_plans,
        )
        self.get_plan = async_to_raw_response_wrapper(
            billing.get_plan,
        )
        self.list_spend_alerts = async_to_raw_response_wrapper(
            billing.list_spend_alerts,
        )
        self.create_spend_alert = async_to_raw_response_wrapper(
            billing.create_spend_alert,
        )
        self.delete_spend_alert = async_to_raw_response_wrapper(
            billing.delete_spend_alert,
        )
        self.get_portal_url = async_to_raw_response_wrapper(
            billing.get_portal_url,
        )


class BillingResourceWithStreamingResponse:
    def __init__(self, billing: BillingResource) -> None:
        self._billing = billing

        self.get_balance = to_streamed_response_wrapper(
            billing.get_balance,
        )
        self.get_usage = to_streamed_response_wrapper(
            billing.get_usage,
        )
        self.list_meters = to_streamed_response_wrapper(
            billing.list_meters,
        )
        self.get_meter = to_streamed_response_wrapper(
            billing.get_meter,
        )
        self.list_credit_grants = to_streamed_response_wrapper(
            billing.list_credit_grants,
        )
        self.create_credit_grant = to_streamed_response_wrapper(
            billing.create_credit_grant,
        )
        self.list_invoices = to_streamed_response_wrapper(
            billing.list_invoices,
        )
        self.get_invoice = to_streamed_response_wrapper(
            billing.get_invoice,
        )
        self.list_subscriptions = to_streamed_response_wrapper(
            billing.list_subscriptions,
        )
        self.get_subscription = to_streamed_response_wrapper(
            billing.get_subscription,
        )
        self.create_subscription = to_streamed_response_wrapper(
            billing.create_subscription,
        )
        self.cancel_subscription = to_streamed_response_wrapper(
            billing.cancel_subscription,
        )
        self.list_payment_intents = to_streamed_response_wrapper(
            billing.list_payment_intents,
        )
        self.create_payment_intent = to_streamed_response_wrapper(
            billing.create_payment_intent,
        )
        self.list_payment_methods = to_streamed_response_wrapper(
            billing.list_payment_methods,
        )
        self.add_payment_method = to_streamed_response_wrapper(
            billing.add_payment_method,
        )
        self.remove_payment_method = to_streamed_response_wrapper(
            billing.remove_payment_method,
        )
        self.list_plans = to_streamed_response_wrapper(
            billing.list_plans,
        )
        self.get_plan = to_streamed_response_wrapper(
            billing.get_plan,
        )
        self.list_spend_alerts = to_streamed_response_wrapper(
            billing.list_spend_alerts,
        )
        self.create_spend_alert = to_streamed_response_wrapper(
            billing.create_spend_alert,
        )
        self.delete_spend_alert = to_streamed_response_wrapper(
            billing.delete_spend_alert,
        )
        self.get_portal_url = to_streamed_response_wrapper(
            billing.get_portal_url,
        )


class AsyncBillingResourceWithStreamingResponse:
    def __init__(self, billing: AsyncBillingResource) -> None:
        self._billing = billing

        self.get_balance = async_to_streamed_response_wrapper(
            billing.get_balance,
        )
        self.get_usage = async_to_streamed_response_wrapper(
            billing.get_usage,
        )
        self.list_meters = async_to_streamed_response_wrapper(
            billing.list_meters,
        )
        self.get_meter = async_to_streamed_response_wrapper(
            billing.get_meter,
        )
        self.list_credit_grants = async_to_streamed_response_wrapper(
            billing.list_credit_grants,
        )
        self.create_credit_grant = async_to_streamed_response_wrapper(
            billing.create_credit_grant,
        )
        self.list_invoices = async_to_streamed_response_wrapper(
            billing.list_invoices,
        )
        self.get_invoice = async_to_streamed_response_wrapper(
            billing.get_invoice,
        )
        self.list_subscriptions = async_to_streamed_response_wrapper(
            billing.list_subscriptions,
        )
        self.get_subscription = async_to_streamed_response_wrapper(
            billing.get_subscription,
        )
        self.create_subscription = async_to_streamed_response_wrapper(
            billing.create_subscription,
        )
        self.cancel_subscription = async_to_streamed_response_wrapper(
            billing.cancel_subscription,
        )
        self.list_payment_intents = async_to_streamed_response_wrapper(
            billing.list_payment_intents,
        )
        self.create_payment_intent = async_to_streamed_response_wrapper(
            billing.create_payment_intent,
        )
        self.list_payment_methods = async_to_streamed_response_wrapper(
            billing.list_payment_methods,
        )
        self.add_payment_method = async_to_streamed_response_wrapper(
            billing.add_payment_method,
        )
        self.remove_payment_method = async_to_streamed_response_wrapper(
            billing.remove_payment_method,
        )
        self.list_plans = async_to_streamed_response_wrapper(
            billing.list_plans,
        )
        self.get_plan = async_to_streamed_response_wrapper(
            billing.get_plan,
        )
        self.list_spend_alerts = async_to_streamed_response_wrapper(
            billing.list_spend_alerts,
        )
        self.create_spend_alert = async_to_streamed_response_wrapper(
            billing.create_spend_alert,
        )
        self.delete_spend_alert = async_to_streamed_response_wrapper(
            billing.delete_spend_alert,
        )
        self.get_portal_url = async_to_streamed_response_wrapper(
            billing.get_portal_url,
        )
