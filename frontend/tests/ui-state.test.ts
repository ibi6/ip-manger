import assert from 'node:assert/strict'
import test from 'node:test'

import {
  adminRouteAllowed,
  releasableAddressIds,
  selectionState,
} from '../src/lib/ui-state.ts'

test('adminRouteAllowed protects administration pages by role', () => {
  assert.equal(adminRouteAllowed('admin'), true)
  assert.equal(adminRouteAllowed('network_admin'), false)
  assert.equal(adminRouteAllowed('dept_user'), false)
  assert.equal(adminRouteAllowed('viewer'), false)
  assert.equal(adminRouteAllowed(undefined), false)
})

test('releasableAddressIds excludes free and special addresses', () => {
  assert.deepEqual(
    releasableAddressIds([
      { id: 1, status: 'allocated', is_network_or_broadcast: false },
      { id: 2, status: 'reserved', is_network_or_broadcast: false },
      { id: 3, status: 'disabled', is_network_or_broadcast: true },
      { id: 4, status: 'free', is_network_or_broadcast: false },
    ]),
    [1, 2],
  )
})

test('selectionState exposes unchecked, mixed, and checked states', () => {
  assert.deepEqual(selectionState([], [1, 2]), { checked: false, indeterminate: false })
  assert.deepEqual(selectionState([1], [1, 2]), { checked: false, indeterminate: true })
  assert.deepEqual(selectionState([1, 2], [1, 2]), { checked: true, indeterminate: false })
  assert.deepEqual(selectionState([], []), { checked: false, indeterminate: false })
})
