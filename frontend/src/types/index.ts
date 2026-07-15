export type Role = 'admin' | 'network_admin' | 'dept_user' | 'viewer'

export type IpStatus = 'free' | 'allocated' | 'reserved' | 'disabled'

export type DeviceType = 'server' | 'pc' | 'printer' | 'ap' | 'camera' | 'other'

export type ConflictType = 'duplicate_mac' | 'rogue_host' | 'status_mismatch'

export interface User {
  id: number
  username: string
  displayName: string
  role: Role
  departmentId: number
  departmentName: string
  avatarColor: string
  isActive?: boolean
}

export interface Site {
  id: number
  name: string
  code: string
  location: string
  remark?: string
}

export interface Subnet {
  id: number
  siteId: number
  siteName: string
  name: string
  cidr: string
  gateway: string
  vlanId?: number
  purpose: string
  departmentId: number
  departmentName: string
  description?: string
  totalIps: number
  usedIps: number
  freeIps: number
  reservedIps: number
  disabledIps: number
  utilization: number
  status: 'active' | 'archived'
  createdAt: string
}

export interface IpAddress {
  id: number
  subnetId: number
  subnetCidr: string
  address: string
  status: IpStatus
  hostname?: string
  mac?: string
  deviceName?: string
  deviceType?: DeviceType
  ownerName?: string
  ownerUserId?: number
  departmentId?: number
  departmentName?: string
  allocatedAt?: string
  expireAt?: string
  remark?: string
  isNetworkOrBroadcast?: boolean
}

export interface ConflictItem {
  id: number
  ipAddress: string
  subnetCidr: string
  type: ConflictType
  detail: string
  status: 'open' | 'resolved'
  detectedAt: string
}

export interface AllocationLog {
  id: number
  address: string
  action: 'allocate' | 'release' | 'reserve' | 'disable' | 'enable'
  operatorName: string
  detail: string
  createdAt: string
}

export interface DashboardStats {
  siteCount: number
  subnetCount: number
  totalIps: number
  freeIps: number
  allocatedIps: number
  reservedIps: number
  disabledIps: number
  openConflicts: number
  expiringSoon: number
  topSubnets: { name: string; cidr: string; utilization: number }[]
  recentLogs: AllocationLog[]
}
