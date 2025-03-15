# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from ..._models import BaseModel
from .pass_through_generic_endpoint import PassThroughGenericEndpoint

__all__ = ["PassThroughEndpointResponse"]


class PassThroughEndpointResponse(BaseModel):
    endpoints: List[PassThroughGenericEndpoint]
