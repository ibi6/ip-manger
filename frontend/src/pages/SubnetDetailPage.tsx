import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/Button'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { SoftBadge, StatusBadge } from '@/components/ui/Badge'
import { ErrorBlock, LoadingBlock } from '@/components/ui/EmptyState'
import { Field, Input, Select } from '@/components/ui/Input'
import { api, ApiError, type ApiDevice, type ApiIp, type ApiSubnet } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import type { DeviceType, IpStatus } from '@/types'
import { deviceTypeLabel } from '@/lib/labels'

export function SubnetDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { canAllocate, canManageNetwork } = useAuth()
  const [subnet, setSubnet] = useState<ApiSubnet | null>(null)
  const [ips, setIps] = useState<ApiIp[]>([])
  const [devices, setDevices] = useState<ApiDevice[]>([])
  const [statusFilter, setStatusFilter] = useState<'all' | IpStatus>('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [toast, setToast] = useState('')
  const [allocTarget, setAllocTarget] = useState<ApiIp | null>(null)
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
      const [s, list, devs] = await Promise.all([
        api.subnet(Number(id)),
        api.ips({ subnet_id: Number(id) }),
        api.devices().catch(() => [] as ApiDevice[]),
      ])
      setSubnet(s)
      setIps(list)
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
  if (error || !subnet) {
    return <ErrorBlock message={error || '未找到子网'} onRetry={load} />
  }

  const filtered = ips.filter((i) => (statusFilter === 'all' ? true : i.status === statusFilter))

  const confirmAllocate = async () => {
    if (!allocTarget) return
    try {
      await api.allocate(allocTarget.id, {
        hostname: hostname || null,
        mac: mac || null,
        device_name: deviceName || null,
        device_type: deviceType,
        device_id: deviceId ? Number(deviceId) : null,
        expire_at: expireAt || null,
        remark: remark || null,
      })
      setToast(`已分配 ${allocTarget.address}`)
      setAllocTarget(null)
      await load()
    } catch (e) {
      setToast(e instanceof ApiError ? e.message : '分配失败')
    }
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

  const release = async (ip: ApiIp) => {
    try {
      await api.release(ip.id)
      setToast(`已回收 ${ip.address}`)
      await load()
    } catch (e) {
      setToast(e instanceof ApiError ? e.message : '回收失败')
    }
  }

  const reserve = async (ip: ApiIp) => {
    try {
      await api.reserve(ip.id)
      setToast(`已预留 ${ip.address}`)
      await load()
    } catch (e) {
      setToast(e instanceof ApiError ? e.message : '预留失败')
    }
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => navigate('/subnets')}
        className="mb-4 inline-flex items-center gap-1 text-sm text-muted hover:text-ink-800"
      >
        <ArrowLeft className="h-4 w-4" /> 返回子网列表
      </button>

      <PageHeader
        title={subnet.name}
        description={`${subnet.cidr} · 网关 ${subnet.gateway} · ${subnet.site_name}`}
        actions={
          <>
            {canAllocate ? (
              <Button
                onClick={async () => {
                  try {
                    const res = await api.allocateNext(subnet.id, {
                      hostname: `auto-${Date.now().toString().slice(-4)}`,
                      device_name: '自动分配',
                      device_type: 'pc',
                    })
                    setToast(`已自动分配 ${res.address}`)
                    await load()
                  } catch (e) {
                    setToast(e instanceof ApiError ? e.message : '自动分配失败')
                  }
                }}
              >
                分配下一空闲
              </Button>
            ) : null}
            <Button variant="outline" onClick={() => navigate(`/addresses?subnet=${subnet.id}`)}>
              在台账中筛选
            </Button>
          </>
        }
      />

      {toast ? (
        <div className="mb-4 rounded-xl border border-teal-200 bg-teal-50 px-4 py-2 text-sm text-teal-900">
          {toast}
        </div>
      ) : null}

      <div className="mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {[
          ['总量', subnet.total_ips],
          ['已分配', subnet.used_ips],
          ['空闲', subnet.free_ips],
          ['预留', subnet.reserved_ips],
          ['利用率', `${subnet.utilization}%`],
        ].map(([k, v]) => (
          <Card key={k as string} className="px-4 py-3">
            <div className="text-xs text-muted">{k}</div>
            <div className="font-display text-xl font-semibold text-ink-900">{v}</div>
          </Card>
        ))}
      </div>

      <div className="mb-4 flex flex-wrap items-center gap-2">
        <SoftBadge>VLAN {subnet.vlan_id ?? '—'}</SoftBadge>
        <SoftBadge>{subnet.purpose}</SoftBadge>
        <SoftBadge>{subnet.department_name}</SoftBadge>
        <Select
          className="ml-auto w-40"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as typeof statusFilter)}
        >
          <option value="all">全部状态</option>
          <option value="free">空闲</option>
          <option value="allocated">已分配</option>
          <option value="reserved">预留</option>
          <option value="disabled">禁用</option>
        </Select>
      </div>

      <Card className="overflow-hidden">
        <CardHeader title="地址池" subtitle="由后端根据 CIDR 自动生成" />
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="border-y border-line bg-ink-50/70 text-xs text-muted">
              <tr>
                <th className="px-4 py-3 font-medium">IP</th>
                <th className="px-4 py-3 font-medium">状态</th>
                <th className="px-4 py-3 font-medium">主机 / 设备</th>
                <th className="px-4 py-3 font-medium">责任人</th>
                <th className="px-4 py-3 font-medium">操作</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((ip) => (
                <tr key={ip.id} className="border-b border-line/70">
                  <td className="px-4 py-3">
                    <Link
                      to={`/addresses/${ip.id}`}
                      className="font-mono font-semibold text-ink-900 hover:text-teal-700"
                    >
                      {ip.address}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={ip.status as IpStatus} />
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm">{ip.hostname ?? '—'}</div>
                    <div className="text-xs text-muted">{ip.device_name ?? ip.remark ?? ''}</div>
                  </td>
                  <td className="px-4 py-3 text-muted">{ip.owner_name ?? '—'}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {ip.status === 'free' && canAllocate ? (
                        <Button
                          size="sm"
                          onClick={() => {
                            setAllocTarget(ip)
                            setHostname('')
                            setMac('')
                            setDeviceName('')
                            setDeviceType('pc')
                            setDeviceId('')
                            setExpireAt('')
                            setRemark('')
                          }}
                        >
                          分配
                        </Button>
                      ) : null}
                      {ip.status === 'free' && canManageNetwork ? (
                        <Button size="sm" variant="outline" onClick={() => void reserve(ip)}>
                          预留
                        </Button>
                      ) : null}
                      {(ip.status === 'allocated' || ip.status === 'reserved') &&
                      canManageNetwork &&
                      !ip.is_network_or_broadcast ? (
                        <Button size="sm" variant="ghost" onClick={() => void release(ip)}>
                          回收
                        </Button>
                      ) : null}
                      {ip.status === 'free' && canManageNetwork && !ip.is_network_or_broadcast ? (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={async () => {
                            try {
                              await api.disableIp(ip.id)
                              setToast(`已禁用 ${ip.address}`)
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
                          size="sm"
                          variant="outline"
                          onClick={async () => {
                            try {
                              await api.enableIp(ip.id)
                              setToast(`已启用 ${ip.address}`)
                              await load()
                            } catch (e) {
                              setToast(e instanceof ApiError ? e.message : '启用失败')
                            }
                          }}
                        >
                          启用
                        </Button>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {allocTarget ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-ink-950/40"
            aria-label="关闭"
            onClick={() => setAllocTarget(null)}
          />
          <Card className="relative z-10 w-full max-w-lg p-0 shadow-2xl">
            <CardHeader title={`分配地址 ${allocTarget.address}`} subtitle="写入数据库" />
            <CardBody className="grid gap-3 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <Field label="关联设备台账（可选）" hint="选了会自动带出名称和 MAC">
                  <Select value={deviceId} onChange={(e) => pickDevice(e.target.value)}>
                    <option value="">不关联，手动填写</option>
                    {devices.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                        {d.bound_ip ? `（已占用 ${d.bound_ip}）` : ''}
                      </option>
                    ))}
                  </Select>
                </Field>
              </div>
              <Field label="主机名">
                <Input value={hostname} onChange={(e) => setHostname(e.target.value)} />
              </Field>
              <Field label="MAC">
                <Input value={mac} onChange={(e) => setMac(e.target.value)} placeholder="AA:BB:CC:DD:EE:FF" />
              </Field>
              <Field label="设备名称">
                <Input value={deviceName} onChange={(e) => setDeviceName(e.target.value)} />
              </Field>
              <Field label="设备类型">
                <Select value={deviceType} onChange={(e) => setDeviceType(e.target.value as DeviceType)}>
                  {(Object.keys(deviceTypeLabel) as DeviceType[]).map((k) => (
                    <option key={k} value={k}>
                      {deviceTypeLabel[k]}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="到期日（可选）">
                <Input type="date" value={expireAt} onChange={(e) => setExpireAt(e.target.value)} />
              </Field>
              <div className="sm:col-span-2">
                <Field label="备注">
                  <Input value={remark} onChange={(e) => setRemark(e.target.value)} />
                </Field>
              </div>
              <div className="sm:col-span-2 flex justify-end gap-2 pt-2">
                <Button variant="outline" onClick={() => setAllocTarget(null)}>
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
