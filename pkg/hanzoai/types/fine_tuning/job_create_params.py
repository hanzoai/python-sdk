# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Union, Optional
from typing_extensions import Literal, Required, TypedDict

__all__ = ["JobCreateParams", "Hyperparameters"]


class JobCreateParams(TypedDict, total=False):
    custom_llm_provider: Required[Literal["openai", "azure", "vertex_ai"]]

    model: Required[str]

    training_file: Required[str]

    hyperparameters: Optional[Hyperparameters]

    integrations: Optional[List[str]]

    seed: Optional[int]

    suffix: Optional[str]

    validation_file: Optional[str]


class Hyperparameters(TypedDict, total=False):
    batch_size: Union[str, int, None]

    learning_rate_multiplier: Union[str, float, None]

    n_epochs: Union[str, int, None]
