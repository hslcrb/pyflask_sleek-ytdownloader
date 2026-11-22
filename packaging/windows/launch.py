"""Launch the packaged local app without a dependency on installed Python."""

from pathlib import Path
import sys
from threading import Thread
import webbrowser

from werkzeug.serving import make_server

sys.path.insert(0, str(Path(__file__).resolve().parent))
from app import app


def smoke_test():
    with app.test_client() as client:
        for route in ("/", "/intro", "/api/settings/path", "/static/favicon.png"):
            if client.get(route).status_code != 200:
                raise RuntimeError(f"Smoke test failed: {route}")
        if client.post("/api/info", json={}).status_code != 400:
            raise RuntimeError("Metadata input validation failed")
    print("Sleek HTTP routes, configuration and static assets passed.")


if __name__ == "__main__":
    if sys.argv[1:] == ["--smoke-test"]:
        smoke_test()
    else:
        with make_server("127.0.0.1", 5000, app, threaded=True) as server:
            url = "http://127.0.0.1:5000"
            print(f"Sleek is running: {url} (Ctrl+C to stop)", flush=True)
            Thread(target=webbrowser.open, args=(url,), daemon=True).start()
            server.serve_forever()
