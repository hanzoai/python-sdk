"""The canonical luxfi/kms HTTP surface.

kms.hanzo.ai runs luxfi/kms. Its entire secret API is the routes below, all
under ``/v1/kms``::

    POST   /v1/kms/auth/login                            {clientId, clientSecret} -> {accessToken, expiresIn}
    GET    /v1/kms/orgs/{org}/secrets?path=&env=         -> {"names": [...]}
    GET    /v1/kms/orgs/{org}/secrets/{path}/{name}?env= -> {"secret": {"value": "..."}}
    POST   /v1/kms/orgs/{org}/secrets                    {path, name, env, value}  (create AND replace)
    DELETE /v1/kms/orgs/{org}/secrets/{path}/{name}?env=
    GET    /healthz | /v1/kms/healthz                    -> {"service": "kms", "status": "ok"}

There is no ``/api/*`` surface and there never was. The Infisical paths this
SDK used to send (``/api/v3/secrets/raw``, ``/api/v3/auth/login``,
``/api/v1/auth/kubernetes-auth/login``) have always 404'd against luxfi/kms.
The break stayed invisible because older builds embedded a console SPA behind
a root catch-all that answered every unmatched path with ``200 text/html`` —
so a wrong URL surfaced as a JSON decode error rather than a 404, and read
like a parsing bug. That catch-all is gone (``cmd/kms/main.go`` now ends in
``notFoundJSON``), so wrong paths answer honest JSON 404s.

Everything here is a pure function: the sync and async clients stay mirror
images by sharing it, and one set of tests pins the wire shape for both.
"""

from typing import Any, Optional
from urllib.parse import quote

#: The server treats a read with no ``env`` as this bucket. Writes have no
#: default at all — the server 400s on an empty ``env`` rather than silently
#: committing to a bucket that project/env/path readers never resolve — so
#: this SDK always sends an explicit value.
DEFAULT_ENV = "default"

LOGIN = "/v1/kms/auth/login"
HEALTH = "/v1/kms/healthz"


class VersionUnsupportedError(ValueError):
    """Raised when a caller asks for a specific version of a secret.

    luxfi/kms stores exactly one value per (path, name, env) — the ZapDB key
    is ``kms/secrets/{path}/{env}/{name}`` and a write upserts it in place.
    There is no version history and no versioned read, so a ``version=``
    argument can only be answered with the current value. Answering it
    silently would hand back something other than what was asked for; this
    fails loudly instead.
    """


def secrets_url(org: str) -> str:
    """Collection URL — list (GET) and upsert (POST)."""
    return f"/v1/kms/orgs/{quote(org, safe='')}/secrets"


def secret_url(org: str, path: str, name: str) -> str:
    """URL of a single secret — read (GET) and delete (DELETE).

    Every segment is escaped INDIVIDUALLY. The server splits the trailing
    path at its LAST slash into (path, name); escaping the joined string
    would percent-encode those separators away and the server would read the
    whole thing as one long name.
    """
    segments = [*_path_segments(path), _checked_name(name)]
    escaped = "/".join(quote(segment, safe="") for segment in segments)
    return f"{secrets_url(org)}/{escaped}"


def list_params(path: str, env: str) -> dict[str, str]:
    """Query for GET /v1/kms/orgs/{org}/secrets.

    ``path`` may be empty here — listing is a prefix scan over
    ``kms/secrets/{path}/{env}/`` and an empty path is a legitimate prefix.
    """
    return {"path": path, "env": _checked_env(env)}


def env_params(env: str) -> dict[str, str]:
    """Query for the single-secret read and delete routes."""
    return {"env": _checked_env(env)}


def upsert_body(path: str, name: str, value: str, env: str) -> dict[str, str]:
    """Body for POST /v1/kms/orgs/{org}/secrets — create and replace alike."""
    return {
        "path": "/".join(_path_segments(path)),
        "name": _checked_name(name),
        "env": _checked_env(env),
        "value": value,
    }


def check_version(version: Optional[int]) -> None:
    """Reject a versioned read. See :class:`VersionUnsupportedError`."""
    if version is not None:
        raise VersionUnsupportedError(
            f"cannot read version {version!r}: luxfi/kms holds exactly one value "
            "per (path, name, env) — there is no version history to read from. "
            "Drop the version argument to read the current value."
        )


def names_of(data: Any) -> list[str]:
    """Decode the list response: ``{"names": [...]}``."""
    if isinstance(data, dict) and isinstance(data.get("names"), list):
        return [str(name) for name in data["names"]]
    raise ValueError(f"unexpected KMS list response: {data!r}")


def value_of(data: Any) -> str:
    """Decode the single-secret response: ``{"secret": {"value": "..."}}``."""
    if isinstance(data, dict):
        secret = data.get("secret")
        if isinstance(secret, dict) and "value" in secret:
            return str(secret["value"])
    raise ValueError(f"unexpected KMS secret response: {data!r}")


def _path_segments(path: str) -> list[str]:
    segments = [segment for segment in path.split("/") if segment]
    if not segments:
        raise ValueError(
            "path is required: the server splits the trailing URL at its last "
            "slash into (path, name), so a bare name has nothing to split"
        )
    return segments


def _checked_name(name: str) -> str:
    if not name:
        raise ValueError("name is required")
    if "/" in name:
        raise ValueError(
            f"name may not contain '/': {name!r}. The server splits the trailing "
            "URL at its last slash, so a slashed name is written under one key "
            "and read back under another — the write looks like it succeeded and "
            "the read never finds it. Move the leading segments into path."
        )
    return name


def _checked_env(env: str) -> str:
    if not env.strip():
        raise ValueError(
            f"env is required (use {DEFAULT_ENV!r} for the default bucket): env is "
            "part of the storage key, and the server rejects an empty env on write"
        )
    return env
