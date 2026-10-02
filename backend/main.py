"""Local bridge: web UI's Accept button -> automate_apply.run_apply().

Run alongside `npm run dev`:
    python main.py

The React app POSTs to http://localhost:8787/apply and this drives a real
(visible) browser window via Playwright, dry-run only — nothing gets sent,
the window is left open for you to check and submit by hand.
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from automate_apply import (
    run_apply, list_offers, delete_offer, kill_stale_chrome,
    is_logged_in, open_login_window, logout, PROFILE_DIR, APPLY_PROFILE_DIR,
)
from github_ai_jobs import get_ai_job_ids

PORT = 8787
ALLOWED_ORIGIN = "http://localhost:5180"
JOBS_JSON = Path(__file__).parent / "jobs.json"
SEARCH_RESULT_LIMIT = 50


def search_jobs(query):
    """Title substring search over the last list_jobs.py scrape (jobs.json).
    Only as fresh as that last run — not live."""
    if not JOBS_JSON.exists():
        return {"jobs": [], "error": "jobs.json not found — run list_jobs.py first"}
    with open(JOBS_JSON, encoding="utf-8") as f:
        jobs = json.load(f)
    q = query.strip().lower()
    if not q:
        return {"jobs": []}
    matches = [j for j in jobs if q in j.get("title", "").lower()]
    return {"jobs": matches[:SEARCH_RESULT_LIMIT], "total": len(matches)}


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, status, payload):
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/search":
            q = parse_qs(parsed.query).get("q", [""])[0]
            self._json(200, search_jobs(q))
            return
        if parsed.path == "/ai-jobs":
            self._json(200, {"ids": sorted(get_ai_job_ids())})
            return
        if parsed.path == "/login-status":
            try:
                self._json(200, {"fastwork": is_logged_in()})
            except Exception as e:
                self._json(500, {"error": str(e)})
            return
        if parsed.path != "/offers":
            self._json(404, {"error": "not found"})
            return
        try:
            self._json(200, list_offers())
        except Exception as e:
            self._json(500, {"error": str(e)})

    def do_DELETE(self):
        # expects /offers/<index>, index from list_offers()'s "index" field
        prefix = "/offers/"
        if not self.path.startswith(prefix):
            self._json(404, {"error": "not found"})
            return
        try:
            index = int(self.path[len(prefix):])
        except ValueError:
            self._json(400, {"error": "bad index"})
            return
        try:
            self._json(200, delete_offer(index))
        except Exception as e:
            self._json(500, {"error": str(e)})

    def do_POST(self):
        if self.path == "/login/fastwork":
            # background thread — same reasoning as /apply below, the
            # browser window stays open after open_login_window() returns
            threading.Thread(target=open_login_window, daemon=True).start()
            self._json(202, {"status": "started"})
            return

        if self.path == "/logout/fastwork":
            try:
                logout()
                self._json(200, {"ok": True})
            except Exception as e:
                self._json(500, {"error": str(e)})
            return

        if self.path != "/apply":
            self._json(404, {"error": "not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        job_url = body.get("job")
        price = body.get("price")
        days = body.get("days") or None
        script = body.get("script") or None

        if not job_url or not price or not days:
            self._json(400, {"error": "job, price and days required"})
            return

        # run in a background thread so this doesn't block the response —
        # the browser window stays open after run_apply() returns
        def worker():
            try:
                kwargs = {"job_url": job_url, "price": price, "days": days}
                if script:
                    kwargs["script_text"] = script
                run_apply(**kwargs)
            except Exception as e:
                print(f"apply failed: {e}")

        threading.Thread(target=worker, daemon=True).start()
        self._json(202, {"status": "started"})

    def log_message(self, fmt, *args):
        print(fmt % args)


if __name__ == "__main__":
    kill_stale_chrome(APPLY_PROFILE_DIR)
    kill_stale_chrome(PROFILE_DIR)
    print(f"main.py listening on http://localhost:{PORT}")
    try:
        ThreadingHTTPServer(("localhost", PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")
