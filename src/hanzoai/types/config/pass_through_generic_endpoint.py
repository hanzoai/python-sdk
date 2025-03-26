# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.


from ..._models import BaseModel

__all__ = ["PassThroughGenericEndpoint"]


class PassThroughGenericEndpoint(BaseModel):
    headers: object
    """Key-value pairs of headers to be forwarded with the request.

    You can set any key value pair here and it will be forwarded to your target
    endpoint
    """

    path: str
    """The route to be added to the LLM Proxy Server."""

    target: str
    """The URL to which requests for this path should be forwarded."""
