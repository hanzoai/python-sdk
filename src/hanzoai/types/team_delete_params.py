# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["TeamDeleteParams"]


class TeamDeleteParams(TypedDict, total=False):
    team_ids: Required[SequenceNotStr[str]]

    litellm_changed_by: Annotated[str, PropertyInfo(alias="litellm-changed-by")]
    """
    The litellm-changed-by header enables tracking of actions performed by
    authorized users on behalf of other users, providing an audit trail for
    accountability
    """
