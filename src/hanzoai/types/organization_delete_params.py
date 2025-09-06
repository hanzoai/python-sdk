# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

from .._types import SequenceNotStr

__all__ = ["OrganizationDeleteParams"]


class OrganizationDeleteParams(TypedDict, total=False):
    organization_ids: Required[SequenceNotStr[str]]
