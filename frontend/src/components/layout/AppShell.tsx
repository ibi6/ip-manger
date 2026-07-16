import {
  AlertTriangle,
  ClipboardList,
  Globe2,
  HardDrive,
  LayoutDashboard,
  LogOut,
  Menu,
  Network,
  Server,
  Settings,
  Users,
  X,
} from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/Button'
import { ThemeToggle } from '@/components/ui/ThemeToggle'
import { productConfig } from '@/config/product'
import { api } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import { cn } from '@/lib/cn'
import { roleLabel } from '@/lib/labels'

const baseNav = [
  { to: '/', label: '工作台', icon: LayoutDashboard, end: true },
  { to: '/sites', label: '站点', icon: Globe2 },
  { to: '/subnets', label: '子网管理', icon: Network },
  { to: '/addresses', label: '地址台账', icon: Server },
  { to: '/devices', label: '设备台账', icon: HardDrive },
  { to: '/logs', label: '操作日志', icon: ClipboardList },
  { to: '/conflicts', label: '冲突记录', icon: AlertTriangle },
  { to: '/settings', label: '系统设置', icon: Settings },
]

export function AppShell() {
  const { user, logout, canManageNetwork, canAdmin } = useAuth()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [openConflicts, setOpenConflicts] = useState(0)
  const closeButtonRef = useRef<HTMLButtonElement>(null)

  const nav = canAdmin
    ? [
        ...baseNav.slice(0, 7),
        { to: '/users', label: '用户管理', icon: Users },
        baseNav[7],
      ]
    : baseNav

  useEffect(() => {
    api
      .conflicts('open')
      .then((list) => setOpenConflicts(list.length))
      .catch(() => setOpenConflicts(0))
  }, [])

  useEffect(() => {
    if (!mobileOpen) return
    const previousOverflow = document.body.style.overflow
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setMobileOpen(false)
    }
    document.body.style.overflow = 'hidden'
    document.addEventListener('keydown', onKeyDown)
    closeButtonRef.current?.focus()
    return () => {
      document.body.style.overflow = previousOverflow
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [mobileOpen])

  if (!user) return null

  const performLogout = () => {
    logout()
    setMobileOpen(false)
    navigate('/login', { replace: true })
  }

  const NavItems = ({ onNavigate }: { onNavigate?: () => void }) => (
    <nav
      className="flex-1 space-y-1 overflow-y-auto px-3 py-4"
      aria-label={onNavigate ? '移动端主导航' : '主导航'}
    >
      {nav.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              'group flex min-h-11 items-center gap-3 rounded-2xl px-3.5 py-2.5 text-[13px] font-medium transition-all',
              isActive
                ? 'nav-active'
                : 'text-white/60 hover:bg-white/[0.07] hover:text-white focus-visible:bg-white/[0.07]',
            )
          }
        >
          {({ isActive }) => (
            <>
              <item.icon
                className={cn(
                  'h-[18px] w-[18px] shrink-0',
                  isActive ? 'text-teal-300' : 'text-white/45 group-hover:text-white/75',
                )}
                aria-hidden="true"
              />
              <span className="flex-1">{item.label}</span>
              {item.to === '/conflicts' && openConflicts > 0 ? (
                <span
                  className="min-w-[1.25rem] rounded-full bg-rose-500 px-1.5 py-0.5 text-center text-[10px] font-semibold text-white"
                  aria-label={`${openConflicts} 条未解决冲突`}
                >
                  {openConflicts}
                </span>
              ) : null}
            </>
          )}
        </NavLink>
      ))}
    </nav>
  )

  const UserPanel = ({ mobile = false }: { mobile?: boolean }) => (
    <div className={cn('border-t border-white/[0.07] p-4', mobile && 'mt-auto')}>
      <div className="rounded-2xl bg-white/[0.055] p-3 ring-1 ring-white/[0.07]">
        <div className="flex items-center gap-3">
          <div
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-sm font-semibold text-white shadow-inner"
            style={{ background: user.avatarColor || '#0d9488' }}
            aria-hidden="true"
          >
            {user.displayName.slice(0, 1)}
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-medium text-white">{user.displayName}</div>
            <div className="truncate text-[11px] text-white/45">{roleLabel[user.role]}</div>
          </div>
        </div>
        <button
          type="button"
          onClick={performLogout}
          className="mt-3 flex min-h-11 w-full items-center justify-center gap-2 rounded-xl bg-white/[0.07] px-3 text-xs text-white/70 transition hover:bg-white/[0.12] hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-300"
        >
          <LogOut className="h-3.5 w-3.5" aria-hidden="true" />
          退出登录
        </button>
      </div>
    </div>
  )

  return (
    <div className="bg-mesh flex min-h-screen">
      <a
        href="#main-content"
        className="fixed left-3 top-3 z-[60] -translate-y-20 rounded-xl bg-action-secondary px-4 py-2 text-sm font-medium text-on-action transition focus:translate-y-0"
      >
        跳到主要内容
      </a>

      <aside className="sidebar-shell fixed inset-y-0 left-0 z-30 hidden w-[232px] flex-col text-white lg:flex">
        <div className="flex items-center gap-3 px-5 py-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-400 to-teal-600 shadow-lg shadow-teal-950/40">
            <Network className="h-5 w-5 text-white" aria-hidden="true" />
          </div>
          <div className="min-w-0">
            <div className="truncate text-[15px] font-semibold tracking-wide text-white">
              {productConfig.name}
            </div>
            <div className="truncate text-[11px] text-white/45">{productConfig.chineseName}</div>
          </div>
        </div>

        <div className="mx-4 flex items-center gap-2 rounded-xl border border-white/[0.06] bg-black/10 px-3 py-2 text-[10px] text-white/45">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.7)]" />
          {productConfig.environmentLabel}
        </div>

        <NavItems />
        <UserPanel />
      </aside>

      {mobileOpen ? (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-ink-950/55 backdrop-blur-[2px]"
            aria-label="关闭导航菜单"
            onClick={() => setMobileOpen(false)}
          />
          <aside
            id="mobile-navigation"
            className="sidebar-shell absolute inset-y-0 left-0 flex w-[min(19rem,86vw)] flex-col text-white shadow-2xl"
            role="dialog"
            aria-modal="true"
            aria-label="移动端导航"
          >
            <div className="flex items-center justify-between px-4 py-4">
              <div className="flex min-w-0 items-center gap-2.5">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-teal-400 to-teal-600">
                  <Network className="h-4 w-4 text-white" aria-hidden="true" />
                </div>
                <div className="min-w-0">
                  <div className="truncate text-base font-semibold">{productConfig.name}</div>
                  <div className="truncate text-[10px] text-white/45">{productConfig.chineseName}</div>
                </div>
              </div>
              <button
                ref={closeButtonRef}
                type="button"
                aria-label="关闭导航菜单"
                onClick={() => setMobileOpen(false)}
                className="flex h-11 w-11 items-center justify-center rounded-xl hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-300"
              >
                <X className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
            <NavItems onNavigate={() => setMobileOpen(false)} />
            <UserPanel mobile />
          </aside>
        </div>
      ) : null}

      <div className="flex min-h-screen min-w-0 flex-1 flex-col lg:pl-[232px]">
        <header className="app-header sticky top-0 z-20 border-b border-line/70 backdrop-blur-xl">
          <div className="flex items-center justify-between gap-3 px-4 py-3.5 sm:px-7">
            <div className="flex min-w-0 items-center gap-3">
              <button
                type="button"
                className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-line bg-surface text-ink-700 shadow-sm focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-teal-500/20 lg:hidden"
                aria-label="打开导航菜单"
                aria-controls="mobile-navigation"
                aria-expanded={mobileOpen}
                onClick={() => setMobileOpen(true)}
              >
                <Menu className="h-5 w-5" aria-hidden="true" />
              </button>
              <div className="min-w-0">
                <div className="truncate text-[11px] text-muted">
                  {user.departmentName || '信息中心'}
                </div>
                <div className="truncate text-sm font-medium text-ink-800">
                  {productConfig.chineseName}
                </div>
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <ThemeToggle />
              {canManageNetwork ? (
                <Button
                  size="sm"
                  className="min-h-11 shrink-0 rounded-full px-4"
                  onClick={() => navigate('/subnets/new')}
                >
                  新建子网
                </Button>
              ) : null}
            </div>
          </div>
        </header>

        <main id="main-content" tabIndex={-1} className="flex-1 px-4 py-6 outline-none sm:px-7 lg:px-8">
          <div className="mx-auto w-full max-w-[1600px]">
            <Outlet />
          </div>
        </main>

        <footer className="px-6 py-5 text-center text-[11px] text-muted/80">
          {productConfig.name} · {productConfig.tagline}
        </footer>
      </div>
    </div>
  )
}
