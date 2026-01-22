# Hanzo AI SDK

from __future__ import annotations

from typing import List, Optional
from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["KeyDeleteParams"]


class KeyDeleteParams(TypedDict, total=False):
    key_aliases: Optional[List[str]]

    keys: Optional[List[str]]

    hanzo_changed_by: Annotated[str, PropertyInfo(alias="hanzo-changed-by")]
    """
    The hanzo-changed-by header enables tracking of actions performed by
    authorized users on behalf of other users, providing an audit trail for
    accountability
    """
