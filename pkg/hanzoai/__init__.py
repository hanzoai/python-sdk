# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

# Import new modules
from . import mcp, auth, types, agents, cluster, grpo
from ._types import NOT_GIVEN, Omit, NoneType, NotGiven, Transport, ProxiesTypes
from ._utils import file_from_path
from ._client import (
    ENVIRONMENTS,
    Hanzo,
    Client,
    Stream,
    Timeout,
    AsyncHanzo,
    AsyncClient,
    AsyncStream,
    RequestOptions,
)
from ._models import BaseModel
from ._version import __title__, __version__
from ._response import APIResponse as APIResponse, AsyncAPIResponse as AsyncAPIResponse
from ._constants import DEFAULT_TIMEOUT, DEFAULT_MAX_RETRIES, DEFAULT_CONNECTION_LIMITS
from .llm_client import SimpleLLMClient, OpenAICompatibleClient, completion, set_api_key
from ._exceptions import (
    APIError,
    HanzoError,
    ConflictError,
    NotFoundError,
    APIStatusError,
    RateLimitError,
    APITimeoutError,
    BadRequestError,
    APIConnectionError,
    AuthenticationError,
    InternalServerError,
    PermissionDeniedError,
    UnprocessableEntityError,
    APIResponseValidationError,
)
from ._base_client import DefaultHttpxClient, DefaultAsyncHttpxClient
from ._utils._logs import setup_logging as _setup_logging

__all__ = [
    "types",
    "__version__",
    "__title__",
    "NoneType",
    "Transport",
    "ProxiesTypes",
    "NotGiven",
    "NOT_GIVEN",
    "Omit",
    "SimpleLLMClient",
    "OpenAICompatibleClient",
    "completion",
    "set_api_key",
    "HanzoError",
    "APIError",
    "APIStatusError",
    "APITimeoutError",
    "APIConnectionError",
    "APIResponseValidationError",
    "BadRequestError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "UnprocessableEntityError",
    "RateLimitError",
    "InternalServerError",
    "Timeout",
    "RequestOptions",
    "Client",
    "AsyncClient",
    "Stream",
    "AsyncStream",
    "Hanzo",
    "AsyncHanzo",
    "ENVIRONMENTS",
    "file_from_path",
    "BaseModel",
    "DEFAULT_TIMEOUT",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_CONNECTION_LIMITS",
    "DefaultHttpxClient",
    "DefaultAsyncHttpxClient",
    # New modules
    "agents",
    "mcp",
    "cluster",
    "auth",
    "grpo",
]

_setup_logging()

# Update the __module__ attribute for exported symbols so that
# error messages point to this module instead of the module
# it was originally defined in, e.g.
# hanzoai._exceptions.NotFoundError -> hanzoai.NotFoundError
__locals = locals()
for __name in __all__:
    if not __name.startswith("__"):
        try:
            __locals[__name].__module__ = "hanzoai"
        except (TypeError, AttributeError):
            # Some of our exported symbols are builtins which we can't set attributes for.
            pass
