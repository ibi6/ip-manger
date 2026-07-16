import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/Button'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { SoftBadge, StatusBadge } from '@/components/ui/Badge'
import { ErrorBlock, LoadingBlock } from '@/components/ui/EmptyState'
import { Field, Input, Select } from '@/components/ui/Input'
import { api, ApiError, type ApiDevice, type ApiIp, type ApiLog } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import { deviceTypeLabel, ipStatusLabel } from '@/lib/labels'
import { formatDateTime } from '@/lib/format'
import type { DeviceType, IpStatus } from '@/types'

export function AddressDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { canAllocate, canManageNetwork } = useAuth()
  const [ip, setIp] = useState<ApiIp | null>(null)
  const [logs, setLogs] = useState<ApiLog[]>([])
  const [devices, setDevices] = useState<ApiDevice[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')
  const [showAlloc, setShowAlloc] = useState(false)
  const [hostname, setHostname] = useState('')
  const [mac, setMac] = useState('')
  const [deviceName, setDeviceName] = useState('')
  const [deviceType, setDeviceType] = useState<DeviceType>('pc')
  const [deviceId, setDeviceId] = useState('')
  const [expireAt, setExpireAt] = useState('')
  const [remark, setRemark] = useState('')

  const load = useCallback(async () => {
    if (!id) return
    setLoading(true)
    setError('')
    try {
      const data = await api.ip(Number(id))
      setIp(data)
      const [l, devs] = await Promise.all([
        api.logs(data.address),
        api.devices().catch(() => [] as ApiDevice[]),
      ])
      setLogs(l)
      setDevices(devs)
    } catch (e) {
      setError(e instanceof Error ? e.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    void load()
  }, [load])

  if (loading) return <LoadingBlock />
  if (error || !ip) return <ErrorBlock message={error || '未找到地址'} onRetry={load} />

  const openAlloc = () => {
    setHostname(ip.hostname || `host-${ip.address.split('.').pop()}`)
    setMac(ip.mac || '')
    setDeviceName(ip.device_name || '')
    setDeviceType((ip.device_type as DeviceType) || 'pc')
    setDeviceId(ip.device_id ? String(ip.device_id) : '')
    setExpireAt('')
    setRemark(ip.remark || '')
    setShowAlloc(true)
  }

  const pickDevice = (idStr: string) => {
    setDeviceId(idStr)
    if (!idStr) return
    const d = devices.find((x) => String(x.id) === idStr)
    if (!d) return
    setDeviceName(d.name)
    if (d.mac) setMac(d.mac)
    if (d.device_type) setDeviceType(d.device_type as DeviceType)
  }

  const confirmAllocate = async () => {
    try {
      await api.allocate(ip.id, {
        hostname: hostname || null,
        mac: mac || null,
        device_name: deviceName || null,
        device_type: deviceType,
        device_id: deviceId ? Number(deviceId) : null,
        expire_at: expireAt || null,
        remark: remark || null,
      })
      setToast('分配成功')
      setShowAlloc(false)
      await load()
    } catch (e) {
      setToast(e instanceof ApiError ? e.message : '分配失败')
    }
  }

  const release = async () => {
    try {
      await api.release(ip.id)
      setToast('已回收为空闲')
      await load()
    } catch (e) {
      setToast(e instanceof ApiError ? e.message : '回收失败')
    }
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => navigate(-1)}
        className="mb-4 inline-flex items-center gap-1 text-sm text-muted hover:text-ink-800"
      >
        <ArrowLeft className="h-4 w-4" /> 返回
      </button>

      <PageHeader
        title={ip.address}
        description={ip.subnet_cidr}
        actions={
          <>
            {ip.status === 'free' && canAllocate ? (
              <Button onClick={openAlloc}>分配</Button>
            ) : null}
            {(ip.status === 'allocated' || ip.status === 'reserved') && canManageNetwork ? (
              <Button variant="outline" onClick={() => void release()}>
                回收
              </Button>
            ) : null}
            {ip.status === 'free' && canManageNetwork && !ip.is_network_or_broadcast ? (
              <Button
                variant="outline"
                onClick={async () => {
                  try {
                    await api.disableIp(ip.id)
                    setToast('已禁用')
                    await load()
                  } catch (e) {
                    setToast(e instanceof ApiError ? e.message : '禁用失败')
                  }
                }}
              >
                禁用
              </Button>
            ) : null}
            {ip.status === 'disabled' && canManageNetwork ? (
              <Button
                variant="outline"
                onClick={async () => {
                  try {
                    await api.enableIp(ip.id)
                    setToast('已启用为空闲')
                    await load()
                  } catch (e) {
                    setToast(e instanceof ApiError ? e.message : '启用失败')
                  }
                }}
              >
                启用
              </Button>
            ) : null}
            {ip.status === 'free' && canManageNetwork && !ip.is_network_or_broadcast ? (
              <Button
                variant="ghost"
                onClick={async () => {
                  try {
                    await api.reserve(ip.id)
                    setToast('已预留')
                    await load()
                  } catch (e) {
                    setToast(e instanceof ApiError ? e.message : '预留失败')
                  }
                }}
              >
                预留
              </Button>
            ) : null}
            <Button variant="ghost" onClick={() => navigate(`/subnets/${ip.subnet_id}`)}>
              打开子网
            </Button>
          </>
        }
      />

      {toast ? (
        <div className="mb-4 rounded-xl border border-teal-200 bg-teal-50 px-4 py-2 text-sm text-teal-900">
          {toast}
        </div>
      ) : null}

      <div className="mb-4 flex flex-wrap gap-2">
        <StatusBadge status={ip.status as IpStatus} />
        {ip.device_type ? (
          <SoftBadge>
            {deviceTypeLabel[ip.device_type as keyof typeof deviceTypeLabel] ?? ip.device_type}
          </SoftBadge>
        ) : null}
        {ip.device_id ? <SoftBadge tone="info">设备#{ip.device_id}</SoftBadge> : null}
        {ip.expire_at ? <SoftBadge tone="warn">到期 {ip.expire_at}</SoftBadge> : null}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader
            title="地址详情"
            subtitle={`状态：${ipStatusLabel[ip.status as IpStatus] ?? ip.status}`}
          />
          <CardBody>
            <dl className="grid gap-3 sm:grid-cols-2">
              {[
                ['IP 地址', ip.address],
                ['所属子网', ip.subnet_cidr],
                ['主机名', ip.hostname ?? '—'],
                ['MAC', ip.mac ?? '—'],
                ['设备', ip.device_name ?? '—'],
                [
                  '设备类型',
                  ip.device_type
                    ? deviceTypeLabel[ip.device_type as keyof typeof deviceTypeLabel] ?? ip.device_type
                    : '—',
                ],
                ['责任人', ip.owner_name ?? '—'],
                ['部门', ip.department_name ?? '—'],
                ['分配时间', formatDateTime(ip.allocated_at)],
                ['到期日', ip.expire_at ?? '—'],
                ['备注', ip.remark ?? '—'],
              ].map(([k, v]) => (
                <div key={k} className="rounded-xl border border-line/80 bg-ink-50/30 px-3 py-2.5">
                  <dt className="text-[11px] font-medium text-muted">{k}</dt>
                  <dd className="mt-0.5 break-all text-sm font-medium text-ink-900">{v}</dd>
                </div>
              ))}
            </dl>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="相关操作记录" />
          <CardBody className="space-y-2">
            {logs.length === 0 ? (
              <p className="text-sm text-muted">暂无日志</p>
            ) : (
              logs.map((l) => (
                <div key={l.id} className="rounded-xl border border-line px-3 py-2 text-sm">
                  <div className="font-medium">{l.action}</div>
                  <div className="text-xs text-muted">
                    {l.operator_name} · {formatDateTime(l.created_at)}
                  </div>
                  <div className="mt-1 text-xs text-ink-700">{l.detail}</div>
                </div>
              ))
            )}
          </CardBody>
        </Card>
      </div>

      {showAlloc ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-ink-950/40"
            aria-label="关闭"
            onClick={() => setShowAlloc(false)}
          />
          <Card className="relative z-10 w-full max-w-lg p-0 shadow-2xl">
            <CardHeader title={`分配 ${ip.address}`} subtitle="可关联设备台账" />
            <CardBody className="grid gap-3 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <Field label="关联设备（可选）">
                  <Select value={deviceId} onChange={(e) => pickDevice(e.target.value)}>
                    <option value="">不关联，手动填</option>
                    {devices.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                        {d.bound_ip ? `（${d.bound_ip}）` : ''}
                      </option>
                    ))}
                  </Select>
                </Field>
              </div>
              <Field label="主机名">
                <Input value={hostname} onChange={(e) => setHostname(e.target.value)} />
              </Field>
              <Field label="MAC">
                <Input value={mac} onChange={(e) => setMac(e.target.value)} />
              </Field>
              <Field label="设备名称">
                <Input value={deviceName} onChange={(e) => setDeviceName(e.target.value)} />
              </Field>
              <Field label="类型">
                <Select value={deviceType} onChange={(e) => setDeviceType(e.target.value as DeviceType)}>
                  {(Object.keys(deviceTypeLabel) as DeviceType[]).map((k) => (
                    <option key={k} value={k}>
                      {deviceTypeLabel[k]}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="到期日">
                <Input type="date" value={expireAt} onChange={(e) => setExpireAt(e.target.value)} />
              </Field>
              <div className="sm:col-span-2">
                <Field label="备注">
                  <Input value={remark} onChange={(e) => setRemark(e.target.value)} />
                </Field>
              </div>
              <div className="sm:col-span-2 flex justify-end gap-2">
                <Button variant="outline" onClick={() => setShowAlloc(false)}>
                  取消
                </Button>
                <Button onClick={() => void confirmAllocate()}>确认分配</Button>
              </div>
            </CardBody>
          </Card>
        </div>
      ) : null}
    </div>
  )
}
