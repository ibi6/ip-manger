import { useEffect, useState } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { SoftBadge } from '@/components/ui/Badge'
import { EmptyState, ErrorBlock, LoadingBlock } from '@/components/ui/EmptyState'
import { api, type ApiLog } from '@/lib/api'

export function LogsPage() {
  const [list, setList] = useState<ApiLog[]>([])
  const [address, setAddress] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      setList(await api.logs(address.trim() || undefined))
    } catch (e) {
      setError(e instanceof Error ? e.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div>
      <PageHeader
        title="操作日志"
        description="记录分配、回收、预留等操作。可以按 IP 过滤。"
      />
      <Card className="mb-4 flex flex-wrap items-center gap-2 p-4">
        <Input
          className="max-w-xs"
          placeholder="例如 10.10.1.2"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && void load()}
        />
        <Button size="sm" variant="outline" onClick={() => void load()}>
          查询
        </Button>
      </Card>

      <Card className="overflow-hidden">
        {loading ? (
          <LoadingBlock />
        ) : error ? (
          <ErrorBlock message={error} onRetry={load} />
        ) : list.length === 0 ? (
          <EmptyState title="暂无日志" />
        ) : (
          <ul className="divide-y divide-line">
            {list.map((log) => (
              <li key={log.id} className="flex flex-wrap items-start justify-between gap-3 px-5 py-3">
                <div>
                  <div className="mb-1 flex flex-wrap items-center gap-2">
                    <span className="font-mono text-sm font-semibold">{log.address}</span>
                    <SoftBadge tone="info">{log.action}</SoftBadge>
                  </div>
                  <div className="text-sm text-ink-800">{log.detail}</div>
                  <div className="mt-1 text-xs text-muted">
                    {log.operator_name} · {log.created_at.slice(0, 19).replace('T', ' ')}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  )
}
