"""Fetch every Fastwork jobboard listing and print/save it. Standalone, no Discord."""
import csv
import json
import sys

import requests

API_URL = "https://jobboard-api.fastwork.co/api/jobs"
API_PARAMS = {
    "page_size": 50,
    "order_by[]": "inserted_at",
    "order_directions[]": "desc",
    "filters[0][field]": "kind",
    "filters[0][value]": "standard",
}


def fetch_all_jobs():
    """Page through the API until it runs out of pages."""
    jobs = []
    page = 1
    while True:
        resp = requests.get(
            API_URL, params={**API_PARAMS, "page": page},
            headers={"User-Agent": "Mozilla/5.0"}, timeout=15,
        )
        resp.raise_for_status()
        body = resp.json()
        batch = body["data"]
        if not batch:
            break
        jobs.extend(batch)
        print(f"page {page}/{body['meta']['total_pages']} ({len(jobs)} jobs so far)", file=sys.stderr)
        if page >= body["meta"]["total_pages"]:
            break
        page += 1
    return jobs


def save_csv(jobs, path="jobs.csv"):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id", "title", "budget", "type", "url"])
        for j in jobs:
            budget = j.get("budget") or "ไม่ระบุ"
            w.writerow([j["id"], j["title"], budget, j.get("type", ""),
                        f"https://jobboard.fastwork.co/jobs/{j['id']}"])


def save_json(jobs, path="jobs.json"):
    # full raw job objects (not just csv's 5 columns) — search endpoint
    # and frontend JobCard both need fields like inserted_at
    with open(path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False)


def main():
    jobs = fetch_all_jobs()
    save_csv(jobs)
    save_json(jobs)
    # console codepage (e.g. Windows cp874) can't encode every character
    # jobs might contain (emoji etc) — save the data first regardless,
    # then print best-effort
    sys.stdout.reconfigure(errors="replace")
    for j in jobs:
        budget = j.get("budget") or "ไม่ระบุ"
        print(f"{j['title']} | {budget} | https://jobboard.fastwork.co/jobs/{j['id']}")
    print(f"\n{len(jobs)} jobs total -> jobs.csv, jobs.json", file=sys.stderr)


if __name__ == "__main__":
    main()
