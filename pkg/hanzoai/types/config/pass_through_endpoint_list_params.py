# Hanzo AI SDK

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["PassThroughEndpointListParams"]


class PassThroughEndpointListParams(TypedDict, total=False):
    endpoint_id: Optional[str]
