import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import { ApiError, api, getToken, mapUser, setToken } from '@/lib/api'
import { AuthContext, type AuthContextValue } from '@/lib/auth-context'
import type { Role, User } from '@/types'

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
    void refreshUser().finally(() => setLoading(false))
  }, [refreshUser])

  const login = useCallback(async (username: string, password: string) => {
    try {
      const response = await api.login(username, password)
      setToken(response.access_token)
      const me = await api.me()
      setUser(mapUser(me))
      return { ok: true as const }
    } catch (error) {
      const message = error instanceof ApiError ? error.message : '登录失败，请检查网络后重试'
      return { ok: false as const, message }
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
      isAuthenticated: Boolean(user),
      canManageNetwork: role === 'admin' || role === 'network_admin',
      canAllocate: role === 'admin' || role === 'network_admin' || role === 'dept_user',
      canAdmin: role === 'admin',
      refreshUser,
    }),
    [user, loading, login, logout, role, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
