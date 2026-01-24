# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional

from .._models import BaseModel

__all__ = ["UtilTransformRequestResponse"]


class UtilTransformRequestResponse(BaseModel):
    error: Optional[str] = None

    raw_request_api_base: Optional[str] = None

    raw_request_body: Optional[Dict[str, object]] = None

    raw_request_headers: Optional[Dict[str, object]] = None
