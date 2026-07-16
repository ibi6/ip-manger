# API Overview

Interactive OpenAPI: **`/docs`** (Swagger UI) when the backend is running.

Base URL (local): `http://127.0.0.1:8000/api/v1`

## Authentication

Login failures are limited per client address. Successful logins do not consume the failure budget and clear prior failures.

```http
POST /auth/login
Content-Type: application/json

{"username":"admin","password":"ChangeMe123!"}
```

Response:

```json
{"access_token":"<jwt>","token_type":"bearer"}
```

All protected routes:

```http
Authorization: Bearer <jwt>
```

Tokens include an authentication version. Changing or resetting a password increments that version, so previously issued tokens receive `401` on their next request.

New passwords must contain 12–128 characters, at least one letter, one digit, and one special character, and must fit bcrypt's 72-byte UTF-8 boundary.

## Resource map

| Method | Path | Notes |
|--------|------|-------|
| POST | `/auth/login` | Public; rate-limited |
| GET | `/auth/me` | Current user |
| POST | `/auth/change-password` | Self-service |
| GET/POST | `/users` | Admin |
| GET/POST | `/users/departments` | List all; create admin |
| GET/POST | `/sites` | Network admin+ |
| GET/POST/DELETE | `/subnets` | Archive-first delete |
| POST | `/subnets/{id}/archive` | Soft archive |
| POST | `/subnets/{id}/allocate-next` | First free IP |
| GET | `/ip-addresses` | Paginated list (array) |
| GET | `/ip-addresses/page` | `{items,total,page,page_size}` |
| POST | `/ip-addresses/{id}/allocate` | Conditional update |
| POST | `/ip-addresses/{id}/release` | |
| POST | `/ip-addresses/batch-release` | Body: `{ids:[…]}` |
| POST | `/ip-addresses/{id}/reserve` | Optional remark |
| POST | `/ip-addresses/{id}/disable` | |
| POST | `/ip-addresses/{id}/enable` | |
| GET/POST/PATCH/DELETE | `/devices` | MAC unique |
| GET | `/logs` | Audit trail |
| GET | `/conflicts` | |
| POST | `/conflicts/simulate-scan` | Demo only |
| GET | `/dashboard/overview` | KPIs |
| GET/POST | `/io/export/*` `/io/import/*` | CSV |

## Error shape

```json
{"detail":"human readable message"}
```

Common codes: `400` business rule · `401` auth/expired or revoked token · `403` permission · `404` missing · `409` uniqueness race · `422` input validation · `429` login throttle.

Validation errors preserve the same top-level shape and include a safe field list:

```json
{
  "detail": "password: String should have at least 12 characters",
  "errors": [{"loc": ["body", "password"], "msg": "String should have at least 12 characters"}]
}
```

All API responses include `X-Request-ID` and browser security headers. Authentication responses include `Cache-Control: no-store`.

## Health

```http
GET /health
```

Returns app version, env, and database connectivity.
