import { networkErrorMessage } from '@/lib/network-error'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000/api/v1'
const configuredTimeout = Number(import.meta.env.VITE_API_TIMEOUT_MS ?? 15_000)
const REQUEST_TIMEOUT_MS =
  Number.isFinite(configuredTimeout) && configuredTimeout > 0 ? configuredTimeout : 15_000

const TOKEN_KEY = 'netledger_access_token'
const LEGACY_TOKEN_KEY = 'ipam_token'

export function getToken() {
  localStorage.removeItem(LEGACY_TOKEN_KEY)
  return sessionStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string | null) {
  localStorage.removeItem(LEGACY_TOKEN_KEY)
  if (token) sessionStorage.setItem(TOKEN_KEY, token)
  else sessionStorage.removeItem(TOKEN_KEY)
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  if (!headers.has('Content-Type') && init.body) {
    headers.set('Content-Type', 'application/json')
  }
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const controller = new AbortController()
  let timedOut = false
  const onCallerAbort = () => controller.abort(init.signal?.reason)
  if (init.signal?.aborted) controller.abort(init.signal.reason)
  else init.signal?.addEventListener('abort', onCallerAbort, { once: true })
  const timeout = globalThis.setTimeout(() => {
    timedOut = true
    controller.abort()
  }, REQUEST_TIMEOUT_MS)

  let res: Response
  try {
    res = await fetch(`${API_BASE}${path}`, { ...init, headers, signal: controller.signal })
  } catch {
    throw new ApiError(0, networkErrorMessage(timedOut))
  } finally {
    globalThis.clearTimeout(timeout)
    init.signal?.removeEventListener('abort', onCallerAbort)
  }
  if (!res.ok) {
    let message = res.statusText
    try {
      const data = await res.json()
      message = data.detail
        ? typeof data.detail === 'string'
          ? data.detail
          : JSON.stringify(data.detail)
        : message
    } catch {
      /* ignore */
    }
    // Token expired / invalid — clear and send user to login
    if (res.status === 401 && !path.includes('/auth/login')) {
      setToken(null)
      if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
        window.location.assign('/login')
      }
    }
    throw new ApiError(res.status, message)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  login: (username: string, password: string) =>
    request<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  me: () => request<ApiUser>('/auth/me'),
  logout: () => request<{ message: string }>('/auth/logout', { method: 'POST' }),
  changePassword: (old_password: string, new_password: string) =>
    request<{ message: string }>('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({ old_password, new_password }),
    }),
  users: () => request<ApiUser[]>('/users'),
  departments: () => request<ApiDepartment[]>('/users/departments'),
  createDepartment: (body: { name: string; code: string }) =>
    request<ApiDepartment>('/users/departments', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  createUser: (body: Record<string, unknown>) =>
    request<ApiUser>('/users', { method: 'POST', body: JSON.stringify(body) }),
  updateUser: (id: number, body: Record<string, unknown>) =>
    request<ApiUser>(`/users/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  devices: (q?: string) =>
    request<ApiDevice[]>(`/devices${q ? `?q=${encodeURIComponent(q)}` : ''}`),
  createDevice: (body: Record<string, unknown>) =>
    request<ApiDevice>('/devices', { method: 'POST', body: JSON.stringify(body) }),
  updateDevice: (id: number, body: Record<string, unknown>) =>
    request<ApiDevice>(`/devices/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  deleteDevice: (id: number) => request<{ message: string }>(`/devices/${id}`, { method: 'DELETE' }),
  exportDevicesUrl: () => `${API_BASE}/io/export/devices`,
  dashboard: () => request<ApiDashboard>('/dashboard/overview'),
  sites: () => request<ApiSite[]>('/sites'),
  createSite: (body: Record<string, unknown>) =>
    request<ApiSite>('/sites', { method: 'POST', body: JSON.stringify(body) }),
  subnets: (params?: { site_id?: number; q?: string }) => {
    const sp = new URLSearchParams()
    if (params?.site_id) sp.set('site_id', String(params.site_id))
    if (params?.q) sp.set('q', params.q)
    const qs = sp.toString()
    return request<ApiSubnet[]>(`/subnets${qs ? `?${qs}` : ''}`)
  },
  subnet: (id: number) => request<ApiSubnet>(`/subnets/${id}`),
  createSubnet: (body: Record<string, unknown>) =>
    request<ApiSubnet>('/subnets', { method: 'POST', body: JSON.stringify(body) }),
  deleteSubnet: (id: number) =>
    request<{ message: string }>(`/subnets/${id}`, { method: 'DELETE' }),
  archiveSubnet: (id: number) =>
    request<{ message: string }>(`/subnets/${id}/archive`, { method: 'POST' }),
  restoreSubnet: (id: number) =>
    request<{ message: string }>(`/subnets/${id}/restore`, { method: 'POST' }),
  ips: (params?: {
    subnet_id?: number
    status?: string
    q?: string
    page?: number
    page_size?: number
  }) => {
    const sp = new URLSearchParams()
    if (params?.subnet_id) sp.set('subnet_id', String(params.subnet_id))
    if (params?.status) sp.set('status', params.status)
    if (params?.q) sp.set('q', params.q)
    if (params?.page) sp.set('page', String(params.page))
    if (params?.page_size) sp.set('page_size', String(params.page_size))
    const qs = sp.toString()
    return request<ApiIp[]>(`/ip-addresses${qs ? `?${qs}` : ''}`)
  },
  ipsPage: (params?: {
    subnet_id?: number
    status?: string
    q?: string
    page?: number
    page_size?: number
  }) => {
    const sp = new URLSearchParams()
    if (params?.subnet_id) sp.set('subnet_id', String(params.subnet_id))
    if (params?.status) sp.set('status', params.status)
    if (params?.q) sp.set('q', params.q)
    sp.set('page', String(params?.page ?? 1))
    sp.set('page_size', String(params?.page_size ?? 50))
    return request<ApiIpPage>(`/ip-addresses/page?${sp.toString()}`)
  },
  ip: (id: number) => request<ApiIp>(`/ip-addresses/${id}`),
  allocate: (id: number, body: Record<string, unknown>) =>
    request<ApiIp>(`/ip-addresses/${id}/allocate`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  release: (id: number) =>
    request<ApiIp>(`/ip-addresses/${id}/release`, { method: 'POST' }),
  batchRelease: (ids: number[]) =>
    request<{ message: string; data?: unknown }>('/ip-addresses/batch-release', {
      method: 'POST',
      body: JSON.stringify({ ids }),
    }),
  reserve: (id: number, remark?: string) =>
    request<ApiIp>(`/ip-addresses/${id}/reserve`, {
      method: 'POST',
      body: JSON.stringify({ remark: remark || '人工预留' }),
    }),
  disableIp: (id: number) =>
    request<ApiIp>(`/ip-addresses/${id}/disable`, { method: 'POST' }),
  enableIp: (id: number) =>
    request<ApiIp>(`/ip-addresses/${id}/enable`, { method: 'POST' }),
  allocateNext: (subnetId: number, body: Record<string, unknown>) =>
    request<ApiIp>(`/subnets/${subnetId}/allocate-next`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  logs: (address?: string) =>
    request<ApiLog[]>(`/logs${address ? `?address=${encodeURIComponent(address)}` : ''}`),
  conflicts: (status: string = 'open') =>
    request<ApiConflict[]>(`/conflicts?status=${encodeURIComponent(status)}`),
  resolveConflict: (id: number) =>
    request<ApiConflict>(`/conflicts/${id}/resolve`, { method: 'POST' }),
  scanConflicts: () =>
    request<{ message: string }>('/conflicts/scan', { method: 'POST' }),
  exportSubnetsUrl: () => `${API_BASE}/io/export/subnets`,
  exportIpsUrl: (subnetId?: number) =>
    `${API_BASE}/io/export/ip-addresses${subnetId ? `?subnet_id=${subnetId}` : ''}`,
  templateSubnetsUrl: () => `${API_BASE}/io/template/subnets`,
  importSubnets: async (file: File) => {
    const headers = new Headers()
    const token = getToken()
    if (token) headers.set('Authorization', `Bearer ${token}`)
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${API_BASE}/io/import/subnets`, {
      method: 'POST',
      headers,
      body: form,
    })
    if (!res.ok) {
      let message = res.statusText
      try {
        const data = await res.json()
        message = typeof data.detail === 'string' ? data.detail : message
      } catch {
        /* ignore */
      }
      throw new ApiError(res.status, message)
    }
    return res.json() as Promise<{ message: string; data?: unknown }>
  },
  downloadAuth: async (url: string, filename: string) => {
    const headers = new Headers()
    const token = getToken()
    if (token) headers.set('Authorization', `Bearer ${token}`)
    const res = await fetch(url, { headers })
    if (!res.ok) throw new ApiError(res.status, '下载失败')
    const blob = await res.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = filename
    a.click()
    URL.revokeObjectURL(a.href)
  },
}

export interface ApiUser {
  id: number
  username: string
  display_name: string
  role: string
  department_id: number
  department_name: string
  avatar_color: string
  is_active?: boolean
}

export interface ApiDepartment {
  id: number
  name: string
  code: string
}

export interface ApiDevice {
  id: number
  name: string
  device_type: string
  mac?: string | null
  location?: string | null
  department_id?: number | null
  department_name?: string | null
  owner_user_id?: number | null
  owner_name?: string | null
  remark?: string | null
  bound_ip?: string | null
  created_at?: string | null
}

export interface ApiSite {
  id: number
  name: string
  code: string
  location: string
  remark?: string | null
  subnet_count: number
}

export interface ApiSubnet {
  id: number
  site_id: number
  site_name: string
  name: string
  cidr: string
  gateway: string
  vlan_id?: number | null
  purpose: string
  department_id: number
  department_name: string
  description?: string | null
  total_ips: number
  used_ips: number
  free_ips: number
  reserved_ips: number
  disabled_ips: number
  utilization: number
  status: string
  created_at?: string | null
}

export interface ApiIp {
  id: number
  subnet_id: number
  subnet_cidr: string
  address: string
  status: string
  hostname?: string | null
  mac?: string | null
  device_name?: string | null
  device_type?: string | null
  device_id?: number | null
  owner_name?: string | null
  owner_user_id?: number | null
  department_id?: number | null
  department_name?: string | null
  allocated_at?: string | null
  expire_at?: string | null
  remark?: string | null
  is_network_or_broadcast: boolean
}

export interface ApiIpPage {
  items: ApiIp[]
  total: number
  page: number
  page_size: number
}

export interface ApiConflict {
  id: number
  ip_address: string
  subnet_cidr: string
  type: string
  detail: string
  status: string
  detected_at: string
}

export interface ApiLog {
  id: number
  address: string
  action: string
  operator_name: string
  detail: string
  created_at: string
}

export interface ApiDashboard {
  site_count: number
  subnet_count: number
  total_ips: number
  free_ips: number
  allocated_ips: number
  reserved_ips: number
  disabled_ips: number
  open_conflicts: number
  expiring_soon: number
  top_subnets: { name: string; cidr: string; utilization: number }[]
  recent_logs: ApiLog[]
}

export function mapUser(u: ApiUser) {
  return {
    id: u.id,
    username: u.username,
    displayName: u.display_name,
    role: u.role as 'admin' | 'network_admin' | 'dept_user' | 'viewer',
    departmentId: u.department_id,
    departmentName: u.department_name,
    avatarColor: u.avatar_color,
    isActive: u.is_active !== false,
  }
}
