from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import json
import os
import mimetypes
import ssl
import time
from collections import defaultdict


# Load server configuration
with open("settings.json", "r") as file:
    config = json.load(file)


# Threaded HTTP Server
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass


# Rate limiting dictionary (IP-based tracking)
RATE_LIMIT = defaultdict(list)  # Tracks request timestamps for each IP
RATE_LIMIT_WINDOW = 10  # seconds
MAX_REQUESTS_PER_WINDOW = 5  # Maximum allowed requests per window


# Secure HTTP Request Handler
class SecureRequestHandler(BaseHTTPRequestHandler):
    # Root directory for serving files
    ROOT_DIR = os.path.abspath(".")  # Serve files from current directory
    ALLOWED_EXTENSIONS = [".html", ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".txt"]  # Restrict file types

    def do_GET(self):
        # Implement rate limiting
        if not self.rate_limit():
            self.send_error(429, "Too Many Requests")
            return

        # Default file for root path
        if self.path == "/":
            self.path = "/index.html"

        # Normalize the path to avoid directory traversal
        requested_path = os.path.normpath(os.path.join(self.ROOT_DIR, self.path.lstrip("/")))
        if not requested_path.startswith(self.ROOT_DIR):
            # Prevent access outside ROOT_DIR
            self.send_error(403, "Forbidden: Access denied")
            return

        # Check for allowed file types
        _, ext = os.path.splitext(requested_path)
        if ext not in self.ALLOWED_EXTENSIONS:
            self.send_error(403, "Forbidden: File type not allowed")
            return

        # Serve the requested file securely
        try:
            with open(requested_path, "rb") as file:
                content = file.read()
                self.send_response(200)
                # Guess MIME type for the file
                mime_type, _ = mimetypes.guess_type(requested_path)
                self.send_header("Content-Type", mime_type or "application/octet-stream")
                self.end_headers()
                self.wfile.write(content)
        except FileNotFoundError:
            # Serve custom 404 error page
            self.send_error(404, "File not found")
        except Exception as e:
            # Log server errors and send 500 response
            self.log_error("Internal server error: %s", str(e))
            self.send_error(500, "Internal server error")

    def rate_limit(self):
        """Implements basic rate limiting."""
        client_ip = self.client_address[0]
        current_time = time.time()
        RATE_LIMIT[client_ip] = [t for t in RATE_LIMIT[client_ip] if t > current_time - RATE_LIMIT_WINDOW]

        if len(RATE_LIMIT[client_ip]) >= MAX_REQUESTS_PER_WINDOW:
            return False  # Rate limit exceeded

        RATE_LIMIT[client_ip].append(current_time)
        return True

    def log_message(self, format, *args):
        """Override to add logging for requests."""
        with open("server.log", "a") as log_file:
            log_file.write("%s - - [%s] %s\n" % (self.client_address[0],
                                                 self.log_date_time_string(),
                                                 format % args))


# Start the server with enhanced security
if __name__ == "__main__":
    server_address = (config["ip"], config["port"])
    httpd = ThreadedHTTPServer(server_address, SecureRequestHandler)

    # Enable HTTPS with SSL/TLS
    try:
        httpd.socket = ssl.wrap_socket(
            httpd.socket,
            certfile="cert.pem",  # Path to SSL certificate
            keyfile="key.pem",    # Path to SSL key
            server_side=True
        )
        print("Running with HTTPS")
    except FileNotFoundError:
        print("SSL certificate or key not found. Starting server without HTTPS.")

    print(f"Secure server started at {config['ip']}:{config['port']}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()
