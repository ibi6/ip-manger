import assert from 'node:assert/strict'
import test from 'node:test'

import { clampPercent, formatDateTime, formatShortDate } from '../src/lib/format.ts'

test('formatDateTime returns a stable display and handles empty input', () => {
  assert.equal(formatDateTime(undefined), '—')
  assert.equal(formatDateTime(null), '—')
  assert.equal(formatDateTime('2026-07-16T12:30:45Z'), '2026-07-16 12:30:45')
})

test('formatShortDate returns the calendar portion of an ISO value', () => {
  assert.equal(formatShortDate(undefined), '—')
  assert.equal(formatShortDate('2026-07-16T12:30:45Z'), '2026-07-16')
})

test('clampPercent protects progress bar boundaries', () => {
  assert.equal(clampPercent(-2), 0)
  assert.equal(clampPercent(42.5), 42.5)
  assert.equal(clampPercent(130), 100)
  assert.equal(clampPercent(Number.NaN), 0)
})
