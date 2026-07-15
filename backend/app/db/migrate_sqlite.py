"""给已有 SQLite 库补列/补表（create_all 不会改旧表）。"""

from __future__ import annotations

from sqlalchemy import inspect, text

from app.db.session import engine


def ensure_sqlite_schema() -> None:
    if engine.dialect.name != "sqlite":
        return
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    with engine.begin() as conn:
        if "devices" not in tables:
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS devices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(100) NOT NULL,
                        device_type VARCHAR(30) NOT NULL DEFAULT 'other',
                        mac VARCHAR(30),
                        location VARCHAR(200),
                        department_id INTEGER,
                        owner_user_id INTEGER,
                        remark VARCHAR(500),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_devices_mac ON devices (mac)"))

        if "ip_addresses" in tables:
            cols = {c["name"] for c in insp.get_columns("ip_addresses")}
            if "device_id" not in cols:
                conn.execute(text("ALTER TABLE ip_addresses ADD COLUMN device_id INTEGER"))
                conn.execute(
                    text("CREATE INDEX IF NOT EXISTS ix_ip_addresses_device_id ON ip_addresses (device_id)")
                )
