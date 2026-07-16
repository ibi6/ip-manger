# Architecture

## High-level

```text
                 ┌─────────────────────────────────────┐
                 │           Clients (Browser)         │
                 │     React 19 + TypeScript + Vite    │
                 └─────────────────┬───────────────────┘
                                   │ HTTPS / JSON
                                   │ Authorization: Bearer <JWT>
                 ┌─────────────────▼───────────────────┐
                 │              FastAPI                │
                 │  routers → services → SQLAlchemy    │
                 │  auth · rate-limit · access log     │
                 └─────────────────┬───────────────────┘
                                   │
                 ┌─────────────────▼───────────────────┐
                 │      SQLite (single node) / PG      │
                 └─────────────────────────────────────┘
```

## Backend layers

| Layer | Path | Responsibility |
|-------|------|----------------|
| API | `backend/app/api/v1/*` | HTTP, auth deps, status codes |
| Schemas | `backend/app/schemas/*` | Request/response validation |
| Services | `backend/app/services/*` | Domain rules (allocate, CIDR, stats) |
| Models | `backend/app/models/*` | Persistence |
| Core | `backend/app/core/*` | Config, password/JWT security, failure limiting, middleware |

## Domain invariants

1. **IP status machine:** `free → allocated|reserved|disabled → free` (with locks)  
2. **System-locked addresses:** network / broadcast / gateway cannot be assigned  
3. **Allocate is conditional:** `UPDATE … WHERE status='free'`  
4. **Department scope:** `dept_user` only on own department subnets for writes  

## Key modules

- `ip_utils.parse_network` — CIDR validation & size guards  
- `subnet_service.generate_pool` — materialize host addresses  
- `ip_service.allocate_ip / release_ip` — lifecycle + audit log  
- `serializers.batch_subnet_stats` — avoid N+1 on dashboards  

## Frontend

- SPA routes under `frontend/src/pages`  
- API client: `frontend/src/lib/api.ts`  
- Auth provider: `frontend/src/lib/auth-provider.tsx`; context hook: `auth-context.ts`
- Bearer token storage is tab-scoped `sessionStorage`, not persistent local storage
- Product/environment policy: `frontend/src/config/product.ts`

## Deployment topologies

1. **Dev:** uvicorn + Vite  
2. **Compose:** hardened Nginx SPA + non-root API container + Alembic + SQLite volume
3. **Production:** outer TLS proxy + managed PostgreSQL + secret manager; production bootstraps one explicit admin and never loads samples

## Authentication sequence

```text
login request
  -> check prior failure bucket
  -> verify bcrypt credential
  -> failure: record event / success: clear bucket
  -> JWT(sub, exp, role, uid, ver)
  -> protected request compares JWT ver with users.auth_version
  -> password change increments auth_version and revokes old tokens
```

Uvicorn 的通用代理头解析在容器内显式关闭，避免任意直连方提前改写 `request.client`。应用默认忽略 `X-Forwarded-For`；仅当 `TRUST_PROXY_HEADERS=true` 时才采用代理链最右侧的合法 IP。Compose 开启该选项，因为公开路径固定为 Nginx → backend，且 Nginx 会覆盖客户端传入的转发链。多实例限流仍需 Redis 等共享存储。

## Extension points

| Adapter | Hook |
|---------|------|
| Discovery | Replace `simulate-scan` with importer writing `conflicts` |
| DHCP | Sync leases into `ip_addresses` via batch job |
| IdP | Swap password login for OIDC, keep JWT session shape |
