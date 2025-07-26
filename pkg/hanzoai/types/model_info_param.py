# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Optional
from datetime import datetime
from typing_extensions import Literal, Required, Annotated, TypeAlias, TypedDict

from .._utils import PropertyInfo

__all__ = ["ModelInfoParam"]


class ModelInfoParamTyped(TypedDict, total=False):
    id: Required[Optional[str]]

    base_model: Optional[str]

    created_at: Annotated[Union[str, datetime, None], PropertyInfo(format="iso8601")]

    created_by: Optional[str]

    db_model: bool

    team_id: Optional[str]

    team_public_model_name: Optional[str]

    tier: Optional[Literal["free", "paid"]]

    updated_at: Annotated[Union[str, datetime, None], PropertyInfo(format="iso8601")]

    updated_by: Optional[str]


ModelInfoParam: TypeAlias = Union[ModelInfoParamTyped, Dict[str, object]]
