.PHONY: help install test backend frontend docker-up docker-down lint

help:
	@echo "NetLedger targets:"
	@echo "  make install     - install backend + frontend deps"
	@echo "  make test        - run pytest"
	@echo "  make backend     - run API on :8000"
	@echo "  make frontend    - run Vite dev server"
	@echo "  make docker-up   - docker compose up --build"
	@echo "  make docker-down - docker compose down"

install:
	cd backend && python -m pip install -r requirements-dev.txt
	cd frontend && npm ci

test:
	cd backend && python -m pytest tests -q
	cd frontend && npm test

lint:
	cd backend && python -m ruff check app tests alembic
	cd frontend && npm run lint

backend:
	cd backend && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

frontend:
	cd frontend && npm run dev

docker-up:
	docker compose up --build

docker-down:
	docker compose down
