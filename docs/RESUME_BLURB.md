# Resume / Portfolio Blurbs

## One-liner

Built **NetLedger**, a lightweight open-source IPAM that manages IPv4 lifecycle (allocate / reclaim / reserve) with JWT RBAC, audit logs, and CIDR-based address pool generation.

## 3–5 bullets (English)

- Designed a full-stack IPAM (FastAPI + React/TS) covering sites, subnets, IP status machine, devices, and operational audit trails.  
- Implemented concurrency-safe allocation via conditional SQL updates and system-locked gateway/broadcast protection.  
- Delivered RBAC (4 roles), login rate limiting, CSV import/export, Docker Compose packaging, and 30+ automated API tests.  
- Productized the repository with CI, OpenAPI docs, security policy, and maintainable service-layer architecture for future discovery/DHCP adapters.  

## 中文简历条目

- 独立设计并实现轻量级企业 IP 地址管理系统（NetLedger）：子网地址池、分配/回收/预留/禁用、设备台账、操作审计。  
- 后端 Python/FastAPI + SQLAlchemy，前端 React/TypeScript；JWT 权限、登录限流、条件更新防并发双分配。  
- 配套 Docker 一键部署、OpenAPI 文档、pytest 自动化测试与完整开源工程规范（CI / SECURITY / CHANGELOG）。  

## Interview talking points

1. Why conditional `UPDATE` beats read-modify-write for IP allocate.  
2. How CIDR expansion is bounded to protect demo databases.  
3. Honest product boundary: inventory IPAM first, discovery/DHCP later.  
