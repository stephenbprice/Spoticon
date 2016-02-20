import os
from http.server import BaseHTTPRequestHandler, HTTPServer

class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):

    def log_message(self,format,*args):
        return

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        message = "Thank you."
        self.wfile.write(bytes(message,"utf8"))

        with open("./url.txt", "w+") as urlfile:
            urlfile.write(self.path)

        return

class Web_Server(object):

    def run(self):
        self.stopped = False
        server_address = ('127.0.0.1', 8081)
        self.httpd = HTTPServer(server_address, testHTTPServer_RequestHandler)
        while not self.stopped:
            self.httpd.handle_request()
            while not os.path.exists("./url.txt"):
                sleep(.5)
            with open("./url.txt", "r") as urlfile:
                url = urlfile.read()
            os.remove("./url.txt")
            self.stopped = True
        return url

