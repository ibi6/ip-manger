import { cn } from '@/lib/cn'
import type { ConflictType, IpStatus } from '@/types'
import { conflictTypeLabel, ipStatusLabel } from '@/lib/labels'

const statusStyles: Record<IpStatus, string> = {
  free: 'bg-emerald-50 text-emerald-700 ring-emerald-100',
  allocated: 'bg-sky-50 text-sky-700 ring-sky-100',
  reserved: 'bg-amber-50 text-amber-800 ring-amber-100',
  disabled: 'bg-stone-100 text-stone-600 ring-stone-200',
}

export function StatusBadge({ status }: { status: IpStatus }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset',
        statusStyles[status],
      )}
    >
      {ipStatusLabel[status]}
    </span>
  )
}

export function SoftBadge({
  children,
  tone = 'neutral',
}: {
  children: React.ReactNode
  tone?: 'neutral' | 'warn' | 'danger' | 'ok' | 'info'
}) {
  const map = {
    neutral: 'bg-ink-50 text-ink-700 ring-black/5',
    warn: 'bg-amber-50 text-amber-800 ring-amber-100',
    danger: 'bg-rose-50 text-rose-700 ring-rose-100',
    ok: 'bg-emerald-50 text-emerald-700 ring-emerald-100',
    info: 'bg-sky-50 text-sky-700 ring-sky-100',
  }
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset',
        map[tone],
      )}
    >
      {children}
    </span>
  )
}

export function ConflictBadge({ type }: { type: ConflictType }) {
  return <SoftBadge tone="danger">{conflictTypeLabel[type]}</SoftBadge>
}