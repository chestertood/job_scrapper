# Job Lister

Fastwork jobboard viewer + auto-apply helper. React frontend, Python backend (browser automation via Playwright).

## What you need

- Node.js 18+
- Python 3.10+
- Google Chrome installed

## Setup

### 1. Install dependencies

```bash
cd frontend && npm install
cd ../backend && pip install -r requirements.txt
playwright install chromium
```

### 2. (Optional) AI job matching

The "AI job" filter pulls a daily job selection from a **private** GitHub repo the original author owns. It only works if you have your own `GITHUB_TOKEN` with read access to that repo (or your own equivalent repo/file laid out the same way). Skip this step if you don't need that filter — everything else works without it.

```bash
cp .env.example .env
# edit .env, paste your GITHUB_TOKEN
```

### 3. Run (3 terminals)

**Terminal 1 — frontend**
```bash
cd frontend
npm run dev
```
Opens at http://localhost:5173

**Terminal 2 — apply/login server**
```bash
cd backend
python main.py
```
Runs on port 8787. Backs the Accept/Apply button and login.

**Terminal 3 — job data (run once, re-run to refresh)**
```bash
cd backend
python list_jobs.py
```
Fetches all Fastwork listings into `jobs.json`/`jobs.csv`. The search box in the app reads from this file, so re-run it whenever you want fresher search results.

### 4. Log in

Open http://localhost:5173, click **Login**. A real Chrome window opens — log into your Fastwork account there, once. The session is saved to `backend/chrome_profile/` on your machine only (gitignored, never pushed, never shared between users). Each person who runs this logs in with their own account.

## Notes

- `main.py`'s Apply flow is dry-run by default: it opens the offer form and fills it in, but leaves the browser window open for you to review and send by hand.
- `.env` holds a secret token — never commit it. `.gitignore` already excludes it; just don't force-add it.
