"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-15

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "sites",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=False),
        sa.Column("remark", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("avatar_color", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "subnets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("site_id", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("cidr", sa.String(length=50), nullable=False),
        sa.Column("gateway", sa.String(length=50), nullable=False),
        sa.Column("vlan_id", sa.Integer(), nullable=True),
        sa.Column("purpose", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cidr", name="uq_subnets_cidr"),
    )
    op.create_index("ix_subnets_site_id", "subnets", ["site_id"])

    op.create_table(
        "ip_addresses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("subnet_id", sa.Integer(), nullable=False),
        sa.Column("address", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("hostname", sa.String(length=100), nullable=True),
        sa.Column("mac", sa.String(length=30), nullable=True),
        sa.Column("device_name", sa.String(length=100), nullable=True),
        sa.Column("device_type", sa.String(length=30), nullable=True),
        sa.Column("owner_user_id", sa.Integer(), nullable=True),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("allocated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expire_at", sa.Date(), nullable=True),
        sa.Column("remark", sa.String(length=500), nullable=True),
        sa.Column("is_network_or_broadcast", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["subnet_id"], ["subnets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("address", name="uq_ip_addresses_address"),
    )
    op.create_index("ix_ip_addresses_subnet_id", "ip_addresses", ["subnet_id"])
    op.create_index("ix_ip_addresses_address", "ip_addresses", ["address"])
    op.create_index("ix_ip_addresses_status", "ip_addresses", ["status"])

    op.create_table(
        "allocation_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ip_address_id", sa.Integer(), nullable=True),
        sa.Column("address", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("operator_id", sa.Integer(), nullable=True),
        sa.Column("operator_name", sa.String(length=100), nullable=False),
        sa.Column("detail", sa.String(length=500), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["ip_address_id"], ["ip_addresses.id"]),
        sa.ForeignKeyConstraint(["operator_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_allocation_logs_address", "allocation_logs", ["address"])

    op.create_table(
        "conflicts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ip_address_id", sa.Integer(), nullable=True),
        sa.Column("ip_address", sa.String(length=50), nullable=False),
        sa.Column("subnet_cidr", sa.String(length=50), nullable=False),
        sa.Column("conflict_type", sa.String(length=40), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "detected_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["ip_address_id"], ["ip_addresses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conflicts_status", "conflicts", ["status"])


def downgrade() -> None:
    op.drop_table("conflicts")
    op.drop_table("allocation_logs")
    op.drop_table("ip_addresses")
    op.drop_table("subnets")
    op.drop_table("users")
    op.drop_table("sites")
    op.drop_table("departments")
