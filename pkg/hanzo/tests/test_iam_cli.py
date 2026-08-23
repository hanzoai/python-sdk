"""The IAM CLI addresses routes IAM serves, with the credential in Authorization."""
import base64, json, os, re
from pathlib import Path
import httpx, pytest
from click.testing import CliRunner
from hanzo.commands import iam as m

IAM = Path(os.environ.get("IAM_SOURCE", Path.home() / "work" / "hanzo" / "iam"))


def served():
    """Every /v1/iam route the server registers, read from its own source.

    A route is registered with a literal, or with a const, or with a const plus
    a suffix. All three are resolved here so the assertion is about what the
    server serves rather than about how it spells it.
    """
    consts = {}
    for p in IAM.rglob("*.go"):
        for name, value in re.findall(r'(\w+)\s*=\s*"(/v1/iam[^"]*)"', p.read_text(errors="ignore")):
            consts[name] = value

    call = re.compile(
        r'zip\.(Get|Post|Put|Patch|Delete)(?:\s*\[[^\]]*\])?\s*\(\s*[A-Za-z_][\w.]*\s*,\s*'
        r'(?:"(?P<lit>/v1/iam[^"]*)"|(?P<const>\w+)(?:\s*\+\s*"(?P<suffix>[^"]*)")?)'
    )
    out = set()
    for p in IAM.rglob("*.go"):
        if p.name.endswith("_test.go") or p.name == "zipdoc_gen.go":
            continue
        for m in call.finditer(p.read_text(errors="ignore")):
            path = m.group("lit")
            if path is None:
                base = consts.get(m.group("const"))
                if base is None:
                    continue
                path = base + (m.group("suffix") or "")
            out.add((m.group(1).upper(), path))
    return out


SERVED = served() if IAM.is_dir() else set()

# The route table is read from IAM's own source. Where that checkout is absent —
# any runner but a developer's — the shape assertions still run and only the
# "does the server serve this" half is skipped.
needs_iam = pytest.mark.skipif(not SERVED, reason="no hanzoai/iam checkout to read routes from")


REAL_CLIENT = httpx.Client
SEEN: dict = {}


@pytest.fixture(autouse=True)
def wire(monkeypatch):
    """One mock transport for the whole module, and a credential to present."""

    def transport(request):
        SEEN["request"] = request
        return httpx.Response(200, json={})

    def client(*a, **kw):
        return REAL_CLIENT(*a, **{**kw, "transport": httpx.MockTransport(transport)})

    monkeypatch.setattr(httpx, "Client", client)
    monkeypatch.setenv("IAM_CLIENT_ID", "app")
    monkeypatch.setenv("IAM_CLIENT_SECRET", "sec")
    monkeypatch.delenv("IAM_TOKEN", raising=False)
    monkeypatch.delenv("HANZO_API_KEY", raising=False)


def run(argv):
    SEEN.clear()
    result = CliRunner().invoke(m.iam_group, argv)
    assert result.exit_code == 0, f"{argv}: {result.output}{result.exception!r}"
    assert "request" in SEEN, f"{argv} sent no request: {result.output}"
    return SEEN["request"]


def test_the_server_serves_every_route_the_cli_names():
    missing = []
    for entity, read in m.ENTITIES.items():
        for argv, expect in (
            ([entity, "list"], ("GET", f"/v1/iam/{entity}")),
            ([entity, "get", "x", "-o", "hanzo"], (read, f"/v1/iam/{entity}/get")),
            ([entity, "create", "-o", "hanzo", "-d", "name=x"], ("POST", f"/v1/iam/{entity}")),
            ([entity, "update", "x", "-o", "hanzo"], ("POST", f"/v1/iam/{entity}/update")),
            ([entity, "delete", "x", "-o", "hanzo"], ("POST", f"/v1/iam/{entity}/delete")),
        ):
            req = run(argv)
            assert (req.method, req.url.path) == expect, argv
            missing.append((tuple(argv), expect)) if expect not in SERVED else None


    if SERVED:
        assert not missing, "the CLI names routes IAM does not serve:\n" + "\n".join(map(str, missing))


def test_password_uses_the_route_iam_registers():
    req = run(["password", "z", "-o", "hanzo", "-p", "s3cret"])
    assert (req.method, req.url.path) == ("PUT", "/v1/iam/password")
    if SERVED:
        assert ("PUT", "/v1/iam/password") in SERVED
    assert b"s3cret" not in bytes(req.url.query)


def test_credential_is_basic_in_authorization():
    req = run(["users", "list"])
    assert req.headers["Authorization"] == "Basic " + base64.b64encode(b"app:sec").decode()
    assert "sec" not in str(req.url.query)


def test_a_bearer_wins(monkeypatch):
    monkeypatch.setenv("IAM_TOKEN", "tok")
    assert run(["users", "list"]).headers["Authorization"] == "Bearer tok"


def test_no_api_path_survives():
    src = Path(m.__file__).read_text()
    assert "/api/" not in src
