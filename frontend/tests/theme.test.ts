import assert from 'node:assert/strict'
import test from 'node:test'

import { normalizeTheme, nextTheme, resolveTheme } from '../src/lib/theme.ts'

test('normalizeTheme rejects damaged stored preferences', () => {
  assert.equal(normalizeTheme('dark'), 'dark')
  assert.equal(normalizeTheme('unexpected'), 'system')
  assert.equal(normalizeTheme(null), 'system')
})

test('resolveTheme follows the operating system only in system mode', () => {
  assert.equal(resolveTheme('system', true), 'dark')
  assert.equal(resolveTheme('system', false), 'light')
  assert.equal(resolveTheme('light', true), 'light')
  assert.equal(resolveTheme('dark', false), 'dark')
})

test('nextTheme cycles system, light, and dark', () => {
  assert.equal(nextTheme('system'), 'light')
  assert.equal(nextTheme('light'), 'dark')
  assert.equal(nextTheme('dark'), 'system')
})
