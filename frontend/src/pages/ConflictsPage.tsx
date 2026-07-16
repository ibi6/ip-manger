import { useCallback, useEffect, useState } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { ConflictBadge, SoftBadge } from '@/components/ui/Badge'
import { EmptyState, ErrorBlock, LoadingBlock } from '@/components/ui/EmptyState'
import { api, ApiError, type ApiConflict } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import { formatDateTime } from '@/lib/format'
import type { ConflictType } from '@/types'

export function ConflictsPage() {
  const { canManageNetwork } = useAuth()
  const [filter, setFilter] = useState<'open' | 'all'>('open')
  const [list, setList] = useState<ApiConflict[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await api.conflicts(filter)
      setList(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }, [filter])

  useEffect(() => {
    void load()
  }, [load])

  const scan = async () => {
    try {
      const res = await api.scanConflicts()
      setToast(res.message)
      await load()
    } catch (e) {
      setToast(e instanceof ApiError ? e.message : '扫描失败')
    }
  }

  const resolve = async (id: number, address: string) => {
    try {
      await api.resolveConflict(id)
      setToast(`已标记 ${address} 冲突为已解决`)
      await load()
    } catch (e) {
      setToast(e instanceof ApiError ? e.message : '操作失败')
    }
  }

  return (
    <div>
      <PageHeader
        title="冲突检测"
        description="台账异常与【模拟】探测结果。simulate-scan 不会访问真实网络。"
        actions={
          <div className="flex flex-wrap gap-2">
            <Button
              size="sm"
              variant={filter === 'open' ? 'primary' : 'outline'}
              onClick={() => setFilter('open')}
            >
              未解决
            </Button>
            <Button
              size="sm"
              variant={filter === 'all' ? 'primary' : 'outline'}
              onClick={() => setFilter('all')}
            >
              全部
            </Button>
            {canManageNetwork ? (
              <Button size="sm" variant="secondary" onClick={() => void scan()}>
                模拟扫描（非真实）
              </Button>
            ) : null}
          </div>
        }
      />

      {toast ? (
        <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-900">
          {toast}
        </div>
      ) : null}

      <Card className="overflow-hidden">
        {loading ? (
          <LoadingBlock />
        ) : error ? (
          <ErrorBlock message={error} onRetry={load} />
        ) : list.length === 0 ? (
          <EmptyState title="没有冲突记录" description="切换到「全部」或执行模拟扫描。" />
        ) : (
          <ul className="divide-y divide-line">
            {list.map((c) => (
              <li
                key={c.id}
                className="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="min-w-0">
                  <div className="mb-1 flex flex-wrap items-center gap-2">
                    <ConflictBadge type={c.type as ConflictType} />
                    <SoftBadge tone={c.status === 'open' ? 'warn' : 'ok'}>
                      {c.status === 'open' ? '未解决' : '已解决'}
                    </SoftBadge>
                  </div>
                  <div className="font-mono text-sm font-semibold text-ink-900">{c.ip_address}</div>
                  <div className="text-xs text-muted">{c.subnet_cidr}</div>
                  <p className="mt-1 text-sm text-ink-800">{c.detail}</p>
                  <div className="mt-1 text-[11px] text-muted">
                    发现于 {formatDateTime(c.detected_at)}
                  </div>
                </div>
                {c.status === 'open' && canManageNetwork ? (
                  <Button size="sm" variant="outline" onClick={() => void resolve(c.id, c.ip_address)}>
                    标记已解决
                  </Button>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  )
}
