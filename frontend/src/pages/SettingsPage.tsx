import { useRef, useState, type FormEvent } from 'react'
import { Download, Upload } from 'lucide-react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/Button'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { SoftBadge } from '@/components/ui/Badge'
import { Field, Input } from '@/components/ui/Input'
import { useAuth } from '@/lib/auth-context'
import { api, ApiError } from '@/lib/api'
import { demoAccounts, roleLabel } from '@/lib/labels'
import { productConfig } from '@/config/product'

const matrix = [
  { code: 'subnet:write', admin: '✓', net: '✓', dept: '—', view: '—' },
  { code: 'ip:allocate', admin: '✓', net: '✓', dept: '本部门空闲', view: '—' },
  { code: 'ip:release', admin: '✓', net: '✓', dept: '—', view: '—' },
  { code: 'conflict:manage', admin: '✓', net: '✓', dept: '只读', view: '只读' },
  { code: 'io:import', admin: '✓', net: '✓', dept: '—', view: '—' },
  { code: 'user:admin', admin: '✓', net: '—', dept: '—', view: '—' },
]

export function SettingsPage() {
  const { user, canManageNetwork, logout } = useAuth()
  const fileRef = useRef<HTMLInputElement>(null)
  const [toast, setToast] = useState('')
  const [busy, setBusy] = useState(false)
  const [oldPwd, setOldPwd] = useState('')
  const [newPwd, setNewPwd] = useState('')
  const [newPwd2, setNewPwd2] = useState('')
  const [pwdBusy, setPwdBusy] = useState(false)

  const run = async (fn: () => Promise<void>, okMsg?: string) => {
    setBusy(true)
    setToast('')
    try {
      await fn()
      if (okMsg) setToast(okMsg)
    } catch (e) {
      setToast(e instanceof ApiError ? e.message : e instanceof Error ? e.message : '操作失败')
    } finally {
      setBusy(false)
    }
  }

  const onChangePassword = async (e: FormEvent) => {
    e.preventDefault()
    if (newPwd !== newPwd2) {
      setToast('两次输入的新密码不一致')
      return
    }
    setPwdBusy(true)
    setToast('')
    try {
      const res = await api.changePassword(oldPwd, newPwd)
      setToast(res.message)
      setOldPwd('')
      setNewPwd('')
      setNewPwd2('')
      // 改密后旧 token 仍可用，但要求重新登录更合理
      window.setTimeout(() => {
        logout()
        window.location.assign('/login')
      }, 800)
    } catch (err) {
      setToast(err instanceof ApiError ? err.message : '修改失败')
    } finally {
      setPwdBusy(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="系统设置"
        description="当前登录信息、改密码、权限说明，以及 CSV 导入导出。"
      />

      {toast ? (
        <div
          className="mb-4 rounded-xl border border-teal-200 bg-teal-50 px-4 py-2 text-sm text-teal-900"
          role="status"
          aria-live="polite"
        >
          {toast}
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="当前会话" />
          <CardBody className="space-y-3">
            <div className="flex items-center gap-3">
              <div
                className="flex h-12 w-12 items-center justify-center rounded-2xl text-lg font-semibold text-white"
                style={{ background: user?.avatarColor }}
              >
                {user?.displayName.slice(0, 1)}
              </div>
              <div>
                <div className="font-medium text-ink-900">{user?.displayName}</div>
                <div className="text-sm text-muted">
                  @{user?.username} · {user ? roleLabel[user.role] : ''}
                </div>
              </div>
            </div>
            <div className="rounded-xl bg-ink-50 px-3 py-2 text-sm text-ink-800">
              部门：{user?.departmentName}
            </div>
            <div className="text-xs text-muted">
              登录令牌仅保留在当前浏览器标签页；退出或关闭标签页后需要重新登录。
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="修改密码" subtitle="修改成功后会退出，请用新密码登录" />
          <CardBody>
            <form className="space-y-3" onSubmit={onChangePassword}>
              <Field label="原密码">
                <Input
                  type="password"
                  value={oldPwd}
                  onChange={(e) => setOldPwd(e.target.value)}
                  required
                />
              </Field>
              <Field label="新密码（至少 12 位，含字母、数字和特殊字符）">
                <Input
                  type="password"
                  value={newPwd}
                  onChange={(e) => setNewPwd(e.target.value)}
                  required
                  minLength={12}
                  maxLength={128}
                />
              </Field>
              <Field label="再输入一次新密码">
                <Input
                  type="password"
                  value={newPwd2}
                  onChange={(e) => setNewPwd2(e.target.value)}
                  required
                  minLength={12}
                  maxLength={128}
                />
              </Field>
              <Button type="submit" disabled={pwdBusy}>
                {pwdBusy ? '提交中…' : '修改密码'}
              </Button>
            </form>
          </CardBody>
        </Card>

        {productConfig.showDemoAccounts ? (
          <Card className="lg:col-span-2">
            <CardHeader title="演示账号" subtitle="仅在开发或显式演示模式显示；初始密码见 README" />
            <CardBody className="grid gap-2 sm:grid-cols-2">
            {demoAccounts.map((u) => (
              <div
                key={u.username}
                className="flex items-center justify-between rounded-xl border border-line px-3 py-2"
              >
                <div>
                  <div className="text-sm font-medium">{u.username}</div>
                  <div className="text-xs text-muted">
                    {u.name}
                  </div>
                </div>
                <SoftBadge>{roleLabel[u.role]}</SoftBadge>
              </div>
            ))}
            </CardBody>
          </Card>
        ) : null}
      </div>

      <Card className="mt-6">
        <CardHeader
          title="数据导入 / 导出"
          subtitle="导出的 CSV 可以用 Excel 打开。导入子网只有管理员和网管能做。"
        />
        <CardBody className="flex flex-wrap gap-2">
          <Button
            size="sm"
            variant="outline"
            disabled={busy}
            onClick={() =>
              void run(
                () => api.downloadAuth(api.exportSubnetsUrl(), 'subnets.csv'),
                '已导出子网 CSV',
              )
            }
          >
            <Download className="h-4 w-4" /> 导出子网
          </Button>
          <Button
            size="sm"
            variant="outline"
            disabled={busy}
            onClick={() =>
              void run(
                () => api.downloadAuth(api.exportIpsUrl(), 'ip_addresses.csv'),
                '已导出地址 CSV',
              )
            }
          >
            <Download className="h-4 w-4" /> 导出地址
          </Button>
          <Button
            size="sm"
            variant="ghost"
            disabled={busy}
            onClick={() =>
              void run(
                () => api.downloadAuth(api.templateSubnetsUrl(), 'subnet_import_template.csv'),
                '已下载导入模板',
              )
            }
          >
            下载导入模板
          </Button>
          {canManageNetwork ? (
            <>
              <input
                ref={fileRef}
                type="file"
                accept=".csv,text/csv"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0]
                  if (!f) return
                  void run(async () => {
                    const res = await api.importSubnets(f)
                    setToast(res.message)
                  })
                  e.target.value = ''
                }}
              />
              <Button
                size="sm"
                disabled={busy}
                onClick={() => fileRef.current?.click()}
              >
                <Upload className="h-4 w-4" /> 导入子网 CSV
              </Button>
            </>
          ) : null}
        </CardBody>
      </Card>

      <Card className="mt-6 overflow-hidden">
        <CardHeader title="RBAC 权限矩阵" />
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="border-y border-line bg-ink-50/80 text-xs text-muted">
              <tr>
                <th className="px-4 py-3 font-medium">权限</th>
                <th className="px-4 py-3 font-medium">管理员</th>
                <th className="px-4 py-3 font-medium">网络管理员</th>
                <th className="px-4 py-3 font-medium">部门申请人</th>
                <th className="px-4 py-3 font-medium">只读</th>
              </tr>
            </thead>
            <tbody>
              {matrix.map((row) => (
                <tr key={row.code} className="border-b border-line/70">
                  <td className="px-4 py-3 font-mono text-xs">{row.code}</td>
                  <td className="px-4 py-3">{row.admin}</td>
                  <td className="px-4 py-3">{row.net}</td>
                  <td className="px-4 py-3">{row.dept}</td>
                  <td className="px-4 py-3">{row.view}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

    </div>
  )
}
