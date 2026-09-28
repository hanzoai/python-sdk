"""RetryPolicy: which failures a call tries again, and how long it waits between tries."""

import math
import random
from dataclasses import dataclass
from collections.abc import Callable, Collection

from hanzo_kai._errors import APIError, KaiError, APITimeoutError, APIConnectionError

RETRY_AFTER_MAX = 60.0
"""Longest wait, in seconds, a `Retry-After` header can ask for."""

STATUSES = frozenset({408, 409, 429, *range(500, 600)})


@dataclass(frozen=True)
class RetryPolicy:
    """How a call retries.

    The defaults retry twice: on 408, 409, 429 and every 5xx, on connection errors and on
    timeouts, waiting 0.5 s doubling to 8 s less up to 25% jitter, or what `Retry-After`
    asks for up to 60 s. Every retry carries `X-Kai-Retry-Count`.

    Examples:
        ```python
        from hanzo_kai import Kai, RetryPolicy

        kai = Kai(retry=RetryPolicy(max_retries=5, http_statuses={429, 503}))
        kai.decide(state, questions, retry=RetryPolicy(max_retries=0))  # this call only
        ```
    """

    max_retries: int = 2
    """Retries after the first attempt; 0 turns retrying off."""

    backoff_initial: float = 0.5
    """Seconds before the first retry, doubled for each one after; 0 retries at once."""

    backoff_max: float = 8.0
    """Longest backoff in seconds; 0 retries at once."""

    backoff_jitter: float = 0.25
    """Share of each backoff taken off at random, from 0 to 1."""

    http_statuses: Collection[int] = STATUSES
    """Statuses that are retried."""

    respect_retry_after: bool = True
    """Wait what `Retry-After` or `retry-after-ms` asks for, up to 60 s, instead of the backoff."""

    api_connection_error: bool = True
    """Retry an `APIConnectionError`: the request got no response."""

    api_timeout_error: bool = True
    """Retry an `APITimeoutError`: an attempt ran past its timeout."""

    exceptions: Collection[type[BaseException]] = ()
    """Further exception types that are retried."""

    predicate: Callable[[BaseException], bool] | None = None
    """Called with each error; True retries it whatever the rules above say."""

    timeout: float | None = None
    """Seconds a call may spend across all its attempts and waits; None sets no limit.

    A retry whose wait would end past this budget is not made, and the last error is raised.
    """

    def __post_init__(self) -> None:
        if isinstance(self.max_retries, bool) or not isinstance(self.max_retries, int) or self.max_retries < 0:
            raise KaiError("max_retries must be a non-negative integer")
        for name in ("backoff_initial", "backoff_max"):
            value = getattr(self, name)
            if not math.isfinite(value) or value < 0:
                raise KaiError(f"{name} must be a non-negative, finite number of seconds")
        if not 0 <= self.backoff_jitter <= 1:
            raise KaiError("backoff_jitter must be between 0 and 1")
        if self.timeout is not None and (not math.isfinite(self.timeout) or self.timeout <= 0):
            raise KaiError("timeout must be a positive, finite number of seconds, or None")

    def _retries(self, error: BaseException) -> bool:
        """Whether the policy tries a call again after `error`."""
        if isinstance(error, APITimeoutError):
            rule = self.api_timeout_error
        elif isinstance(error, APIConnectionError):
            rule = self.api_connection_error
        elif isinstance(error, APIError):
            rule = error.status in self.http_statuses
        else:
            rule = False
        return (
            rule or isinstance(error, tuple(self.exceptions)) or (self.predicate is not None and self.predicate(error))
        )

    def _delay(self, retry: int, error: BaseException) -> float:
        """Seconds to wait before retry number `retry`, counted from 1."""
        if self.respect_retry_after and isinstance(error, APIError) and error.retry_after is not None:
            return min(error.retry_after, RETRY_AFTER_MAX)
        if not self.backoff_initial or not self.backoff_max:
            return 0.0
        step = min(math.ldexp(self.backoff_initial, min(retry - 1, 64)), self.backoff_max)
        return step * (1 - self.backoff_jitter * random.random())
