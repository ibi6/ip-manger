import { Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { useAuth } from '@/lib/auth'
import { AppShell } from '@/components/layout/AppShell'
import { LoginPage } from '@/pages/LoginPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { SitesPage } from '@/pages/SitesPage'
import { SubnetsPage } from '@/pages/SubnetsPage'
import { SubnetDetailPage } from '@/pages/SubnetDetailPage'
import { SubnetFormPage } from '@/pages/SubnetFormPage'
import { AddressesPage } from '@/pages/AddressesPage'
import { AddressDetailPage } from '@/pages/AddressDetailPage'
import { ConflictsPage } from '@/pages/ConflictsPage'
import { SettingsPage } from '@/pages/SettingsPage'
import { UsersPage } from '@/pages/UsersPage'
import { DevicesPage } from '@/pages/DevicesPage'
import { LogsPage } from '@/pages/LogsPage'
import { LoadingBlock } from '@/components/ui/EmptyState'

function Protected() {
  const { isAuthenticated, loading } = useAuth()
  if (loading) {
    return (
      <div className="bg-mesh flex min-h-screen items-center justify-center">
        <LoadingBlock label="正在恢复登录状态…" />
      </div>
    )
  }
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <Outlet />
}

export function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<Protected />}>
        <Route element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="sites" element={<SitesPage />} />
          <Route path="subnets" element={<SubnetsPage />} />
          <Route path="subnets/new" element={<SubnetFormPage />} />
          <Route path="subnets/:id" element={<SubnetDetailPage />} />
          <Route path="addresses" element={<AddressesPage />} />
          <Route path="addresses/:id" element={<AddressDetailPage />} />
          <Route path="devices" element={<DevicesPage />} />
          <Route path="logs" element={<LogsPage />} />
          <Route path="conflicts" element={<ConflictsPage />} />
          <Route path="users" element={<UsersPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
