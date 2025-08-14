#!/usr/bin/env python3
"""Comprehensive mock server for all test endpoints."""

import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler


class MockHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        
        # Default response
        response = {}
        
        # Handle specific endpoints
        if "/files/" in self.path and "/content" in self.path:
            response = "file content"
        elif self.path == "/guardrails/list":
            response = {"guardrails": []}
        elif self.path == "/global/spend/tags":
            response = []
        elif self.path == "/global/spend/report":
            response = []
        elif self.path == "/organization/info":
            response = {
                "budget_id": "budget-123",
                "created_at": "2024-01-01T00:00:00Z",
                "created_by": "user-123",
                "models": ["gpt-3.5-turbo"],
                "updated_at": "2024-01-01T00:00:00Z",
                "updated_by": "user-123"
            }
        elif self.path == "/config/pass_through_endpoint":
            response = {"endpoints": []}
        elif self.path == "/":
            response = {}
        else:
            response = {"data": []}
        
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        """Handle POST requests."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        
        # Default response
        response = {}
        
        # Handle specific endpoints
        if self.path == "/utils/token_counter":
            response = {
                "model_used": "gpt-3.5-turbo",
                "request_model": "gpt-3.5-turbo",
                "tokenizer_type": "cl100k_base",
                "total_tokens": 10
            }
        elif self.path == "/chat/completions":
            response = {
                "id": "chatcmpl-123",
                "object": "chat.completion",
                "created": 1677652288,
                "model": "gpt-3.5-turbo",
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": "Hello!"},
                    "finish_reason": "stop"
                }]
            }
        
        self.wfile.write(json.dumps(response).encode())
    
    def do_PUT(self):
        """Handle PUT requests."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b"{}")
    
    def do_DELETE(self):
        """Handle DELETE requests."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        
        # Handle specific endpoints
        if self.path == "/config/pass_through_endpoint":
            response = {"endpoints": []}
        else:
            response = {}
        
        self.wfile.write(json.dumps(response).encode())
    
    def log_message(self, format, *args):
        pass  # Suppress logs


if __name__ == "__main__":
    try:
        server = HTTPServer(("127.0.0.1", 4010), MockHandler)
        print("Mock server started on http://127.0.0.1:4010")
        print("Press Ctrl+C to stop")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down mock server...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)