import { Link } from 'react-router-dom'
import {
  AlertTriangle,
  ArrowUpRight,
  Globe2,
  Network,
  Server,
  Timer,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { SoftBadge, StatusBadge } from '@/components/ui/Badge'
import { ErrorBlock, LoadingBlock } from '@/components/ui/EmptyState'
import { api, type ApiDashboard, type ApiIp } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { cn } from '@/lib/cn'
import type { IpStatus } from '@/types'

export function DashboardPage() {
  const { user } = useAuth()
  const [stats, setStats] = useState<ApiDashboard | null>(null)
  const [sampleIps, setSampleIps] = useState<ApiIp[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const [d, ips] = await Promise.all([
        api.dashboard(),
        api.ips({ status: 'allocated' }),
      ])
      setStats(d)
      setSampleIps(ips.slice(0, 5))
    } catch (e) {
      setError(e instanceof Error ? e.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  if (loading) return <LoadingBlock label="加载工作台…" />
  if (error || !stats) return <ErrorBlock message={error || '无数据'} onRetry={load} />

  const metrics = [
    {
      label: '站点 / 子网',
      value: `${stats.site_count} / ${stats.subnet_count}`,
      icon: Globe2,
      iconBg: 'bg-[#111827]',
      iconColor: 'text-teal-300',
      hint: '活跃规划范围',
    },
    {
      label: '地址总量',
      value: stats.total_ips.toLocaleString(),
      icon: Network,
      iconBg: 'bg-teal-50',
      iconColor: 'text-teal-600',
      hint: `空闲 ${stats.free_ips} · 已分配 ${stats.allocated_ips}`,
    },
    {
      label: '开放冲突',
      value: String(stats.open_conflicts),
      icon: AlertTriangle,
      iconBg: 'bg-rose-50',
      iconColor: 'text-rose-500',
      hint: '需网络管理员处理',
    },
    {
      label: '30 日内到期',
      value: String(stats.expiring_soon),
      icon: Timer,
      iconBg: 'bg-amber-50',
      iconColor: 'text-amber-600',
      hint: '临时地址即将过期',
    },
  ]

  const statusBars = [
    { label: '已分配', n: stats.allocated_ips, color: 'bg-sky-500' },
    { label: '空闲', n: stats.free_ips, color: 'bg-emerald-500' },
    { label: '预留', n: stats.reserved_ips, color: 'bg-amber-500' },
    { label: '禁用', n: stats.disabled_ips, color: 'bg-stone-300' },
  ]

  return (
    <div>
      <PageHeader
        title={`你好，${user?.displayName ?? ''}`}
        description="下面是地址使用情况和最近操作，数据来自后端接口。"
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((m) => (
          <Card key={m.label} className="p-5">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="text-[12px] font-medium text-muted">{m.label}</div>
                <div className="mt-2 font-display text-[28px] font-semibold leading-none tracking-tight text-ink-900">
                  {m.value}
                </div>
                <div className="mt-2.5 text-[11px] text-muted">{m.hint}</div>
              </div>
              <div className={cn('metric-icon', m.iconBg, m.iconColor)}>
                <m.icon className="h-[18px] w-[18px]" />
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-5">
        <Card className="xl:col-span-3">
          <CardHeader title="地址状态分布" subtitle="全库聚合" />
          <CardBody className="space-y-5">
            {statusBars.map((s) => (
              <div key={s.label}>
                <div className="mb-1.5 flex justify-between text-[13px]">
                  <span className="text-ink-700">{s.label}</span>
                  <span className="font-medium tabular-nums text-ink-800">{s.n.toLocaleString()}</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-[#eef1f3]">
                  <div
                    className={cn('h-full rounded-full transition-all', s.color)}
                    style={{ width: `${(s.n / Math.max(stats.total_ips, 1)) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </CardBody>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader
            title="利用率 TOP"
            action={
              <Link
                to="/subnets"
                className="inline-flex items-center gap-0.5 text-xs font-medium text-teal-700 hover:text-teal-800"
              >
                全部 <ArrowUpRight className="h-3.5 w-3.5" />
              </Link>
            }
          />
          <CardBody className="space-y-4">
            {stats.top_subnets.length === 0 ? (
              <p className="text-sm text-muted">暂无子网数据</p>
            ) : (
              stats.top_subnets.map((s) => (
                <div key={s.cidr}>
                  <div className="mb-1.5 flex items-center justify-between gap-3 text-[13px]">
                    <div className="min-w-0">
                      <div className="truncate font-medium text-ink-900">{s.name}</div>
                      <div className="font-mono text-[11px] text-muted">{s.cidr}</div>
                    </div>
                    <span className="shrink-0 font-semibold tabular-nums text-ink-800">
                      {s.utilization}%
                    </span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-[#eef1f3]">
                    <div
                      className={cn(
                        'h-full rounded-full',
                        s.utilization >= 80
                          ? 'bg-rose-500'
                          : s.utilization >= 60
                            ? 'bg-amber-500'
                            : 'bg-teal-600',
                      )}
                      style={{ width: `${Math.min(s.utilization, 100)}%` }}
                    />
                  </div>
                </div>
              ))
            )}
          </CardBody>
        </Card>
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader
            title="已分配地址"
            action={
              <Link
                to="/addresses"
                className="inline-flex items-center gap-0.5 text-xs font-medium text-teal-700 hover:text-teal-800"
              >
                地址台账 <ArrowUpRight className="h-3.5 w-3.5" />
              </Link>
            }
          />
          <CardBody className="space-y-1 !pt-2">
            {sampleIps.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted">暂无已分配地址</p>
            ) : (
              sampleIps.map((ip) => (
                <Link
                  key={ip.id}
                  to={`/addresses/${ip.id}`}
                  className="flex items-center justify-between gap-3 rounded-2xl px-2.5 py-2.5 transition hover:bg-[#f6f8f9]"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <Server className="h-3.5 w-3.5 text-muted" />
                      <span className="font-mono text-sm font-semibold text-ink-900">{ip.address}</span>
                    </div>
                    <div className="mt-0.5 truncate text-xs text-muted">
                      {ip.hostname ?? '—'} · {ip.device_name ?? '未绑定设备'}
                    </div>
                  </div>
                  <StatusBadge status={ip.status as IpStatus} />
                </Link>
              ))
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="最近操作" subtitle="分配 / 回收审计" />
          <CardBody className="space-y-2 !pt-2">
            {stats.recent_logs.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted">暂无操作记录</p>
            ) : (
              stats.recent_logs.map((log) => (
                <div
                  key={log.id}
                  className="flex items-start justify-between gap-3 rounded-2xl border border-black/[0.04] bg-[#fafbfc] px-3.5 py-2.5"
                >
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-sm font-semibold text-ink-900">{log.address}</span>
                      <SoftBadge tone="info">{log.action}</SoftBadge>
                    </div>
                    <div className="mt-0.5 text-xs text-muted">
                      {log.operator_name} · {log.detail}
                    </div>
                  </div>
                  <div className="shrink-0 text-[11px] text-muted">{log.created_at.slice(0, 10)}</div>
                </div>
              ))
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  )
}