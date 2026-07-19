import assert from 'node:assert/strict'
import test from 'node:test'

import * as networkErrors from '../src/lib/network-error.ts'

test('networkErrorMessage distinguishes timeout from connectivity failure', () => {
  assert.equal(networkErrors.networkErrorMessage(true), '请求超时，请稍后重试')
  assert.equal(networkErrors.networkErrorMessage(false), '无法连接服务，请检查网络后重试')
})

test('normalizeRequestTimeout rejects invalid configuration', () => {
  const normalize = Reflect.get(networkErrors, 'normalizeRequestTimeout')
  assert.equal(typeof normalize, 'function')
  assert.equal(normalize('2500'), 2500)
  assert.equal(normalize(0), 15_000)
  assert.equal(normalize('not-a-number'), 15_000)
})

test('apiErrorMessage accepts only a non-empty detail string', () => {
  const message = Reflect.get(networkErrors, 'apiErrorMessage')
  assert.equal(typeof message, 'function')
  assert.equal(message('Bad Request', { detail: '字段无效' }), '字段无效')
  assert.equal(message('Bad Request', { detail: { internal: true } }), 'Bad Request')
  assert.equal(message('Request failed', null), 'Request failed')
})
