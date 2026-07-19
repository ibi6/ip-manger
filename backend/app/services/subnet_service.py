from __future__ import annotations

import ipaddress

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import IpAddress, Subnet
from app.services.ip_utils import host_status_for, parse_network


def generate_pool(db: Session, subnet: Subnet) -> int:
    """Generate IP rows for subnet. Returns created count."""
    net = parse_network(subnet.cidr)
    existing = set(
        db.scalars(select(IpAddress.address).where(IpAddress.subnet_id == subnet.id)).all()
    )
    created = 0
    for addr in net:
        ip_str = str(addr)
        if ip_str in existing:
            continue
        status, is_nb, remark = host_status_for(addr, net, subnet.gateway)
        db.add(
            IpAddress(
                subnet_id=subnet.id,
                address=ip_str,
                status=status,
                remark=remark,
                is_network_or_broadcast=is_nb,
            )
        )
        created += 1
    db.flush()
    return created


def create_subnet_with_pool(
    db: Session,
    *,
    name: str,
    cidr: str,
    site_id: int,
    department_id: int,
    gateway: str = "",
    vlan_id: int | None = None,
    purpose: str = "通用",
    description: str | None = None,
) -> Subnet:
    net = parse_network(cidr)
    # normalize cidr string
    cidr_norm = str(net)
    exists = db.scalar(select(Subnet).where(Subnet.cidr == cidr_norm))
    if exists:
        raise ValueError("该 CIDR 已存在")

    if gateway:
        try:
            gw = ipaddress.IPv4Address(gateway)
            if gw not in net:
                raise ValueError("网关不在子网范围内")
        except ipaddress.AddressValueError as exc:
            raise ValueError("网关地址无效") from exc

    subnet = Subnet(
        site_id=site_id,
        department_id=department_id,
        name=name,
        cidr=cidr_norm,
        gateway=gateway or "",
        vlan_id=vlan_id,
        purpose=purpose,
        description=description,
        status="active",
    )
    db.add(subnet)
    db.flush()
    generate_pool(db, subnet)
    db.refresh(subnet)
    # reload relationships
    subnet = db.scalar(
        select(Subnet)
        .options(joinedload(Subnet.site), joinedload(Subnet.department))
        .where(Subnet.id == subnet.id)
    )
    if subnet is None:
        raise RuntimeError("子网写入后无法重新加载")
    return subnet
