import { useEffect, useState, type FormEvent } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/Button'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { Field, Input, Select } from '@/components/ui/Input'
import { SoftBadge } from '@/components/ui/Badge'
import { EmptyState, ErrorBlock, LoadingBlock } from '@/components/ui/EmptyState'
import { api, ApiError, type ApiDevice } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { deviceTypeLabel } from '@/lib/labels'
import type { DeviceType } from '@/types'

const emptyForm = {
  name: '',
  deviceType: 'pc' as DeviceType,
  mac: '',
  location: '',
  remark: '',
}

export function DevicesPage() {
  const { canManageNetwork, canAllocate } = useAuth()
  const [list, setList] = useState<ApiDevice[]>([])
  const [q, setQ] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')
  const [form, setForm] = useState(emptyForm)
  const [editId, setEditId] = useState<number | null>(null)
  const [saving, setSaving] = useState(false)

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      setList(await api.devices(q || undefined))
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

  const resetForm = () => {
    setForm(emptyForm)
    setEditId(null)
  }

  const startEdit = (d: ApiDevice) => {
    setEditId(d.id)
    setForm({
      name: d.name,
      deviceType: (d.device_type as DeviceType) || 'pc',
      mac: d.mac || '',
      location: d.location || '',
      remark: d.remark || '',
    })
  }

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setMsg('')
    const body = {
      name: form.name.trim(),
      device_type: form.deviceType,
      mac: form.mac || null,
      location: form.location || null,
      remark: form.remark || null,
    }
    try {
      if (editId != null) {
        await api.updateDevice(editId, body)
        setMsg('已保存修改')
      } else {
        await api.createDevice(body)
        setMsg('设备已登记')
      }
      resetForm()
      await load()
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : '保存失败')
    } finally {
      setSaving(false)
    }
  }

  const onDelete = async (id: number) => {
    if (!window.confirm('确定删除这台设备？已绑定分配中 IP 时会失败。')) return
    try {
      await api.deleteDevice(id)
      setMsg('已删除')
      if (editId === id) resetForm()
      await load()
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : '删除失败')
    }
  }

  const canWrite = canManageNetwork || canAllocate

  return (
    <div>
      <PageHeader
        title="设备台账"
        description="登记设备后，分配 IP 时可直接关联。绑定了已分配地址的设备不能删。"
        actions={
          <Button
            size="sm"
            variant="outline"
            onClick={() =>
              void api
                .downloadAuth(api.exportDevicesUrl(), 'devices.csv')
                .then(() => setMsg('已导出设备 CSV'))
                .catch((e) => setMsg(e instanceof ApiError ? e.message : '导出失败'))
            }
          >
            导出 CSV
          </Button>
        }
      />

      {msg ? (
        <div className="mb-4 rounded-xl border border-line bg-ink-50 px-4 py-2 text-sm">{msg}</div>
      ) : null}

      <Card className="mb-4 p-4">
        <div className="flex flex-wrap gap-2">
          <Input
            className="max-w-xs"
            placeholder="搜名称 / MAC / 位置"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && void load()}
          />
          <Button size="sm" variant="outline" onClick={() => void load()}>
            查询
          </Button>
        </div>
      </Card>

      <div className="grid gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-3 overflow-hidden">
          {loading ? (
            <LoadingBlock />
          ) : error ? (
            <ErrorBlock message={error} onRetry={load} />
          ) : list.length === 0 ? (
            <EmptyState title="还没有设备" description="右侧可以先登记几台。" />
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="border-b border-line bg-ink-50/80 text-xs text-muted">
                  <tr>
                    <th className="px-4 py-3">名称</th>
                    <th className="px-4 py-3">类型</th>
                    <th className="px-4 py-3">MAC</th>
                    <th className="px-4 py-3">位置 / 绑定 IP</th>
                    <th className="px-4 py-3">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {list.map((d) => (
                    <tr key={d.id} className="border-b border-line/70">
                      <td className="px-4 py-3 font-medium">{d.name}</td>
                      <td className="px-4 py-3">
                        <SoftBadge>
                          {deviceTypeLabel[d.device_type as DeviceType] ?? d.device_type}
                        </SoftBadge>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs">{d.mac ?? '—'}</td>
                      <td className="px-4 py-3 text-xs text-muted">
                        {d.location ?? '—'}
                        {d.bound_ip ? ` · ${d.bound_ip}` : ' · 未绑定'}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {canManageNetwork ? (
                            <>
                              <Button size="sm" variant="outline" onClick={() => startEdit(d)}>
                                编辑
                              </Button>
                              <Button size="sm" variant="ghost" onClick={() => void onDelete(d.id)}>
                                删除
                              </Button>
                            </>
                          ) : (
                            '—'
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        {canWrite ? (
          <Card className="lg:col-span-2">
            <CardHeader
              title={editId != null ? `编辑设备 #${editId}` : '登记设备'}
              action={
                editId != null ? (
                  <Button size="sm" variant="ghost" onClick={resetForm}>
                    取消编辑
                  </Button>
                ) : null
              }
            />
            <CardBody>
              <form className="space-y-3" onSubmit={onSubmit}>
                <Field label="设备名称">
                  <Input
                    value={form.name}
                    onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                    required
                  />
                </Field>
                <Field label="类型">
                  <Select
                    value={form.deviceType}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, deviceType: e.target.value as DeviceType }))
                    }
                  >
                    {(Object.keys(deviceTypeLabel) as DeviceType[]).map((k) => (
                      <option key={k} value={k}>
                        {deviceTypeLabel[k]}
                      </option>
                    ))}
                  </Select>
                </Field>
                <Field label="MAC（可选）">
                  <Input
                    value={form.mac}
                    onChange={(e) => setForm((f) => ({ ...f, mac: e.target.value }))}
                    placeholder="AA:BB:CC:DD:EE:FF"
                  />
                </Field>
                <Field label="位置（可选）">
                  <Input
                    value={form.location}
                    onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
                  />
                </Field>
                <Field label="备注（可选）">
                  <Input
                    value={form.remark}
                    onChange={(e) => setForm((f) => ({ ...f, remark: e.target.value }))}
                  />
                </Field>
                <Button type="submit" className="w-full" disabled={saving}>
                  {saving ? '保存中…' : editId != null ? '保存修改' : '登记'}
                </Button>
              </form>
            </CardBody>
          </Card>
        ) : null}
      </div>
    </div>
  )
}
