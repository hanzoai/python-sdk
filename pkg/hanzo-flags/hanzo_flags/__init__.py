# Copyright 2026 Hanzo AI, Inc. All rights reserved.
"""hanzo-flags — feature flags + A/B for the Hanzo native flags engine.

The Python client for cloud ``/v1/flags`` (the PostHog-compatible evaluation
endpoint the Rust core, Go, and @hanzo/flags all speak). Zero runtime deps.

    from hanzo_flags import HanzoFlags

    flags = HanzoFlags("https://api.hanzo.ai", token=tok)
    flags.load("user-123", person_properties={"plan": "pro"})
    if flags.is_enabled("checkout-exp"):
        ...
    variant = flags.variant("pricing-test")   # "control" | "b" | None
"""

from .async_client import AsyncHanzoFlags
from .client import HanzoFlags, evaluate
from .models import EvalContext, EvalResult, Group

__all__ = [
    "HanzoFlags",
    "AsyncHanzoFlags",
    "evaluate",
    "EvalContext",
    "EvalResult",
    "Group",
]

__version__ = "0.1.0"
