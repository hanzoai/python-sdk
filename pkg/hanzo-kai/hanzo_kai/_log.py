"""The `hanzo_kai` logger: its level comes from KAI_LOG_LEVEL, and no credential reaches it."""

import os
import logging
from collections.abc import Mapping

from hanzo_kai.constants import LOG_LEVEL_ENV

logger = logging.getLogger("hanzo_kai")

LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "off": logging.CRITICAL + 1,
}

SECRETS = frozenset({"authorization", "proxy-authorization", "cookie", "set-cookie", "x-api-key"})


def secret(name: str) -> bool:
    """Whether a header carries a credential."""
    name = name.lower()
    return name in SECRETS or "token" in name or "secret" in name


def redact(headers: Mapping[str, str]) -> dict[str, str]:
    """Headers with every credential masked, fit to log."""
    return {name: "<redacted>" if secret(name) else value for name, value in headers.items()}


def configure() -> None:
    """Sets the logger's level from KAI_LOG_LEVEL, warn when it is unset."""
    raw = os.environ.get(LOG_LEVEL_ENV, "").strip().lower()
    logger.setLevel(LEVELS.get(raw, logging.WARNING))
    if raw and raw not in LEVELS:
        logger.warning("%s=%r names no level; use one of %s", LOG_LEVEL_ENV, raw, ", ".join(LEVELS))


logger.addHandler(logging.NullHandler())
configure()
