"""Pin what the sync and async clients actually put on the wire.

Every request is captured through an httpx MockTransport and asserted
whole — method, URL, query and body. Two invariants matter most:

* no request may touch an ``/api/`` path (the Infisical regression), and
* the sync and async clients must emit byte-identical request lines, so the
  two files cannot drift apart.
"""

import asyncio
import os
from typing import Any

import httpx
import pytest

from hanzo_kms import AsyncKMSClient, ClientSettings, KMSClient, routes
from hanzo_kms.models import settings_from_env

SITE_URL = "https://kms.test"
TOKEN = "test-access-token"
VALUE = "correct horse battery staple"

SETTINGS = ClientSettings(
    site_url=SITE_URL,
    org="lux",
    client_id="cid",
    client_secret="csecret",
)


class Recorder:
    """Captures requests and answers with the server's documented shapes."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path
        if path == routes.LOGIN:
            return httpx.Response(200, json={"accessToken": TOKEN, "expiresIn": 3600})
        if path == routes.HEALTH:
            return httpx.Response(200, json={"service": "kms", "status": "ok"})
        if request.method == "GET" and path.endswith("/secrets"):
            return httpx.Response(200, json={"names": ["deploy-mnemonic", "bls-key"]})
        if request.method == "GET":
            return httpx.Response(200, json={"secret": {"value": VALUE}})
        if request.method == "POST":
            return httpx.Response(201, json={"ok": True})
        return httpx.Response(200, json={"ok": True})

    @property
    def lines(self) -> list[tuple[str, str, bytes]]:
        return [(r.method, str(r.url), r.content) for r in self.requests]

    @property
    def urls(self) -> list[str]:
        return [str(r.url) for r in self.requests]


def sync_client(recorder: Recorder) -> KMSClient:
    """A client whose lazily-built transport is the recorder."""
    client = KMSClient(SETTINGS.model_copy())
    client._http_client = httpx.Client(
        base_url=SITE_URL, transport=httpx.MockTransport(recorder)
    )
    return client


def async_client(recorder: Recorder) -> AsyncKMSClient:
    client = AsyncKMSClient(SETTINGS.model_copy())
    client._http_client = httpx.AsyncClient(
        base_url=SITE_URL, transport=httpx.MockTransport(recorder)
    )
    return client


def record_sync() -> Recorder:
    """Drive every operation once, synchronously."""
    recorder = Recorder()
    with sync_client(recorder) as client:
        client.health()
        client.list_secrets("providers/lux", "prod")
        client.get_secret("providers/lux", "deploy-mnemonic", "prod")
        client.put_secret("providers/lux", "deploy-mnemonic", VALUE, "prod")
        client.delete_secret("providers/lux", "deploy-mnemonic", "prod")
    return recorder


def record_async() -> Recorder:
    """Drive every operation once, asynchronously — same order."""
    recorder = Recorder()

    async def run() -> None:
        async with async_client(recorder) as client:
            await client.health()
            await client.list_secrets("providers/lux", "prod")
            await client.get_secret("providers/lux", "deploy-mnemonic", "prod")
            await client.put_secret("providers/lux", "deploy-mnemonic", VALUE, "prod")
            await client.delete_secret("providers/lux", "deploy-mnemonic", "prod")

    asyncio.run(run())
    return recorder


@pytest.fixture(params=[record_sync, record_async], ids=["sync", "async"])
def recorded(request: Any) -> Recorder:
    return request.param()


def test_no_request_touches_an_api_path(recorded: Recorder) -> None:
    """The regression pin: /api/* is Infisical's surface, never luxfi/kms's."""
    assert recorded.urls
    for url in recorded.urls:
        assert "/api/" not in url, f"{url} regressed onto an Infisical /api/ path"


def test_full_request_sequence(recorded: Recorder) -> None:
    """Every route, exactly as cmd/kms/main.go registers it."""
    assert recorded.lines == [
        ("GET", f"{SITE_URL}/v1/kms/healthz", b""),
        ("POST", f"{SITE_URL}/v1/kms/auth/login", b'{"clientId":"cid","clientSecret":"csecret"}'),
        ("GET", f"{SITE_URL}/v1/kms/orgs/lux/secrets?path=providers%2Flux&env=prod", b""),
        ("GET", f"{SITE_URL}/v1/kms/orgs/lux/secrets/providers/lux/deploy-mnemonic?env=prod", b""),
        (
            "POST",
            f"{SITE_URL}/v1/kms/orgs/lux/secrets",
            b'{"path":"providers/lux","name":"deploy-mnemonic","env":"prod","value":"%s"}'
            % VALUE.encode(),
        ),
        (
            "DELETE",
            f"{SITE_URL}/v1/kms/orgs/lux/secrets/providers/lux/deploy-mnemonic?env=prod",
            b"",
        ),
    ]


def test_sync_and_async_are_mirror_images() -> None:
    """The two clients are one surface with two I/O models. Keep them equal."""
    assert record_sync().lines == record_async().lines


def test_bearer_on_every_call_except_login_and_health(recorded: Recorder) -> None:
    for request in recorded.requests:
        authorization = request.headers.get("authorization")
        if request.url.path in (routes.LOGIN, routes.HEALTH):
            assert authorization is None
        else:
            assert authorization == f"Bearer {TOKEN}"


def test_org_scopes_the_url() -> None:
    recorder = Recorder()
    client = KMSClient(SETTINGS.model_copy(update={"org": "hanzo"}))
    client._http_client = httpx.Client(
        base_url=SITE_URL, transport=httpx.MockTransport(recorder)
    )
    client.get_secret("providers/hanzo", "deploy-mnemonic")
    client.close()
    assert recorder.urls[-1] == (
        f"{SITE_URL}/v1/kms/orgs/hanzo/secrets/providers/hanzo/deploy-mnemonic?env=default"
    )


def test_returned_values() -> None:
    recorder = Recorder()
    with sync_client(recorder) as client:
        assert client.health() == {"service": "kms", "status": "ok"}
        assert client.list_secrets("providers/lux", "prod") == ["deploy-mnemonic", "bls-key"]
        assert client.get_secret("providers/lux", "deploy-mnemonic", "prod") == VALUE


def test_versioned_read_refused_before_any_request() -> None:
    recorder = Recorder()
    with sync_client(recorder) as client:
        with pytest.raises(routes.VersionUnsupportedError):
            client.get_secret("providers/lux", "deploy-mnemonic", "prod", version=2)
    assert recorder.requests == []


def test_pre_issued_token_skips_login() -> None:
    recorder = Recorder()
    client = KMSClient(
        ClientSettings(site_url=SITE_URL, org="lux", access_token="pre-issued")
    )
    client._http_client = httpx.Client(
        base_url=SITE_URL, transport=httpx.MockTransport(recorder)
    )
    client.list_secrets("providers/lux", "prod")
    client.close()
    assert routes.LOGIN not in recorder.urls[0]
    assert recorder.requests[0].headers["authorization"] == "Bearer pre-issued"


def test_missing_credentials_fail_loudly() -> None:
    client = KMSClient(ClientSettings(site_url=SITE_URL, org="lux"))
    with pytest.raises(ValueError, match="no KMS credentials"):
        client.list_secrets("providers/lux", "prod")


def test_inject_env_lists_then_reads_each(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("deploy-mnemonic", raising=False)
    monkeypatch.delenv("bls-key", raising=False)
    recorder = Recorder()
    with sync_client(recorder) as client:
        assert client.inject_env("providers/lux", "prod") == 2
    assert os.environ["deploy-mnemonic"] == VALUE
    assert os.environ["bls-key"] == VALUE
    # one login + one list + one read per name
    assert len(recorder.requests) == 4


@pytest.mark.parametrize(
    ("env_var", "field", "value"),
    [
        ("HANZO_KMS_URL", "site_url", "https://kms.lux.network"),
        ("HANZO_KMS_ORG", "org", "zoo"),
        ("HANZO_KMS_CLIENT_ID", "client_id", "an-id"),
        ("HANZO_KMS_CLIENT_SECRET", "client_secret", "a-secret"),
        ("HANZO_KMS_TOKEN", "access_token", "a-token"),
    ],
)
def test_settings_from_env(
    monkeypatch: pytest.MonkeyPatch, env_var: str, field: str, value: str
) -> None:
    monkeypatch.setenv(env_var, value)
    assert getattr(settings_from_env(), field) == value


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for env_var in (
        "HANZO_KMS_URL",
        "HANZO_KMS_ORG",
        "HANZO_KMS_CLIENT_ID",
        "HANZO_KMS_CLIENT_SECRET",
        "HANZO_KMS_TOKEN",
    ):
        monkeypatch.delenv(env_var, raising=False)
    settings = settings_from_env()
    assert settings.site_url == "https://kms.hanzo.ai"
    assert settings.org == "hanzo"


def test_both_clients_expose_the_same_methods() -> None:
    """Mirror images down to the method names."""

    def public(cls: type) -> set[str]:
        return {name for name in vars(cls) if not name.startswith("_")}

    assert public(KMSClient) == public(AsyncKMSClient)
