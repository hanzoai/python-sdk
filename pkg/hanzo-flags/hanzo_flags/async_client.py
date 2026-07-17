# Copyright 2026 Hanzo AI, Inc. All rights reserved.
"""Async facade for :class:`hanzo_flags.HanzoFlags`.

Zero-dependency: the sync client's blocking urllib call runs in the default
executor, so an asyncio service gets ``await flags.load(...)`` without pulling an
async HTTP library in. The caching, fail-open, and accessors are the sync
client's — this only moves the one blocking call off the event loop.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from .client import HanzoFlags
from .models import EvalResult, Group


class AsyncHanzoFlags:
    """The async twin of :class:`HanzoFlags`; same constructor, awaitable ``load``."""

    def __init__(
        self,
        host: str,
        *,
        token: Optional[str] = None,
        project: Optional[str] = None,
        ttl_ms: int = 15_000,
        timeout_s: float = 3.0,
    ) -> None:
        self._c = HanzoFlags(
            host, token=token, project=project, ttl_ms=ttl_ms, timeout_s=timeout_s
        )

    async def load(
        self,
        distinct_id: str,
        *,
        person_properties: Optional[Dict[str, Any]] = None,
        groups: Optional[Dict[str, Group]] = None,
    ) -> EvalResult:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._c.load(
                distinct_id, person_properties=person_properties, groups=groups
            ),
        )

    def is_enabled(self, key: str) -> bool:
        return self._c.is_enabled(key)

    def variant(self, key: str) -> Optional[str]:
        return self._c.variant(key)

    def payload(self, key: str) -> Any:
        return self._c.payload(key)

    def all(self) -> EvalResult:
        return self._c.all()
