# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["UtilTokenCounterResponse"]


class UtilTokenCounterResponse(BaseModel):
    api_model_used: str = FieldInfo(alias="model_used")

    request_model: str

    tokenizer_type: str

    total_tokens: int

    error: Optional[bool] = None

    error_message: Optional[str] = None

    original_response: Optional[Dict[str, object]] = None

    status_code: Optional[int] = None
