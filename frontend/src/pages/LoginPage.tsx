import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { Network, ShieldCheck } from 'lucide-react'
import { useAuth } from '@/lib/auth'
import { demoAccounts, roleLabel } from '@/lib/labels'
import { Button } from '@/components/ui/Button'
import { Field, Input } from '@/components/ui/Input'

export function LoginPage() {
  const { login, isAuthenticated, loading } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('ChangeMe123!')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (!loading && isAuthenticated) return <Navigate to="/" replace />

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    const res = await login(username.trim(), password)
    setSubmitting(false)
    if (res.ok) navigate('/', { replace: true })
    else setError(res.message)
  }

  return (
    <div className="bg-mesh min-h-screen">
      <div className="mx-auto grid min-h-screen max-w-6xl items-center gap-10 px-4 py-10 lg:grid-cols-2 lg:px-8">
        <section className="order-2 lg:order-1">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-black/[0.05] bg-white px-3 py-1 text-xs text-muted shadow-sm">
            <ShieldCheck className="h-3.5 w-3.5 text-teal-600" />
            毕业设计演示环境
          </div>
          <h1 className="font-display text-3xl font-semibold tracking-tight text-ink-900 sm:text-4xl">
            企业内网
            <br />
            <span className="text-teal-700">IP 地址管理系统</span>
          </h1>
          <p className="mt-4 max-w-md text-sm leading-relaxed text-muted">
            统一管理站点、子网与地址分配，减少 Excel 撞号与回收遗漏。深色导航 + 浅色工作台，便于日常运维演示。
          </p>
          <ul className="mt-6 space-y-2 text-sm text-ink-700">
            <li className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-teal-500" />
              子网建池 · 分配 / 预留 / 回收
            </li>
            <li className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-teal-500" />
              角色权限 · JWT 登录
            </li>
            <li className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-teal-500" />
              操作日志 · 冲突登记
            </li>
          </ul>
        </section>

        <section className="order-1 lg:order-2">
          <div className="card-surface mx-auto w-full max-w-md rounded-[24px] p-6 sm:p-8">
            <div className="mb-6 flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-400 to-teal-600 text-white shadow-md shadow-teal-700/20">
                <Network className="h-5 w-5" />
              </div>
              <div>
                <div className="text-lg font-semibold text-ink-900">登录</div>
                <div className="text-xs text-muted">演示账号可一键填入</div>
              </div>
            </div>

            <form className="space-y-4" onSubmit={onSubmit}>
              <Field label="用户名">
                <Input
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoComplete="username"
                  required
                />
              </Field>
              <Field label="密码">
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                />
              </Field>
              {error ? (
                <div className="rounded-2xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
                  {error}
                </div>
              ) : null}
              <Button type="submit" className="w-full rounded-2xl" disabled={submitting}>
                {submitting ? '登录中…' : '登录'}
              </Button>
            </form>

            <div className="mt-6">
              <div className="mb-2 text-xs text-muted">演示账号（密码均为 ChangeMe123!）</div>
              <div className="grid grid-cols-2 gap-2">
                {demoAccounts.map((a) => (
                  <button
                    key={a.username}
                    type="button"
                    onClick={() => {
                      setUsername(a.username)
                      setPassword(a.password)
                      setError('')
                    }}
                    className="rounded-2xl border border-black/[0.05] bg-[#f7f9f8] px-3 py-2.5 text-left text-xs transition hover:border-teal-200 hover:bg-white"
                  >
                    <div className="font-semibold text-ink-900">{a.username}</div>
                    <div className="mt-0.5 text-muted">{roleLabel[a.role]}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}