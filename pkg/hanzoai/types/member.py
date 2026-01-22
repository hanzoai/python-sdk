# Hanzo AI SDK

from typing import Optional
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["Member"]


class Member(BaseModel):
    role: Literal["admin", "user"]

    user_email: Optional[str] = None

    user_id: Optional[str] = None
