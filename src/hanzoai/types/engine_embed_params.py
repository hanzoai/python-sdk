# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Optional
from typing_extensions import Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["EngineEmbedParams"]


class EngineEmbedParams(TypedDict, total=False):
    body_model: Required[Annotated[str, PropertyInfo(alias="model")]]

    api_base: Optional[str]

    api_key: Optional[str]

    api_type: Optional[str]

    api_version: Optional[str]

    caching: bool

    custom_llm_provider: Union[str, Dict[str, object], None]

    input: SequenceNotStr[str]

    litellm_call_id: Optional[str]

    litellm_logging_obj: Optional[Dict[str, object]]

    logger_fn: Optional[str]

    api_timeout: Annotated[int, PropertyInfo(alias="timeout")]

    user: Optional[str]
