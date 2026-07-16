import type { ConflictType, DeviceType, IpStatus, Role } from '@/types'

export const roleLabel: Record<Role, string> = {
  admin: '系统管理员',
  network_admin: '网络管理员',
  dept_user: '部门申请人',
  viewer: '只读访客',
}

export const ipStatusLabel: Record<IpStatus, string> = {
  free: '空闲',
  allocated: '已分配',
  reserved: '预留',
  disabled: '禁用',
}

export const deviceTypeLabel: Record<DeviceType, string> = {
  server: '服务器',
  pc: '办公电脑',
  printer: '打印机',
  ap: '无线 AP',
  camera: '摄像头',
  other: '其他',
}

export const conflictTypeLabel: Record<ConflictType, string> = {
  duplicate_mac: 'MAC 冲突',
  rogue_host: '未登记主机',
  status_mismatch: '状态不一致',
}

export const demoAccounts = [
  { username: 'admin', role: 'admin' as Role, name: '陈启明' },
  { username: 'netadmin', role: 'network_admin' as Role, name: '林知微' },
  { username: 'biz', role: 'dept_user' as Role, name: '周景行' },
  { username: 'viewer', role: 'viewer' as Role, name: '苏晚晴' },
]
