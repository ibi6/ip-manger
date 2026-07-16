import { ArrowRight, Network, ShieldCheck } from 'lucide-react'
import { useRef, useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/Button'
import { Field, Input } from '@/components/ui/Input'
import { ThemeToggle } from '@/components/ui/ThemeToggle'
import { productConfig } from '@/config/product'
import { useAuth } from '@/lib/auth-context'
import { demoAccounts, roleLabel } from '@/lib/labels'

export function LoginPage() {
  const { login, isAuthenticated, loading } = useAuth()
  const navigate = useNavigate()
  const passwordRef = useRef<HTMLInputElement>(null)
  const [username, setUsername] = useState(productConfig.showDemoAccounts ? 'admin' : '')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (!loading && isAuthenticated) return <Navigate to="/" replace />

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    const result = await login(username.trim(), password)
    setSubmitting(false)
    if (result.ok) navigate('/', { replace: true })
    else setError(result.message)
  }

  return (
    <div className="login-canvas relative min-h-screen">
      <ThemeToggle compact className="fixed right-4 top-4 z-20 sm:right-7 sm:top-6" />
      <div className="mx-auto grid min-h-screen max-w-7xl items-center gap-12 px-4 pb-10 pt-20 sm:px-7 lg:grid-cols-[1.12fr_0.88fr] lg:px-10 lg:py-10">
        <section className="order-2 lg:order-1" aria-labelledby="login-introduction">
          <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-line bg-surface/75 px-3.5 py-1.5 text-xs font-medium text-ink-600 shadow-sm backdrop-blur">
            <ShieldCheck className="h-3.5 w-3.5 text-teal-700" aria-hidden="true" />
            {productConfig.environmentLabel} · 权限与操作全程留痕
          </div>
          <div className="mb-5 flex items-center gap-3 text-ink-900">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-400 to-teal-700 text-white shadow-lg shadow-teal-900/20">
              <Network className="h-6 w-6" aria-hidden="true" />
            </div>
            <div>
              <div className="text-xl font-bold tracking-tight">{productConfig.name}</div>
              <div className="text-xs text-muted">轻量企业 IPAM</div>
            </div>
          </div>
          <h1
            id="login-introduction"
            className="font-display max-w-2xl text-[2.65rem] font-semibold leading-[1.08] tracking-tight text-ink-950 sm:text-6xl"
          >
            让每一个地址
            <br />
            <span className="text-teal-700">都有清晰归属</span>
          </h1>
          <p className="mt-5 max-w-xl text-[15px] leading-7 text-ink-600">
            统一管理站点、子网、地址与设备，用结构化台账替代分散表格；分配、回收与冲突处理都有记录可追溯。
          </p>
          <div className="mt-8 grid max-w-xl gap-3 sm:grid-cols-3">
            {['地址生命周期', '角色权限边界', '完整审计记录'].map((item, index) => (
              <div
                key={item}
                className="rounded-2xl border border-line/70 bg-surface/55 px-4 py-3 backdrop-blur"
              >
                <div className="font-mono text-[10px] font-semibold text-teal-700">
                  0{index + 1}
                </div>
                <div className="mt-1 text-sm font-medium text-ink-800">{item}</div>
              </div>
            ))}
          </div>
        </section>

        <section className="order-1 lg:order-2" aria-label="登录表单">
          <div className="card-surface login-card mx-auto w-full max-w-md rounded-[28px] p-6 sm:p-8">
            <div className="mb-7">
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-teal-700">
                Secure access
              </div>
              <h2 className="mt-2 font-display text-3xl font-semibold tracking-tight text-ink-950">
                登录工作台
              </h2>
              <p className="mt-2 text-sm leading-6 text-muted">
                使用组织账号进入 NetLedger。
              </p>
            </div>

            <form className="space-y-4" onSubmit={onSubmit} aria-busy={submitting}>
              <Field label="用户名">
                <Input
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  autoComplete="username"
                  required
                  maxLength={50}
                  placeholder="请输入用户名"
                />
              </Field>
              <Field label="密码">
                <Input
                  ref={passwordRef}
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  autoComplete="current-password"
                  required
                  maxLength={128}
                  placeholder="请输入密码"
                />
              </Field>
              {error ? (
                <div
                  className="rounded-2xl border border-rose-200 bg-rose-50 px-3.5 py-2.5 text-sm text-rose-800"
                  role="alert"
                >
                  {error}
                </div>
              ) : null}
              <Button type="submit" size="lg" className="group min-h-12 w-full" disabled={submitting}>
                {submitting ? '正在验证…' : '安全登录'}
                {!submitting ? (
                  <ArrowRight
                    className="h-4 w-4 transition-transform group-hover:translate-x-0.5"
                    aria-hidden="true"
                  />
                ) : null}
              </Button>
            </form>

            {productConfig.showDemoAccounts ? (
              <div className="mt-7 border-t border-line pt-5">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <div className="text-xs font-medium text-ink-700">演示身份</div>
                  <div className="text-[11px] text-muted">初始密码见 README</div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {demoAccounts.map((account) => (
                    <button
                      key={account.username}
                      type="button"
                      onClick={() => {
                        setUsername(account.username)
                        setPassword('')
                        setError('')
                        passwordRef.current?.focus()
                      }}
                      className="min-h-12 rounded-2xl border border-line bg-surface-subtle px-3 py-2.5 text-left text-xs transition hover:border-teal-300 hover:bg-surface focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-teal-500/15"
                      aria-label={`选择 ${account.username}，${roleLabel[account.role]}`}
                    >
                      <div className="font-semibold text-ink-900">{account.username}</div>
                      <div className="mt-0.5 text-muted">{roleLabel[account.role]}</div>
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </section>
      </div>
    </div>
  )
}
