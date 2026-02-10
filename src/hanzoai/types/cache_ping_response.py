# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["CachePingResponse"]


class CachePingResponse(BaseModel):
    cache_type: str

    status: str

    health_check_cache_params: Optional[object] = None

    llm_cache_params: Optional[str] = None

    ping_response: Optional[bool] = None

    set_cache_response: Optional[str] = None
