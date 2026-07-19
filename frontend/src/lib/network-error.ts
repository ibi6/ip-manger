/** Return a stable, user-facing message for transport-level failures. */
export function networkErrorMessage(timedOut: boolean): string {
  return timedOut ? '请求超时，请稍后重试' : '无法连接服务，请检查网络后重试'
}

/** Normalize a user-provided timeout without allowing requests to hang forever. */
export function normalizeRequestTimeout(value: unknown, fallback = 15_000): number {
  const timeout = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(timeout) && timeout > 0 ? timeout : fallback
}

/** Extract only the public string detail returned by the API. */
export function apiErrorMessage(statusText: string, payload: unknown): string {
  if (typeof payload !== 'object' || payload === null || !('detail' in payload)) {
    return statusText
  }

  const detail = Reflect.get(payload, 'detail')
  return typeof detail === 'string' && detail.trim() ? detail : statusText
}
