import { NavLink, Outlet, useNavigate } from 'react-router-dom'
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
import { useEffect, useState } from 'react'
import { useAuth } from '@/lib/auth'
import { roleLabel } from '@/lib/labels'
import { api } from '@/lib/api'
import { cn } from '@/lib/cn'
import { Button } from '@/components/ui/Button'

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
  const nav = canAdmin
    ? [
        ...baseNav.slice(0, 7),
        { to: '/users', label: '用户管理', icon: Users },
        baseNav[7],
      ]
    : baseNav
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [openConflicts, setOpenConflicts] = useState(0)

  useEffect(() => {
    api
      .conflicts('open')
      .then((list) => setOpenConflicts(list.length))
      .catch(() => setOpenConflicts(0))
  }, [])

  if (!user) return null

  const NavItems = ({ onNavigate }: { onNavigate?: () => void }) => (
    <nav className="flex-1 space-y-1 px-3 py-4">
      {nav.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              'group flex items-center gap-3 rounded-2xl px-3.5 py-2.5 text-[13px] font-medium transition-all',
              isActive
                ? 'nav-active'
                : 'text-white/55 hover:bg-white/[0.06] hover:text-white/90',
            )
          }
        >
          {({ isActive }) => (
            <>
              <item.icon
                className={cn(
                  'h-[18px] w-[18px]',
                  isActive ? 'text-teal-300' : 'text-white/40 group-hover:text-white/70',
                )}
              />
              <span className="flex-1">{item.label}</span>
              {item.to === '/conflicts' && openConflicts > 0 ? (
                <span className="min-w-[1.25rem] rounded-full bg-rose-500 px-1.5 py-0.5 text-center text-[10px] font-semibold text-white">
                  {openConflicts}
                </span>
              ) : null}
            </>
          )}
        </NavLink>
      ))}
    </nav>
  )

  return (
    <div className="bg-mesh flex min-h-screen">
      <aside className="sidebar-shell fixed inset-y-0 left-0 z-30 hidden w-[232px] flex-col text-white lg:flex">
        <div className="flex items-center gap-3 px-5 py-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-400 to-teal-600 shadow-lg shadow-teal-900/40">
            <Network className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="text-[15px] font-semibold tracking-wide text-white">IP 管理系统</div>
            <div className="text-[11px] text-white/40">毕业设计演示</div>
          </div>
        </div>

        <NavItems />

        <div className="border-t border-white/[0.06] p-4">
          <div className="rounded-2xl bg-white/[0.05] p-3 ring-1 ring-white/[0.06]">
            <div className="flex items-center gap-3">
              <div
                className="flex h-9 w-9 items-center justify-center rounded-full text-sm font-semibold text-white shadow-inner"
                style={{ background: user.avatarColor || '#0d9488' }}
              >
                {user.displayName.slice(0, 1)}
              </div>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium text-white">{user.displayName}</div>
                <div className="truncate text-[11px] text-white/40">{roleLabel[user.role]}</div>
              </div>
            </div>
            <button
              type="button"
              onClick={() => {
                logout()
                navigate('/login')
              }}
              className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-white/[0.06] py-2 text-xs text-white/60 transition hover:bg-white/[0.1] hover:text-white"
            >
              <LogOut className="h-3.5 w-3.5" />
              退出登录
            </button>
          </div>
        </div>
      </aside>

      {mobileOpen ? (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-ink-950/50"
            aria-label="关闭菜单"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="sidebar-shell absolute inset-y-0 left-0 flex w-72 flex-col text-white shadow-2xl">
            <div className="flex items-center justify-between px-4 py-4">
              <div className="flex items-center gap-2">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-teal-400 to-teal-600">
                  <Network className="h-4 w-4 text-white" />
                </div>
                <span className="text-base font-semibold">IP 管理系统</span>
              </div>
              <button type="button" onClick={() => setMobileOpen(false)} className="rounded-lg p-2 hover:bg-white/10">
                <X className="h-5 w-5" />
              </button>
            </div>
            <NavItems onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      ) : null}

      <div className="flex min-h-screen flex-1 flex-col lg:pl-[232px]">
        <header className="sticky top-0 z-20 border-b border-black/[0.04] bg-[#f6f8f7]/80 backdrop-blur-xl">
          <div className="flex items-center justify-between gap-3 px-4 py-3.5 sm:px-7">
            <div className="flex items-center gap-3">
              <button
                type="button"
                className="rounded-xl border border-line bg-white p-2 text-ink-700 shadow-sm lg:hidden"
                onClick={() => setMobileOpen(true)}
              >
                <Menu className="h-5 w-5" />
              </button>
              <div>
                <div className="text-[11px] text-muted">{user.departmentName || '信息中心'}</div>
                <div className="text-sm font-medium text-ink-800">内网 IP 地址管理</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {canManageNetwork ? (
                <Button size="sm" className="rounded-full px-4" onClick={() => navigate('/subnets/new')}>
                  新建子网
                </Button>
              ) : null}
            </div>
          </div>
        </header>

        <main className="flex-1 px-4 py-6 sm:px-7 lg:px-8">
          <Outlet />
        </main>

        <footer className="px-6 py-4 text-center text-[11px] text-muted/80">
          企业IP地址管理系统 · 毕业设计
        </footer>
      </div>
    </div>
  )
}