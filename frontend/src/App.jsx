import { useEffect, useState, useCallback, useRef } from "react";
import "./App.css";
import {
  fetchJobsPage,
  fetchOffers,
  deleteOffer,
  searchJobs,
  fetchAiJobIds,
  loginStatus,
  logout,
} from "./api";
import {
  FILTERS,
  SCRIPT_KEY,
  jobDate,
  sameUtcDate,
  loadRemoved,
  REMOVED_KEY,
} from "./utils";
import JobListTab from "./components/JobListTab";
import ProfileTab from "./components/ProfileTab";
import LoginPage from "./components/LoginPage";

export default function App() {
  // null = still checking on first load, true/false once we know
  const [fastworkLoggedIn, setFastworkLoggedIn] = useState(null);

  const checkLogin = useCallback(() => {
    loginStatus()
      .then(({ fastwork }) => setFastworkLoggedIn(fastwork))
      .catch(() => setFastworkLoggedIn(false));
  }, []);

  // StrictMode double-invokes mount effects in dev, which would otherwise
  // fire two concurrent is_logged_in() calls against the same Playwright
  // profile dir on the backend — same race loadOffers() below guards
  // against. Guard so it only fires once.
  const loginCheckRequested = useRef(false);
  useEffect(() => {
    if (loginCheckRequested.current) return;
    loginCheckRequested.current = true;
    checkLogin();
  }, [checkLogin]);

  const doLogout = () => {
    if (!confirm("ออกจากระบบ Fastwork?")) return;
    logout("fastwork").finally(() => setFastworkLoggedIn(false));
  };

  const [tab, setTab] = useState("job");
  const [pageJobs, setPageJobs] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filter, setFilter] = useState("all");
  // job ids the bot picked as AI-relevant today (github_ai_jobs.py on the
  // backend) — fetched once, not per filter-switch
  const [aiJobIds, setAiJobIds] = useState(new Set());
  useEffect(() => {
    fetchAiJobIds().then(setAiJobIds).catch(() => {});
  }, []);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [removedIds, setRemovedIds] = useState(loadRemoved);

  const removeJob = (id) => {
    setRemovedIds((prev) => {
      const next = new Set(prev);
      next.add(id);
      try {
        localStorage.setItem(REMOVED_KEY, JSON.stringify([...next]));
      } catch {
        /* storage unavailable, ignore */
      }
      return next;
    });
  };
  const [script, setScript] = useState(() => {
    try {
      return localStorage.getItem(SCRIPT_KEY) || "";
    } catch {
      return "";
    }
  });

  const saveScript = (value) => {
    setScript(value);
    try {
      localStorage.setItem(SCRIPT_KEY, value);
    } catch {
      /* storage unavailable, ignore */
    }
  };

  // free-text search hits jobs.json (last list_jobs.py scrape) via the
  // backend, not the live paginated API — see api.js searchJobs
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => clearTimeout(t);
  }, [search]);

  // API page size — matches api.js's API_PARAMS.page_size
  const PAGE_SIZE = 50;

  // in-memory cache, keyed by page number — lives only for this tab's
  // session (cleared on refresh, never stale beyond that). Both "all"
  // pagination and the today/yesterday walk below share it, so once a page
  // has been fetched once (by either), switching filters/pages again never
  // re-fetches it — only genuinely new pages hit the network.
  const pageCache = useRef(new Map());
  const cachedFetchPage = async (pg) => {
    if (pageCache.current.has(pg)) return pageCache.current.get(pg);
    const result = await fetchJobsPage(pg);
    pageCache.current.set(pg, result);
    return result;
  };

  // today/yesterday: the API has no date filter (probed — 400s on any extra
  // filters[] param), and on a busy day a single 50-job page can be entirely
  // "today", pushing "yesterday" off page 1 completely — the old "today/
  // yesterday land on page 1" assumption doesn't hold. So instead of only
  // ever filtering whatever page the "all" pager happens to be on, walk
  // subsequent pages (newest-first, via the shared cache above) until a
  // page's oldest job is already past the target day.
  const fetchJobsForDate = async (daysAgo, page) => {
    const target = new Date();
    target.setUTCDate(target.getUTCDate() - daysAgo);
    const MAX_PAGES = 20; // safety net against a near-empty/misdated feed
    let matches = [];
    for (let pg = 1; pg <= MAX_PAGES; pg++) {
      const { jobs, totalPages: tp } = await cachedFetchPage(pg);
      if (jobs.length === 0) break;
      matches.push(...jobs.filter((j) => sameUtcDate(jobDate(j), target)));
      const oldest = jobDate(jobs[jobs.length - 1]);
      if (oldest < target && !sameUtcDate(oldest, target)) break;
      if (pg >= tp) break;
    }
    const totalPages = Math.max(1, Math.ceil(matches.length / PAGE_SIZE));
    const slice = matches.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
    return { jobs: slice, totalPages };
  };

  // AI job: like fetchJobsForDate above, matches can land on any Fastwork
  // page — walk pages collecting them all instead of only whatever the
  // currently-loaded page happens to contain, so 4-on-page-1 + 3-on-page-2
  // shows as one list of 7, not split across Prev/Next.
  const fetchAiJobs = async (aiIds, page) => {
    const MAX_PAGES = 20; // safety net, same as fetchJobsForDate
    let matches = [];
    for (let pg = 1; pg <= MAX_PAGES && matches.length < aiIds.size; pg++) {
      const { jobs, totalPages: tp } = await cachedFetchPage(pg);
      if (jobs.length === 0) break;
      matches.push(...jobs.filter((j) => aiIds.has(j.id)));
      if (pg >= tp) break;
    }
    const totalPages = Math.max(1, Math.ceil(matches.length / PAGE_SIZE));
    const slice = matches.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
    return { jobs: slice, totalPages };
  };

  const loadJobs = useCallback((p, q, f, aiIds) => {
    setLoading(true);
    setError(null);
    const daysAgo = FILTERS[f];
    const req = q
      ? searchJobs(q).then(({ jobs, error }) => {
          if (error) throw new Error(error);
          return { jobs, totalPages: 1 };
        })
      : f === "AI_job"
        ? fetchAiJobs(aiIds, p)
        : daysAgo == null
          ? cachedFetchPage(p)
          : fetchJobsForDate(daysAgo, p);
    req
      .then(({ jobs, totalPages: tp }) => {
        setPageJobs(jobs);
        setTotalPages(tp);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(
    () => loadJobs(page, debouncedSearch, filter, aiJobIds),
    [loadJobs, page, debouncedSearch, filter, aiJobIds],
  );

  // warm the shared page cache for today/yesterday alongside the initial
  // "all" load, so switching the filter later hits cache instead of making
  // the user wait through the page-walk then — same data, just fetched
  // ahead of time instead of on click. Silent: no loading/error state of
  // its own, whatever it fills in just makes the later real fetch faster.
  const prefetchRequested = useRef(false);
  useEffect(() => {
    if (!fastworkLoggedIn || prefetchRequested.current) return;
    prefetchRequested.current = true;
    fetchJobsForDate(0, 1).catch(() => {});
    fetchJobsForDate(1, 1).catch(() => {});
  }, [fastworkLoggedIn]);

  // filter switch starts back at page 1 of the (unfiltered) API pages
  const changeFilter = (f) => {
    setFilter(f);
    setPage(1);
  };

  // offers state lives here (not in ProfileTab) so it loads once and
  // survives switching away from the Profile tab and back
  const [offersData, setOffersData] = useState(null);
  const [offersError, setOffersError] = useState(null);
  const [offersBusy, setOffersBusy] = useState(null);

  const loadOffers = useCallback(() => {
    setOffersError(null);
    // return the promise: removeOffer waits on this to keep the spinner up
    // until the refreshed list actually lands, not just until delete finishes
    return fetchOffers()
      .then(setOffersData)
      .catch(() =>
        setOffersError("เชื่อมต่อ main.py ไม่ได้ — รันมันอยู่ไหม?"),
      );
  }, []);

  // StrictMode double-invokes mount effects in dev, which would otherwise
  // fire two concurrent list_offers() calls against the same Playwright
  // profile dir on the backend — the second one loses the profile lock
  // race and hangs for ~30s before failing. Guard so it only fires once.
  const offersRequested = useRef(false);
  useEffect(() => {
    if (offersRequested.current) return;
    offersRequested.current = true;
    loadOffers();
  }, [loadOffers]);

  const removeOffer = (index) => {
    setOffersBusy(index);
    deleteOffer(index)
      .then((res) =>
        res.ok ? loadOffers() : setOffersError(res.error || "ลบไม่สำเร็จ"),
      )
      .catch(() => setOffersError("เชื่อมต่อ main.py ไม่ได้"))
      .finally(() => setOffersBusy(null));
  };

  // pageJobs is already date-matched by fetchJobsForDate() above when a
  // date filter is active (and by loadJobs' search branch it isn't, so this
  // re-applies the same check there) — cheap and correct either way, no
  // need to branch on which path populated pageJobs
  const daysAgo = FILTERS[filter];
  const jobs = (
    daysAgo == null // null ("all"/"AI_job") or undefined (unmapped) both mean no date filter
      ? pageJobs
      : pageJobs.filter((j) => {
          const target = new Date();
          target.setUTCDate(target.getUTCDate() - daysAgo);
          return sameUtcDate(jobDate(j), target);
        })
  )
    .filter((j) => !removedIds.has(j.id))
    .filter((j) => filter !== "AI_job" || aiJobIds.has(j.id));

  if (fastworkLoggedIn === null) {
    return <div className="app-loading">กำลังเช็ค login...</div>;
  }
  if (!fastworkLoggedIn) {
    return <LoginPage onRecheck={checkLogin} />;
  }

  return (
    <div className="app">
      <header className="appbar">
        <button className="appbar-logo" onClick={() => setTab("job")}>
          Job Scraper
        </button>
        <input
          type="search"
          className="appbar-search"
          placeholder="ค้นหางาน..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <div className="appbar-right">
          <button
            className={`appbar-profile${tab === "profile" ? " appbar-profile-active" : ""}`}
            title="Profile"
            onClick={() => setTab("profile")}
          >
            👤
          </button>
          <button className="appbar-logout" title="Logout" onClick={doLogout}>
            ออกจากระบบ
          </button>
        </div>
      </header>

      <main className="content">
        {tab === "job" ? (
          <JobListTab
            jobs={jobs}
            filter={filter}
            onFilterChange={changeFilter}
            page={page}
            totalPages={totalPages}
            loading={loading}
            error={error}
            onPageChange={setPage}
            onRemove={removeJob}
            script={script}
          />
        ) : (
          <ProfileTab
            script={script}
            saveScript={saveScript}
            data={offersData}
            error={offersError}
            busy={offersBusy}
            onRemove={removeOffer}
          />
        )}
      </main>
    </div>
  );
}
