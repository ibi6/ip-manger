import assert from 'node:assert/strict'
import test from 'node:test'

import { networkErrorMessage } from '../src/lib/network-error.ts'

test('networkErrorMessage distinguishes timeout from connectivity failure', () => {
  assert.equal(networkErrorMessage(true), '请求超时，请稍后重试')
  assert.equal(networkErrorMessage(false), '无法连接服务，请检查网络后重试')
})
