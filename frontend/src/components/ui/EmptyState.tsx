import { Inbox } from 'lucide-react'
import { Button } from './Button'

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
}: {
  title: string
  description?: string
  actionLabel?: string
  onAction?: () => void
}) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-16 text-center">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-surface-muted text-ink-600">
        <Inbox className="h-7 w-7" />
      </div>
      <h3 className="text-lg font-semibold text-ink-900">{title}</h3>
      {description ? <p className="mt-2 max-w-sm text-sm text-muted">{description}</p> : null}
      {actionLabel && onAction ? (
        <Button className="mt-5" onClick={onAction}>
          {actionLabel}
        </Button>
      ) : null}
    </div>
  )
}

export function LoadingBlock({ label = '加载中…' }: { label?: string }) {
  return (
    <div
      className="flex flex-col items-center justify-center gap-3 py-20"
      role="status"
      aria-live="polite"
    >
      <div
        className="h-9 w-9 animate-spin rounded-full border-2 border-teal-600 border-t-transparent"
        aria-hidden="true"
      />
      <p className="text-sm text-muted">{label}</p>
    </div>
  )
}

export function ErrorBlock({
  message,
  onRetry,
}: {
  message: string
  onRetry?: () => void
}) {
  return (
    <div
      className="flex flex-col items-center justify-center px-6 py-16 text-center"
      role="alert"
    >
      <div className="mb-3 rounded-full bg-rose-50 px-3 py-1 text-xs font-medium text-rose-700">
        出错了
      </div>
      <p className="max-w-md text-sm text-ink-800">{message}</p>
      {onRetry ? (
        <Button variant="outline" className="mt-5" onClick={onRetry}>
          重试
        </Button>
      ) : null}
    </div>
  )
}
