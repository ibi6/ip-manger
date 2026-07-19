from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AllocationLog, Conflict, IpAddress, Site, Subnet, User
from app.schemas.common import (
    ConflictOut,
    DashboardOut,
    DeviceOut,
    IpOut,
    LogOut,
    SiteOut,
    SubnetOut,
    UserOut,
)


def _dt(v: datetime | date | None) -> str | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.isoformat()
    return v.isoformat()


def user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        department_id=user.department_id,
        department_name=user.department.name if user.department else "",
        avatar_color=user.avatar_color,
        is_active=bool(user.is_active),
    )


def site_out(site: Site, subnet_count: int = 0) -> SiteOut:
    return SiteOut(
        id=site.id,
        name=site.name,
        code=site.code,
        location=site.location or "",
        remark=site.remark,
        subnet_count=subnet_count,
    )


def _stats_from_counts(counts: dict[str, int]) -> dict[str, int | float]:
    total = sum(counts.values())
    used = counts.get("allocated", 0)
    free = counts.get("free", 0)
    reserved = counts.get("reserved", 0)
    disabled = counts.get("disabled", 0)
    non_free = used + reserved + disabled
    util = round(non_free / total * 100, 1) if total else 0.0
    return {
        "total_ips": total,
        "used_ips": used,
        "free_ips": free,
        "reserved_ips": reserved,
        "disabled_ips": disabled,
        "utilization": util,
    }


def subnet_stats(db: Session, subnet_id: int) -> dict[str, int | float]:
    rows = db.execute(
        select(IpAddress.status, func.count())
        .where(IpAddress.subnet_id == subnet_id)
        .group_by(IpAddress.status)
    ).all()
    counts = {status: n for status, n in rows}
    return _stats_from_counts(counts)


def batch_subnet_stats(db: Session, subnet_ids: list[int]) -> dict[int, dict[str, int | float]]:
    """One GROUP BY query for many subnets — avoids N+1 on list endpoints."""
    if not subnet_ids:
        return {}
    rows = db.execute(
        select(IpAddress.subnet_id, IpAddress.status, func.count())
        .where(IpAddress.subnet_id.in_(subnet_ids))
        .group_by(IpAddress.subnet_id, IpAddress.status)
    ).all()
    by_subnet: dict[int, dict[str, int]] = {sid: {} for sid in subnet_ids}
    for sid, status, n in rows:
        by_subnet.setdefault(sid, {})[status] = n
    return {sid: _stats_from_counts(counts) for sid, counts in by_subnet.items()}


def subnet_out(
    db: Session,
    subnet: Subnet,
    stats: dict[str, int | float] | None = None,
) -> SubnetOut:
    st = stats if stats is not None else subnet_stats(db, subnet.id)
    return SubnetOut(
        id=subnet.id,
        site_id=subnet.site_id,
        site_name=subnet.site.name if subnet.site else "",
        name=subnet.name,
        cidr=subnet.cidr,
        gateway=subnet.gateway or "",
        vlan_id=subnet.vlan_id,
        purpose=subnet.purpose,
        department_id=subnet.department_id,
        department_name=subnet.department.name if subnet.department else "",
        description=subnet.description,
        total_ips=int(st["total_ips"]),
        used_ips=int(st["used_ips"]),
        free_ips=int(st["free_ips"]),
        reserved_ips=int(st["reserved_ips"]),
        disabled_ips=int(st["disabled_ips"]),
        utilization=float(st["utilization"]),
        status=subnet.status,
        created_at=_dt(subnet.created_at),
    )


def subnets_out(db: Session, subnets: list[Subnet]) -> list[SubnetOut]:
    stats_map = batch_subnet_stats(db, [s.id for s in subnets])
    return [subnet_out(db, s, stats=stats_map.get(s.id)) for s in subnets]


def ip_out(ip: IpAddress) -> IpOut:
    return IpOut(
        id=ip.id,
        subnet_id=ip.subnet_id,
        subnet_cidr=ip.subnet.cidr if ip.subnet else "",
        address=ip.address,
        status=ip.status,
        hostname=ip.hostname,
        mac=ip.mac,
        device_name=ip.device_name,
        device_type=ip.device_type,
        device_id=ip.device_id,
        owner_name=ip.owner.display_name if ip.owner else None,
        owner_user_id=ip.owner_user_id,
        department_id=ip.department_id,
        department_name=ip.department.name if ip.department else None,
        allocated_at=_dt(ip.allocated_at),
        expire_at=_dt(ip.expire_at),
        remark=ip.remark,
        is_network_or_broadcast=ip.is_network_or_broadcast,
    )


def device_out(dev) -> DeviceOut:
    bound = None
    if getattr(dev, "addresses", None):
        for a in dev.addresses:
            if a.status == "allocated":
                bound = a.address
                break
    return DeviceOut(
        id=dev.id,
        name=dev.name,
        device_type=dev.device_type,
        mac=dev.mac,
        location=dev.location,
        department_id=dev.department_id,
        department_name=dev.department.name if dev.department else None,
        owner_user_id=dev.owner_user_id,
        owner_name=dev.owner.display_name if dev.owner else None,
        remark=dev.remark,
        bound_ip=bound,
        created_at=_dt(dev.created_at),
    )


def log_out(log: AllocationLog) -> LogOut:
    return LogOut(
        id=log.id,
        address=log.address,
        action=log.action,
        operator_name=log.operator_name,
        detail=log.detail,
        created_at=_dt(log.created_at) or "",
    )


def conflict_out(c: Conflict) -> ConflictOut:
    return ConflictOut(
        id=c.id,
        ip_address=c.ip_address,
        subnet_cidr=c.subnet_cidr,
        type=c.conflict_type,
        detail=c.detail,
        status=c.status,
        detected_at=_dt(c.detected_at) or "",
    )


def dashboard_out(db: Session, user: User) -> DashboardOut:
    department_id = user.department_id if user.role == "dept_user" else None
    if department_id is None:
        site_count = db.scalar(select(func.count()).select_from(Site)) or 0
    else:
        site_count = (
            db.scalar(
                select(func.count(func.distinct(Subnet.site_id))).where(
                    Subnet.status == "active",
                    Subnet.department_id == department_id,
                )
            )
            or 0
        )

    subnet_count_stmt = select(func.count()).select_from(Subnet).where(Subnet.status == "active")
    if department_id is not None:
        subnet_count_stmt = subnet_count_stmt.where(Subnet.department_id == department_id)
    subnet_count = db.scalar(subnet_count_stmt) or 0

    status_stmt = select(IpAddress.status, func.count()).group_by(IpAddress.status)
    if department_id is not None:
        status_stmt = status_stmt.join(Subnet).where(Subnet.department_id == department_id)
    status_rows = db.execute(status_stmt).all()
    counts = {s: n for s, n in status_rows}
    total = sum(counts.values())
    free = counts.get("free", 0)
    allocated = counts.get("allocated", 0)
    reserved = counts.get("reserved", 0)
    disabled = counts.get("disabled", 0)

    conflict_stmt = select(func.count()).select_from(Conflict).where(Conflict.status == "open")
    if department_id is not None:
        conflict_stmt = (
            conflict_stmt.join(IpAddress, Conflict.ip_address_id == IpAddress.id)
            .join(Subnet, IpAddress.subnet_id == Subnet.id)
            .where(Subnet.department_id == department_id)
        )
    open_conflicts = db.scalar(conflict_stmt) or 0

    now = datetime.now(UTC).date()
    soon = now + timedelta(days=30)
    expiring_stmt = (
        select(func.count())
        .select_from(IpAddress)
        .where(
            IpAddress.status == "allocated",
            IpAddress.expire_at.is_not(None),
            IpAddress.expire_at >= now,
            IpAddress.expire_at <= soon,
        )
    )
    if department_id is not None:
        expiring_stmt = expiring_stmt.join(Subnet).where(Subnet.department_id == department_id)
    expiring = db.scalar(expiring_stmt) or 0

    subnet_stmt = select(Subnet).where(Subnet.status == "active")
    if department_id is not None:
        subnet_stmt = subnet_stmt.where(Subnet.department_id == department_id)
    subnets = list(db.scalars(subnet_stmt).all())
    stats_map = batch_subnet_stats(db, [s.id for s in subnets])
    top = [
        {
            "name": s.name,
            "cidr": s.cidr,
            "utilization": stats_map.get(s.id, {}).get("utilization", 0.0),
        }
        for s in subnets
    ]
    top.sort(key=lambda x: x["utilization"], reverse=True)

    logs_stmt = select(AllocationLog)
    if department_id is not None:
        logs_stmt = (
            logs_stmt.join(IpAddress, AllocationLog.ip_address_id == IpAddress.id)
            .join(Subnet, IpAddress.subnet_id == Subnet.id)
            .where(Subnet.department_id == department_id)
        )
    logs = db.scalars(logs_stmt.order_by(AllocationLog.id.desc()).limit(8)).all()

    return DashboardOut(
        site_count=site_count,
        subnet_count=subnet_count,
        total_ips=total,
        free_ips=free,
        allocated_ips=allocated,
        reserved_ips=reserved,
        disabled_ips=disabled,
        open_conflicts=open_conflicts,
        expiring_soon=expiring,
        top_subnets=top[:5],
        recent_logs=[log_out(x) for x in logs],
    )
