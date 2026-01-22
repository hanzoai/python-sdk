# Hanzo AI SDK

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["PassThroughEndpointDeleteParams"]


class PassThroughEndpointDeleteParams(TypedDict, total=False):
    endpoint_id: Required[str]
