import { useEffect, useState, type FormEvent } from 'react'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/Button'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { Field, Input, Select } from '@/components/ui/Input'
import { SoftBadge } from '@/components/ui/Badge'
import { ErrorBlock, LoadingBlock } from '@/components/ui/EmptyState'
import { api, ApiError, type ApiDepartment, type ApiUser } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { roleLabel } from '@/lib/labels'
import type { Role } from '@/types'

export function UsersPage() {
  const { canAdmin, user: me } = useAuth()
  const [list, setList] = useState<ApiUser[]>([])
  const [depts, setDepts] = useState<ApiDepartment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('123456')
  const [displayName, setDisplayName] = useState('')
  const [role, setRole] = useState<Role>('viewer')
  const [departmentId, setDepartmentId] = useState('')
  const [saving, setSaving] = useState(false)
  const [deptName, setDeptName] = useState('')
  const [deptCode, setDeptCode] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const [users, departments] = await Promise.all([api.users(), api.departments()])
      setList(users)
      setDepts(departments)
      if (departments[0] && !departmentId) setDepartmentId(String(departments[0].id))
    } catch (e) {
      setError(e instanceof Error ? e.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }

  const onCreateDept = async (e: FormEvent) => {
    e.preventDefault()
    try {
      await api.createDepartment({ name: deptName.trim(), code: deptCode.trim() })
      setMsg('部门已添加')
      setDeptName('')
      setDeptCode('')
      await load()
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : '添加部门失败')
    }
  }

  useEffect(() => {
    if (canAdmin) void load()
    else setLoading(false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canAdmin])

  if (!canAdmin) {
    return (
      <Card className="p-8 text-center text-sm text-muted">
        用户管理只有管理员能进。当前账号：{me?.username}
      </Card>
    )
  }

  const onCreate = async (e: FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setMsg('')
    try {
      await api.createUser({
        username: username.trim(),
        password,
        display_name: displayName.trim(),
        role,
        department_id: Number(departmentId),
      })
      setMsg('已添加用户')
      setUsername('')
      setDisplayName('')
      setPassword('123456')
      await load()
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : '添加失败')
    } finally {
      setSaving(false)
    }
  }

  const toggleActive = async (u: ApiUser) => {
    try {
      await api.updateUser(u.id, { is_active: !u.is_active })
      setMsg(u.is_active ? `已停用 ${u.username}` : `已启用 ${u.username}`)
      await load()
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : '操作失败')
    }
  }

  if (loading) return <LoadingBlock label="读取用户列表…" />
  if (error) return <ErrorBlock message={error} onRetry={load} />

  return (
    <div>
      <PageHeader
        title="用户管理"
        description="管理员可以新增账号、改角色、停用用户。密码默认 123456，上线前记得改。"
      />

      {msg ? (
        <div className="mb-4 rounded-xl border border-line bg-ink-50 px-4 py-2 text-sm text-ink-800">
          {msg}
        </div>
      ) : null}

      <div className="mb-6 grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="新增部门" subtitle="给用户挂部门用" />
          <CardBody>
            <form className="flex flex-wrap gap-2" onSubmit={onCreateDept}>
              <Input
                className="max-w-[10rem]"
                placeholder="名称"
                value={deptName}
                onChange={(e) => setDeptName(e.target.value)}
                required
              />
              <Input
                className="max-w-[8rem]"
                placeholder="编码"
                value={deptCode}
                onChange={(e) => setDeptCode(e.target.value)}
                required
              />
              <Button type="submit" size="sm">
                添加部门
              </Button>
            </form>
            <div className="mt-3 flex flex-wrap gap-2">
              {depts.map((d) => (
                <SoftBadge key={d.id}>
                  {d.name}({d.code})
                </SoftBadge>
              ))}
            </div>
          </CardBody>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-3 overflow-hidden">
          <CardHeader title="现有用户" subtitle={`共 ${list.length} 人`} />
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-y border-line bg-ink-50/80 text-xs text-muted">
                <tr>
                  <th className="px-4 py-3">用户名</th>
                  <th className="px-4 py-3">姓名</th>
                  <th className="px-4 py-3">角色</th>
                  <th className="px-4 py-3">部门</th>
                  <th className="px-4 py-3">状态</th>
                  <th className="px-4 py-3">操作</th>
                </tr>
              </thead>
              <tbody>
                {list.map((u) => (
                  <tr key={u.id} className="border-b border-line/70">
                    <td className="px-4 py-3 font-mono text-xs">{u.username}</td>
                    <td className="px-4 py-3">{u.display_name}</td>
                    <td className="px-4 py-3">
                      <SoftBadge>{roleLabel[u.role as Role] ?? u.role}</SoftBadge>
                    </td>
                    <td className="px-4 py-3 text-muted">{u.department_name}</td>
                    <td className="px-4 py-3">
                      {u.is_active === false ? (
                        <SoftBadge tone="danger">停用</SoftBadge>
                      ) : (
                        <SoftBadge tone="ok">正常</SoftBadge>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <Button size="sm" variant="ghost" onClick={() => void toggleActive(u)}>
                        {u.is_active === false ? '启用' : '停用'}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader title="新增用户" />
          <CardBody>
            <form className="space-y-3" onSubmit={onCreate}>
              <Field label="用户名">
                <Input value={username} onChange={(e) => setUsername(e.target.value)} required />
              </Field>
              <Field label="显示名">
                <Input value={displayName} onChange={(e) => setDisplayName(e.target.value)} required />
              </Field>
              <Field label="初始密码">
                <Input value={password} onChange={(e) => setPassword(e.target.value)} required />
              </Field>
              <Field label="角色">
                <Select value={role} onChange={(e) => setRole(e.target.value as Role)}>
                  <option value="admin">系统管理员</option>
                  <option value="network_admin">网络管理员</option>
                  <option value="dept_user">部门申请人</option>
                  <option value="viewer">只读</option>
                </Select>
              </Field>
              <Field label="部门">
                <Select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)}>
                  {depts.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name}
                    </option>
                  ))}
                </Select>
              </Field>
              <Button type="submit" disabled={saving} className="w-full">
                {saving ? '提交中…' : '创建'}
              </Button>
            </form>
          </CardBody>
        </Card>
      </div>
    </div>
  )
}
