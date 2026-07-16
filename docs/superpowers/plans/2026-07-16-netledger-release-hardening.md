# NetLedger Release Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有 NetLedger 提升为品牌统一、移动端可用、认证安全、迁移可靠且可通过自动化验证的轻量 IPAM 发布版本。

**Architecture:** 保留 React/Vite SPA 与 FastAPI/SQLAlchemy REST 架构。前端通过统一品牌、字段和反馈组件改善 UI/无障碍；后端通过失败限流、强密码、认证版本和生产初始化策略加固认证；Alembic、Docker 与 Nginx 形成可重复发布链路。

**Tech Stack:** React 19、TypeScript 6、Vite 8、Tailwind CSS 4、Python 3.11、FastAPI、SQLAlchemy 2、Pydantic 2、Alembic、pytest、Node test runner、Docker Compose、Nginx。

## Global Constraints

- 保持 `/api/v1` REST 路径和现有 JSON `detail` 错误结构兼容。
- 开发环境允许显式演示数据；生产环境禁止默认账号和默认密码。
- 所有新业务行为必须先有失败测试，随后才写实现。
- 不引入 Next.js、Redis、OIDC、IPv6 或真实网络扫描。
- UI 必须在 375px、768px、1440px 下可用，触控目标至少 44px，整页不得横向溢出。
- 不暴露真实密钥、令牌或生产密码。

---

### Task 1: Frontend test foundation and formatting utilities

**Files:**
- Create: `frontend/tests/format.test.ts`
- Create: `frontend/src/lib/format.ts`
- Modify: `frontend/package.json`
- Modify: `frontend/src/pages/DashboardPage.tsx`
- Modify: `frontend/src/pages/LogsPage.tsx`
- Modify: `frontend/src/pages/ConflictsPage.tsx`
- Modify: `frontend/src/pages/AddressDetailPage.tsx`

**Interfaces:**
- Produces: `formatDateTime(value?: string | null): string`
- Produces: `formatShortDate(value?: string | null): string`
- Produces: `clampPercent(value: number): number`

- [ ] **Step 1: Write failing utility tests**

```ts
import test from 'node:test'
import assert from 'node:assert/strict'
import { clampPercent, formatDateTime, formatShortDate } from '../src/lib/format.ts'

test('formatDateTime returns a stable local display without throwing on empty input', () => {
  assert.equal(formatDateTime(undefined), '—')
  assert.match(formatDateTime('2026-07-16T12:30:45Z'), /^2026-07-16 /)
})

test('formatShortDate and clampPercent protect UI boundaries', () => {
  assert.equal(formatShortDate('2026-07-16T12:30:45Z'), '2026-07-16')
  assert.equal(clampPercent(-2), 0)
  assert.equal(clampPercent(130), 100)
})
```

- [ ] **Step 2: Run the test and verify RED**

Run: `npm test`

Expected: FAIL because `src/lib/format.ts` does not exist.

- [ ] **Step 3: Add the minimal typed implementation and package script**

```ts
export function formatDateTime(value?: string | null): string {
  if (!value) return '—'
  const normalized = value.replace('T', ' ')
  return normalized.slice(0, 19)
}

export function formatShortDate(value?: string | null): string {
  return value ? value.slice(0, 10) : '—'
}

export function clampPercent(value: number): number {
  return Math.min(100, Math.max(0, Number.isFinite(value) ? value : 0))
}
```

Add script: `"test": "node --experimental-strip-types --test tests/*.test.ts"`.

- [ ] **Step 4: Replace duplicated slicing/clamping and verify GREEN**

Run: `npm test && npm run lint && npm run build`

Expected: tests pass, build passes, no new lint warning.

### Task 2: Brand, accessibility, responsive shell, and production-safe demo UI

**Files:**
- Create: `frontend/src/config/product.ts`
- Create: `frontend/src/lib/auth-context.ts`
- Modify: `frontend/src/lib/auth.tsx`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/lib/labels.ts`
- Modify: `frontend/src/components/layout/AppShell.tsx`
- Modify: `frontend/src/components/ui/Input.tsx`
- Modify: `frontend/src/components/ui/EmptyState.tsx`
- Modify: `frontend/src/components/ErrorBoundary.tsx`
- Modify: `frontend/src/pages/LoginPage.tsx`
- Modify: `frontend/src/pages/SettingsPage.tsx`
- Modify: `frontend/src/index.css`
- Modify: `frontend/.env.example`

**Interfaces:**
- Produces: `productConfig` with `name`, `tagline`, `showDemoAccounts`, `environmentLabel`.
- Produces: `useAuth()` from a component-free module to satisfy Fast Refresh.
- Changes: token storage from persistent `localStorage` to tab-scoped `sessionStorage`.

- [ ] **Step 1: Record current browser failures**

Verify on 375px: mobile menu trigger has no accessible name; drawer has no logout; form labels do not resolve to their inputs; production build contains demo password copy.

- [ ] **Step 2: Define product configuration**

```ts
export const productConfig = {
  name: 'NetLedger',
  chineseName: '企业 IP 地址管理',
  tagline: '让每一个地址都有归属、有状态、有记录',
  showDemoAccounts: import.meta.env.DEV || import.meta.env.VITE_SHOW_DEMO_ACCOUNTS === 'true',
  environmentLabel: import.meta.env.MODE === 'production' ? '生产环境' : '开发环境',
} as const
```

- [ ] **Step 3: Associate fields and feedback semantically**

Use `useId()` in `Field`, clone the single input/select/textarea child with a stable `id`, and connect hints with `aria-describedby`. Add `role="status"`/`aria-live="polite"` to loading and feedback; mark decorative icons `aria-hidden` where appropriate.

- [ ] **Step 4: Rebuild AppShell mobile behavior**

Add `aria-label="打开导航菜单"`, `aria-expanded`, labeled close control, Escape handling, scroll lock, a visible user card, and a 44px logout button inside the drawer. Add a skip link and environment-neutral NetLedger footer.

- [ ] **Step 5: Remove production demo leakage**

When `showDemoAccounts` is false, login fields start empty and no account/password card renders. Settings hides demo-account and local-run cards in production. Store bearer tokens in `sessionStorage` and remove stale legacy `localStorage` tokens.

- [ ] **Step 6: Apply the design system**

Use deep ink navigation, emerald action, amber risk, warm paper background, local serif display stack, subtle network grid/radial depth, consistent focus rings, `prefers-reduced-motion`, and 44px touch targets.

- [ ] **Step 7: Verify UI**

Run: `npm test && npm run lint && npm run build`.

Browser acceptance: login, workbench, mobile drawer and a visible form at 375/768/1440; no body horizontal overflow; every button has a non-empty accessible name; every visible form control has a label.

### Task 3: Authentication hardening with TDD

**Files:**
- Modify: `backend/tests/test_auth.py`
- Modify: `backend/tests/test_auth_password.py`
- Create: `backend/tests/test_security_headers.py`
- Modify: `backend/app/core/rate_limit.py`
- Modify: `backend/app/core/security.py`
- Modify: `backend/app/schemas/common.py`
- Modify: `backend/app/api/v1/auth.py`
- Modify: `backend/app/api/deps.py`
- Modify: `backend/app/api/v1/users.py`
- Modify: `backend/app/models/entities.py`
- Modify: `backend/app/core/middleware.py`

**Interfaces:**
- Produces: `assert_login_allowed(request)`, `record_login_failure(request)`, `clear_login_failures(request)`.
- Produces: `validate_password_strength(value): str`.
- Changes: JWT payload includes integer `ver`; current user must have matching `auth_version`.

- [ ] **Step 1: Write failing authentication tests**

```py
def test_successful_logins_do_not_consume_failure_budget(client):
    for _ in range(12):
        assert client.post('/api/v1/auth/login', json={
            'username': 'admin', 'password': 'ChangeMe123!'
        }).status_code == 200

def test_old_token_is_rejected_after_password_change(client):
    old = auth_header(client, 'viewer')
    changed = client.post('/api/v1/auth/change-password', headers=old, json={
        'old_password': 'ChangeMe123!', 'new_password': 'NewSecurePass99!'
    })
    assert changed.status_code == 200
    assert client.get('/api/v1/auth/me', headers=old).status_code == 401

def test_weak_new_password_is_rejected(client):
    response = client.post('/api/v1/auth/change-password', headers=auth_header(client), json={
        'old_password': 'ChangeMe123!', 'new_password': 'short'
    })
    assert response.status_code == 422
```

- [ ] **Step 2: Run targeted tests and verify RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_auth.py tests/test_auth_password.py -q`

Expected: successful login loop reaches 429, old token remains valid, and weak password behavior does not match the new contract.

- [ ] **Step 3: Implement failure-only rate limiting**

Check before authentication, record only invalid credentials, clear on success, bound stale buckets, and trust `X-Forwarded-For` only when configured.

- [ ] **Step 4: Implement password strength and auth version**

Require 12–128 characters, at least one letter, digit, special character, and at most 72 UTF-8 bytes. Add `User.auth_version`; include `ver` at login; compare in dependency; increment on self-change and admin password reset.

- [ ] **Step 5: Add security headers**

Add `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, `Cache-Control: no-store` for auth responses, and preserve `X-Request-ID`.

- [ ] **Step 6: Verify GREEN and full regression**

Run: `.\.venv\Scripts\python.exe -m pytest -q`

Expected: all original and new tests pass.

### Task 4: Secure startup and database migration consistency

**Files:**
- Create: `backend/tests/test_startup_policy.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/seed.py`
- Modify: `backend/app/db/migrate_sqlite.py`
- Create: `backend/alembic/versions/0002_release_hardening.py`
- Modify: `backend/.env.example`

**Interfaces:**
- Produces: settings `seed_demo_data`, `bootstrap_admin_username`, `bootstrap_admin_password`, `trust_proxy_headers`.
- Produces: `initialize_data(db, settings)` that selects demo seed or production bootstrap.

- [ ] **Step 1: Write failing startup-policy tests**

```py
def test_production_never_seeds_demo_accounts(empty_db, production_settings):
    with pytest.raises(RuntimeError, match='BOOTSTRAP_ADMIN_PASSWORD'):
        initialize_data(empty_db, production_settings)

def test_production_bootstrap_creates_only_admin(empty_db, production_bootstrap_settings):
    initialize_data(empty_db, production_bootstrap_settings)
    assert empty_db.scalar(select(func.count()).select_from(User)) == 1
    assert empty_db.scalar(select(User.username)) == 'admin'
```

- [ ] **Step 2: Verify RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_startup_policy.py -q`

Expected: import or behavior failure because initialization policy does not exist.

- [ ] **Step 3: Implement environment-aware initialization**

Development defaults to demo data only when enabled. Production with an empty user table requires a strong bootstrap password and creates only the admin plus its department. Existing databases are not reseeded.

- [ ] **Step 4: Add 0002 migration and SQLite compatibility**

Migration creates `devices` if absent, adds `ip_addresses.device_id`, adds `users.auth_version`, foreign keys/indexes where supported, and a unique MAC index. SQLite compatibility updater mirrors additive columns/indexes for legacy local files.

- [ ] **Step 5: Verify migrations**

Run against a temporary SQLite file: `alembic upgrade head`, inspect tables/columns/indexes, then run full pytest.

### Task 5: Validation and query performance

**Files:**
- Create: `backend/tests/test_validation_and_sites.py`
- Modify: `backend/app/schemas/common.py`
- Modify: `backend/app/api/v1/sites.py`
- Modify: `backend/app/api/v1/devices.py`
- Modify: `backend/app/models/entities.py`

**Interfaces:**
- Changes: bounded/patterned Pydantic inputs for site, subnet, device, user and allocation payloads.
- Changes: site counts use one grouped query instead of one query per site.

- [ ] **Step 1: Write failing validation tests**

Test blank site names, invalid site codes, VLAN outside 1–4094, invalid device type, overly long queries, and unique MAC conflict.

- [ ] **Step 2: Verify RED**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_validation_and_sites.py -q`.

- [ ] **Step 3: Add exact schema constraints**

Use `Field(min_length=..., max_length=..., pattern=...)`, `Literal` for roles/status/device types, whitespace validation, and typed `date` for expiry while keeping serializer output unchanged.

- [ ] **Step 4: Remove site N+1 query**

Build one outer join/group-by statement returning `(Site, subnet_count)` and pass the count to `site_out`.

- [ ] **Step 5: Verify full regression**

Run full pytest and confirm no query/validation contract breaks the frontend.

### Task 6: Production container and proxy hardening

**Files:**
- Create: `backend/requirements-dev.txt`
- Create: `backend/docker-entrypoint.sh`
- Modify: `backend/requirements.txt`
- Modify: `backend/Dockerfile`
- Modify: `frontend/nginx.conf`
- Modify: `docker-compose.yml`
- Modify: `.github/workflows/ci.yml`
- Modify: `Makefile`

**Interfaces:**
- Container startup contract: `alembic upgrade head` must succeed before Uvicorn starts.
- Runtime image runs API as user `netledger`, not root.

- [ ] **Step 1: Split runtime and development dependencies**

Runtime keeps FastAPI/SQLAlchemy/Alembic and adds `psycopg[binary]`; development adds pytest and Ruff via `-r requirements.txt`.

- [ ] **Step 2: Add migration entrypoint and non-root image**

Create `/app/docker-entrypoint.sh` with `set -eu`, run `alembic upgrade head`, then `exec "$@"`. Create a fixed non-root user and an owned `/data` directory.

- [ ] **Step 3: Harden Nginx and Compose**

Add gzip, hashed-asset immutable caching, no-cache HTML, CSP/security headers, upload body limit, proxy timeouts, frontend health check, `init: true`, and `no-new-privileges` where compatible.

- [ ] **Step 4: Align CI and Makefile**

CI installs `requirements-dev.txt`, runs Ruff and pytest; frontend runs test, lint and build. `make test` mirrors both stacks.

- [ ] **Step 5: Validate deployment configuration**

Run: `docker compose config`.

If Docker is available, run: `docker compose build` then `docker compose up -d`, wait for healthy services, request `/health`, and finally `docker compose down` without deleting the data volume.

### Task 7: Documentation, final QA, and release report

**Files:**
- Modify: `README.md`
- Modify: `docs/API.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/schema.sql`
- Create: `docs/DEPLOYMENT.md`
- Create: `docs/TESTING.md`
- Modify: `SECURITY.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Produces: exact local run, production bootstrap, backup, restore, rollback, migration and verification commands.

- [ ] **Step 1: Update product and configuration documentation**

Document NetLedger naming, demo-vs-production behavior, every required environment variable, SQLite/PostgreSQL URLs, and the absence of real network scanning.

- [ ] **Step 2: Document deployment and rollback**

Include TLS termination, Compose commands, Alembic upgrade, SQLite/PostgreSQL backup, restore drill, image rollback, secret rotation, log collection and `/health` monitoring.

- [ ] **Step 3: Document test matrix**

List unit, integration, UI, security and load-smoke cases with exact commands and expected results.

- [ ] **Step 4: Run release-readiness checks**

Run frontend `npm test`, `npm run lint`, `npm run build`; backend Ruff and full pytest; `docker compose config`; API smoke; browser desktop/tablet/mobile acceptance.

- [ ] **Step 5: Inspect final diff and report residual risks**

Confirm no secrets, generated DBs, `.env.local`, logs or build outputs are tracked. Record what is complete, what remains intentionally demo-only, and that multi-instance login limiting still needs Redis.
