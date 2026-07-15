from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.constants import VALID_DEVICE_TYPES, VALID_IP_STATUS
from app.models import AllocationLog, Device, IpAddress, User
from app.services.ip_utils import normalize_mac

# 这几类地址不能拿去分配，不然网关没了就麻烦了
SYSTEM_RESERVED_REMARKS = frozenset({"网络地址", "广播地址", "默认网关"})


def write_log(
    db: Session,
    *,
    ip: IpAddress,
    action: str,
    operator: User,
    detail: str = "",
) -> None:
    db.add(
        AllocationLog(
            ip_address_id=ip.id,
            address=ip.address,
            action=action,
            operator_id=operator.id,
            operator_name=operator.display_name,
            detail=detail,
        )
    )


def _is_system_locked(ip: IpAddress) -> bool:
    """Network / broadcast / gateway rows must not be reclaimed or reassigned."""
    if ip.is_network_or_broadcast:
        return True
    if (ip.remark or "") in SYSTEM_RESERVED_REMARKS:
        return True
    if ip.subnet is not None and ip.subnet.gateway and ip.address == ip.subnet.gateway:
        return True
    return False


def _parse_expire(expire_at: str | None) -> date | None:
    if not expire_at or not str(expire_at).strip():
        return None
    try:
        return date.fromisoformat(str(expire_at).strip())
    except ValueError as exc:
        raise ValueError("到期日格式应为 YYYY-MM-DD") from exc


def allocate_ip(
    db: Session,
    ip: IpAddress,
    operator: User,
    *,
    hostname: str | None = None,
    mac: str | None = None,
    device_name: str | None = None,
    device_type: str | None = "pc",
    device_id: int | None = None,
    expire_at: str | None = None,
    remark: str | None = None,
) -> IpAddress:
    if _is_system_locked(ip):
        raise ValueError("系统预留地址（网络/广播/网关）不可分配")
    if ip.status != "free":
        raise ValueError("只能分配空闲地址")

    dtype = device_type or "pc"
    if dtype not in VALID_DEVICE_TYPES:
        raise ValueError(f"无效设备类型，允许: {', '.join(sorted(VALID_DEVICE_TYPES))}")

    exp = _parse_expire(expire_at)
    mac_norm = normalize_mac(mac)
    now = datetime.now(timezone.utc)

    # 如果传了 device_id，从设备台账带出名称/MAC，方便统计
    bound_device_id = device_id
    if device_id is not None:
        dev = db.get(Device, device_id)
        if not dev:
            raise ValueError("设备不存在")
        device_name = device_name or dev.name
        dtype = dev.device_type or dtype
        if not mac_norm and dev.mac:
            mac_norm = dev.mac

    # 用 where status=free 做更新，避免两个人同时点分配抢到同一个 IP
    result = db.execute(
        update(IpAddress)
        .where(
            IpAddress.id == ip.id,
            IpAddress.status == "free",
            IpAddress.is_network_or_broadcast.is_(False),
        )
        .values(
            status="allocated",
            hostname=hostname,
            mac=mac_norm,
            device_name=device_name,
            device_type=dtype,
            device_id=bound_device_id,
            owner_user_id=operator.id,
            department_id=operator.department_id,
            allocated_at=now,
            expire_at=exp,
            remark=remark,
        )
    )
    if result.rowcount != 1:
        raise ValueError("地址已被占用或不存在，请刷新后重试")

    db.refresh(ip)
    if ip.status not in VALID_IP_STATUS:
        raise ValueError("内部状态异常")

    write_log(
        db,
        ip=ip,
        action="allocate",
        operator=operator,
        detail=f"分配给 {operator.display_name}" + (f" / {device_name}" if device_name else ""),
    )
    db.flush()
    return ip


def release_ip(db: Session, ip: IpAddress, operator: User) -> IpAddress:
    if ip.status not in {"allocated", "reserved", "disabled"}:
        raise ValueError("当前状态不可回收")
    if _is_system_locked(ip):
        raise ValueError("系统预留地址（网络/广播/网关）不可回收")

    prev = ip.status
    result = db.execute(
        update(IpAddress)
        .where(
            IpAddress.id == ip.id,
            IpAddress.status.in_(["allocated", "reserved", "disabled"]),
        )
        .values(
            status="free",
            hostname=None,
            mac=None,
            device_name=None,
            device_type=None,
            device_id=None,
            owner_user_id=None,
            department_id=None,
            allocated_at=None,
            expire_at=None,
            remark=None,
        )
    )
    if result.rowcount != 1:
        raise ValueError("回收失败，地址状态已变更")

    db.refresh(ip)
    write_log(db, ip=ip, action="release", operator=operator, detail=f"从 {prev} 回收为空闲")
    db.flush()
    return ip


def reserve_ip(db: Session, ip: IpAddress, operator: User, remark: str | None = "人工预留") -> IpAddress:
    if ip.status != "free":
        raise ValueError("只能预留空闲地址")
    if _is_system_locked(ip):
        raise ValueError("网络/广播/网关地址不可再次预留操作")

    note = remark or "人工预留"
    result = db.execute(
        update(IpAddress)
        .where(IpAddress.id == ip.id, IpAddress.status == "free")
        .values(status="reserved", remark=note, owner_user_id=operator.id)
    )
    if result.rowcount != 1:
        raise ValueError("预留失败，地址状态已变更")
    db.refresh(ip)
    write_log(db, ip=ip, action="reserve", operator=operator, detail=note)
    db.flush()
    return ip


def disable_ip(db: Session, ip: IpAddress, operator: User, remark: str | None = "禁用") -> IpAddress:
    if _is_system_locked(ip):
        raise ValueError("系统预留地址不可禁用")
    if ip.status == "disabled":
        raise ValueError("已是禁用状态")

    prev = ip.status
    values: dict = {
        "status": "disabled",
        "remark": remark or "禁用",
        "hostname": None,
        "mac": None,
        "device_name": None,
        "device_type": None,
        "device_id": None,
        "owner_user_id": None,
        "department_id": None,
        "allocated_at": None,
        "expire_at": None,
    }
    result = db.execute(
        update(IpAddress)
        .where(IpAddress.id == ip.id, IpAddress.status != "disabled")
        .values(**values)
    )
    if result.rowcount != 1:
        raise ValueError("禁用失败，地址状态已变更")
    db.refresh(ip)
    write_log(db, ip=ip, action="disable", operator=operator, detail=f"从 {prev} 禁用")
    db.flush()
    return ip


def enable_ip(db: Session, ip: IpAddress, operator: User) -> IpAddress:
    """把禁用地址恢复成空闲，方便重新分配。"""
    if _is_system_locked(ip):
        raise ValueError("系统预留地址不可操作")
    if ip.status != "disabled":
        raise ValueError("只有禁用状态的地址可以启用")
    result = db.execute(
        update(IpAddress)
        .where(IpAddress.id == ip.id, IpAddress.status == "disabled")
        .values(status="free", remark=None)
    )
    if result.rowcount != 1:
        raise ValueError("启用失败，地址状态已变更")
    db.refresh(ip)
    write_log(db, ip=ip, action="enable", operator=operator, detail="从 disabled 恢复为 free")
    db.flush()
    return ip
