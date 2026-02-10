# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from datetime import datetime
from typing_extensions import TypeAlias

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["SpendListTagsResponse", "SpendListTagsResponseItem"]


class SpendListTagsResponseItem(BaseModel):
    api_key: str

    call_type: str

    end_time: Union[str, datetime, None] = FieldInfo(alias="endTime", default=None)

    messages: Union[str, List[object], object, None] = None

    request_id: str

    response: Union[str, List[object], object, None] = None

    start_time: Union[str, datetime, None] = FieldInfo(alias="startTime", default=None)

    api_base: Optional[str] = None

    cache_hit: Optional[str] = None

    cache_key: Optional[str] = None

    completion_tokens: Optional[int] = None

    metadata: Optional[object] = None

    model: Optional[str] = None

    prompt_tokens: Optional[int] = None

    request_tags: Optional[object] = None

    requester_ip_address: Optional[str] = None

    spend: Optional[float] = None

    total_tokens: Optional[int] = None

    user: Optional[str] = None


SpendListTagsResponse: TypeAlias = List[SpendListTagsResponseItem]
