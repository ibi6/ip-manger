# NetLedger 测试与验收

## 1. 本地质量门禁

后端：

```powershell
cd backend
python -m pip install -r requirements-dev.txt
ruff check app tests alembic
python -m pytest -q
```

前端：

```powershell
cd frontend
npm ci
npm test
npm run lint
npm run build
```

部署配置：

```powershell
docker compose config
```

根目录也可运行：

```powershell
make lint
make test
```

## 2. 自动化覆盖

### 2.1 单元测试

| 领域 | 关键用例 | 期望 |
|------|----------|------|
| CIDR | 超大网段、网络/广播/网关 | 拒绝超限；系统地址不可分配 |
| MAC | 标准化、非法格式、唯一性 | 统一大写冒号；重复被拒绝 |
| 格式化 | 空日期、ISO 时间、百分比越界 | 输出稳定；0–100 限幅 |
| 地址服务 | 分配后再次分配、回收 | 条件更新防重复；状态恢复 free |

### 2.2 集成测试

| 场景 | 请求 | 期望 |
|------|------|------|
| 登录 | 正确/错误凭据 | 200/401；只有失败消耗额度 |
| 暴力破解 | 连续 8 次失败后再试 | 第 9 次 429 |
| 恢复登录 | 失败后使用正确密码 | 成功并清空失败桶 |
| 改密 | 旧 token 再访问 `/auth/me` | 401 |
| 生产空库 | 无 bootstrap 密码 | 启动策略快速失败 |
| 跨部门设备 | dept_user 指定其他部门 | 403 |
| 输入校验 | 空站点、非法编码、VLAN 4095 | 422 |
| 安全头 | `/health`、`/auth/login` | CSP/nosniff/frame deny；认证 no-store |
| RBAC | viewer 创建子网 | 403 |
| 地址生命周期 | 分配、预留、禁用、启用、回收 | 状态与审计一致 |

## 3. API 冒烟

启动后端后：

```powershell
cd backend
python scripts/smoke_test.py
curl.exe -i http://127.0.0.1:8000/health
```

健康响应必须同时满足：HTTP 200、`status=ok`、`database=up`、版本与发布版本一致，并包含 `X-Request-ID`。

## 4. UI 验收

对 375×812、768×1024、1440×900 分别检查：

1. 登录页不横向溢出；生产构建不显示演示账号入口。
2. 用户名/密码 label 与输入框关联；错误信息使用 alert/live region。
3. 工作台统计、利用率、最近操作正常加载，失败时有重试入口。
4. 移动菜单按钮有名称与 expanded 状态；Escape 可关闭；抽屉包含用户、角色和退出。
5. 表格只在自身容器内横向滚动；页面主体不横向滚动。
6. 所有按钮在手机端至少 44px；键盘焦点清晰；跳过导航可用。
7. 站点、子网、地址、设备、冲突、用户、设置页面的空/加载/错误/成功状态可辨识。
8. 修改密码前端最小长度为 12，后端继续执行完整复杂度校验。

可访问性快速检查：所有可见 `button`/`a` 有非空可访问名称；每个可见 `input`/`select`/`textarea` 可由 label 定位；标题层级不跳跃；颜色不是唯一状态信号。

## 5. 安全测试

- 修改 JWT 任一字符，访问受保护接口应为 401。
- 修改密码后旧 token 应为 401。
- viewer/network_admin/admin 的管理入口和 API 权限应与矩阵一致。
- CSV 上传超过代理限制时由 Nginx 拒绝；格式错误时 API 返回 400，不写入半成品事务。
- 生产空库不设置 bootstrap 密码时必须启动失败，且不能出现 `ChangeMe123!` 用户。
- 发送伪造 `X-Forwarded-For` 时，直接运行模式应继续按真实连接地址限流。
- API/SPA 响应应包含 CSP、frame deny、nosniff、referrer 与 permissions policy。

## 6. 性能与压力烟测

在与生产相近的 PostgreSQL 测试环境执行，避免把 SQLite 单写限制误判为应用吞吐：

- 读：工作台、站点、子网和分页地址列表，各 20 并发、持续 5 分钟。
- 写：不同空闲地址上的分配/回收，验证无双分配且审计数量一致。
- 目标：无 5xx、无数据库连接泄漏、P95 可解释且无随时间增长趋势。
- 观察：CPU、内存、数据库连接、锁等待、P95、429、5xx 和日志 request id。

任何压力测试都使用专用数据和账号，不对生产地址池执行写入。

## 7. 用户验收用例

| 编号 | 角色 | 操作 | 验收结果 |
|------|------|------|----------|
| UAT-01 | admin | 首次登录并修改密码 | 新密码可登录，旧密码和旧 token 均失效 |
| UAT-02 | network_admin | 新建站点/子网并自动建池 | 地址数量、网关预留、利用率正确 |
| UAT-03 | dept_user | 分配本部门空闲 IP | 成功且有审计；其他部门返回 403 |
| UAT-04 | viewer | 浏览台账并尝试写操作 | 浏览成功，写操作不可见且 API 返回 403 |
| UAT-05 | network_admin | 绑定设备、回收地址 | 设备/IP 关系与状态同步 |
| UAT-06 | admin | 手机端打开菜单并退出 | 抽屉可用、焦点可见、成功返回登录页 |
