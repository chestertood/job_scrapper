// Small date/storage helpers shared across components.

export const FILTERS = { today: 0, yesterday: 1, all: null }
export const MIN_SCRIPT_CHARS = 100

export const SCRIPT_KEY = 'applyScript'
export const REMOVED_KEY = 'removedJobIds'

export function jobDate(job) {
  return new Date(job.inserted_at)
}

export function sameUtcDate(a, b) {
  return (
    a.getUTCFullYear() === b.getUTCFullYear() &&
    a.getUTCMonth() === b.getUTCMonth() &&
    a.getUTCDate() === b.getUTCDate()
  )
}

export function loadRemoved() {
  try {
    return new Set(JSON.parse(localStorage.getItem(REMOVED_KEY) || '[]'))
  } catch {
    return new Set()
  }
}
