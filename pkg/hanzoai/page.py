"""One page of a list, and the count the whole filter matched."""

from __future__ import annotations

from typing import Tuple, Generic, TypeVar, Iterator
from dataclasses import dataclass

__all__ = ["Page"]

T = TypeVar("T")


@dataclass(frozen=True)
class Page(Generic[T]):
    """`items` is this page. `total` is what the filter matched across all pages.

    `total` is the server's own count for the filter the server applied, which
    is what a pager needs to size itself. Where a capability narrows further on
    the client, the argument that narrows says so.
    """

    items: Tuple[T, ...] = ()
    total: int = 0

    def __iter__(self) -> Iterator[T]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)
