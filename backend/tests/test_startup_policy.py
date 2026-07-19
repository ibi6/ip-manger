from __future__ import annotations

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.base import Base
from app.models import Site, User
from app.seed import initialize_data


@pytest.fixture()
def empty_db():
    """Provide an isolated empty schema for startup-policy tests."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)


def production_settings(**overrides) -> Settings:
    """Build production settings without reading a developer `.env` file."""
    values = {
        "APP_ENV": "production",
        "SECRET_KEY": "production-test-secret-key-at-least-32-chars",
        "seed_demo_data": False,
        "bootstrap_admin_username": "admin",
        "bootstrap_admin_display_name": "Platform Administrator",
        "bootstrap_admin_password": "",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_production_requires_bootstrap_password_for_empty_database(empty_db):
    with pytest.raises(RuntimeError, match="BOOTSTRAP_ADMIN_PASSWORD"):
        initialize_data(empty_db, production_settings())

    assert empty_db.scalar(select(func.count()).select_from(User)) == 0


def test_production_rejects_demo_seed_even_when_explicitly_requested(empty_db):
    with pytest.raises(RuntimeError, match="SEED_DEMO_DATA"):
        initialize_data(empty_db, production_settings(seed_demo_data=True))


def test_production_bootstrap_creates_only_one_admin(empty_db):
    initialize_data(
        empty_db,
        production_settings(bootstrap_admin_password="BootstrapSecure99!"),
    )

    assert empty_db.scalar(select(func.count()).select_from(User)) == 1
    assert empty_db.scalar(select(User.username)) == "admin"
    assert empty_db.scalar(select(User.role)) == "admin"
    assert empty_db.scalar(select(func.count()).select_from(Site)) == 0


def test_unknown_app_environment_is_rejected():
    """A production typo must not silently downgrade to development safety rules."""
    with pytest.raises(ValidationError, match="APP_ENV"):
        Settings(
            _env_file=None,
            APP_ENV="prodution",
            SECRET_KEY="production-test-secret-key-at-least-32-chars",
        )


def test_production_secret_policy_cannot_be_bypassed_by_environment_flag():
    """Production must fail closed even if a legacy bypass flag is supplied."""
    settings = Settings(
        _env_file=None,
        APP_ENV="production",
        SECRET_KEY="",
        allow_insecure_defaults=True,
    )

    with pytest.raises(RuntimeError, match="生产环境必须设置足够长的 SECRET_KEY"):
        settings.resolve_secret_key()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("access_token_expire_minutes", 0),
        ("access_token_expire_minutes", 10081),
        ("login_rate_limit", 0),
        ("login_rate_limit", 1001),
        ("login_rate_window_seconds", 0),
        ("login_rate_window_seconds", 86401),
    ],
)
def test_security_runtime_limits_are_bounded(field, value):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{field: value})
