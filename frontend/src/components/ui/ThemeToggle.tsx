import { Monitor, Moon, Sun } from 'lucide-react'

import { cn } from '@/lib/cn'
import { nextTheme, type ThemePreference } from '@/lib/theme'
import { useTheme } from '@/lib/theme-context'

const themeDetails = {
  system: { label: '跟随系统', icon: Monitor },
  light: { label: '浅色', icon: Sun },
  dark: { label: '深色', icon: Moon },
} satisfies Record<ThemePreference, { label: string; icon: typeof Monitor }>

export function ThemeToggle({
  compact = false,
  className,
}: {
  compact?: boolean
  className?: string
}) {
  const { preference, setPreference } = useTheme()
  const nextPreference = nextTheme(preference)
  const current = themeDetails[preference]
  const next = themeDetails[nextPreference]
  const Icon = current.icon
  const accessibleLabel = `当前主题：${current.label}；切换为：${next.label}`

  return (
    <button
      type="button"
      className={cn('theme-toggle', compact && 'theme-toggle-compact', className)}
      aria-label={accessibleLabel}
      title={accessibleLabel}
      onClick={() => setPreference(nextPreference)}
    >
      <Icon className="h-[17px] w-[17px]" aria-hidden="true" />
      {!compact ? <span className="hidden text-xs font-medium sm:inline">{current.label}</span> : null}
    </button>
  )
}
