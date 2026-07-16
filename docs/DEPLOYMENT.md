# NetLedger 部署、备份与回滚

## 1. 部署模型

NetLedger 发布链路为：浏览器 → HTTPS 入口 → Nginx SPA → FastAPI → SQLite 或 PostgreSQL。仓库内 Compose 提供 Nginx 与 API；生产 TLS 建议由负载均衡、Ingress、Caddy 或外层 Nginx 终止。

- SQLite：适合单节点、小团队、低并发写入；数据位于 `ipam_data` volume。
- PostgreSQL：适合正式多用户环境；使用托管实例或独立数据库服务。
- API 容器启动前运行 Alembic；检测到旧版 `create_all` 数据库时先标记 0001 基线，再升级到 head。

## 2. 首次生产部署

### 2.1 准备根目录 `.env`

```env
APP_ENV=production
SECRET_KEY=替换为至少32字符的密码学随机值
ACCESS_TOKEN_EXPIRE_MINUTES=120
SEED_DEMO_DATA=false
BOOTSTRAP_ADMIN_USERNAME=admin
BOOTSTRAP_ADMIN_DISPLAY_NAME=平台管理员
BOOTSTRAP_ADMIN_PASSWORD=替换为至少12位且含字母数字特殊字符的强密码
CORS_ORIGINS=https://ipam.example.com

# 单节点 SQLite
DATABASE_URL=sqlite:////data/ipam.db

# PostgreSQL（二选一；容器内不要使用 127.0.0.1 指向宿主数据库）
# DATABASE_URL=postgresql+psycopg://netledger:强密码@postgres.example.internal:5432/netledger
```

生成密钥示例：

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 2.2 校验并启动

```powershell
docker compose config
docker compose build
docker compose up -d
docker compose ps
curl.exe -fsS http://127.0.0.1:8000/health
```

首次健康后立即登录、修改管理员密码，并从 `.env` 删除 `BOOTSTRAP_ADMIN_PASSWORD`。已有用户的数据库不会再次执行引导。

```powershell
docker compose up -d --force-recreate backend
```

### 2.3 TLS 与网络边界

- 公网或跨网段访问必须启用 HTTPS。
- 只向外暴露 TLS 入口；Compose 已把 API 8000 绑定到宿主回环地址。
- 容器显式以 `--no-proxy-headers` 启动 Uvicorn，代理身份只由应用策略解析；`TRUST_PROXY_HEADERS` 在 Compose 内固定为 `true`，因为 API 通过受控 Nginx 到达。Nginx 会覆盖客户端传入的 `X-Forwarded-For`，后端仅采用代理追加链最右侧的合法 IP。直接运行 Uvicorn 时保持默认 `false`。
- `CORS_ORIGINS` 只列出实际前端源，不使用 `*`。

## 3. 数据库迁移

查看当前版本：

```powershell
docker compose exec backend alembic current
docker compose exec backend alembic history
```

手动升级（容器入口正常情况下已自动执行）：

```powershell
docker compose exec backend python -m app.db.prepare_database
```

发布前必须先备份。不要在没有备份的情况下执行 downgrade；本项目回滚优先恢复数据库快照。

## 4. 备份与恢复

### 4.1 SQLite 在线备份

先在容器内使用 SQLite backup API 生成一致性副本，再复制到宿主机：

```powershell
docker compose exec backend python -c "import sqlite3; s=sqlite3.connect('/data/ipam.db'); d=sqlite3.connect('/data/ipam.backup.db'); s.backup(d); d.close(); s.close()"
docker compose cp backend:/data/ipam.backup.db .\backups\ipam-$(Get-Date -Format yyyyMMdd-HHmmss).db
```

恢复前停止 API 并保留当前文件：

```powershell
docker compose stop backend
docker compose cp .\backups\ipam-YYYYMMDD-HHMMSS.db backend:/data/ipam.restore.db
docker compose run --rm --entrypoint python backend -c "from pathlib import Path; Path('/data/ipam.db').replace('/data/ipam.pre-restore.db'); Path('/data/ipam.restore.db').replace('/data/ipam.db')"
docker compose up -d backend frontend
curl.exe -fsS http://127.0.0.1:8000/health
```

### 4.2 PostgreSQL

```powershell
pg_dump --format=custom --no-owner --file .\backups\netledger-YYYYMMDD.dump $env:DATABASE_URL
pg_restore --clean --if-exists --no-owner --dbname $env:DATABASE_URL .\backups\netledger-YYYYMMDD.dump
```

恢复应先在隔离环境演练，并核对用户数、站点数、子网数、地址状态总数和最近审计记录。

## 5. 版本回滚

1. 记录当前镜像摘要与 `alembic current`。
2. 创建数据库备份。
3. 切换到上一个已验证 tag/commit 或镜像摘要。
4. 若新版本执行了不可逆数据变更，恢复发布前数据库备份；不要盲目 downgrade。
5. `docker compose up -d --build`。
6. 验证 `/health`、登录、工作台、地址查询、一次可回滚的分配/回收流程。

## 6. 监控与日志

```powershell
docker compose ps
docker compose logs --tail 200 backend
docker compose logs --tail 200 frontend
curl.exe -i http://127.0.0.1:8000/health
```

建议监控：

- `/health` 非 200、`status=degraded` 或 `database=down`。
- 5xx 比例、P95 延迟、429 数量、容器重启次数。
- volume/数据库磁盘使用率和备份新鲜度。
- 开放冲突、30 日内到期地址以及异常审计事件。

日志中包含 `X-Request-ID`，排障时应同时记录客户端时间、路径、状态码和 request id。日志不得记录密码、JWT 或生产密钥。

## 7. 发布检查清单

- [ ] `SEED_DEMO_DATA=false`。
- [ ] 强 `SECRET_KEY` 已进入密钥系统而非仓库。
- [ ] 引导密码已在首次启动后移除。
- [ ] HTTPS、CORS、备份、恢复演练完成。
- [ ] `docker compose config`、Ruff、pytest、前端 test/lint/build 全通过。
- [ ] 375/768/1440 三档 UI 主流程通过。
- [ ] 已记录镜像摘要、迁移版本和回滚点。
