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
                 │     SQLite (demo) / MySQL / PG      │
                 └─────────────────────────────────────┘
```

## Backend layers

| Layer | Path | Responsibility |
|-------|------|----------------|
| API | `backend/app/api/v1/*` | HTTP, auth deps, status codes |
| Schemas | `backend/app/schemas/*` | Request/response validation |
| Services | `backend/app/services/*` | Domain rules (allocate, CIDR, stats) |
| Models | `backend/app/models/*` | Persistence |
| Core | `backend/app/core/*` | Config, security, middleware |

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
- Auth context + token storage: `frontend/src/lib/auth.tsx`  

## Deployment topologies

1. **Dev:** uvicorn + Vite  
2. **Compose:** nginx SPA + API container + volume for SQLite  
3. **Prod target:** reverse proxy TLS + managed Postgres + secret manager  

## Extension points

| Adapter | Hook |
|---------|------|
| Discovery | Replace `simulate-scan` with importer writing `conflicts` |
| DHCP | Sync leases into `ip_addresses` via batch job |
| IdP | Swap password login for OIDC, keep JWT session shape |
