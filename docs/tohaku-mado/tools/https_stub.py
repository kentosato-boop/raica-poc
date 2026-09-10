#!/usr/bin/env python3
"""443番でQRコードスタブJSを返すHTTPSサーバー（document.write製ポップアップ用）"""
import http.server, ssl, os, subprocess, sys

D = os.path.dirname(os.path.abspath(__file__))
CERT = os.path.join(D, "stub-cert.pem")
KEY = os.path.join(D, "stub-key.pem")
if not (os.path.exists(CERT) and os.path.exists(KEY)):
    subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-keyout", KEY,
                    "-out", CERT, "-days", "30", "-nodes", "-subj", "/CN=cdnjs.cloudflare.com"],
                   check=True, capture_output=True)

sys.path.insert(0, D)
from capture import QRCODE_STUB  # noqa: E402

class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        body = QRCODE_STUB.encode() if ".js" in self.path else b"/* empty */"
        ctype = "application/javascript" if ".js" in self.path else "text/css"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


srv = http.server.HTTPServer(("127.0.0.1", 443), H)
sctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
sctx.load_cert_chain(CERT, KEY)
srv.socket = sctx.wrap_socket(srv.socket, server_side=True)
print("https stub on :443")
srv.serve_forever()
