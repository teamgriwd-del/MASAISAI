"""Serve dist/ locally the way a VPS would, including the SPA fallback.

    python src/serve_dist.py [--port 8600] [--dir dist]

This is a development convenience only -- on the server nginx or Caddy does the
same job. The one rule that matters is the fallback: unknown paths return
index.html so /live-sensing survives a refresh and a pasted link.
"""

from __future__ import annotations

import argparse
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class SpaHandler(SimpleHTTPRequestHandler):
    """Static files, with unknown paths falling back to index.html."""

    def do_GET(self):                                     # noqa: N802
        path = self.translate_path(self.path)
        if not os.path.exists(path) and "." not in Path(self.path).name:
            self.path = "/index.html"
        return super().do_GET()

    def end_headers(self):
        if self.path in ("/index.html", "/data.json", "/"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        print("  %s" % (fmt % args))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8600)
    ap.add_argument("--dir", default=str(Path(__file__).resolve().parent.parent / "dist"))
    args = ap.parse_args()
    root = Path(args.dir).resolve()
    if not (root / "index.html").exists():
        raise SystemExit("No index.html in %s -- run src/export_site.py first." % root)
    handler = partial(SpaHandler, directory=str(root))
    print("MASAISAI static site on http://localhost:%d  (serving %s)" % (args.port, root))
    ThreadingHTTPServer(("0.0.0.0", args.port), handler).serve_forever()


if __name__ == "__main__":
    main()
