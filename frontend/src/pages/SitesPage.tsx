import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { MapPin } from 'lucide-react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/Button'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { SoftBadge } from '@/components/ui/Badge'
import { Field, Input, Textarea } from '@/components/ui/Input'
import { ErrorBlock, LoadingBlock } from '@/components/ui/EmptyState'
import { api, ApiError, type ApiSite, type ApiSubnet } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'

export function SitesPage() {
  const { canManageNetwork } = useAuth()
  const [sites, setSites] = useState<ApiSite[]>([])
  const [subnets, setSubnets] = useState<ApiSubnet[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [location, setLocation] = useState('')
  const [remark, setRemark] = useState('')
  const [saving, setSaving] = useState(false)

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const [s, subs] = await Promise.all([api.sites(), api.subnets()])
      setSites(s)
      setSubnets(subs)
    } catch (e) {
      setError(e instanceof Error ? e.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const onCreate = async (e: FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setMsg('')
    try {
      await api.createSite({
        name: name.trim(),
        code: code.trim().toUpperCase(),
        location: location.trim(),
        remark: remark.trim() || null,
      })
      setMsg('站点已添加')
      setName('')
      setCode('')
      setLocation('')
      setRemark('')
      setShowForm(false)
      await load()
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : '添加失败')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <LoadingBlock />
  if (error) return <ErrorBlock message={error} onRetry={load} />

  return (
    <div>
      <PageHeader
        title="站点管理"
        description="机房 / 园区 / 分支。每个站点下面再挂子网。"
        actions={
          canManageNetwork ? (
            <Button size="sm" onClick={() => setShowForm((v) => !v)}>
              {showForm ? '收起' : '新建站点'}
            </Button>
          ) : null
        }
      />

      {msg ? (
        <div className="mb-4 rounded-xl border border-line bg-ink-50 px-4 py-2 text-sm">{msg}</div>
      ) : null}

      {showForm && canManageNetwork ? (
        <Card className="mb-6">
          <CardHeader title="新建站点" />
          <CardBody>
            <form className="grid gap-3 sm:grid-cols-2" onSubmit={onCreate}>
              <Field label="名称">
                <Input value={name} onChange={(e) => setName(e.target.value)} required placeholder="比如 二号机房" />
              </Field>
              <Field label="编码" hint="唯一，英文数字">
                <Input value={code} onChange={(e) => setCode(e.target.value)} required placeholder="IDC2" />
              </Field>
              <Field label="位置">
                <Input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="大楼/楼层" />
              </Field>
              <div className="sm:col-span-2">
                <Field label="备注">
                  <Textarea rows={2} value={remark} onChange={(e) => setRemark(e.target.value)} />
                </Field>
              </div>
              <div className="sm:col-span-2">
                <Button type="submit" disabled={saving}>
                  {saving ? '保存中…' : '保存'}
                </Button>
              </div>
            </form>
          </CardBody>
        </Card>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {sites.map((site) => {
          const subs = subnets.filter((s) => s.site_id === site.id)
          return (
            <Card key={site.id} className="p-5">
              <div className="mb-3 flex items-start justify-between gap-2">
                <div>
                  <div className="font-display text-lg font-semibold text-ink-900">{site.name}</div>
                  <SoftBadge>{site.code}</SoftBadge>
                </div>
                <div className="rounded-xl bg-ink-50 p-2 text-ink-700">
                  <MapPin className="h-4 w-4" />
                </div>
              </div>
              <p className="text-sm text-muted">{site.location}</p>
              {site.remark ? <p className="mt-2 text-xs text-muted">{site.remark}</p> : null}
              <div className="mt-4 border-t border-line pt-3">
                <div className="mb-2 text-xs font-medium text-muted">
                  下属子网 · {site.subnet_count || subs.length}
                </div>
                <div className="space-y-1.5">
                  {subs.map((s) => (
                    <Link
                      key={s.id}
                      to={`/subnets/${s.id}`}
                      className="flex items-center justify-between rounded-lg px-2 py-1.5 text-sm hover:bg-ink-50"
                    >
                      <span className="truncate">{s.name}</span>
                      <span className="font-mono text-xs text-muted">{s.cidr}</span>
                    </Link>
                  ))}
                  {subs.length === 0 ? (
                    <p className="px-2 text-xs text-muted">还没有子网，去「子网管理」里加。</p>
                  ) : null}
                </div>
              </div>
              <CardBody className="!px-0 !pb-0 !pt-3">
                <Link to="/subnets" className="text-sm text-teal-700 hover:underline">
                  打开子网列表 →
                </Link>
              </CardBody>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
