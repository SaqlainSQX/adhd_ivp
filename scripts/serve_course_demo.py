"""Serve the local course explorer on loopback; frozen predictions, no GPU work."""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from gaze_audit.explorer import AuditExplorer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--main", type=Path, default=Path("outputs/experiments/course-20261107-v1"))
    parser.add_argument("--processed", type=Path, default=Path("data/processed/vsgaze-17357752-v1"))
    parser.add_argument(
        "--acquisition", type=Path, default=Path("data/raw/childplay/verified-population-v2")
    )
    parser.add_argument(
        "--extension", type=Path, default=Path("outputs/experiments/strengthening-20261107-v1")
    )
    args = parser.parse_args()
    explorer = AuditExplorer(args.main, args.processed, args.acquisition, args.extension)
    assets = Path(__file__).resolve().parents[1] / "demo"

    class Handler(BaseHTTPRequestHandler):
        def respond(self, body, mime="application/json; charset=utf-8", status=200):
            if not isinstance(body, bytes):
                body = json.dumps(body, allow_nan=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            url = urlparse(self.path)
            query = parse_qs(url.query)
            try:
                if url.path in ["/", "/index.html", "/app.js", "/style.css"]:
                    name = "index.html" if url.path == "/" else url.path[1:]
                    mime = {
                        "index.html": "text/html",
                        "app.js": "text/javascript",
                        "style.css": "text/css",
                    }[name]
                    self.respond((assets / name).read_bytes(), mime + "; charset=utf-8")
                elif url.path == "/api/summary":
                    self.respond(explorer.summary())
                elif url.path == "/api/replay":
                    self.respond(
                        explorer.replay(
                            query.get("method", ["M3"])[0],
                            float(query.get("fraction", ["0.1"])[0]),
                            int(query.get("draw", ["0"])[0]),
                        )
                    )
                elif url.path == "/api/frame":
                    self.respond(explorer.frame(query.get("id", [""])[0]), "image/jpeg")
                elif url.path == "/api/health":
                    self.respond({"ready": True, "mode": "local frozen-cache replay"})
                else:
                    self.respond({"error": "Route not found"}, status=404)
            except (ValueError, KeyError, IndexError) as exc:
                self.respond({"error": str(exc)}, status=400)
            except (FileNotFoundError, ModuleNotFoundError) as exc:
                self.respond({"error": f"Local prerequisite unavailable: {exc}"}, status=503)
            except Exception as exc:
                self.respond({"error": f"Replay failed: {type(exc).__name__}: {exc}"}, status=500)

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Course explorer ready: http://127.0.0.1:{args.port} (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
