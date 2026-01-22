# Hanzo AI SDK

from __future__ import annotations

from typing import List
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["UserDeleteParams"]


class UserDeleteParams(TypedDict, total=False):
    user_ids: Required[List[str]]

    hanzo_changed_by: Annotated[str, PropertyInfo(alias="hanzo-changed-by")]
    """
    The hanzo-changed-by header enables tracking of actions performed by
    authorized users on behalf of other users, providing an audit trail for
    accountability
    """
