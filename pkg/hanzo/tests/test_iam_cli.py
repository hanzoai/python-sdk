"""The IAM CLI addresses routes IAM serves, with the credential in Authorization.

Every entity has the same five routes. A collection is a plural noun and one row
of it is {collection}/{owner}/{name}. A list arrives under the key the entity
declares, a row arrives as the record itself, absence is 404, and a refusal is an
RFC 9457 problem document.

The failure worth catching is not a crash. It is an address that parses, greps
clean of every retired verb, and still answers 404 to every call — which is why
the route table below is read from IAM's own source rather than from this file.
"""
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
        for match in call.finditer(p.read_text(errors="ignore")):
            path = match.group("lit")
            if path is None:
                base = consts.get(match.group("const"))
                if base is None:
                    continue
                path = base + (match.group("suffix") or "")
            out.add((match.group(1).upper(), path))
    return out


SERVED = served() if IAM.is_dir() else set()

# The route table is read from IAM's own source. Where that checkout is absent —
# any runner but a developer's — the shape assertions still run and only the
# "does the server serve this" half is skipped.
needs_iam = pytest.mark.skipif(not SERVED, reason="no hanzoai/iam checkout to read routes from")

RECORD = {"owner": "hanzo", "name": "x", "displayName": "X", "email": "x@hanzo.ai"}

REAL_CLIENT = httpx.Client
SEEN: dict = {}


@pytest.fixture(autouse=True)
def wire(monkeypatch, tmp_path):
    """One mock transport for the whole module, and a credential to present."""

    def transport(request):
        SEEN["request"] = request
        SEEN.setdefault("sent", []).append((request.method, request.url.path))
        # Every list key the table declares, plus one record, so any command reads.
        body = {key: [RECORD] for key in m.ENTITIES.values()}
        body.update(RECORD, total=1, deleted=True, status="ok", msg="", data={})
        return httpx.Response(200, json=body)

    def client(*a, **kw):
        return REAL_CLIENT(*a, **{**kw, "transport": httpx.MockTransport(transport)})

    monkeypatch.setattr(httpx, "Client", client)
    monkeypatch.setattr(m, "AUTH", tmp_path / "auth.json")
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


def pattern(path: str) -> str:
    """The concrete path, as the route it matched: .../hanzo/x -> .../:owner/:name."""
    return re.sub(r"/hanzo/x$", "/:owner/:name", path)


def test_the_server_serves_every_route_the_cli_names():
    missing = []
    for entity in m.ENTITIES:
        for argv, expect in (
            ([entity, "list"], ("GET", f"/v1/iam/{entity}")),
            ([entity, "get", "x", "-o", "hanzo"], ("GET", f"/v1/iam/{entity}/:owner/:name")),
            ([entity, "create", "-o", "hanzo", "-d", "name=x"], ("POST", f"/v1/iam/{entity}")),
            ([entity, "update", "x", "-o", "hanzo"], ("PUT", f"/v1/iam/{entity}/:owner/:name")),
            ([entity, "delete", "x", "-o", "hanzo"], ("DELETE", f"/v1/iam/{entity}/:owner/:name")),
        ):
            req = run(argv)
            assert (req.method, pattern(req.url.path)) == expect, argv
            if expect not in SERVED:
                missing.append((tuple(argv), expect))

    if SERVED:
        assert not missing, "the CLI names routes IAM does not serve:\n" + "\n".join(map(str, missing))


def test_no_route_is_a_verb_hanging_off_the_collection():
    """/<entity>/get, /update and /delete parse fine and answer 404."""
    for entity in m.ENTITIES:
        for argv in ([entity, "list"], [entity, "get", "x", "-o", "hanzo"]):
            assert not run(argv).url.path.endswith(("/get", "/update", "/delete"))


def test_password_uses_the_route_iam_registers():
    req = run(["password", "z", "-o", "hanzo", "-p", "s3cret"])
    assert (req.method, req.url.path) == ("PUT", "/v1/iam/password")
    if SERVED:
        assert ("PUT", "/v1/iam/password") in SERVED
    assert b"s3cret" not in bytes(req.url.query)


def test_updating_replaces_the_row_it_read():
    run(["users", "update", "z", "-o", "hanzo", "-d", "displayName=Zed"])
    assert SEEN["sent"] == [
        ("GET", "/v1/iam/users/hanzo/z"),
        ("PUT", "/v1/iam/users/hanzo/z"),
    ]
    # A PUT is a full replace, so the fields nobody touched have to still be there.
    sent = json.loads(SEEN["request"].read())["user"]
    assert sent["displayName"] == "Zed"
    assert sent["email"] == "x@hanzo.ai"


def test_a_password_rides_beside_the_user_row_never_inside_it():
    req = run(["users", "create", "-o", "hanzo", "-d", "name=z", "-d", "password=secret-pw"])
    body = json.loads(req.read())
    assert body["password"] == "secret-pw"
    assert "password" not in body["user"]


def test_only_users_nests_its_record():
    req = run(["roles", "create", "-o", "hanzo", "-d", "name=admin"])
    assert json.loads(req.read()) == {"owner": "hanzo", "name": "admin"}


def test_a_row_needs_the_organization_that_names_it():
    for argv in (["users", "get", "z"], ["users", "update", "z"], ["users", "delete", "z"]):
        result = CliRunner().invoke(m.iam_group, argv)
        assert result.exit_code != 0
        assert "--org" in result.output


def test_the_table_names_the_key_the_server_uses_not_the_word_in_the_path():
    # audit-logs answers "auditLogs" and webauthn-credentials "webauthnCredentials";
    # deriving the key from the path would read both as empty.
    assert m.ENTITIES["audit-logs"] == "auditLogs"
    assert m.ENTITIES["webauthn-credentials"] == "webauthnCredentials"


def test_credential_is_basic_in_authorization():
    req = run(["users", "list"])
    assert req.headers["Authorization"] == "Basic " + base64.b64encode(b"app:sec").decode()
    assert "sec" not in str(req.url.query)


def test_a_bearer_wins(monkeypatch):
    monkeypatch.setenv("IAM_TOKEN", "tok")
    assert run(["users", "list"]).headers["Authorization"] == "Bearer tok"


def _answer(monkeypatch, response: httpx.Response):
    monkeypatch.setattr(
        httpx,
        "Client",
        lambda *a, **kw: REAL_CLIENT(*a, **{**kw, "transport": httpx.MockTransport(lambda r: response)}),
    )


def test_absence_arrives_as_a_404_and_says_why(monkeypatch):
    _answer(monkeypatch, httpx.Response(
        404,
        json={"type": "about:blank", "title": "not found", "detail": "no such user"},
        headers={"content-type": "application/problem+json"},
    ))
    result = CliRunner().invoke(m.iam_group, ["users", "get", "nobody", "-o", "hanzo"])
    assert result.exit_code == 1
    assert "404" in result.output
    assert "no such user" in result.output


def test_a_reply_without_the_list_is_an_error_not_an_empty_page(monkeypatch):
    _answer(monkeypatch, httpx.Response(200, json={"total": 3}))
    result = CliRunner().invoke(m.iam_group, ["users", "list"])
    assert result.exit_code == 1
    assert "no users" in result.output


def test_no_api_path_survives():
    src = Path(m.__file__).read_text()
    assert "/api/" not in src
