# Contributing

Thanks for your interest in improving this project.

## Development

1. Fork & clone the repository  
2. Start backend and frontend (see [README](README.md))  
3. Run tests before opening a PR:

```bash
cd backend && pytest tests -q
cd frontend && npm run build
```

## Guidelines

- Keep commits focused and messages clear  
- Prefer small PRs with a short description of *why*  
- Do not commit secrets, `.env`, or `*.db` files  
- Match existing code style (Python type hints, TS strict)  

## Scope

This is primarily a **learning / demo IPAM**. Large product features (real Nmap scanning, multi-tenant SaaS, full DHCP) should be discussed in an issue first.
