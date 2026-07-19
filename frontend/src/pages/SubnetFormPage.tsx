import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/Button'
import { Card, CardBody } from '@/components/ui/Card'
import { EmptyState, ErrorBlock, LoadingBlock } from '@/components/ui/EmptyState'
import { Field, Input, Select, Textarea } from '@/components/ui/Input'
import { api, ApiError, type ApiSite } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'

export function SubnetFormPage() {
  const { canManageNetwork, user } = useAuth()
  const navigate = useNavigate()
  const [sites, setSites] = useState<ApiSite[]>([])
  const [sitesState, setSitesState] = useState<'loading' | 'ready' | 'error'>('loading')
  const [sitesError, setSitesError] = useState('')
  const [name, setName] = useState('')
  const [cidr, setCidr] = useState('10.30.1.0/28')
  const [siteId, setSiteId] = useState('')
  const [gateway, setGateway] = useState('10.30.1.1')
  const [vlanId, setVlanId] = useState('30')
  const [purpose, setPurpose] = useState('办公终端')
  const [description, setDescription] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const loadSites = useCallback(async () => {
    setSitesState('loading')
    setSitesError('')
    try {
      const result = await api.sites()
      setSites(result)
      setSiteId((current) =>
        current && result.some((site) => String(site.id) === current)
          ? current
          : result[0]
            ? String(result[0].id)
            : '',
      )
      setSitesState('ready')
    } catch (loadError) {
      setSites([])
      setSitesError(loadError instanceof ApiError ? loadError.message : '站点加载失败，请稍后重试')
      setSitesState('error')
    }
  }, [])

  useEffect(() => {
    void loadSites()
  }, [loadSites])

  if (!canManageNetwork) {
    return (
      <Card className="p-8 text-center">
        <p className="text-ink-800">仅管理员 / 网络管理员可新建子网。</p>
        <Button className="mt-4" variant="outline" onClick={() => navigate('/subnets')}>
          返回
        </Button>
      </Card>
    )
  }

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!name.trim()) {
      setError('请填写子网名称')
      return
    }
    if (!siteId) {
      setError('请先选择所属站点')
      return
    }
    setSaving(true)
    setError('')
    try {
      const created = await api.createSubnet({
        name: name.trim(),
        cidr: cidr.trim(),
        site_id: Number(siteId),
        department_id: user?.departmentId,
        gateway: gateway.trim(),
        vlan_id: vlanId ? Number(vlanId) : null,
        purpose,
        description: description || null,
      })
      navigate(`/subnets/${created.id}`)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '创建失败')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="新建子网"
        description="后端使用 ipaddress 校验 CIDR 并自动生成地址池。演示建议 /28（16 个地址）。"
      />
      <Card>
        {sitesState === 'loading' ? (
          <LoadingBlock label="正在加载站点…" />
        ) : sitesState === 'error' ? (
          <ErrorBlock message={sitesError} onRetry={() => void loadSites()} />
        ) : sites.length === 0 ? (
          <EmptyState
            title="还没有可用站点"
            description="创建子网前需要先建立一个站点，用于归属和统计。"
            actionLabel="前往站点管理"
            onAction={() => navigate('/sites')}
          />
        ) : (
          <CardBody>
            <form className="grid gap-4 md:grid-cols-2" onSubmit={onSubmit}>
              <Field label="名称 *">
                <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="办公网-B" />
              </Field>
              <Field label="CIDR *" hint="支持 /16–/30，地址数 ≤ 1024">
                <Input value={cidr} onChange={(e) => setCidr(e.target.value)} className="font-mono" />
              </Field>
              <Field label="所属站点">
                <Select value={siteId} onChange={(e) => setSiteId(e.target.value)} disabled={saving}>
                  {sites.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="网关">
                <Input value={gateway} onChange={(e) => setGateway(e.target.value)} className="font-mono" />
              </Field>
              <Field label="VLAN ID">
                <Input value={vlanId} onChange={(e) => setVlanId(e.target.value)} />
              </Field>
              <Field label="用途">
                <Input value={purpose} onChange={(e) => setPurpose(e.target.value)} />
              </Field>
              <div className="md:col-span-2">
                <Field label="说明">
                  <Textarea rows={3} value={description} onChange={(e) => setDescription(e.target.value)} />
                </Field>
              </div>
              {error ? (
                <div className="md:col-span-2 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
                  {error}
                </div>
              ) : null}
              <div className="md:col-span-2 flex gap-2">
                <Button type="submit" disabled={saving}>
                  {saving ? '创建中…' : '创建子网'}
                </Button>
                <Button type="button" variant="outline" onClick={() => navigate(-1)}>
                  取消
                </Button>
              </div>
            </form>
          </CardBody>
        )}
      </Card>
    </div>
  )
}
