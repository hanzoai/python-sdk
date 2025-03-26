# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, List, Union, Optional
from typing_extensions import TypeAlias, TypedDict

from ..model_info_param import ModelInfoParam
from ..configurable_clientside_params_custom_auth_param import ConfigurableClientsideParamsCustomAuthParam

__all__ = ["UpdatePartialParams", "LlmParams", "LlmParamsConfigurableClientsideAuthParam"]


class UpdatePartialParams(TypedDict, total=False):
    llm_params: Optional[LlmParams]

    model_info: Optional[ModelInfoParam]

    model_name: Optional[str]


LlmParamsConfigurableClientsideAuthParam: TypeAlias = Union[str, ConfigurableClientsideParamsCustomAuthParam]


class LlmParamsTyped(TypedDict, total=False):
    api_base: Optional[str]

    api_key: Optional[str]

    api_version: Optional[str]

    aws_access_key_id: Optional[str]

    aws_region_name: Optional[str]

    aws_secret_access_key: Optional[str]

    budget_duration: Optional[str]

    configurable_clientside_auth_params: Optional[List[LlmParamsConfigurableClientsideAuthParam]]

    custom_llm_provider: Optional[str]

    input_cost_per_second: Optional[float]

    input_cost_per_token: Optional[float]

    llm_trace_id: Optional[str]

    max_budget: Optional[float]

    max_file_size_mb: Optional[float]

    max_retries: Optional[int]

    merge_reasoning_content_in_choices: Optional[bool]

    model: Optional[str]

    model_info: Optional[object]

    organization: Optional[str]

    output_cost_per_second: Optional[float]

    output_cost_per_token: Optional[float]

    region_name: Optional[str]

    rpm: Optional[int]

    stream_timeout: Union[float, str, None]

    timeout: Union[float, str, None]

    tpm: Optional[int]

    use_in_pass_through: Optional[bool]

    vertex_credentials: Union[str, object, None]

    vertex_location: Optional[str]

    vertex_project: Optional[str]

    watsonx_region_name: Optional[str]


LlmParams: TypeAlias = Union[LlmParamsTyped, Dict[str, object]]
