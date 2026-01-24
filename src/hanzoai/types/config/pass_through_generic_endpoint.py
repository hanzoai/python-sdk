# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional

from ..._models import BaseModel

__all__ = ["PassThroughGenericEndpoint", "Guardrails"]


class Guardrails(BaseModel):
    """Settings for a specific guardrail on a passthrough endpoint.

    Allows field-level targeting for guardrail execution.
    """

    request_fields: Optional[List[str]] = None
    """JSONPath expressions for input field targeting (pre_call).

    Examples: 'query', 'documents[*].text', 'messages[*].content'. If not specified,
    guardrail runs on entire request payload.
    """

    response_fields: Optional[List[str]] = None
    """JSONPath expressions for output field targeting (post_call).

    Examples: 'results[*].text', 'output'. If not specified, guardrail runs on
    entire response payload.
    """


class PassThroughGenericEndpoint(BaseModel):
    path: str
    """The route to be added to the LiteLLM Proxy Server."""

    target: str
    """The URL to which requests for this path should be forwarded."""

    id: Optional[str] = None
    """Optional unique identifier for the pass-through endpoint.

    If not provided, endpoints will be identified by path for backwards
    compatibility.
    """

    auth: Optional[bool] = None
    """Whether authentication is required for the pass-through endpoint.

    If True, requests to the endpoint will require a valid LiteLLM API key.
    """

    cost_per_request: Optional[float] = None
    """The USD cost per request to the target endpoint.

    This is used to calculate the cost of the request to the target endpoint.
    """

    guardrails: Optional[Dict[str, Optional[Guardrails]]] = None
    """Guardrails configuration for this passthrough endpoint.

    Dict keys are guardrail names, values are optional settings for field targeting.
    When set, all org/team/key level guardrails will also execute. Defaults to None
    (no guardrails execute).
    """

    headers: Optional[Dict[str, object]] = None
    """Key-value pairs of headers to be forwarded with the request.

    You can set any key value pair here and it will be forwarded to your target
    endpoint
    """

    include_subpath: Optional[bool] = None
    """
    If True, requests to subpaths of the path will be forwarded to the target
    endpoint. For example, if the path is /bria and include_subpath is True,
    requests to /bria/v1/text-to-image/base/2.3 will be forwarded to the target
    endpoint.
    """
