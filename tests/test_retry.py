"""A server that asks for a long wait gets an answer back, not a sleeping caller.

api.hanzo.ai answers an exhausted quota with 429 and Retry-After set to the
seconds until the quota resets, about 23,000. urllib3 sleeps for whatever
Retry-After says and retries three times, so a call left to its defaults holds
its caller for most of a day. The client sleeps through a wait of at most
:data:`hanzoai.client.WAIT` seconds; past that the answer reaches the caller at
once, with the wait on it.

A local server answers over a real socket. `time.sleep` is recorded rather than
slept, so a call that would block for hours fails here in milliseconds.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from hanzoai import Fault, Client
from hanzoai.answer import value
from hanzoai.cloud import AiApi
from hanzoai.cloud.exceptions import ApiException


class Minted:
    """A credential that already holds its token, so no call goes to IAM."""

    def token(self):
        return "tok"

    def invalidate(self):
        pass


@pytest.fixture
def slept(monkeypatch):
    """Every sleep urllib3 asks for, in order, and none of them taken."""
    asked = []
    monkeypatch.setattr("urllib3.util.retry.time.sleep", asked.append)
    return asked


@pytest.fixture
def server():
    """A server on a free port: the base URL, the staged answers, the paths it saw."""
    staged, seen = [], []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append(self.path)
            status, headers, body = staged.pop(0) if staged else (500, {}, {"title": "nothing staged"})
            data = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            for name, v in headers.items():
                self.send_header(name, v)
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        yield "http://127.0.0.1:{0}".format(httpd.server_address[1]), staged, seen
    finally:
        httpd.shutdown()
        httpd.server_close()


def limited(n, after, request="req_1"):
    return [(429, {"Retry-After": after, "x-request-id": request}, {"title": "Too Many Requests"})] * n


def test_a_long_wait_raises_at_once(server, slept):
    """23,000 seconds is not waited: one request, no sleep, and the 429 carries the header."""
    base, staged, seen = server
    staged.extend(limited(4, "23000"))
    with pytest.raises(Exception) as raised:
        AiApi(Client(base=base, credential=Minted())).get_models()
    assert (slept, len(seen)) == ([], 1)
    assert isinstance(raised.value, ApiException)
    assert (raised.value.status, raised.value.headers["Retry-After"]) == (429, "23000")


def test_a_short_wait_is_slept_and_retried(server, slept):
    """A wait under the ceiling is honoured as before: three sleeps, four requests, the API's error."""
    base, staged, seen = server
    staged.extend([(503, {"Retry-After": "1"}, {"title": "Service Unavailable"})] * 4)
    with pytest.raises(Exception) as raised:
        AiApi(Client(base=base, credential=Minted())).get_models()
    assert (slept, len(seen)) == ([1, 1, 1], 4)
    assert isinstance(raised.value, ApiException) and raised.value.status == 503


def test_the_fault_carries_the_wait(server, slept):
    """A capability reads the same answer through `send`, and its fault says how long to wait."""
    base, staged, seen = server
    staged.extend(limited(4, "23000", request="req_9"))
    with pytest.raises(Exception) as raised:
        value(Client(base=base, credential=Minted()).send("GET", "/v1/budget"))
    assert (slept, len(seen)) == ([], 1)
    assert isinstance(raised.value, Fault)
    assert (raised.value.status, raised.value.retry_after, raised.value.request) == (429, 23000, "req_9")
