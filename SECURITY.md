# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.6.x   | ✅ |
| 1.5.x   | Security fixes only |
| < 1.5   | ❌ Best-effort |

## Reporting a Vulnerability

**Please do not open a public issue for security-sensitive reports.**

1. Contact the repository owner via GitHub private channels (Security advisory if enabled, or direct message).  
2. Include: affected version, reproduction steps, impact assessment.  
3. Allow reasonable time for a fix before public disclosure.

We aim to acknowledge reports within **72 hours**.

## Security Features (current)

- Password hashing with **bcrypt**  
- Strong password validation (12+ characters; letters, digits, special characters)
- **JWT** bearer authentication with credential-version revocation
- Role-based authorization on mutating endpoints  
- Failure-only login **rate limiting** (process-local)
- Proxy-aware rate-limit identity that ignores forwarding headers by default and rejects spoofed first-hop values
- Request **access logs** with `X-Request-ID`  
- CSP, frame denial, MIME sniffing protection, referrer and permissions policies
- Production requires a strong `SECRET_KEY` when `APP_ENV=production`  
- Production refuses demo seed data and requires an explicit bootstrap administrator on an empty DB

## Hardening Checklist (production)

- [ ] Set a long random `SECRET_KEY`  
- [ ] Terminate TLS at a reverse proxy  
- [ ] Use PostgreSQL instead of SQLite for multi-user write load
- [ ] Restrict `CORS_ORIGINS`  
- [ ] Set `SEED_DEMO_DATA=false` and remove `BOOTSTRAP_ADMIN_PASSWORD` after first start
- [ ] Keep `TRUST_PROXY_HEADERS=false` unless every API request crosses a controlled proxy
- [ ] Back up the database regularly  
- [ ] Run behind a WAF / fail2ban if internet-exposed  

## Known Limitations

- In-memory rate limiting does not sync across multiple workers  
- Conflict “scan” is a **simulation** for demo workflows, not network discovery  
- Logout is client-side; password changes and admin password resets revoke existing tokens
- Bearer tokens remain accessible to same-origin JavaScript, so CSP and dependency hygiene remain important

## Dependencies

Keep `backend/requirements.txt` and `frontend/package-lock.json` updated.
Run `pip audit` / `npm audit` in CI for your fork if you deploy publicly.
