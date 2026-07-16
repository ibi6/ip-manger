import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Plus, Search } from 'lucide-react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input, Select } from '@/components/ui/Input'
import { SoftBadge } from '@/components/ui/Badge'
import { EmptyState, ErrorBlock, LoadingBlock } from '@/components/ui/EmptyState'
import { api, ApiError, type ApiSite, type ApiSubnet } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import { cn } from '@/lib/cn'

export function SubnetsPage() {
  const { canManageNetwork } = useAuth()
  const navigate = useNavigate()
  const [q, setQ] = useState('')
  const [siteId, setSiteId] = useState('all')
  const [sites, setSites] = useState<ApiSite[]>([])
  const [rows, setRows] = useState<ApiSubnet[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const [s, subs] = await Promise.all([
        api.sites(),
        api.subnets({
          site_id: siteId === 'all' ? undefined : Number(siteId),
          q: q || undefined,
        }),
      ])
      setSites(s)
      setRows(subs)
    } catch (e) {
      setError(e instanceof Error ? e.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }

  const onArchive = async (s: ApiSubnet) => {
    if (!window.confirm(`归档子网 ${s.name}（${s.cidr}）？有已分配地址时会失败。`)) return
    try {
      // 第一次 delete 接口会归档；已归档再用 archive 也行
      const res =
        s.status === 'archived'
          ? await api.deleteSubnet(s.id)
          : await api.archiveSubnet(s.id)
      setMsg(res.message)
      await load()
    } catch (e) {
      setMsg(e instanceof ApiError ? e.message : '操作失败')
    }
  }

  useEffect(() => {
    void load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [siteId])

  const filtered = useMemo(() => {
    if (!q) return rows
    const ql = q.toLowerCase()
    return rows.filter(
      (s) =>
        s.name.toLowerCase().includes(ql) ||
        s.cidr.toLowerCase().includes(ql) ||
        s.purpose.toLowerCase().includes(ql),
    )
  }, [rows, q])

  return (
    <div>
      <PageHeader
        title="子网管理"
        description="以 CIDR 管理地址池。点击子网进入地址明细，可分配 / 回收。"
        actions={
          canManageNetwork ? (
            <Button onClick={() => navigate('/subnets/new')}>
              <Plus className="h-4 w-4" /> 新建子网
            </Button>
          ) : null
        }
      />

      {msg ? (
        <div className="mb-4 rounded-xl border border-line bg-ink-50 px-4 py-2 text-sm">{msg}</div>
      ) : null}

      <Card className="mb-4 p-4">
        <div className="grid gap-3 md:grid-cols-3">
          <div className="relative md:col-span-2">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
            <Input
              className="pl-9"
              placeholder="搜索名称 / CIDR / 用途"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && void load()}
            />
          </div>
          <Select value={siteId} onChange={(e) => setSiteId(e.target.value)}>
            <option value="all">全部站点</option>
            {sites.map((s) => (
              <option key={s.id} value={String(s.id)}>
                {s.name}
              </option>
            ))}
          </Select>
        </div>
        <div className="mt-3">
          <Button size="sm" variant="outline" onClick={() => void load()}>
            刷新
          </Button>
        </div>
      </Card>

      <Card className="overflow-hidden">
        {loading ? (
          <LoadingBlock label="正在拉取子网…" />
        ) : error ? (
          <ErrorBlock message={error} onRetry={load} />
        ) : filtered.length === 0 ? (
          <EmptyState
            title="暂无子网"
            description="调整筛选，或新建一条 /28 演示子网。"
            actionLabel={canManageNetwork ? '新建子网' : undefined}
            onAction={canManageNetwork ? () => navigate('/subnets/new') : undefined}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-line bg-ink-50/70 text-xs uppercase tracking-wide text-muted">
                <tr>
                  <th className="px-4 py-3 font-medium">子网</th>
                  <th className="px-4 py-3 font-medium">站点</th>
                  <th className="px-4 py-3 font-medium">VLAN</th>
                  <th className="px-4 py-3 font-medium">用途 / 部门</th>
                  <th className="px-4 py-3 font-medium">利用率</th>
                  <th className="px-4 py-3 font-medium">空闲</th>
                  {canManageNetwork ? <th className="px-4 py-3 font-medium">操作</th> : null}
                </tr>
              </thead>
              <tbody>
                {filtered.map((s) => (
                  <tr key={s.id} className="border-b border-line/70 transition hover:bg-teal-50/30">
                    <td className="px-4 py-3">
                      <Link to={`/subnets/${s.id}`} className="group block">
                        <div className="font-medium text-ink-900 group-hover:text-teal-700">{s.name}</div>
                        <div className="font-mono text-xs text-muted">{s.cidr}</div>
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-muted">{s.site_name}</td>
                    <td className="px-4 py-3">
                      {s.vlan_id != null ? <SoftBadge>VLAN {s.vlan_id}</SoftBadge> : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <div>{s.purpose}</div>
                      <div className="text-xs text-muted">{s.department_name}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-16 overflow-hidden rounded-full bg-ink-50">
                          <div
                            className={cn(
                              'h-full rounded-full',
                              s.utilization >= 80
                                ? 'bg-rose-500'
                                : s.utilization >= 60
                                  ? 'bg-amber-500'
                                  : 'bg-teal-600',
                            )}
                            style={{ width: `${s.utilization}%` }}
                          />
                        </div>
                        <span className="text-xs font-semibold">{s.utilization}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 font-medium text-emerald-700">{s.free_ips}</td>
                    {canManageNetwork ? (
                      <td className="px-4 py-3">
                        <Button size="sm" variant="ghost" onClick={() => void onArchive(s)}>
                          {s.status === 'archived' ? '永久删除' : '归档'}
                        </Button>
                      </td>
                    ) : null}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
