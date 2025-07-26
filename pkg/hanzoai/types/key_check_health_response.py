# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["KeyCheckHealthResponse", "LoggingCallbacks"]


class LoggingCallbacks(BaseModel):
    callbacks: Optional[List[str]] = None

    details: Optional[str] = None

    status: Optional[Literal["healthy", "unhealthy"]] = None


class KeyCheckHealthResponse(BaseModel):
    key: Optional[Literal["healthy", "unhealthy"]] = None

    logging_callbacks: Optional[LoggingCallbacks] = None
