export const productConfig = {
  name: 'NetLedger',
  chineseName: '企业 IP 地址管理',
  tagline: '让每一个地址都有归属、有状态、有记录',
  showDemoAccounts: import.meta.env.DEV || import.meta.env.VITE_SHOW_DEMO_ACCOUNTS === 'true',
  environmentLabel: import.meta.env.PROD ? '生产环境' : '开发环境',
} as const
