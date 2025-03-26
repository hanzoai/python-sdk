# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["PassThroughEndpointCreateParams"]


class PassThroughEndpointCreateParams(TypedDict, total=False):
    headers: Required[object]
    """Key-value pairs of headers to be forwarded with the request.

    You can set any key value pair here and it will be forwarded to your target
    endpoint
    """

    path: Required[str]
    """The route to be added to the LLM Proxy Server."""

    target: Required[str]
    """The URL to which requests for this path should be forwarded."""
