import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Search } from 'lucide-react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input, Select } from '@/components/ui/Input'
import { StatusBadge } from '@/components/ui/Badge'
import { EmptyState, ErrorBlock, LoadingBlock } from '@/components/ui/EmptyState'
import { api, ApiError, type ApiIp, type ApiSubnet } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import type { IpStatus } from '@/types'
import { deviceTypeLabel } from '@/lib/labels'

export function AddressesPage() {
  const { canManageNetwork } = useAuth()
  const [params] = useSearchParams()
  const [q, setQ] = useState('')
  const [subnetId, setSubnetId] = useState(params.get('subnet') ?? 'all')
  const [status, setStatus] = useState<'all' | IpStatus>('all')
  const [subnets, setSubnets] = useState<ApiSubnet[]>([])
  const [rows, setRows] = useState<ApiIp[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const pageSize = 50
  const [selected, setSelected] = useState<number[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const [subs, pageData] = await Promise.all([
        api.subnets(),
        api.ipsPage({
          subnet_id: subnetId === 'all' ? undefined : Number(subnetId),
          status: status === 'all' ? undefined : status,
          q: q || undefined,
          page,
          page_size: pageSize,
        }),
      ])
      setSubnets(subs)
      setRows(pageData.items)
      setTotal(pageData.total)
      setSelected([])
    } catch (e) {
      setError(e instanceof Error ? e.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [subnetId, status, page])

  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  const toggle = (id: number) => {
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  const toggleAll = () => {
    const releasable = rows
      .filter((ip) => ['allocated', 'reserved', 'disabled'].includes(ip.status) && !ip.is_network_or_broadcast)
      .map((ip) => ip.id)
    if (selected.length === releasable.length) setSelected([])
    else setSelected(releasable)
  }

  const onBatchRelease = async () => {
    if (!selected.length) {
      setMsg('请先勾选要回收的地址')
      return
    }
    if (!window.confirm(`确定批量回收 ${selected.length} 个地址？`)) return
    try {
      const res = await api.batchRelease(selected)
      setMsg(res.message)
      await load()
    } catch (e) {
      setMsg(e instanceof ApiError ? e.message : '批量回收失败')
    }
  }

  return (
    <div>
      <PageHeader
        title="地址台账"
        description="支持分页、筛选和批量回收。"
        actions={
          <div className="flex flex-wrap gap-2">
            {canManageNetwork ? (
              <Button size="sm" variant="outline" onClick={() => void onBatchRelease()}>
                批量回收({selected.length})
              </Button>
            ) : null}
            <Button
              size="sm"
              variant="outline"
              onClick={() =>
                void api
                  .downloadAuth(
                    api.exportIpsUrl(subnetId === 'all' ? undefined : Number(subnetId)),
                    'ip_addresses.csv',
                  )
                  .then(() => setMsg('已导出 CSV'))
                  .catch((e) => setMsg(e instanceof ApiError ? e.message : '导出失败'))
              }
            >
              导出 CSV
            </Button>
          </div>
        }
      />

      {msg ? (
        <div className="mb-4 rounded-xl border border-line bg-ink-50 px-4 py-2 text-sm">{msg}</div>
      ) : null}

      <Card className="mb-4 p-4">
        <div className="grid gap-3 md:grid-cols-4">
          <div className="relative md:col-span-2">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
            <Input
              className="pl-9"
              placeholder="IP / 主机名 / MAC / 设备 / 责任人"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  setPage(1)
                  void load()
                }
              }}
            />
          </div>
          <Select
            value={subnetId}
            onChange={(e) => {
              setPage(1)
              setSubnetId(e.target.value)
            }}
          >
            <option value="all">全部子网</option>
            {subnets.map((s) => (
              <option key={s.id} value={String(s.id)}>
                {s.name} ({s.cidr})
              </option>
            ))}
          </Select>
          <Select
            value={status}
            onChange={(e) => {
              setPage(1)
              setStatus(e.target.value as typeof status)
            }}
          >
            <option value="all">全部状态</option>
            <option value="free">空闲</option>
            <option value="allocated">已分配</option>
            <option value="reserved">预留</option>
            <option value="disabled">禁用</option>
          </Select>
        </div>
        <div className="mt-3">
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              setPage(1)
              void load()
            }}
          >
            查询
          </Button>
        </div>
      </Card>

      <Card className="overflow-hidden">
        {loading ? (
          <LoadingBlock />
        ) : error ? (
          <ErrorBlock message={error} onRetry={load} />
        ) : rows.length === 0 ? (
          <EmptyState title="没有匹配的地址" description="尝试清空筛选条件。" />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="border-b border-line bg-ink-50/70 text-xs uppercase tracking-wide text-muted">
                  <tr>
                    {canManageNetwork ? (
                      <th className="px-3 py-3">
                        <input type="checkbox" onChange={toggleAll} checked={selected.length > 0} />
                      </th>
                    ) : null}
                    <th className="px-4 py-3 font-medium">地址</th>
                    <th className="px-4 py-3 font-medium">子网</th>
                    <th className="px-4 py-3 font-medium">状态</th>
                    <th className="px-4 py-3 font-medium">主机 / MAC</th>
                    <th className="px-4 py-3 font-medium">设备</th>
                    <th className="px-4 py-3 font-medium">责任人</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((ip) => (
                    <tr key={ip.id} className="border-b border-line/70 hover:bg-teal-50/30">
                      {canManageNetwork ? (
                        <td className="px-3 py-3">
                          <input
                            type="checkbox"
                            disabled={
                              ip.is_network_or_broadcast ||
                              !['allocated', 'reserved', 'disabled'].includes(ip.status)
                            }
                            checked={selected.includes(ip.id)}
                            onChange={() => toggle(ip.id)}
                          />
                        </td>
                      ) : null}
                      <td className="px-4 py-3">
                        <Link
                          to={`/addresses/${ip.id}`}
                          className="font-mono font-semibold text-ink-900 hover:text-teal-700"
                        >
                          {ip.address}
                        </Link>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-muted">{ip.subnet_cidr}</td>
                      <td className="px-4 py-3">
                        <StatusBadge status={ip.status as IpStatus} />
                      </td>
                      <td className="px-4 py-3">
                        <div>{ip.hostname ?? '—'}</div>
                        <div className="font-mono text-xs text-muted">{ip.mac ?? ''}</div>
                      </td>
                      <td className="px-4 py-3">
                        <div>{ip.device_name ?? '—'}</div>
                        <div className="text-xs text-muted">
                          {ip.device_type
                            ? deviceTypeLabel[ip.device_type as keyof typeof deviceTypeLabel] ??
                              ip.device_type
                            : ''}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-muted">{ip.owner_name ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="flex items-center justify-between border-t border-line px-4 py-3 text-sm">
              <span className="text-muted">
                共 {total} 条 · 第 {page}/{totalPages} 页
              </span>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  上一页
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  下一页
                </Button>
              </div>
            </div>
          </>
        )}
      </Card>
    </div>
  )
}
