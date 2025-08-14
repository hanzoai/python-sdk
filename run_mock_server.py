#!/usr/bin/env python3
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

class MockHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/utils/token_counter":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {
                "model_used": "gpt-3.5-turbo",
                "request_model": "gpt-3.5-turbo", 
                "tokenizer_type": "cl100k_base",
                "total_tokens": 10
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{}')
    
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{}')
    
    def do_PUT(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{}')
        
    def do_DELETE(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{}')
    
    def log_message(self, format, *args):
        pass

server = HTTPServer(("127.0.0.1", 4010), MockHandler)
thread = Thread(target=server.serve_forever)
thread.daemon = True
thread.start()
print("Mock server ready on port 4010")

# Keep server running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    server.shutdown()