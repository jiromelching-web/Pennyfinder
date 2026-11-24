#!/usr/bin/env python3
"""Run PennyFinder on your own PC with a live Refresh button.
   python3 serve_local.py      -> open http://localhost:8765  (phone on same Wi-Fi: http://<PC-IP>:8765)
Refresh calls POST /api/refresh, which runs scripts/refresh.py right then."""
import http.server, subprocess, sys, os, functools
ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(ROOT, "docs")
class H(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path.rstrip("/").endswith("/api/refresh"):
            p = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "refresh.py"),
                                "--out", os.path.join(DOCS, "data", "deals.json")], capture_output=True, text=True)
            body = (p.stdout + p.stderr).encode()
            self.send_response(200 if p.returncode == 0 else 502)
            self.send_header("Content-Type", "text/plain"); self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body)
        else:
            self.send_error(404)
    def end_headers(self):
        self.send_header("Cache-Control", "no-store"); super().end_headers()
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8765))
    print(f"PennyFinder at http://localhost:{port}  (Ctrl+C to stop)")
    http.server.ThreadingHTTPServer(("0.0.0.0", port), functools.partial(H, directory=DOCS)).serve_forever()
