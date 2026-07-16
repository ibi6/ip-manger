/** Format an API timestamp without applying an implicit timezone conversion. */
export function formatDateTime(value?: string | null): string {
  if (!value) return '—'
  return value.replace('T', ' ').slice(0, 19)
}

/** Return the calendar portion of an API date or timestamp. */
export function formatShortDate(value?: string | null): string {
  return value ? value.slice(0, 10) : '—'
}

/** Keep progress values within valid CSS percentage boundaries. */
export function clampPercent(value: number): number {
  if (!Number.isFinite(value)) return 0
  return Math.min(100, Math.max(0, value))
}
