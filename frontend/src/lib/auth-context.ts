import { createContext, useContext } from 'react'

import type { User } from '@/types'

export interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<{ ok: true } | { ok: false; message: string }>
  logout: () => Promise<boolean>
  isAuthenticated: boolean
  canManageNetwork: boolean
  canAllocate: boolean
  canAdmin: boolean
  refreshUser: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

/** Access the authenticated user and the role-derived UI capabilities. */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
