# Hanzo AI SDK

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["ModelDeleteParams"]


class ModelDeleteParams(TypedDict, total=False):
    id: Required[str]
