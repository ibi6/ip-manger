<p align="center">
  <img src="frontend/public/favicon.svg" width="72" height="72" alt="logo" />
</p>

<h1 align="center">企业 IP 地址管理系统</h1>

<p align="center">
  <b>Enterprise IP Address Management (IPAM)</b><br/>
  轻量、可演示、可扩展的内网 IPv4 地址全生命周期管理平台
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" />
  <img alt="React" src="https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black" />
  <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white" />
  <img alt="SQLite" src="https://img.shields.io/badge/SQLite-Ready-003B57?logo=sqlite&logoColor=white" />
  <img alt="Tests" src="https://img.shields.io/badge/pytest-32%20passed-success" />
  <img alt="License" src="https://img.shields.io/badge/License-MIT-yellow.svg" />
</p>

<p align="center">
  <a href="#-features">Features</a> ·
  <a href="#-architecture">Architecture</a> ·
  <a href="#-quick-start">Quick Start</a> ·
  <a href="#-api">API</a> ·
  <a href="#-security">Security</a> ·
  <a href="#-screenshots">Screens</a>
</p>

---

## ✨ Features

| Module | Capabilities |
|--------|----------------|
| **Auth & RBAC** | JWT login, 4 roles, login rate-limit, change password |
| **Sites / Subnets** | CIDR validation, auto IP pool generation, archive safety |
| **IP Lifecycle** | allocate · reserve · release · disable · enable · allocate-next |
| **Concurrency** | Conditional `UPDATE … WHERE status='free'` to avoid double-assign |
| **Devices** | Device inventory, MAC uniqueness, bind on allocate, CSV export |
| **Ops** | Audit logs, conflict records (simulate scan), dashboard stats |
| **Admin** | User CRUD, departments, CSV import/export |
| **DX** | OpenAPI `/docs`, Docker Compose, pytest suite |

### Role matrix (simplified)

| Role | Read | Allocate | Release / Archive | Users |
|------|------|----------|-------------------|-------|
| `admin` | ✅ | ✅ | ✅ | ✅ |
| `network_admin` | ✅ | ✅ | ✅ | — |
| `dept_user` | own dept | own dept free IPs | — | — |
| `viewer` | ✅ | — | — | — |

---

## 🏗 Architecture

```text
┌──────────────┐     JWT + REST      ┌─────────────────┐
│  React SPA   │ ──────────────────► │  FastAPI (v1)   │
│  Vite + TS   │ ◄────────────────── │  SQLAlchemy 2   │
└──────────────┘                     └────────┬────────┘
                                              │
                                     ┌────────▼────────┐
                                     │ SQLite / MySQL  │
                                     │  (schema.sql)   │
                                     └─────────────────┘
```

**Backend layers:** `api` → `services` → `models`  
**Key domain logic:** `app/services/ip_utils.py`, `ip_service.py`, `subnet_service.py`

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- (Optional) Docker

### 1) Backend

```bash
cd backend
python -m venv .venv

# Windows
.\.venv\Scripts\activate

pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API docs: http://127.0.0.1:8000/docs  
- Health: http://127.0.0.1:8000/health  

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the URL shown in terminal (e.g. http://localhost:5173).

### 3) Docker (one command)

```bash
docker compose up --build
```

- Web: http://localhost  
- API: http://localhost:8000/docs  

### 4) Tests

```bash
cd backend
pytest tests -q
```

---

## 🔐 Demo accounts

| Username | Role | Password |
|----------|------|----------|
| `admin` | Administrator | `ChangeMe123!` |
| `netadmin` | Network admin | `ChangeMe123!` |
| `biz` | Department user | `ChangeMe123!` |
| `viewer` | Read-only | `ChangeMe123!` |

> Demo passwords only. Change them in real deployments.

---

## 📡 API

Base path: `/api/v1`

| Area | Examples |
|------|----------|
| Auth | `POST /auth/login` · `POST /auth/change-password` |
| Users | `GET/POST /users` · `POST /users/departments` |
| Sites / Subnets | `CRUD` + `POST /subnets/{id}/archive` |
| IPs | allocate / release / reserve / disable / enable / batch-release |
| Devices | `GET/POST/PATCH/DELETE /devices` |
| Ops | `/dashboard/overview` · `/logs` · `/conflicts` · `/io/export/*` |

Interactive docs: **Swagger UI** at `/docs`.

---

## 🛡 Security

- Passwords hashed with **bcrypt**
- **JWT** access tokens
- Login **rate limiting** (in-process)
- Request access log + `X-Request-ID`
- Production requires strong `SECRET_KEY` (`APP_ENV=production`)
- Department-scoped allocate for `dept_user`

---

## 🗄 Data model (core)

```text
departments ─┬─ users
             └─ subnets ── ip_addresses ── allocation_logs
sites ───────┘                 │
devices ───────────────────────┘
conflicts
```

Full SQL: [`docs/schema.sql`](docs/schema.sql) (SQLite + MySQL samples).

---

## 🖥 Screens

| Screen | Path |
|--------|------|
| Login | `/login` |
| Dashboard | `/` |
| Subnets & IP pool | `/subnets`, `/subnets/:id` |
| Address ledger | `/addresses` |
| Devices | `/devices` |
| Audit logs | `/logs` |
| Users | `/users` (admin) |
| Settings / CSV / password | `/settings` |

---

## 📁 Project layout

```text
.
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/v1/          # REST routers
│   │   ├── core/            # config, security, middleware
│   │   ├── models/          # SQLAlchemy models
│   │   ├── services/        # domain logic
│   │   └── seed.py          # demo data
│   ├── tests/               # pytest
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                # React SPA
│   ├── src/pages/
│   ├── src/components/
│   └── Dockerfile
├── docs/                    # design notes & schema
├── docker-compose.yml
└── README.md
```

---

## ⚙️ Configuration

Copy `backend/.env.example` → `backend/.env` if needed:

```env
APP_ENV=development
SECRET_KEY=          # empty = auto file for local dev
DATABASE_URL=sqlite:///./ipam.db
CORS_ORIGINS=http://localhost:5173,http://localhost:5175
```

Production:

```env
APP_ENV=production
SECRET_KEY=<random-32+-chars>
DATABASE_URL=postgresql+psycopg2://user:pass@host/ipam
```

---

## 🗺️ Roadmap

- [x] IP lifecycle + RBAC + devices + logs  
- [x] Conditional allocate / batch release / subnet archive  
- [x] pytest + Docker  
- [ ] Real network discovery (ARP/Nmap adapters)  
- [ ] DHCP integration  
- [ ] IPv6 planning  

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

<p align="center">
  Built for learning & demo · Not a commercial IPAM replacement<br/>
  If this repo helps you, consider giving it a ⭐
</p>
