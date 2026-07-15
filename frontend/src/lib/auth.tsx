import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { api, mapUser, setToken, getToken, ApiError } from '@/lib/api'
import type { Role, User } from '@/types'

interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<{ ok: true } | { ok: false; message: string }>
  logout: () => void
  isAuthenticated: boolean
  canManageNetwork: boolean
  canAllocate: boolean
  canAdmin: boolean
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    if (!getToken()) {
      setUser(null)
      return
    }
    try {
      const me = await api.me()
      setUser(mapUser(me))
    } catch {
      setToken(null)
      setUser(null)
    }
  }, [])

  useEffect(() => {
    ;(async () => {
      await refreshUser()
      setLoading(false)
    })()
  }, [refreshUser])

  const login = useCallback(async (username: string, password: string) => {
    try {
      const res = await api.login(username, password)
      setToken(res.access_token)
      const me = await api.me()
      setUser(mapUser(me))
      return { ok: true as const }
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : '登录失败'
      return { ok: false as const, message: msg }
    }
  }, [])

  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
  }, [])

  const role = user?.role as Role | undefined

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      login,
      logout,
      isAuthenticated: !!user,
      canManageNetwork: role === 'admin' || role === 'network_admin',
      canAllocate: role === 'admin' || role === 'network_admin' || role === 'dept_user',
      canAdmin: role === 'admin',
      refreshUser,
    }),
    [user, loading, login, logout, role, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
