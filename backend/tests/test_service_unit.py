"""Unit-level tests without HTTP."""

from __future__ import annotations

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-characters-long!!")
os.environ.setdefault("APP_ENV", "development")

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import exceptions
from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.models import Department, IpAddress, Site, Subnet, User
from app.services.ip_service import allocate_ip, release_ip
from app.services.ip_utils import parse_network


def test_parse_network_rejects_huge():
    with pytest.raises(ValueError) as exc_info:
        parse_network("10.0.0.0/8")
    message = str(exc_info.value)
    assert "1024" in message or "前缀" in message or "展开" in message


def test_require_persisted_rejects_missing_reload():
    helper = getattr(exceptions, "require_persisted", None)
    assert helper is not None
    marker = object()
    assert helper(marker, "测试资源") is marker

    with pytest.raises(HTTPException) as exc_info:
        helper(None, "测试资源")

    assert exc_info.value.status_code == 500
    assert "数据状态异常" in exc_info.value.detail


def test_atomic_allocate_unit():
    get_settings.cache_clear()
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    db = Session()
    dept = Department(name="D", code="D")
    db.add(dept)
    db.flush()
    site = Site(name="S", code="S", location="")
    db.add(site)
    db.flush()
    user = User(
        username="u",
        display_name="U",
        password_hash=hash_password("x"),
        role="admin",
        department_id=dept.id,
    )
    db.add(user)
    db.flush()
    subnet = Subnet(
        site_id=site.id,
        department_id=dept.id,
        name="n",
        cidr="10.1.1.0/30",
        gateway="10.1.1.1",
        purpose="t",
        status="active",
    )
    db.add(subnet)
    db.flush()
    ip = IpAddress(
        subnet_id=subnet.id, address="10.1.1.2", status="free", is_network_or_broadcast=False
    )
    db.add(ip)
    db.commit()

    ip = db.get(IpAddress, ip.id)
    user = db.get(User, user.id)
    allocate_ip(db, ip, user, hostname="h1")
    db.commit()
    ip = db.get(IpAddress, ip.id)
    assert ip.status == "allocated"

    with pytest.raises(ValueError):
        allocate_ip(db, ip, user, hostname="h2")

    release_ip(db, ip, user)
    db.commit()
    ip = db.get(IpAddress, ip.id)
    assert ip.status == "free"
    db.close()
