from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

from app.core.config import get_settings
from app.db.prepare_database import prepare_database


def test_prepare_database_upgrades_an_empty_database(tmp_path, monkeypatch):
    """The container migration entrypoint must build the complete schema from zero."""
    database_path = tmp_path / "netledger.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    backend_root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(backend_root)
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()
    exception_logger = logging.getLogger("ipam.exceptions")
    exception_logger.disabled = False

    try:
        prepare_database()
        engine = create_engine(database_url)
        schema = inspect(engine)
        assert "devices" in schema.get_table_names()
        assert "auth_version" in {column["name"] for column in schema.get_columns("users")}
        assert "device_id" in {column["name"] for column in schema.get_columns("ip_addresses")}
        assert any(
            index["name"] == "uq_devices_mac" and index["unique"]
            for index in schema.get_indexes("devices")
        )
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0002"
        assert exception_logger.disabled is False
        engine.dispose()
    finally:
        get_settings.cache_clear()
