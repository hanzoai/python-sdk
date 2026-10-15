"""The record wire against a local stand-in for /v1/research: each batch posts to its
own path under its own key, a filter reaches the query, and compare names both runs."""
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import hanzo_research as research

SEEN = []


class Fake(BaseHTTPRequestHandler):
    def _answer(self, body):
        raw = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        SEEN.append(("POST", self.path, json.loads(self.rfile.read(n)), self.headers.get("Authorization")))
        self._answer({"project": "default", "recorded": 1})

    def do_GET(self):
        SEEN.append(("GET", self.path, None, self.headers.get("Authorization")))
        self._answer({"data": [{"id": "r1"}], "total": 1} if "/runs" in self.path else {"a": {}, "b": {}})

    def log_message(self, *a):
        pass


class RecordWire(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(("127.0.0.1", 0), Fake)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        research.configure(base=f"http://127.0.0.1:{cls.srv.server_port}", api_key="k", project="enso")

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        SEEN.clear()

    def test_each_batch_posts_to_its_path(self):
        out = research.record(benchmarks=[{"id": "b"}], runs=[{"id": "r", "benchmark": "b"}])
        self.assertEqual(sorted(out), ["benchmarks", "runs"])
        posted = {p: body for m, p, body, _ in SEEN if m == "POST"}
        self.assertEqual(posted["/v1/research/benchmarks"], {"benchmarks": [{"id": "b"}]})
        self.assertEqual(posted["/v1/research/runs"], {"runs": [{"id": "r", "benchmark": "b"}]})
        self.assertTrue(all(auth == "Bearer k" for *_, auth in SEEN))

    def test_an_empty_batch_is_not_sent(self):
        self.assertEqual(research.record(), {})
        self.assertEqual(SEEN, [])

    def test_runs_carry_their_filters(self):
        self.assertEqual(research.runs(benchmark="enso.route", org="hanzo"), [{"id": "r1"}])
        self.assertEqual(SEEN[0][1], "/v1/research/runs?benchmark=enso.route&org=hanzo")

    def test_compare_names_both_runs(self):
        research.compare("x", "y")
        self.assertEqual(SEEN[0][1], "/v1/research/compare?a=x&b=y")


if __name__ == "__main__":
    unittest.main()
