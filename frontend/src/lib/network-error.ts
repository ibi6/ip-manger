/** Return a stable, user-facing message for transport-level failures. */
export function networkErrorMessage(timedOut: boolean): string {
  return timedOut ? '请求超时，请稍后重试' : '无法连接服务，请检查网络后重试'
}
