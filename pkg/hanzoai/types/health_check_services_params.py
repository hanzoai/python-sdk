# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from typing_extensions import Literal, Required, TypedDict

__all__ = ["HealthCheckServicesParams"]


class HealthCheckServicesParams(TypedDict, total=False):
    service: Required[
        Union[
            Literal[
                "slack_budget_alerts", "langfuse", "slack", "openmeter", "webhook", "email", "braintrust", "datadog"
            ],
            str,
        ]
    ]
    """Specify the service being hit."""
