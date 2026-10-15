"""RFC 8785 JSON canonicalization (JCS) and SHA-256 digests over it.

The Python peer of `canonical.rs` in the Rust crate: keys sorted by UTF-16 code
units, no whitespace, strings escaped by RFC 8785's table, numbers written as
ECMAScript writes them. Over strings, booleans, null, integers within 2**53 and
floats from 1e-6 up to 1e21 in magnitude the bytes equal the crate's
(`tests/vectors/rust.json` holds the crate's own output). Outside that range the
crate writes Rust's `Display` (`1e21` as 22 digits, `-0.0` as `-0`), which is not
RFC 8785; this module writes the RFC's `1e+21` and `0`.
"""

from __future__ import annotations

import enum
import math
import hashlib
import dataclasses
from typing import Any

__all__ = ["canonicalize", "digest", "number"]

_ESCAPES = {'"': '\\"', "\\": "\\\\", "\b": "\\b", "\f": "\\f", "\n": "\\n", "\r": "\\r", "\t": "\\t"}


def canonicalize(value: Any) -> bytes:
    """The RFC 8785 canonical bytes of a JSON value, a wire dataclass, or a mix of them."""
    out: list[str] = []
    _write(_plain(value), out)
    try:
        return "".join(out).encode("utf-8")
    except UnicodeEncodeError as e:
        raise ValueError(f"canonical JSON needs valid Unicode: {e}") from None


def digest(value: Any) -> str:
    """Lowercase hex SHA-256 of `canonicalize(value)`, as `rfc8785_digest` in the crate."""
    return hashlib.sha256(canonicalize(value)).hexdigest()


def number(x: int | float) -> str:
    """A number as ECMAScript's Number.prototype.toString writes it (RFC 8785 section 3.2.2.3)."""
    if isinstance(x, bool):
        raise TypeError("a boolean is not a number")
    if isinstance(x, int) and abs(x) <= 2**53:
        return str(x)
    try:
        f = float(x)
    except OverflowError:
        raise ValueError(f"{x} is past the range of a double") from None
    if not math.isfinite(f):
        raise ValueError(f"{f} has no JSON form")
    if f == 0:
        return "0"
    sign = "-" if f < 0 else ""
    # repr is the shortest decimal that reads back as f, as ECMAScript's digits are
    mantissa, _, exp = repr(abs(f)).partition("e")
    whole, _, frac = mantissa.partition(".")
    every = whole + frac
    digits = every.lstrip("0")
    # value = 0.<digits> * 10**n
    n = len(whole) + int(exp or 0) - (len(every) - len(digits))
    digits = digits.rstrip("0")
    k = len(digits)
    if k <= n <= 21:
        return sign + digits + "0" * (n - k)
    if 0 < n <= 21:
        return sign + digits[:n] + "." + digits[n:]
    if -6 < n <= 0:
        return sign + "0." + "0" * -n + digits
    e = n - 1
    mark = "+" if e > 0 else "-"
    head = digits if k == 1 else digits[0] + "." + digits[1:]
    return f"{sign}{head}e{mark}{abs(e)}"


def _plain(value: Any) -> Any:
    """Wire objects to plain JSON values: dataclasses by their fields, enums by value."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        dump = getattr(value, "dump", None)
        return _plain(dump() if callable(dump) else dataclasses.asdict(value))
    if isinstance(value, enum.Enum):
        return _plain(value.value)
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def _write(v: Any, out: list[str]) -> None:
    if v is None:
        out.append("null")
    elif v is True:
        out.append("true")
    elif v is False:
        out.append("false")
    elif isinstance(v, (int, float)):
        out.append(number(v))
    elif isinstance(v, str):
        _string(v, out)
    elif isinstance(v, list):
        out.append("[")
        for i, x in enumerate(v):
            if i:
                out.append(",")
            _write(x, out)
        out.append("]")
    elif isinstance(v, dict):
        for k in v:
            if not isinstance(k, str):
                raise TypeError(f"a JSON object key is a string, not {type(k).__name__}")
        out.append("{")
        for i, k in enumerate(sorted(v, key=lambda s: s.encode("utf-16-be", "surrogatepass"))):
            if i:
                out.append(",")
            _string(k, out)
            out.append(":")
            _write(v[k], out)
        out.append("}")
    else:
        raise TypeError(f"{type(v).__name__} has no JSON form")


def _string(s: str, out: list[str]) -> None:
    out.append('"')
    for c in s:
        e = _ESCAPES.get(c)
        if e is not None:
            out.append(e)
        elif c < " ":
            out.append(f"\\u{ord(c):04x}")
        else:
            out.append(c)
    out.append('"')
