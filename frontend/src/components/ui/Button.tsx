import { cn } from '@/lib/cn'
import type { ButtonHTMLAttributes } from 'react'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline'

const variants: Record<Variant, string> = {
  primary:
    'bg-[#0b9185] text-white shadow-sm shadow-teal-700/15 hover:bg-[#08756d] focus-visible:ring-teal-500/30 disabled:bg-[#0b9185]/50',
  secondary:
    'bg-action-secondary text-on-action shadow-sm hover:bg-action-secondary-hover focus-visible:ring-ink-500/25 disabled:opacity-50',
  ghost: 'bg-transparent text-ink-700 hover:bg-surface-muted focus-visible:ring-ink-500/15',
  danger: 'bg-rose-600 text-white hover:bg-rose-700 focus-visible:ring-rose-500/25',
  outline:
    'border border-line bg-surface text-ink-800 hover:bg-surface-subtle focus-visible:ring-ink-500/15',
}

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: 'sm' | 'md' | 'lg'
}

export function Button({
  className,
  variant = 'primary',
  size = 'md',
  type = 'button',
  ...props
}: Props) {
  return (
    <button
      type={type}
      className={cn(
        'inline-flex min-h-11 items-center justify-center gap-2 rounded-2xl font-medium transition focus-visible:outline-none focus-visible:ring-4 disabled:cursor-not-allowed disabled:opacity-60',
        size === 'sm' && 'px-3.5 py-1.5 text-xs',
        size === 'md' && 'px-4 py-2.5 text-sm',
        size === 'lg' && 'px-5 py-3 text-sm',
        variants[variant],
        className,
      )}
      {...props}
    />
  )
}
