// All network calls in one place.

export const API_URL = '/api/jobs'
export const API_PARAMS = {
  page_size: 50,
  'order_by[]': 'inserted_at',
  'order_directions[]': 'desc',
  'filters[0][field]': 'kind',
  'filters[0][value]': 'standard',
}

export const APPLY_SERVER_URL = 'http://localhost:8787/apply'
export const OFFERS_URL = 'http://localhost:8787/offers'
export const SEARCH_URL = 'http://localhost:8787/search'
export const LOGIN_STATUS_URL = 'http://localhost:8787/login-status'
export const LOGIN_URL = 'http://localhost:8787/login'
export const AI_JOBS_URL = 'http://localhost:8787/ai-jobs'

// fetch one page at a time (not the whole dataset up front) so the list
// shows fast — Prev/Next fetches the next page on demand
export async function fetchJobsPage(page) {
  const params = new URLSearchParams({ ...API_PARAMS, page })
  const resp = await fetch(`${API_URL}?${params}`, {
    headers: { 'User-Agent': 'Mozilla/5.0' },
  })
  if (!resp.ok) throw new Error(`API ${resp.status}`)
  const body = await resp.json()
  return { jobs: body.data, totalPages: body.meta.total_pages }
}

export async function fetchOffers() {
  const resp = await fetch(OFFERS_URL)
  return resp.json()
}

export async function deleteOffer(index) {
  const resp = await fetch(`${OFFERS_URL}/${index}`, { method: 'DELETE' })
  return resp.json()
}

export async function searchJobs(q) {
  const resp = await fetch(`${SEARCH_URL}?${new URLSearchParams({ q })}`)
  if (!resp.ok) throw new Error(`search ${resp.status}`)
  return resp.json()
}

export async function submitApply({ job, price, days, script }) {
  return fetch(APPLY_SERVER_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job, price, days, script }),
  })
}

export async function fetchAiJobIds() {
  const resp = await fetch(AI_JOBS_URL)
  if (!resp.ok) throw new Error(`ai-jobs ${resp.status}`)
  const { ids } = await resp.json()
  return new Set(ids)
}

export async function loginStatus() {
  const resp = await fetch(LOGIN_STATUS_URL)
  return resp.json() // { fastwork: true|false }
}

export async function startLogin(site) {
  return fetch(`${LOGIN_URL}/${site}`, { method: 'POST' })
}

export async function logout(site) {
  return fetch(`http://localhost:8787/logout/${site}`, { method: 'POST' })
}
