# Hanzo AI SDK

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["InfoRetrieveParams"]


class InfoRetrieveParams(TypedDict, total=False):
    organization_id: Required[str]
