# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.5.x   | ✅ |
| < 1.4   | ❌ Best-effort |

## Reporting a Vulnerability

**Please do not open a public issue for security-sensitive reports.**

1. Contact the repository owner via GitHub private channels (Security advisory if enabled, or direct message).  
2. Include: affected version, reproduction steps, impact assessment.  
3. Allow reasonable time for a fix before public disclosure.

We aim to acknowledge reports within **72 hours**.

## Security Features (current)

- Password hashing with **bcrypt**  
- **JWT** bearer authentication  
- Role-based authorization on mutating endpoints  
- Login **rate limiting** (process-local)  
- Request **access logs** with `X-Request-ID`  
- Production requires a strong `SECRET_KEY` when `APP_ENV=production`  

## Hardening Checklist (production)

- [ ] Set a long random `SECRET_KEY`  
- [ ] Terminate TLS at a reverse proxy  
- [ ] Use PostgreSQL/MySQL instead of SQLite for multi-user load  
- [ ] Restrict `CORS_ORIGINS`  
- [ ] Change all seed passwords  
- [ ] Disable public demo accounts  
- [ ] Back up the database regularly  
- [ ] Run behind a WAF / fail2ban if internet-exposed  

## Known Limitations

- In-memory rate limiting does not sync across multiple workers  
- Conflict “scan” is a **simulation** for demo workflows, not network discovery  
- JWT tokens are not server-side revoked until expiry (logout is client-side)  

## Dependencies

Keep `backend/requirements.txt` and `frontend/package-lock.json` updated.
Run `pip audit` / `npm audit` in CI for your fork if you deploy publicly.
