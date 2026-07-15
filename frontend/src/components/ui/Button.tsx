import { cn } from '@/lib/cn'
import type { ButtonHTMLAttributes } from 'react'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline'

const variants: Record<Variant, string> = {
  primary:
    'bg-teal-600 text-white shadow-sm shadow-teal-700/15 hover:bg-teal-700 focus-visible:ring-teal-500/30 disabled:bg-teal-600/50',
  secondary:
    'bg-ink-900 text-white shadow-sm hover:bg-ink-800 focus-visible:ring-ink-500/25 disabled:bg-ink-900/50',
  ghost: 'bg-transparent text-ink-700 hover:bg-black/[0.04] focus-visible:ring-ink-500/15',
  danger: 'bg-rose-600 text-white hover:bg-rose-700 focus-visible:ring-rose-500/25',
  outline:
    'border border-line bg-white text-ink-800 hover:bg-ink-50 focus-visible:ring-ink-500/15',
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
        'inline-flex items-center justify-center gap-2 rounded-2xl font-medium transition focus-visible:outline-none focus-visible:ring-4 disabled:cursor-not-allowed disabled:opacity-60',
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