from __future__ import annotations

import os

# Must set before app imports
os.environ["APP_ENV"] = "development"
os.environ["SECRET_KEY"] = "test-secret-key-at-least-32-characters-long!!"
os.environ["DATABASE_URL"] = "sqlite://"  # in-memory will be overridden per connection

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.rate_limit import reset_rate_limits
from app.core.security import get_secret_key  # noqa: F401 — warm settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.seed import seed_if_empty

get_settings.cache_clear()


@pytest.fixture()
def client():
    reset_rate_limits()
    get_settings.cache_clear()

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _fk(dbapi_connection, _):  # type: ignore[no-untyped-def]
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()

    def _override():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def auth_header(client: TestClient, username: str = "admin") -> dict[str, str]:
    r = client.post("/api/v1/auth/login", json={"username": username, "password": "ChangeMe123!"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
