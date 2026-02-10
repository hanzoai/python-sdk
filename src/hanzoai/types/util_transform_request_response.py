# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["UtilTransformRequestResponse"]


class UtilTransformRequestResponse(BaseModel):
    error: Optional[str] = None

    raw_request_api_base: Optional[str] = None

    raw_request_body: Optional[object] = None

    raw_request_headers: Optional[object] = None
