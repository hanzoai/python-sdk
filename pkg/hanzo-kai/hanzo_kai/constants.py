"""Environment variables the clients read, and the defaults they fall back to."""

API_KEY_ENV = "HANZO_API_KEY"
"""API key: a Hanzo `sk-` key or an IAM access token. A publishable `pk-` key is refused."""

BASE_URL_ENV = "HANZO_BASE_URL"
"""API root the clients call."""

DEFAULT_MODEL_ENV = "KAI_MODEL"
"""Model a decision asks for when the call names none."""

LOG_LEVEL_ENV = "KAI_LOG_LEVEL"
"""Level of the `hanzo_kai` logger: debug, info, warn, error or off."""

DEFAULT_BASE_URL = "https://api.hanzo.ai"
"""API root when neither `base_url` nor `HANZO_BASE_URL` names one."""

DEFAULT_MODEL = "kai"
"""Model when neither `model` nor `KAI_MODEL` names one."""

DEFAULT_TIMEOUT = 60.0
"""Seconds each HTTP attempt may take."""
