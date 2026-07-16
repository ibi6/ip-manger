"""Prepare a new or legacy database before the API process starts."""

from __future__ import annotations

import logging

from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command
from app.core.config import get_settings

logger = logging.getLogger("netledger.migrations")
BASELINE_TABLES = {
    "departments",
    "sites",
    "users",
    "subnets",
    "ip_addresses",
    "allocation_logs",
    "conflicts",
}


def prepare_database() -> None:
    """Stamp legacy create-all databases, then upgrade every database to head."""
    settings = get_settings()
    engine = create_engine(settings.database_url)
    try:
        tables = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    alembic_config = Config("alembic.ini")
    if tables and "alembic_version" not in tables:
        missing = BASELINE_TABLES - tables
        if missing:
            missing_text = ", ".join(sorted(missing))
            raise RuntimeError(f"旧数据库结构不完整，缺少基础表：{missing_text}")
        logger.warning("检测到未纳入 Alembic 的旧数据库，将从 0001 基线继续迁移")
        command.stamp(alembic_config, "0001")
    command.upgrade(alembic_config, "head")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    prepare_database()
