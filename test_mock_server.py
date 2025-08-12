#!/usr/bin/env python3
"""Simple mock server for testing cache endpoints."""

import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler


class MockHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/cache/ping":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {
                "status": "healthy",
                "cache_type": "redis",
                "ping_response": True,
                "set_cache_response": None,
                "llm_cache_params": None,
                "health_check_cache_params": None,
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/cache/delete":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b"{}")
        elif self.path == "/cache/flushall":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b"{}")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress logs


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 4010), MockHandler)
    print("Mock server running on http://127.0.0.1:4010")
    print("Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        sys.exit(0)
