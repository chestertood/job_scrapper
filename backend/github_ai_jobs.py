"""Fetch the bot's AI-job selections (select_jobs/DD-MM-YY.json, every file in
the dir — not just today's) from the private discord_bot_scrape GitHub repo.
Auth pattern lifted from test_fetch_github_jobs.py — GITHUB_TOKEN read from
job-lister/.env.
"""
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

BANGKOK_TZ = timezone(timedelta(hours=7))
OWNER = "ohmrawit"
REPO = "discord_bot_scrape"
BRANCH = "master"
ENV_PATH = Path(__file__).parent.parent / ".env"


def _load_github_token():
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    if not ENV_PATH.exists():
        return None
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("GITHUB_TOKEN") and "=" in line:
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


# in-memory cache: one GitHub call per day, not per request
_cache = {"date": None, "ids": set()}


def get_ai_job_ids():
    """Set of Fastwork job ids the bot ever selected as AI-relevant — union
    across every select_jobs/*.json file, newest and oldest alike (the
    frontend's own newest-first ordering handles latest-to-oldest display).
    Empty set (not an error) if the token/dir/network isn't available —
    callers just show no AI matches rather than failing the whole page."""
    today = datetime.now(BANGKOK_TZ).strftime("%d-%m-%y")
    if _cache["date"] == today:
        return _cache["ids"]

    token = _load_github_token()
    if not token:
        return set()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.raw+json",
    }
    try:
        list_url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/select_jobs?ref={BRANCH}"
        files = requests.get(list_url, headers=headers, timeout=15)
        files.raise_for_status()
        ids = set()
        for entry in files.json():
            name = entry.get("name", "")
            if not name.endswith(".json"):
                continue
            file_url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/select_jobs/{name}?ref={BRANCH}"
            resp = requests.get(file_url, headers=headers, timeout=15)
            resp.raise_for_status()
            ids.update(j["id"] for j in resp.json() if j.get("id"))
    except (requests.RequestException, ValueError, KeyError):
        ids = set()

    _cache["date"] = today
    _cache["ids"] = ids
    return ids
