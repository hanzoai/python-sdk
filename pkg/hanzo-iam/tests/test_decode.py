"""One wire decision: is the body JSON, and did IAM answer at all?

hanzo.id serves its sign-in SPA on every unmatched path, so a wrong path answers
200 text/html. A decoder that trusts the status code dies inside .json() with a
byte offset that names neither the path nor the reason.
"""

import ast
from pathlib import Path

import httpx
import pytest

from hanzo_iam import routes


def response(body: bytes, content_type: str, status: int = 200) -> httpx.Response:
    request = httpx.Request("GET", "https://hanzo.id/v1/iam/nope")
    return httpx.Response(status, content=body, headers={"content-type": content_type}, request=request)


def test_json_decodes():
    assert routes.decode(response(b'{"users": []}', "application/json")) == {"users": []}


def test_the_sign_in_page_names_the_path():
    with pytest.raises(routes.IAMError) as caught:
        routes.decode(response(b"<!doctype html><title>Sign in</title>", "text/html"))

    message = str(caught.value)
    assert "/v1/iam/nope" in message
    assert "text/html" in message
    assert "not a refusal" in message


def test_a_body_with_no_content_type_is_not_guessed():
    with pytest.raises(routes.IAMError):
        routes.decode(response(b"{}", ""))


def test_unparseable_json_names_the_url():
    with pytest.raises(routes.IAMError) as caught:
        routes.decode(response(b"{not json", "application/json"))
    assert "hanzo.id" in str(caught.value)


def test_nothing_decodes_a_body_on_its_own():
    """Every module asks routes.decode.

    routes owns the decision; oauth carries the same guard for the login flow,
    which runs before a client exists. A mention in a comment is not a call, so
    this reads the syntax tree rather than the text.
    """
    package = Path(__file__).resolve().parent.parent / "hanzo_iam"
    loose = set()
    for f in package.glob("*.py"):
        if f.name in {"routes.py", "oauth.py"}:
            continue
        for node in ast.walk(ast.parse(f.read_text())):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "json"
                and not node.args
            ):
                loose.add(f.name)
    assert not loose, loose
