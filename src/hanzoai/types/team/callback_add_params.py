# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import Literal, Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["CallbackAddParams"]


class CallbackAddParams(TypedDict, total=False):
    callback_name: Required[str]

    callback_vars: Required[Dict[str, str]]

    callback_type: Optional[Literal["success", "failure", "success_and_failure"]]

    llm_changed_by: Annotated[str, PropertyInfo(alias="llm-changed-by")]
    """
    The llm-changed-by header enables tracking of actions performed by authorized
    users on behalf of other users, providing an audit trail for accountability
    """
