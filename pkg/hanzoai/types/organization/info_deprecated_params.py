# Hanzo AI SDK

from __future__ import annotations

from typing import List
from typing_extensions import Required, TypedDict

__all__ = ["InfoDeprecatedParams"]


class InfoDeprecatedParams(TypedDict, total=False):
    organizations: Required[List[str]]
