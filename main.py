import server
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

    print(f"Server started at {config['ip']}:{config['port']}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()
