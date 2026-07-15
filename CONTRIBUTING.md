# Contributing to NetLedger

Thanks for helping improve **NetLedger**, a lightweight IP address management platform.

## Development setup

```bash
# API
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# UI
cd frontend
npm install
npm run dev
```

Or: `make install` then `make backend` / `make frontend`.

## Quality bar

Before opening a PR:

```bash
cd backend && pytest tests -q
cd frontend && npm run build
```

Optional (if ruff installed):

```bash
cd backend && ruff check app
```

## Pull requests

1. Fork and branch from `main`  
2. Keep changes focused  
3. Update `CHANGELOG.md` under `[Unreleased]` when behavior changes  
4. Fill the PR template  

## Project principles

- Prefer clear domain services over clever abstractions  
- Keep product claims honest (no fake “AI discovery”)  
- Never commit secrets, `.env`, or database files  

## Security

Report vulnerabilities privately — see [SECURITY.md](SECURITY.md).
