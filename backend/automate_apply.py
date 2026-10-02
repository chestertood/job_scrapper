"""Test script: open a Fastwork job's offer form and fill it in with Playwright.

Flow: open job link -> go to /offer -> fill script text + price -> (dry-run by default,
pass --submit to actually click send).

Setup:
    pip install playwright
    playwright install chromium

First run opens a real browser window using a saved profile folder (chrome_profile/),
so log into Fastwork manually once there — the session persists for later runs.

Usage:
    python automate_apply.py <job_id_or_url> --price 1000 --days 3
    python automate_apply.py <job_id_or_url> --price 1000 --submit   # actually sends
"""
import argparse
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

ASSETS_DIR = Path(__file__).parent.parent / "frontend" / "src" / "assets"

SCRIPT_TEXT = "สนใจงานครับ จบวิศวะมา มีพื้นฐานด้าน AI/ML, Data Science, NLP, และเขียนโค้ด backend มาพอสมควรครับ เคยทำงานด้าน automated system มาก่อน  เลยคุ้นกับการเชื่อมต่อระบบ, API และเขียนสคริปต์ให้ทำงานอัตโนมัติ ผลงาน: https://github.com/chestertood ขอบคุณครับ 🙏"

PROFILE_DIR = "chrome_profile"  # keeps your login between runs
OFFERS_URL = "https://jobboard.fastwork.co/me/offers"

# run_apply()'s review window is left open indefinitely (by design, for
# manual review before sending) — if it shared PROFILE_DIR, that held lock
# would block every list_offers()/delete_offer() call for as long as the
# window stays open. Separate dir so the two never contend.
APPLY_PROFILE_DIR = "chrome_profile_apply"

BANGKOK_TZ = timezone(timedelta(hours=7))  # API returns UTC, site displays Thai local time


def kill_stale_chrome(profile_dir):
    """Startup cleanup: run_apply()'s review window and open_login_window()'s
    manual-login window are both meant to outlive one call, but if the
    *server* process gets restarted while one is still open, the new
    process's session global starts at None and has no way to know the old
    Chrome is still alive — it's still holding that profile's lock, so every
    launch on it fails with "context has been closed" until the orphan is
    killed. Best-effort, Windows-only (matches this project's target platform)."""
    profile_path = str((Path(__file__).parent / profile_dir).resolve())
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" "
             f"| Where-Object {{ $_.CommandLine -like '*{profile_path}*' }} "
             "| ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"],
            capture_output=True, timeout=10,
        )
    except Exception:
        pass  # not fatal — a stale lock just surfaces as the usual apply-failed error later


PORTFOLIO_FILES = [
    ASSETS_DIR / "pic1.png",
    ASSETS_DIR / "pic2.png",
    ASSETS_DIR / "pic3.png",
    ASSETS_DIR / "pic4.jpg",
]


def fill_offer_form(page, price, days, script_text):
    # Locate fields relative to their Thai heading text — real page has no
    # stable id/class on these, so we walk from the label to the nearest input.
    textarea = page.locator(
        "xpath=//*[contains(text(),'ข้อมูลที่ทำให้ลูกค้าต้องตัดสินใจจ้างคุณ')]"
        "/following::textarea[1]"
    )
    price_input = page.locator("input[name='budget']")
    days_input = page.locator(
        "xpath=//*[contains(text(),'ระยะเวลาทำงาน')]/following::input[1]"
    )

    textarea.fill(script_text)
    price_input.fill(str(price))
    if days:
        days_input.fill(str(days))

    # native <select>: pick whichever <option> mentions "AI"
    select = page.locator(
        "xpath=//*[contains(text(),'เลือกงานของคุณที่เกี่ยวข้อง')]/following::select[1]"
    )
    ai_option = select.locator("option", has_text="AI").first
    select.select_option(value=ai_option.get_attribute("value"))

    # upload portfolio images via the hidden file input
    page.locator("input[type='file']").first.set_input_files(PORTFOLIO_FILES)


# Playwright's sync API is bound to whatever OS thread created it — handing
# a context to a different thread blows up with "greenlet.error: cannot
# switch to a different thread". main.py is a ThreadingHTTPServer
# (one new thread per request), so any browser session meant to survive
# across requests (the apply-review window, the manual-login window) has to
# have every one of its calls, from every request, funneled through the
# *same* dedicated thread — that's what these single-worker executors do.
#
# _profile_executor also serializes every *other* PROFILE_DIR call
# (list_offers/delete_offer/logout/is_logged_in's one-off fallback) even
# though those don't share state — two concurrent launch_persistent_context()
# calls on the same profile dir (e.g. the frontend's /offers and
# /login-status firing together on mount) race for Chrome's profile lock
# just like the reused-session case does, and it's not always a clean crash:
# one call can silently get back an empty/wrong cookie jar instead of an
# exception. Routing everything through one worker thread means these calls
# queue instead of racing.
_apply_executor = ThreadPoolExecutor(max_workers=1)
_profile_executor = ThreadPoolExecutor(max_workers=1)

# kept alive so the launched browser window doesn't get closed when
# run_apply() returns and its local playwright/context vars go out of scope.
# Reused across calls (one tab per apply) instead of relaunching — a second
# launch_persistent_context() on the same APPLY_PROFILE_DIR while the first
# window is still open hits Chrome's profile-dir singleton lock and dies.
_apply_session = None  # (playwright, context) | None


def _apply_page():
    global _apply_session
    if _apply_session is not None:
        try:
            return _apply_session[1].new_page()
        except Exception:
            # window was closed by hand — relaunch below. Must stop the old
            # driver too, not just drop the reference, or it leaks and wedges
            # every future job on _apply_executor's one dedicated thread.
            p, _ = _apply_session
            _apply_session = None
            p.stop()
    p = sync_playwright().start()
    try:
        ctx = p.chromium.launch_persistent_context(APPLY_PROFILE_DIR, headless=False)
    except Exception:
        # if we don't stop it here, this leaked driver wedges every future
        # job on _apply_executor's one dedicated thread, not just this call
        p.stop()
        raise
    _apply_session = (p, ctx)
    return ctx.new_page()


def _login_check(page):
    if page.get_by_text(re.compile("เข้าสู่ระบบ|ล็อกอิน|log ?in", re.I)).count():
        raise RuntimeError("ยังไม่ได้ login fastwork — เปิด chrome_profile browser แล้ว login มือก่อน")


# kept alive the same way _apply_session is — a manual-login window a user
# is actively typing into shouldn't get relaunched out from under them.
_login_session = None  # (playwright, context) | None


def _is_logged_in(profile_dir):
    """accessToken cookie present in the profile? Must run on _profile_executor's
    thread — reads _login_session directly, no thread-hop of its own."""
    global _login_session
    if _login_session is not None:
        try:
            ctx = _login_session[1]
            logged_in = any(c["name"] == "accessToken" for c in ctx.cookies())
        except Exception:
            # window's dead (e.g. user closed it by hand) — stop the driver
            # too, not just drop the reference, or it leaks the same way
            p, _ = _login_session
            _login_session = None
            p.stop()
        else:
            if logged_in:
                # done with the manual-login window — close it so it doesn't
                # keep holding PROFILE_DIR's lock for headless calls after
                # this. try/finally: if ctx.close() throws (e.g. the user
                # already closed the window by hand), p.stop() must still
                # run or the leaked driver wedges every future job on this
                # executor thread — the exact bug that bit open_login_window().
                p, ctx = _login_session
                _login_session = None
                try:
                    ctx.close()
                finally:
                    p.stop()
            return logged_in

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(profile_dir, headless=True)
        try:
            return any(c["name"] == "accessToken" for c in ctx.cookies())
        finally:
            ctx.close()


def is_logged_in(profile_dir=PROFILE_DIR):
    return _profile_executor.submit(_is_logged_in, profile_dir).result()


def logout(profile_dir=PROFILE_DIR):
    return _profile_executor.submit(_logout, profile_dir).result()


def _logout(profile_dir):
    """Clear the profile's cookies so is_logged_in() goes back to False.
    Must run on _profile_executor's thread — see the executor comment above."""
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(profile_dir, headless=True)
        try:
            ctx.clear_cookies()
        finally:
            ctx.close()


def _open_login_window():
    """Open PROFILE_DIR non-headless on the offers page so the user can log
    into Fastwork by hand (same SPA shows its own login prompt there when
    unauthenticated) — left open for _is_logged_in() to notice and close.
    Must run on _profile_executor's thread — writes _login_session directly."""
    global _login_session
    if _login_session is not None:
        try:
            _login_session[1].new_page().goto(OFFERS_URL, wait_until="domcontentloaded")
            return
        except Exception:
            # same leak risk as _apply_page()'s equivalent branch — must
            # stop the old driver, not just drop the reference
            p, _ = _login_session
            _login_session = None
            p.stop()
    p = sync_playwright().start()
    try:
        ctx = p.chromium.launch_persistent_context(PROFILE_DIR, headless=False)
    except Exception:
        # if we don't stop it here, this leaked driver wedges every future
        # job on _profile_executor's one dedicated thread, not just this call
        p.stop()
        raise
    _login_session = (p, ctx)
    ctx.new_page().goto(OFFERS_URL, wait_until="domcontentloaded")


def open_login_window():
    _profile_executor.submit(_open_login_window).result()


def _run_apply(job_url, price, days, script_text, submit):
    """Must run on _apply_executor's thread — reads/writes _apply_session directly."""
    page = _apply_page()

    page.goto(job_url, wait_until="domcontentloaded")
    _login_check(page)

    page.get_by_text("นำเสนองาน").first.click()
    page.wait_for_timeout(3000)  # let the SPA finish rendering the form

    fill_offer_form(page, price, days, script_text)

    page.screenshot(path="debug_offer.png", full_page=True)
    return {"ok": True, "url": page.url, "price": price, "days": days}


def run_apply(job_url, price, days, script_text=SCRIPT_TEXT, submit=False):
    """Open the job's offer form and fill it in. Leaves the browser window
    open for a human to review (and click send) — never submits itself,
    the --submit/submit flag is reserved for later, not wired up yet.
    Returns a status dict; raises RuntimeError if login is required.
    """
    return _apply_executor.submit(_run_apply, job_url, price, days, script_text, submit).result()


# JSON endpoints the offers page itself calls to render that table (found
# by sniffing network traffic while the page loaded — see PR notes). Read
# these straight instead of scraping the rendered table + popup-clicking
# every row just to recover its url; no page/tab needed, just the
# persistent context's cookies.
OFFERS_API = "https://jobboard-api.fastwork.co/api/me/job-freelance-offers"
ME_API = "https://jobboard-api.fastwork.co/api/me"


def _thb(value):
    """Format a numeric-string budget/price like the site does ("15000" ->
    "15,000"); missing/zero means the job listed no budget."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return "ไม่ระบุ"
    return f"{n:,}" if n else "ไม่ระบุ"


def _auth_headers(ctx):
    # jobboard-api.fastwork.co is a different origin from jobboard.fastwork.co,
    # so it isn't cookie-authenticated — the site's own JS reads this
    # (non-httpOnly) cookie and attaches it as a bearer token by hand, so we
    # do the same instead of leaving it to ctx.request's automatic cookie jar.
    token = next((c["value"] for c in ctx.cookies() if c["name"] == "accessToken"), None)
    if not token:
        raise RuntimeError("ยังไม่ได้ login fastwork — เปิด chrome_profile browser แล้ว login มือก่อน")
    return {"Authorization": f"Bearer {token}"}


def list_offers():
    return _profile_executor.submit(_list_offers).result()


def _list_offers():
    """Submitted-offer rows (title/status/budget/offered price/days/posted
    date, whether it's still deletable) plus the remaining monthly offer
    quota — read straight from OFFERS_API/ME_API, no browser rendering.
    Must run on _profile_executor's thread — see the executor comment above."""
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(PROFILE_DIR, headless=True)
        try:
            headers = _auth_headers(ctx)
            resp = ctx.request.get(
                OFFERS_API,
                params={"page": 1, "page_size": 50,
                        "order_by[]": "updated_at", "order_directions[]": "desc"},
                headers=headers,
            )
            if resp.status in (401, 403):
                raise RuntimeError("ยังไม่ได้ login fastwork — เปิด chrome_profile browser แล้ว login มือก่อน")
            resp_data = resp.json()

            remaining = None
            quota = ctx.request.get(ME_API, headers=headers).json().get("freelance_offers_quota")
            if quota:
                remaining = quota.get("max_freelance_offers_count", 0) - quota.get("current_freelance_offers_count", 0)

            offers = []
            for i, it in enumerate(resp_data.get("data", [])):
                job = it["job"]
                posted = datetime.fromisoformat(it["inserted_at"].replace("Z", "+00:00")).astimezone(BANGKOK_TZ)
                offers.append({
                    "index": i,
                    "title": job["title"],
                    "url": f"https://jobboard.fastwork.co/jobs/{job['id']}",  # bare id redirects to the canonical slug url fine
                    "status": "เปิดรับ" if job["status"] == "open" else "หมดอายุ",
                    "budget": _thb(job.get("budget")),
                    "price": _thb(it.get("budget")),
                    "days": f"{it['working_days']} วัน",
                    "posted": posted.strftime("%d/%m/%Y %H:%M"),
                    "can_delete": job["status"] == "open",
                })
            return {"offers": offers, "remaining": remaining}
        finally:
            ctx.close()


def delete_offer(index):
    return _profile_executor.submit(_delete_offer, index).result()


def _delete_offer(index):
    """Delete the offer at `index` (as returned by list_offers) via the same
    confirm-modal flow as the site's own ลบ button. Must run on
    _profile_executor's thread — see the executor comment above."""
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(PROFILE_DIR, headless=True)
        page = ctx.new_page()
        try:
            page.goto(OFFERS_URL, wait_until="domcontentloaded")
            _login_check(page)
            page.get_by_text("งานที่คุณนำเสนอ").first.click()
            page.wait_for_timeout(1500)

            row = page.locator("table tbody tr").nth(index)
            delete_btn = row.get_by_text("ลบ", exact=True)
            if delete_btn.count() == 0:
                raise RuntimeError("ข้อเสนอนี้ลบไม่ได้ (งานหมดอายุไปแล้ว)")
            delete_btn.first.click()

            # confirm button's "ลบ" text sits in a nested <span>, not a
            # direct text-node child of <button> — text() only sees direct
            # children so it never matched; normalize-space(.) checks all
            # descendant text instead
            confirm_btn = page.locator(
                "xpath=//*[contains(text(),'ยืนยันลบข้อเสนอในการทำงาน')]"
                "/following::button[normalize-space(.)='ลบ'][1]"
            )
            confirm_btn.first.click()
            page.wait_for_timeout(1000)
            return {"ok": True}
        finally:
            ctx.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("job", help="job id or full job URL")
    ap.add_argument("--price", required=True, type=int)
    ap.add_argument("--days", type=int, default=None)
    ap.add_argument("--submit", action="store_true", help="actually click send (default: dry-run)")
    args = ap.parse_args()

    job_url = args.job  # use the link as given, it already has the slug + id
    print(f"-> {job_url}")
    result = run_apply(job_url, args.price, args.days, submit=args.submit)
    print(f"   landed on: {result['url']}")
    print(f"   filled budget = {args.price}, days = {args.days}, script text")
    print("   saved screenshot -> debug_offer.png")
    input("หยุดตรงนี้ — ดูหน้าจอ/screenshot แล้วกด Enter เพื่อปิด...")

    def _close():
        p, ctx = _apply_session
        ctx.close()
        p.stop()

    _apply_executor.submit(_close).result()


if __name__ == "__main__":
    main()
