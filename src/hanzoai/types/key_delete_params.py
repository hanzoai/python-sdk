# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["KeyDeleteParams"]


class KeyDeleteParams(TypedDict, total=False):
    key_aliases: Optional[SequenceNotStr[str]]

    keys: Optional[SequenceNotStr[str]]

    litellm_changed_by: Annotated[str, PropertyInfo(alias="litellm-changed-by")]
    """
    The litellm-changed-by header enables tracking of actions performed by
    authorized users on behalf of other users, providing an audit trail for
    accountability
    """
