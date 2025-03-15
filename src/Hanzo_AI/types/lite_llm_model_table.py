# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Union

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["LiteLlmModelTable"]


class LiteLlmModelTable(BaseModel):
    created_by: str

    updated_by: str

    api_model_aliases: Union[str, object, None] = FieldInfo(alias="model_aliases", default=None)
