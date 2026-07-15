from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    users: Mapped[list[User]] = relationship(back_populates="department")
    subnets: Mapped[list[Subnet]] = relationship(back_populates="department")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="viewer")
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)
    avatar_color: Mapped[str] = mapped_column(String(20), default="#0d9488")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    department: Mapped[Department] = relationship(back_populates="users")


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    location: Mapped[str] = mapped_column(String(200), default="")
    remark: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    subnets: Mapped[list[Subnet]] = relationship(back_populates="site", cascade="all, delete-orphan")


class Subnet(Base):
    __tablename__ = "subnets"
    __table_args__ = (UniqueConstraint("cidr", name="uq_subnets_cidr"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"), nullable=False, index=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    cidr: Mapped[str] = mapped_column(String(50), nullable=False)
    gateway: Mapped[str] = mapped_column(String(50), default="")
    vlan_id: Mapped[int | None] = mapped_column(Integer)
    purpose: Mapped[str] = mapped_column(String(100), default="通用")
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    site: Mapped[Site] = relationship(back_populates="subnets")
    department: Mapped[Department] = relationship(back_populates="subnets")
    addresses: Mapped[list[IpAddress]] = relationship(
        back_populates="subnet", cascade="all, delete-orphan"
    )


class Device(Base):
    """设备台账：可以先建设备，再绑到某个 IP 上。"""

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    device_type: Mapped[str] = mapped_column(String(30), default="other")
    mac: Mapped[str | None] = mapped_column(String(30), index=True)
    location: Mapped[str | None] = mapped_column(String(200))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    remark: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    department: Mapped[Department | None] = relationship(foreign_keys=[department_id])
    owner: Mapped[User | None] = relationship(foreign_keys=[owner_user_id])
    addresses: Mapped[list[IpAddress]] = relationship(back_populates="device")


class IpAddress(Base):
    __tablename__ = "ip_addresses"
    __table_args__ = (UniqueConstraint("address", name="uq_ip_addresses_address"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subnet_id: Mapped[int] = mapped_column(ForeignKey("subnets.id"), nullable=False, index=True)
    address: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="free", index=True)
    hostname: Mapped[str | None] = mapped_column(String(100))
    mac: Mapped[str | None] = mapped_column(String(30))
    device_name: Mapped[str | None] = mapped_column(String(100))
    device_type: Mapped[str | None] = mapped_column(String(30))
    device_id: Mapped[int | None] = mapped_column(ForeignKey("devices.id"), index=True)
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    allocated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expire_at: Mapped[date | None] = mapped_column(Date)
    remark: Mapped[str | None] = mapped_column(String(500))
    is_network_or_broadcast: Mapped[bool] = mapped_column(Boolean, default=False)

    subnet: Mapped[Subnet] = relationship(back_populates="addresses")
    device: Mapped[Device | None] = relationship(back_populates="addresses")
    owner: Mapped[User | None] = relationship(foreign_keys=[owner_user_id])
    department: Mapped[Department | None] = relationship(foreign_keys=[department_id])


class AllocationLog(Base):
    __tablename__ = "allocation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ip_address_id: Mapped[int | None] = mapped_column(ForeignKey("ip_addresses.id"))
    address: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    operator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    operator_name: Mapped[str] = mapped_column(String(100), default="")
    detail: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Conflict(Base):
    __tablename__ = "conflicts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ip_address_id: Mapped[int | None] = mapped_column(ForeignKey("ip_addresses.id"))
    ip_address: Mapped[str] = mapped_column(String(50), nullable=False)
    subnet_cidr: Mapped[str] = mapped_column(String(50), default="")
    conflict_type: Mapped[str] = mapped_column(String(40), nullable=False)
    detail: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
