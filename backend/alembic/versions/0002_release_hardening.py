"""Align migrations with devices and revocable authentication.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _column_names(table: str) -> set[str]:
    """Return current column names through the active migration connection."""
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)}


def _index_names(table: str) -> set[str]:
    """Return current index names through the active migration connection."""
    return {
        index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table) if index.get("name")
    }


def _foreign_key_names(table: str) -> set[str]:
    """Return named foreign keys; unnamed SQLite keys are represented as empty strings."""
    return {
        foreign_key.get("name") or ""
        for foreign_key in sa.inspect(op.get_bind()).get_foreign_keys(table)
    }


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    if "devices" not in tables:
        op.create_table(
            "devices",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("device_type", sa.String(length=30), server_default="other", nullable=False),
            sa.Column("mac", sa.String(length=30), nullable=True),
            sa.Column("location", sa.String(length=200), nullable=True),
            sa.Column("department_id", sa.Integer(), nullable=True),
            sa.Column("owner_user_id", sa.Integer(), nullable=True),
            sa.Column("remark", sa.String(length=500), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
            sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    if "uq_devices_mac" not in _index_names("devices"):
        op.create_index("uq_devices_mac", "devices", ["mac"], unique=True)

    if "auth_version" not in _column_names("users"):
        op.add_column(
            "users",
            sa.Column("auth_version", sa.Integer(), server_default="0", nullable=False),
        )

    ip_columns = _column_names("ip_addresses")
    ip_indexes = _index_names("ip_addresses")
    ip_foreign_keys = _foreign_key_names("ip_addresses")
    with op.batch_alter_table("ip_addresses") as batch:
        if "device_id" not in ip_columns:
            batch.add_column(sa.Column("device_id", sa.Integer(), nullable=True))
        if "fk_ip_addresses_device_id_devices" not in ip_foreign_keys:
            batch.create_foreign_key(
                "fk_ip_addresses_device_id_devices",
                "devices",
                ["device_id"],
                ["id"],
            )
        if "ix_ip_addresses_device_id" not in ip_indexes:
            batch.create_index("ix_ip_addresses_device_id", ["device_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("ip_addresses") as batch:
        if "ix_ip_addresses_device_id" in _index_names("ip_addresses"):
            batch.drop_index("ix_ip_addresses_device_id")
        if "device_id" in _column_names("ip_addresses"):
            batch.drop_column("device_id")

    if "auth_version" in _column_names("users"):
        with op.batch_alter_table("users") as batch:
            batch.drop_column("auth_version")

    if "devices" in set(sa.inspect(op.get_bind()).get_table_names()):
        op.drop_table("devices")
