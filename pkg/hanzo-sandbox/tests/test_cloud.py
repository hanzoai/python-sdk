"""The cloud sandboxes client, checked against the contract cloud actually serves.

Served by a real HTTP server rather than a mocked urlopen, because most of what
can go wrong here is in the request: the path, the method, and the credential.

The org is NOT sent. cloud derives it from the validated principal the API key
carries, and the gateway strips a client-supplied X-Org-Id anyway — so a test
that asserted the header would be pinning a thing the server ignores.
"""

from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from hanzo_sandbox import Exec, Sandbox, SandboxError, Sandboxes

SEEN: list[dict] = []


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # keep the test output quiet
        pass

    def _record(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n)) if n else None
        row = {"method": self.command, "path": self.path, "org": self.headers.get("X-Org-Id"),
               "auth": self.headers.get("Authorization"), "body": body}  # org captured to prove it is absent
        SEEN.append(row)
        return row

    def _send(self, code: int, payload) -> None:
        raw = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        row = self._record()
        # cloud refuses an unauthenticated caller; the org rides inside the key
        if not row["auth"]:
            return self._send(403, {"error": "X-Org-Id required"})
        if row["path"] == "/v1/sandboxes":
            return self._send(200, [{"id": "sb_1", "class": "small", "status": "running"}])
        if row["path"].endswith("/fs?path=/etc/hosts"):
            return self._send(200, {"content": "127.0.0.1 localhost"})
        return self._send(200, {"id": "sb_1", "class": "small", "status": "running", "createdAt": 7})

    def do_POST(self):
        row = self._record()
        if row["path"].endswith("/exec"):
            return self._send(200, {"exitCode": 0, "stdout": "hi\n", "stderr": ""})
        if row["path"].endswith("/fs"):
            return self._send(200, {})
        return self._send(200, {"id": "sb_new", "status": "pending", "image": row["body"].get("image", "")})

    def do_DELETE(self):
        self._record()
        self._send(200, {})


class CloudSandboxesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.srv.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        SEEN.clear()
        self.boxes = Sandboxes(api_key="sk-test", base_url=self.base)

    def test_list_hits_the_collection_and_parses_class(self):
        got = self.boxes.list()
        self.assertEqual(SEEN[0]["path"], "/v1/sandboxes")
        self.assertEqual(SEEN[0]["method"], "GET")
        # cloud spells it `class`, which python cannot; the client maps it to cls
        self.assertEqual(got[0].cls, "small")
        self.assertTrue(got[0].running)

    def test_every_call_carries_the_key_and_never_the_org(self):
        self.boxes.list()
        self.boxes.get("sb_1")
        self.boxes.delete("sb_1")
        self.assertTrue(all(r["auth"] == "Bearer sk-test" for r in SEEN), SEEN)
        # the org is the key's to state, not the caller's
        self.assertTrue(all(r["org"] is None for r in SEEN), SEEN)

    def test_create_posts_to_the_collection_and_drops_empty_fields(self):
        got = self.boxes.create(image="ghcr.io/hanzoai/base:latest")
        self.assertEqual(SEEN[0]["method"], "POST")
        self.assertEqual(SEEN[0]["path"], "/v1/sandboxes")
        self.assertEqual(SEEN[0]["body"], {"image": "ghcr.io/hanzoai/base:latest"})
        self.assertEqual(got.id, "sb_new")

    def test_exec_sends_argv_and_reads_exitcode(self):
        got = self.boxes.exec("sb_1", argv=["echo", "hi"], timeout_sec=5)
        self.assertEqual(SEEN[0]["path"], "/v1/sandboxes/sb_1/exec")
        self.assertEqual(SEEN[0]["body"], {"argv": ["echo", "hi"], "timeoutSec": 5})
        self.assertTrue(got.ok)
        self.assertEqual(got.stdout, "hi\n")

    def test_exec_refuses_to_send_nothing(self):
        with self.assertRaises(ValueError):
            self.boxes.exec("sb_1")
        self.assertEqual(SEEN, [], "a call with no command must not reach the network")

    def test_fs_round_trip(self):
        self.assertEqual(self.boxes.read("sb_1", "/etc/hosts"), "127.0.0.1 localhost")
        self.boxes.write("sb_1", "/tmp/x", "body")
        self.assertEqual(SEEN[-1]["body"], {"path": "/tmp/x", "content": "body"})

    def test_a_refusal_arrives_as_SandboxError_with_its_status(self):
        anon = Sandboxes(api_key="", base_url=self.base)
        with self.assertRaises(SandboxError) as e:
            anon.list()
        self.assertEqual(e.exception.status, 403)
        self.assertIn("X-Org-Id", e.exception.message)


if __name__ == "__main__":
    unittest.main()
