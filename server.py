#!/usr/bin/env python
import http.server
import socketserver
from urllib.parse import urlparse

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Set correct MIME type for .pbf files (vector tiles)
        if self.path.endswith('.pbf'):
            self.send_header('Content-Type', 'application/x-protobuf')
            # Don't set Content-Encoding: gzip since tiles were created with --no-tile-compression
        super().end_headers()

PORT = 8000

with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
    print(f"Server running at http://localhost:{PORT}/")
    print("Press Ctrl+C to stop")
    httpd.serve_forever()
