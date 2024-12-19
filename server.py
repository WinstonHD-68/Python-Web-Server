from http.server import HTTPServer, BaseHTTPRequestHandler
import json

with open("settings.json", "r") as file:
    data = json.load(file)
class Serv(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.path = "/index.html"
        try:
            fto = open(self.path[1:]).read()
            self.send_response(200)
        except:
            fto = open("404.html").read()
            self.send_response(404)
        self.end_headers()
        self.wfile.write(bytes(fto, "utf-8"))

httpd = HTTPServer((str(data["ip"]), data["port"]), Serv)
print("Server started")
print("Running on " + str(data["ip"]) + ":" + str(data["port"]))

httpd.serve_forever()
