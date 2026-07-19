# NetLedger Comprehensive Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按《毕业设计项目优化与调试指南》消除已确认的依赖漏洞、越权、数据泄露、异常处理、性能和页面闭环问题，并以真实启动、接口、浏览器、生产构建和部署检查证明项目可演示、可部署。

**Architecture:** 保留 React 19 + TypeScript + Vite 前端、Python 3.11+ + FastAPI + SQLAlchemy 后端和 SQLite/PostgreSQL 双数据库架构。修复围绕现有 API 契约进行：后端统一数据范围和认证撤销语义，前端统一请求生命周期与路由状态，数据库只通过现有 ORM/Alembic 管理，不引入新中间件或微服务。

**Tech Stack:** Python 3.11、FastAPI、SQLAlchemy 2、Alembic、PyJWT、pytest、React 19、TypeScript、Vite、Tailwind CSS 4、oxlint、Docker Compose、Nginx。

## Global Constraints

- 保持 Python/FastAPI 后端与 React/TypeScript 前端，不更换框架或数据库。
- 不生成或修改论文、PPT、开题报告和答辩材料。
- 所有权限必须由后端强制执行，前端权限仅用于界面展示。
- 任何数据库结构变化必须保留已有数据并提供 Alembic 迁移；本计划未要求新增字段。
- 不硬编码密钥、密码或 Token；开发演示账号与生产初始化严格隔离。
- 每个修复先写能复现问题的测试，再实施最小修复并运行相关回归。
- 保持现有青绿色 NetLedger 视觉方向；只补齐错误、无权限、404、加载和响应式状态。

---

### Task 1: 修复已知依赖漏洞并替换无修复 JWT 依赖

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/app/core/security.py`
- Test: `backend/tests/test_auth.py`

**Interfaces:**
- Consumes: `get_secret_key()`, `Settings.algorithm`, JWT `sub`/`exp`/`ver` 载荷。
- Produces: `create_access_token(subject, extra) -> str` 与 `decode_token(token) -> dict[str, Any]`，签名和异常契约保持不变。

- [x] **Step 1: 增加 JWT 兼容测试**

在 `backend/tests/test_auth.py` 增加测试，断言登录 Token 可被 `decode_token` 解码，`sub`、`ver` 与登录用户一致，损坏 Token 抛出 `ValueError`。

```python
def test_login_token_round_trip(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "ChangeMe123!"},
    )
    payload = decode_token(response.json()["access_token"])
    assert payload["sub"] == "admin"
    assert isinstance(payload["ver"], int)


def test_decode_rejects_damaged_token():
    with pytest.raises(ValueError, match="invalid token"):
        decode_token("not-a-jwt")
```

- [x] **Step 2: 运行 JWT 测试确认当前契约**

Run: `backend\.venv\Scripts\python.exe -m pytest tests/test_auth.py -q`

Expected: 现有实现通过 round-trip；损坏 Token 由统一 `ValueError` 契约处理。

- [x] **Step 3: 最小化升级受影响依赖**

将生产依赖锁定为：

```text
fastapi==0.139.2
starlette==1.3.1
PyJWT==2.13.0
python-multipart==0.0.32
```

删除 `python-jose[cryptography]`，保留其余依赖版本不变。这样移除无修复 `ecdsa` 及旧 `pyasn1` 依赖，同时满足 `pip-audit` 报告的 Starlette 和 multipart 修复版本。

- [x] **Step 4: 将 JWT 实现切换到 PyJWT**

在 `backend/app/core/security.py` 使用：

```python
import jwt
from jwt import InvalidTokenError


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, get_secret_key(), algorithms=[settings.algorithm])
    except InvalidTokenError as exc:
        raise ValueError("invalid token") from exc
```

`create_access_token` 继续使用 `jwt.encode(payload, key, algorithm=...)`，不改变 API 返回格式。

- [x] **Step 5: 安装并验证依赖安全**

Run:

```powershell
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
$env:PYTHONUTF8='1'
backend\.venv\Scripts\python.exe -m pip_audit -r backend\requirements.txt
backend\.venv\Scripts\python.exe -m pytest backend\tests\test_auth.py -q
```

Expected: `pip-audit` 输出 `No known vulnerabilities found`，认证测试通过。

### Task 2: 增加服务端注销并完善认证配置边界

**Files:**
- Modify: `backend/app/api/v1/auth.py`
- Modify: `backend/app/core/config.py`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/lib/auth-context.ts`
- Modify: `frontend/src/lib/auth-provider.tsx`
- Modify: `frontend/src/components/layout/AppShell.tsx`
- Test: `backend/tests/test_auth.py`
- Test: `backend/tests/test_startup_policy.py`

**Interfaces:**
- Produces: `POST /api/v1/auth/logout -> Message`，成功后递增当前用户 `auth_version`，使旧 Token 立即失效。
- Produces: `logout() -> Promise<void>`，前端无论网络结果如何都清理本地 Token。

- [x] **Step 1: 写旧 Token 注销失效测试**

```python
def test_logout_revokes_current_token(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "viewer", "password": "ChangeMe123!"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 200
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
```

- [x] **Step 2: 实现服务端注销**

`logout` 通过 `db.get(User, user.id)` 取得实体，递增 `auth_version`、提交并返回 `Message(message="已安全退出")`。不存在用户时返回 404，不记录 Token 或密码。

- [x] **Step 3: 约束认证相关环境变量**

将 `access_token_expire_minutes`、`login_rate_limit`、`login_rate_window_seconds` 改为带边界的 Pydantic `Field`：分别为 `1..10080`、`1..1000`、`1..86400`。增加配置越界测试，预期 `ValidationError`。

- [x] **Step 4: 同步前端注销调用**

新增 `api.logout()`；`AuthContextValue.logout` 改为异步。`AuthProvider.logout` 先尝试调用接口，在 `finally` 中执行 `setToken(null)` 与 `setUser(null)`；`AppShell.performLogout` 等待完成后跳转登录页并防止重复点击。

- [x] **Step 5: 验证认证生命周期**

Run: `backend\.venv\Scripts\python.exe -m pytest backend\tests\test_auth.py backend\tests\test_startup_policy.py -q`

Expected: 登录、注销、改密、生产密钥和配置边界测试全部通过。

### Task 3: 修复部门数据越权与导出泄露

**Files:**
- Modify: `backend/app/services/ip_service.py`
- Modify: `backend/app/api/v1/io_csv.py`
- Modify: `backend/app/api/v1/addresses.py`
- Modify: `backend/app/api/v1/conflicts.py`
- Modify: `backend/app/api/v1/dashboard.py`
- Modify: `backend/app/services/serializers.py`
- Test: `backend/tests/test_rbac.py`
- Test: `backend/tests/test_csv_security.py`

**Interfaces:**
- Consumes: `User.role`, `User.department_id` 与 `Subnet.department_id`。
- Produces: 部门用户只能读取、导出和绑定本部门的子网、地址、设备、冲突、日志和看板统计；管理员、网络管理员和 viewer 的现有全局读取能力保持不变。

- [ ] **Step 1: 写跨部门设备绑定拒绝测试**

以 admin 取得其他部门设备 ID 与研发中心空闲 IP，再用 `biz` 调用 allocate 并传入该设备 ID，断言 403 且地址仍为 free。

- [ ] **Step 2: 写 CSV 数据范围测试**

使用 `biz` 导出 subnets 与 ip-addresses，断言响应中不包含其他部门 CIDR；使用 admin 导出时仍包含全部数据。

- [ ] **Step 3: 在服务层强制设备数据范围**

`allocate_ip` 读取 `Device` 后执行：

```python
if operator.role == "dept_user" and dev.department_id != operator.department_id:
    raise PermissionError("无权绑定其他部门设备")
```

路由层将 `PermissionError` 映射为 403，`ValueError` 保持 400。

- [ ] **Step 4: 统一部门过滤**

CSV 查询在 `user.role == "dept_user"` 时按 `Subnet.department_id == user.department_id` 过滤。日志和冲突通过关联 IP/Subnet 限制数据范围；`dashboard_out(db, user)` 对部门用户的地址、子网、冲突和最近日志应用同一过滤条件。

- [ ] **Step 5: 运行权限回归**

Run: `backend\.venv\Scripts\python.exe -m pytest backend\tests\test_rbac.py backend\tests\test_csv_security.py -q`

Expected: 越权请求 403，部门导出无跨部门数据，管理员路径不回归。

### Task 4: 加固 CSV 导入与异常处理

**Files:**
- Modify: `backend/app/api/v1/io_csv.py`
- Modify: `backend/app/core/exceptions.py`
- Test: `backend/tests/test_csv_security.py`
- Test: `backend/tests/test_validation_and_sites.py`

**Interfaces:**
- Produces: CSV 仅接受 `.csv` 且 MIME 为 `text/csv`、`application/csv`、`application/vnd.ms-excel` 或 `application/octet-stream`；仅接受严格 UTF-8 BOM/UTF-8/GBK 文本；VLAN 必须为空或 `1..4094`。

- [ ] **Step 1: 写无效 MIME、编码和 VLAN 测试**

分别上传伪装为 `.csv` 的 `image/png`、无法按 UTF-8/GBK 解码的字节、`vlan_id=abc` 与 `vlan_id=4095`，断言 400/415 且不创建子网。

- [ ] **Step 2: 实施严格输入校验**

读取文件前校验扩展名和 MIME；GBK 回退不使用 `errors="ignore"`；表头必须包含 `name,cidr,site_code`；VLAN 非空时必须是十进制且在范围内。

- [ ] **Step 3: 避免内部异常泄露**

为 `io_csv` 建立模块 logger。未知异常执行 `logger.exception("CSV 第 %s 行导入失败", i)`，用户响应只返回 `第{i}行：服务器处理失败`，不拼接数据库或路径异常文本。

- [ ] **Step 4: 保留 HTTP 异常响应头并记录未处理异常**

`http_exception_handler` 将 `exc.headers` 传给 `JSONResponse`；`unhandled_exception_handler` 使用 `logger.exception` 记录服务端堆栈，响应继续使用通用 500 文案。

- [ ] **Step 5: 运行 CSV 与异常测试**

Run: `backend\.venv\Scripts\python.exe -m pytest backend\tests\test_csv_security.py backend\tests\test_validation_and_sites.py -q`

Expected: 所有恶意或损坏输入被拒绝，响应不泄露内部异常。

### Task 5: 将地址搜索和分页下推数据库

**Files:**
- Modify: `backend/app/api/v1/addresses.py`
- Test: `backend/tests/test_page_and_mac.py`
- Test: `backend/tests/test_service_unit.py`

**Interfaces:**
- Produces: `_ip_query(db, user, subnet_id, status, q) -> Select`；分页接口以 SQL `COUNT/LIMIT/OFFSET` 返回相同 `IpListPage` 契约。

- [ ] **Step 1: 写稳定分页与搜索测试**

创建至少两个子网，验证 page 1/page 2 无重复、`total` 正确、责任人和 MAC 搜索仍能命中，部门用户搜索不越权。

- [ ] **Step 2: 构建 SQL 查询**

使用 SQLAlchemy `or_` 与 `ilike` 过滤 address/hostname/mac/device_name/owner display name；部门用户通过 Subnet join 加范围条件。按 `IpAddress.subnet_id, IpAddress.id` 稳定排序，因为地址池按数字顺序创建。

- [ ] **Step 3: 下推分页**

`list_ips_page` 使用 count 子查询和 `offset((page - 1) * page_size).limit(page_size)`；兼容数组接口使用相同查询与最大 500 条限制，不再把全部地址载入 Python。

- [ ] **Step 4: 优化下一空闲地址查询**

将候选地址查询改为 `order_by(IpAddress.id).limit(1)`，保留条件更新防并发双分配。

- [ ] **Step 5: 运行地址生命周期回归**

Run: `backend\.venv\Scripts\python.exe -m pytest backend\tests\test_page_and_mac.py backend\tests\test_ip_lifecycle.py backend\tests\test_service_unit.py -q`

Expected: 分页/搜索正确，分配并发保护和生命周期行为不变。

### Task 6: 清除生产 assert 并修复统一错误语义

**Files:**
- Modify: `backend/app/core/exceptions.py`
- Modify: `backend/app/api/v1/addresses.py`
- Modify: `backend/app/api/v1/devices.py`
- Modify: `backend/app/api/v1/subnets.py`
- Modify: `backend/app/api/v1/users.py`
- Modify: `backend/app/services/subnet_service.py`
- Format: `backend/scripts/smoke_test.py`
- Test: `backend/tests/test_service_unit.py`

**Interfaces:**
- Produces: `require_persisted(entity, resource) -> entity`，在提交后实体意外消失时记录错误并返回稳定 500，而不是依赖会被 `python -O` 删除的 assert。

- [ ] **Step 1: 增加持久化不变量测试**

直接调用 `require_persisted(None, "地址")`，断言抛出 500 HTTPException 且文案不含 SQL/路径；非空实体原样返回。

- [ ] **Step 2: 实现并替换 13 处生产 assert**

```python
def require_persisted(entity: T | None, resource: str) -> T:
    if entity is None:
        logger.error("%s 写入后无法重新加载", resource)
        raise HTTPException(status_code=500, detail="数据状态异常，请重试")
    return entity
```

所有 API 与服务重载位置使用此函数或等价显式 `RuntimeError`，不保留生产 `assert`。

- [ ] **Step 3: 修复 Ruff 格式门禁**

Run: `backend\.venv\Scripts\python.exe -m ruff format backend\scripts\smoke_test.py`

- [ ] **Step 4: 执行源码安全和格式检查**

Run:

```powershell
backend\.venv\Scripts\python.exe -m bandit -r backend\app -q
backend\.venv\Scripts\python.exe -m ruff check backend
backend\.venv\Scripts\python.exe -m ruff format --check backend
```

Expected: Bandit 无问题，Ruff lint/format 全通过。

### Task 7: 统一前端请求超时、上传下载和认证失效处理

**Files:**
- Modify: `frontend/src/lib/api.ts`
- Test: `frontend/tests/network-error.test.ts`

**Interfaces:**
- Produces: 所有 JSON、上传与下载请求共享 Authorization、AbortController、15 秒超时、401 清理和网络错误文案。

- [ ] **Step 1: 提取请求上下文辅助函数并补测试**

为超时配置归一化、401 判断和错误消息提取建立可导出的纯函数，Node 测试覆盖无效超时值、JSON detail 与非 JSON 响应。

- [ ] **Step 2: 统一 fetch 生命周期**

将超时、调用方 abort、Authorization 和 401 跳转放入一个底层 `authorizedFetch(pathOrUrl, init)`；`request`、`importSubnets`、`downloadAuth` 都通过它执行。

- [ ] **Step 3: 修复对象 URL 生命周期**

下载后将临时 `<a>` 插入 DOM、点击、移除，再在下一事件循环撤销 Object URL，确保 Firefox/Chromium 均能完成下载。

- [ ] **Step 4: 执行前端单测与构建**

Run: `npm test -- --run && npm run lint && npm run build`（工作目录 `frontend`）

Expected: 测试、oxlint、TypeScript 与 Vite 构建通过。

### Task 8: 补齐权限页、404 与页面交互闭环

**Files:**
- Create: `frontend/src/pages/ForbiddenPage.tsx`
- Create: `frontend/src/pages/NotFoundPage.tsx`
- Modify: `frontend/src/app/router.tsx`
- Modify: `frontend/src/pages/SubnetFormPage.tsx`
- Modify: `frontend/src/pages/AddressesPage.tsx`
- Modify: `frontend/src/components/layout/AppShell.tsx`

**Interfaces:**
- Produces: `/users` 非管理员显示明确 403 页面；未知 URL 显示 404 并提供返回工作台；新建子网页面有站点加载/失败/空状态；搜索总从第 1 页执行。

- [ ] **Step 1: 增加管理员路由守卫**

在路由层新增 `AdminOnly`，从 `useAuth().canAdmin` 判断；无权限时渲染 `ForbiddenPage`，后端 403 仍为最终安全边界。

- [ ] **Step 2: 增加 403/404 页面**

复用 `Card`、`Button`、lucide-react 图标与现有色板，包含清晰标题、说明和返回工作台按钮；不增加依赖。

- [ ] **Step 3: 修复子网表单异步状态**

`SubnetFormPage` 捕获 `api.sites()` 失败并显示 `ErrorBlock`；加载时显示 `LoadingBlock`；无站点时提示先创建站点并禁用提交；组件卸载后不更新状态。

- [ ] **Step 4: 修复地址搜索页码竞态**

让 `load` 接收明确的 `targetPage`，搜索按钮和 Enter 调用 `load(1)`；筛选变更由 effect 使用当前 page 加载，避免 `setPage(1)` 后仍请求旧页。

- [ ] **Step 5: 修复批量选择可访问状态**

表头复选框仅在本页全部可回收项选中时 `checked=true`，部分选择使用 `indeterminate=true`，并提供 `aria-label`。

- [ ] **Step 6: 执行 UI 静态门禁**

Run: `npm test -- --run && npm run lint && npm run build`（工作目录 `frontend`）

Expected: 生产构建通过，无类型与 Lint 错误。

### Task 9: 真实启动、接口、浏览器、数据库和部署验收

**Files:**
- Modify: `docs/TESTING.md`
- Modify: `CHANGELOG.md`
- Modify: `README.md` only if actual run commands or behavior changed.

**Interfaces:**
- Consumes: 完成后的后端、前端、SQLite 数据库和 Compose 配置。
- Produces: 可复现的最终测试证据与剩余外部条件。

- [ ] **Step 1: 完整自动化门禁**

Run:

```powershell
backend\.venv\Scripts\python.exe -m pytest backend\tests -q
backend\.venv\Scripts\python.exe -m ruff check backend
backend\.venv\Scripts\python.exe -m ruff format --check backend
frontend\node_modules\.bin\oxlint frontend\src frontend\tests
npm --prefix frontend test -- --run
npm --prefix frontend run build
docker compose config
git diff --check
```

Expected: 全部退出码为 0。

- [ ] **Step 2: 真实启动独立测试实例**

后端使用临时 SQLite、`127.0.0.1:8002`，前端使用 `127.0.0.1:5176` 并指向 8002。轮询 `/health` 与登录页直至就绪，不用固定 sleep。

- [ ] **Step 3: 执行 API 核心流程**

运行 `backend/scripts/smoke_test.py --base-url http://127.0.0.1:8002/api/v1`，并额外验证 admin、viewer、biz 的 401/403、注销失效、跨部门设备绑定拒绝、CSV 导入/导出、分页和数据库持久化。

- [ ] **Step 4: 执行浏览器验收**

检查登录、退出、工作台、站点、子网、地址、设备、日志、冲突、用户、设置、403、404；检查控制台和网络错误；在 375、768、1024、1440、1920 宽度确认无页面级横向溢出、导航可用、表格可滚动、弹窗不越界、主题切换持久化。

- [ ] **Step 5: 验证生产容器**

Run: `docker compose build`。若 Docker daemon 可用，再执行 `docker compose up -d`、`docker compose ps` 与前端 `/health`；若 daemon 不可用，保留真实错误作为外部条件，不伪造成功。

- [ ] **Step 6: 更新文档和变更记录**

在 `docs/TESTING.md` 记录新增安全/权限/注销/CSV/404 验收项；在 `CHANGELOG.md` 的 2.0.0 后增加 `Unreleased` 修复条目，准确描述已完成内容与命令。

- [ ] **Step 7: 最终完成度审计**

逐项对照 Word 指南的运行、功能、页面、数据库、安全、测试和部署清单；最终报告按“项目分析、发现问题、已完成修改、测试结果、剩余问题、运行说明、10 分制评估”输出，所有结论只引用本轮实际证据。

