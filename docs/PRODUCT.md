# NetLedger — Product Positioning

## 1. What this looks like today

| Lens | Verdict | Why |
|------|---------|-----|
| Course homework | No | Scope exceeds a single-course CRUD demo |
| Graduation project | Partially | Strong fit for thesis *if* documented that way |
| Side / practice project | No longer accurate | Has tests, Docker, RBAC, lifecycle domain logic |
| Open-source project | **Target** | Public repo, CI, license, contribution path |
| Commercial product | **Early-stage** | Productized UX + ops story; not multi-tenant SaaS yet |

**Current identity:** a **product-shaped open-source IPAM** (inventory & lifecycle), not a student folder dump.

---

## 2. Product definition

| | |
|--|--|
| **Name** | **NetLedger** |
| **Category** | Network IP Address Management (IPAM) — lightweight |
| **One-liner** | Give every IPv4 address a clear owner, status, and audit trail. |
| **Promise** | Stop managing production networks with spreadsheets. |

### Core value

1. **Visibility** — know free / allocated / reserved / disabled at a glance  
2. **Control** — allocate, reclaim, reserve, and disable with role checks  
3. **Accountability** — every change is logged  
4. **Speed** — auto-generate address pools from CIDR in seconds  

### Target users

| Persona | Need |
|---------|------|
| Network admin (SMB / campus) | Subnet pools, reclaim, conflict notes |
| IT ops lead | RBAC, export, simple deploy |
| Student / lab engineer | Learn real IPAM flows without Infoblox cost |
| Indie consultant | Lightweight tool for client network audits |

### Typical scenarios

- New office floor: create site → subnet `/24` or `/28` → bulk-aware allocate  
- Employee offboarding: release IPs, keep audit history  
- Server room: reserve VIP / gateway, disable broken ports  
- Audit week: export CSV of addresses & devices  

### Differentiation

| vs Spreadsheets | Structured status machine, concurrency-safe allocate, roles |
| vs Full commercial IPAM | Open, free, minutes to run, no agent fleet required |
| vs Generic admin templates | Domain logic (`ipaddress`, system-locked gateway, batch release) |

**Not competing with:** Infoblox / BlueCat full stack.  
**Competing with:** “Excel + tribal knowledge”.

---

## 3. Product principles

1. **Honest scope** — simulate scan is labeled; no fake “AI discovery”  
2. **Safe defaults** — system addresses locked; archive before hard delete  
3. **Demo in 5 minutes** — seed users, one Docker compose, OpenAPI live  
4. **Extend, don’t rewrite** — clear service layer for DHCP / discovery adapters later  
