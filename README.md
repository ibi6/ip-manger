<p align="center">
  <img src="docs/assets/logo.svg" width="88" alt="NetLedger logo" />
</p>

<h1 align="center">NetLedger</h1>

<p align="center">
  <b>Enterprise-grade IP Address Management — without the enterprise tax.</b><br/>
  Operational clarity for every IPv4 address: pool · allocate · reclaim · audit.
</p>

<p align="center">
  <a href="https://github.com/ibi6/ip-manger/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/ibi6/ip-manger/actions/workflows/ci.yml/badge.svg" /></a>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-Async%20API-009688?logo=fastapi&logoColor=white" />
  <img alt="React" src="https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black" />
  <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-Strict-3178C6?logo=typescript&logoColor=white" />
  <img alt="License" src="https://img.shields.io/badge/License-MIT-yellow.svg" />
  <img alt="PRs" src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" />
</p>

<p align="center">
  <img src="docs/assets/banner.svg" width="100%" alt="NetLedger banner" />
</p>

<p align="center">
  <a href="#-why-netledger">Why</a> ·
  <a href="#-features">Features</a> ·
  <a href="#-architecture">Architecture</a> ·
  <a href="#-quick-start">Quick Start</a> ·
  <a href="#-api">API</a> ·
  <a href="#-security">Security</a> ·
  <a href="#-roadmap">Roadmap</a> ·
  <a href="#-faq">FAQ</a>
</p>

---

## 🎯 Why NetLedger

Most small networks still track IPs in **Excel**. That works until:

- two people get the same address  
- leavers never release space  
- nobody knows what `/24` utilization really is  
- audits ask “who changed this last month?”

**NetLedger** is a lightweight **IPAM control plane**: structured status, safe lifecycle operations, RBAC, and audit logs — runnable in minutes on a laptop or in Docker.

| | Spreadsheets | Heavy commercial IPAM | **NetLedger** |
|--|--------------|----------------------|---------------|
| Time to first value | Fast | Slow | **Minutes** |
| Lifecycle + audit | Manual | Strong | **Built-in** |
| Cost | Free | High | **Open source** |
| Honest scope | — | Full suite | **Inventory-first IPAM** |

> Product positioning (users, scenarios, differentiation): [`docs/PRODUCT.md`](docs/PRODUCT.md)

---

## ✨ Features

### Capability matrix

| Domain | Capabilities |
|--------|----------------|
| **Identity** | JWT auth · 4 roles · password change · login rate limit |
| **Topology** | Sites · subnets (CIDR) · auto host-pool generation |
| **Lifecycle** | allocate · reserve · release · disable · enable · allocate-next |
| **Safety** | Gateway/broadcast lock · conditional allocate · archive-first subnet delete |
| **Assets** | Device inventory · MAC uniqueness · bind device on allocate |
| **Operations** | Dashboard KPIs · audit logs · conflict records · CSV import/export |
| **Platform** | OpenAPI `/docs` · Docker Compose · pytest · GitHub Actions CI |

### Roles

| Role | Typical access |
|------|----------------|
| `admin` | Full control including users & departments |
| `network_admin` | Subnets, IP ops, devices, conflicts |
| `dept_user` | Allocate free IPs in own department scope |
| `viewer` | Read-mostly |

---

## 🧱 Tech stack

<p>
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/ORM-SQLAlchemy%202-D71F00?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Frontend-React%2019-61DAFB?style=for-the-badge&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/Language-TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white" />
  <img src="https://img.shields.io/badge/DB-SQLite%20%7C%20MySQL-003B57?style=for-the-badge&logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/Auth-JWT%20%2B%20bcrypt-000000?style=for-the-badge" />
</p>

---

## 🏗 Architecture

```text
Browser (React SPA)
        │  JWT Bearer
        ▼
   FastAPI routers  ──►  domain services  ──►  SQLAlchemy
        │                      │
        │                      ├─ CIDR pool generation
        │                      ├─ lifecycle + audit log
        │                      └─ stats aggregation
        ▼
   SQLite (demo) / MySQL / PostgreSQL
```

Deep dive: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

---

## 🖼 Screens

| Area | Route |
|------|--------|
| Login | `/login` |
| Operations dashboard | `/` |
| Subnet & live pool | `/subnets/:id` |
| Address ledger (page + batch) | `/addresses` |
| Devices | `/devices` |
| Audit log | `/logs` |
| Admin users | `/users` |

> Tip for maintainers: add a short GIF under `docs/assets/demo.gif` and embed it here for instant social proof.

---

## 🚀 Quick start

### Option A — Local (recommended for development)

**API**

```bash
cd backend
python -m venv .venv
# Windows: .\.venv\Scripts\activate
source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**UI**

```bash
cd frontend
npm install
npm run dev
```

| Service | URL |
|---------|-----|
| Web app | http://localhost:5173 (or port printed by Vite) |
| Swagger | http://127.0.0.1:8000/docs |
| Health | http://127.0.0.1:8000/health |

### Option B — Docker Compose

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Web | http://localhost |
| API | http://localhost:8000/docs |

### Option C — Makefile

```bash
make install
make test
make backend   # terminal 1
make frontend  # terminal 2
```

### Demo accounts

| User | Password | Role |
|------|----------|------|
| `admin` | `ChangeMe123!` | Administrator |
| `netadmin` | `ChangeMe123!` | Network admin |
| `biz` | `ChangeMe123!` | Department user |
| `viewer` | `ChangeMe123!` | Read-only |

---

## 📡 API

Full interactive contract: **OpenAPI at `/docs`**.  
Human overview: [`docs/API.md`](docs/API.md)

```bash
# login
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"ChangeMe123!"}'
```

Core mutations:

```http
POST /api/v1/ip-addresses/{id}/allocate
POST /api/v1/ip-addresses/{id}/release
POST /api/v1/ip-addresses/batch-release
POST /api/v1/subnets/{id}/allocate-next
POST /api/v1/subnets/{id}/archive
```

---

## 🚢 Deployment notes

| Environment | Guidance |
|-------------|----------|
| **Demo / lab** | SQLite file + Compose is enough |
| **Team internal** | Put TLS in front (Caddy/Nginx), set `SECRET_KEY`, lock CORS |
| **Production path** | Postgres/MySQL, managed secrets, backups, no default passwords |

Config template: [`backend/.env.example`](backend/.env.example)  
Schema reference: [`docs/schema.sql`](docs/schema.sql)

```env
APP_ENV=production
SECRET_KEY=<generate-a-long-random-string>
DATABASE_URL=postgresql+psycopg2://netledger:********@db:5432/netledger
CORS_ORIGINS=https://ipam.example.com
```

---

## 📊 Performance notes (design targets)

| Metric | Target (lab hardware) |
|--------|------------------------|
| List page (paginated) | Interactive on tens of thousands of rows with filters |
| Allocate under concurrency | Safe via conditional `UPDATE` (no double free→allocated race) |
| Subnet materialization | Bounded expansion (guards against huge prefixes) |
| Dashboard stats | Aggregations batched to avoid N+1 |

> Numbers vary by disk and DB engine; SQLite is for demo, not multi-writer HA.

---

## 🗺 Roadmap

- [x] IP lifecycle + RBAC + devices + audit  
- [x] Conditional allocate, batch release, subnet archive  
- [x] CI, Docker, security policy, product docs  
- [ ] Public demo environment + demo GIF  
- [ ] GHCR container publish  
- [ ] Discovery adapter interface (import ARP/Nmap results)  
- [ ] Optional OIDC login  
- [ ] First-class PostgreSQL compose profile  

---

## ❓ FAQ

**Is this a full Infoblox replacement?**  
No. NetLedger is a **lightweight inventory IPAM**. It optimizes for clarity and speed-to-deploy, not global DDI.

**Is conflict scan real network probing?**  
No. `simulate-scan` generates demo conflict records so operators can practice resolution workflows.

**Can I use MySQL?**  
Yes. Schema samples are in `docs/schema.sql`. Point `DATABASE_URL` at MySQL/Postgres for multi-user deployments.

**Is the backend Python?**  
Yes — **Python + FastAPI** is the system of record. The UI is a React SPA.

**Is this only a student project?**  
It started as a serious full-stack IPAM implementation and is packaged as a maintainable open-source product. Use it for learning, labs, or as a foundation for internal tools.

---

## 📁 Repository layout

```text
netledger/
├── backend/                 # FastAPI application + pytest
├── frontend/                # React SPA
├── docs/                    # Product, architecture, schema
├── .github/workflows/       # CI
├── docker-compose.yml
├── Makefile
└── README.md
```

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).  
Security reports: [SECURITY.md](SECURITY.md).  
Changes: [CHANGELOG.md](CHANGELOG.md).

---

## 📄 License

[MIT](LICENSE) © 2026 NetLedger contributors

---

<p align="center">
  <b>NetLedger</b> — stop managing production IPs in spreadsheets.<br/>
  Star the repo if it saves you an afternoon of Excel archaeology.
</p>
