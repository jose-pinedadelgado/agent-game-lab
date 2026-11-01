"""Run: python village/server.py  ->  http://localhost:8765
Agent API:  GET /state   POST /action {json}"""
import json
import pathlib
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from world import World  # noqa: E402

WORLD = World(seed=1)
STATIC = pathlib.Path(__file__).parent / "static"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(STATIC), **kw)

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/state":
            return self._json(WORLD.state())
        return super().do_GET()

    def do_POST(self):
        if self.path != "/action":
            return self._json({"ok": False, "error": "not found"}, 404)
        try:
            action = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        except json.JSONDecodeError:
            return self._json({"ok": False, "error": "invalid json"}, 400)
        res = WORLD.act(action)
        self._json(res, 200 if res["ok"] else 400)

    def log_message(self, *a):
        pass


def ticker():
    while True:
        WORLD.tick()
        time.sleep(0.5)


if __name__ == "__main__":
    threading.Thread(target=ticker, daemon=True).start()
    print("Village running at http://localhost:8765")
    ThreadingHTTPServer(("0.0.0.0", 8765), Handler).serve_forever()
