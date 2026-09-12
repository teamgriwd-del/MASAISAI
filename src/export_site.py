"""Build the MASAISAI console as a static site, for hosting on a plain web server.

    python src/export_site.py                 # -> dist/
    python src/export_site.py --out /srv/masaisai --base /

Streamlit is only ever the host here: the interface in src/ui/ is already a
self-contained HTML/CSS/JS application, and dashboard_data.py is a pure
function from the backend to a JSON payload. This script runs the backend once,
freezes the payload, and writes a directory you can rsync to a VPS.

Two things improve as a side effect of dropping the component frame:

* Real URLs. Inside Streamlit the console lives in an ``about:srcdoc`` iframe
  with an opaque origin, where ``history.pushState`` throws, so routes have to
  live in the fragment. Served as an ordinary page, app.js switches itself to
  real paths (``/live-sensing``) with working back/forward and deep links.
* No sandbox, no iframe, no Streamlit runtime on the wire.

The payload is inlined into index.html, so the site works from ``file://`` and
needs no fetch, no CORS and no API. ``data.json`` is written alongside it so the
data can be refreshed on its own if you ever want to.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from dashboard_data import build_payload, run_backend      # noqa: E402

UI_DIR = HERE / "ui"

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="MASAISAI -- AI-driven dynamic spectrum access for rural broadband. POTRAZ AI for Impact.">
<meta name="theme-color" content="#15110b">
<title>MASAISAI -- Spectrum Intelligence</title>
<link rel="icon" href="data:image/svg+xml,{FAVICON}">
<link rel="stylesheet" href="{BASE}styles.css?v={VERSION}">
</head>
<body>
<div id="app" class="app"></div>
<noscript><div style="padding:32px;color:#b6c3d6;font:15px system-ui,sans-serif">
  MASAISAI needs JavaScript to render the spectrum console.</div></noscript>
<script>window.MASAISAI_BASE = {BASE_JSON};</script>
<script>window.MASAISAI_DATA = {DATA};</script>
<script src="{BASE}app.js?v={VERSION}"></script>
</body>
</html>
"""

FAVICON = (
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' "
    "stroke='%23e3b04b' stroke-width='1.8' stroke-linecap='round'%3E"
    "%3Ccircle cx='12' cy='11' r='1.8'/%3E"
    "%3Cpath d='M7.6 6.6a6.2 6.2 0 0 0 0 8.8M16.4 15.4a6.2 6.2 0 0 0 0-8.8'/%3E"
    "%3Cpath d='M12 13v8.5'/%3E%3C/svg%3E"
)

NGINX = """# MASAISAI -- static console. Every route is served by index.html so that
# /live-sensing and friends survive a refresh and a direct link.
server {
    listen 80;
    server_name masaisai.example.com;          # <- your domain
    root /var/www/masaisai;                    # <- where you rsync dist/
    index index.html;

    # Single-page routes.
    location / {
        try_files $uri $uri/ /index.html;
    }

    # The payload and the shell change together on every deploy; the assets are
    # cache-busted by ?v= so they can be cached hard.
    location = /index.html { add_header Cache-Control "no-store"; }
    location = /data.json  { add_header Cache-Control "no-store"; }
    location ~* \\.(css|js|svg|woff2?)$ {
        add_header Cache-Control "public, max-age=31536000, immutable";
    }

    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;
    gzip_min_length 1024;
}
"""

CADDY = """# Caddyfile -- same site, if you prefer Caddy (HTTPS is automatic).
masaisai.example.com {
    root * /var/www/masaisai
    encode gzip
    try_files {path} {path}/ /index.html
    file_server
}
"""

README = """# Deploying the MASAISAI console

The console is a static site: HTML, CSS, one JavaScript file and a frozen JSON
payload. No Python, no Streamlit and no database on the server.

## Build

    python src/export_site.py                    # writes ./dist
    python src/export_site.py --base /masaisai/  # if serving from a subpath

`--base` only matters when the site is not at the domain root. It is written
into the page as `window.MASAISAI_BASE` and app.js builds its routes from it.

## Upload

    rsync -avz --delete dist/ user@your-vps:/var/www/masaisai/

Then point a server at that directory. `dist/nginx.conf.example` and
`dist/Caddyfile.example` are ready to copy; the only rule that matters is the
SPA fallback, because the routes are real paths:

    try_files $uri $uri/ /index.html;

Without it, `/live-sensing` returns 404 on refresh.

## Refreshing the data

The payload is a snapshot of one backend run, inlined into `index.html`. To
refresh it, rebuild and re-upload:

    python src/export_site.py && rsync -avz --delete dist/ user@vps:/var/www/masaisai/

A cron entry on the VPS can do this if the repo is checked out there.

## What the site is, honestly

Sensing data is simulated -- the console says so in the footer, the sidebar and
on every page header. The ML layer is advisory throughout; POTRAZ rules decide.
Operator actions (revoking a grant) change the state in the browser session and
are written to the on-screen audit log; they do not write back to a server,
because there is no server. That is the correct behaviour for a demonstration
build and it is labelled as such.

## Streamlit

`src/dashboard_app.py` still works and is unchanged in behaviour -- useful for
local development, where it rebuilds the payload on every rerun. The same
`app.js` runs in both hosts and detects which one it is in.
"""


def build(out_dir: Path, base: str) -> None:
    t0 = datetime.now(timezone.utc)
    print("MASAISAI static export")
    print("  running backend ...", flush=True)
    payload = build_payload(run_backend())
    version = t0.strftime("%Y%m%d%H%M")
    payload.setdefault("meta", {})["built_at"] = t0.isoformat(timespec="seconds")

    out_dir.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")

    page = (PAGE.replace("{DATA}", data)
                .replace("{BASE_JSON}", json.dumps(base))
                .replace("{BASE}", base)
                .replace("{VERSION}", version)
                .replace("{FAVICON}", FAVICON))

    (out_dir / "index.html").write_text(page, encoding="utf-8")
    # Static hosts that use 404.html as the SPA fallback (GitHub Pages, some
    # object stores) get the same document.
    (out_dir / "404.html").write_text(page, encoding="utf-8")
    (out_dir / "data.json").write_text(json.dumps(payload, indent=1), encoding="utf-8")
    shutil.copyfile(UI_DIR / "styles.css", out_dir / "styles.css")
    shutil.copyfile(UI_DIR / "app.js", out_dir / "app.js")
    (out_dir / "nginx.conf.example").write_text(NGINX, encoding="utf-8")
    (out_dir / "Caddyfile.example").write_text(CADDY, encoding="utf-8")
    (out_dir / "README.md").write_text(README, encoding="utf-8")
    (out_dir / "robots.txt").write_text("User-agent: *\nDisallow:\n", encoding="utf-8")

    total = 0
    print("  wrote %s" % out_dir)
    for f in sorted(out_dir.iterdir()):
        if f.is_file():
            total += f.stat().st_size
            print("    %-22s %8.1f KB" % (f.name, f.stat().st_size / 1024))
    print("  %d channels, %d nodes, %d decisions, %d audit events"
          % (len(payload["channels"]), len(payload["nodes"]),
             len(payload["decisions"]), len(payload["audit"])))
    print("  total %.1f KB, base %r, built in %.1fs"
          % (total / 1024, base, (datetime.now(timezone.utc) - t0).total_seconds()))


def main() -> None:
    ap = argparse.ArgumentParser(description="Build the MASAISAI console as a static site.")
    ap.add_argument("--out", default=str(HERE.parent / "dist"), help="output directory")
    ap.add_argument("--base", default="/", help="URL path the site is served from")
    args = ap.parse_args()
    base = args.base if args.base.endswith("/") else args.base + "/"
    build(Path(args.out), base)


if __name__ == "__main__":
    main()
