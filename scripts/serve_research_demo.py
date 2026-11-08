"""Serve aggregate research evidence and optional verified D replay on loopback."""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from gaze_audit.research_explorer import ResearchExplorer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--aggregate-only", action="store_true")
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    explorer = ResearchExplorer(project, aggregate_only=args.aggregate_only)
    assets = project / "demo/research"

    class Handler(BaseHTTPRequestHandler):
        def respond(self, body, mime="application/json; charset=utf-8", status=200):
            if not isinstance(body, bytes):
                body = json.dumps(body, allow_nan=False).encode("utf-8")
            self.send_response(status)
            for key, value in [
                ("Content-Type", mime),
                ("Content-Length", str(len(body))),
                ("Cache-Control", "no-store"),
                ("X-Content-Type-Options", "nosniff"),
            ]:
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            url = urlparse(self.path)
            query = parse_qs(url.query, keep_blank_values=True)
            try:
                if any(len(v) != 1 for v in query.values()):
                    raise ValueError("Query arguments must be unique")
                if url.path in [
                    "/",
                    "/index.html",
                    "/app.js",
                    "/style.css",
                    "/data.js",
                    "/data.json",
                ]:
                    name = "index.html" if url.path == "/" else url.path[1:]
                    mime = {
                        "index.html": "text/html",
                        "app.js": "text/javascript",
                        "style.css": "text/css",
                        "data.js": "text/javascript",
                        "data.json": "application/json",
                    }[name]
                    self.respond((assets / name).read_bytes(), mime + "; charset=utf-8")
                elif url.path == "/api/health":
                    self.respond(explorer.health())
                elif url.path == "/api/replay":
                    if set(query) - {"method", "fraction", "draw", "reveal"}:
                        raise ValueError("Unknown replay argument")
                    reveal = query.get("reveal", ["0"])[0]
                    if reveal not in ["0", "1"]:
                        raise ValueError("Reveal must be0 or1")
                    self.respond(
                        explorer.replay(
                            query.get("method", ["power-score"])[0],
                            float(query.get("fraction", [".1"])[0]),
                            int(query.get("draw", ["0"])[0]),
                            reveal=reveal == "1",
                        )
                    )
                elif url.path == "/api/frame":
                    if set(query) != {"id"}:
                        raise ValueError("One frame id is required")
                    self.respond(explorer.frame(query["id"][0]), "image/jpeg")
                elif url.path == "/api/benchmark":
                    summary = json.loads((assets / "data.json").read_text())
                    self.respond(
                        dict(
                            prevalence=summary["main"]["truth"],
                            scope="Aggregate benchmark truth for evaluation, not an audit input",
                        )
                    )
                else:
                    self.respond(dict(error="Route not found"), status=404)
            except (ValueError, KeyError, IndexError) as exc:
                self.respond(dict(error=str(exc)), status=400)
            except FileNotFoundError as exc:
                self.respond(dict(error=str(exc)), status=503)
            except Exception as exc:
                self.respond(dict(error=f"Replay failed: {type(exc).__name__}: {exc}"), status=500)

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Research explorer ready: http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
