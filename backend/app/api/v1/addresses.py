from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import can_allocate, can_manage_network, get_current_user
from app.db.session import get_db
from app.models import AllocationLog, IpAddress, Subnet, User
from app.schemas.common import (
    AllocateRequest,
    BatchIdsRequest,
    IpListPage,
    IpOut,
    LogOut,
    Message,
    ReserveRequest,
)
from app.services import ip_service
from app.services.serializers import ip_out, log_out

router = APIRouter()


def _load_ip(db: Session, ip_id: int) -> IpAddress | None:
    return db.scalar(
        select(IpAddress)
        .options(
            joinedload(IpAddress.subnet).joinedload(Subnet.department),
            joinedload(IpAddress.subnet).joinedload(Subnet.site),
            joinedload(IpAddress.owner),
            joinedload(IpAddress.department),
        )
        .where(IpAddress.id == ip_id)
    )


def _ip_query(
    user: User,
    *,
    subnet_id: int | None,
    status: str | None,
    q: str | None,
) -> Select[tuple[IpAddress]]:
    stmt = select(IpAddress)
    if subnet_id is not None:
        stmt = stmt.where(IpAddress.subnet_id == subnet_id)
    if status:
        stmt = stmt.where(IpAddress.status == status)
    if user.role == "dept_user":
        stmt = stmt.join(Subnet).where(Subnet.department_id == user.department_id)
    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.outerjoin(User, IpAddress.owner_user_id == User.id).where(
            or_(
                IpAddress.address.ilike(pattern),
                IpAddress.hostname.ilike(pattern),
                IpAddress.mac.ilike(pattern),
                IpAddress.device_name.ilike(pattern),
                User.display_name.ilike(pattern),
            )
        )
    return stmt


def _paged_ip_rows(
    db: Session,
    stmt: Select[tuple[IpAddress]],
    *,
    page: int,
    page_size: int,
) -> list[IpAddress]:
    paged = (
        stmt.options(
            joinedload(IpAddress.subnet),
            joinedload(IpAddress.owner),
            joinedload(IpAddress.department),
        )
        .order_by(IpAddress.subnet_id, IpAddress.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(db.scalars(paged).unique().all())


def _ip_count(db: Session, stmt: Select[tuple[IpAddress]]) -> int:
    ids = stmt.with_only_columns(IpAddress.id, maintain_column_froms=True).order_by(None).subquery()
    return int(db.scalar(select(func.count()).select_from(ids)) or 0)


@router.get("/ip-addresses", response_model=list[IpOut])
def list_ips(
    subnet_id: int | None = Query(default=None, gt=0),
    status: Literal["free", "allocated", "reserved", "disabled"] | None = None,
    q: str | None = Query(default=None, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[IpOut]:
    """兼容旧前端：仍返回数组，但支持 page / page_size。"""
    stmt = _ip_query(user, subnet_id=subnet_id, status=status, q=q)
    ips = _paged_ip_rows(db, stmt, page=page, page_size=page_size)
    return [ip_out(ip) for ip in ips]


@router.get("/ip-addresses/page", response_model=IpListPage)
def list_ips_page(
    subnet_id: int | None = Query(default=None, gt=0),
    status: Literal["free", "allocated", "reserved", "disabled"] | None = None,
    q: str | None = Query(default=None, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> IpListPage:
    stmt = _ip_query(user, subnet_id=subnet_id, status=status, q=q)
    total = _ip_count(db, stmt)
    chunk = _paged_ip_rows(db, stmt, page=page, page_size=page_size)
    return IpListPage(
        items=[ip_out(ip) for ip in chunk],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/ip-addresses/{ip_id}", response_model=IpOut)
def get_ip(
    ip_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> IpOut:
    ip = _load_ip(db, ip_id)
    if not ip:
        raise HTTPException(status_code=404, detail="地址不存在")
    if user.role == "dept_user" and ip.subnet.department_id != user.department_id:
        raise HTTPException(status_code=403, detail="无权查看")
    return ip_out(ip)


@router.post("/ip-addresses/{ip_id}/allocate", response_model=IpOut)
def allocate(
    ip_id: int,
    body: AllocateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> IpOut:
    if not can_allocate(user):
        raise HTTPException(status_code=403, detail="权限不足")
    ip = _load_ip(db, ip_id)
    if not ip:
        raise HTTPException(status_code=404, detail="地址不存在")
    if user.role == "dept_user" and ip.subnet.department_id != user.department_id:
        raise HTTPException(status_code=403, detail="只能分配本部门子网地址")
    try:
        ip_service.allocate_ip(
            db,
            ip,
            user,
            hostname=body.hostname,
            mac=body.mac,
            device_name=body.device_name,
            device_type=body.device_type,
            device_id=body.device_id,
            expire_at=body.expire_at,
            remark=body.remark,
        )
        db.commit()
    except PermissionError as exc:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    ip = _load_ip(db, ip_id)
    assert ip is not None
    return ip_out(ip)


@router.post("/ip-addresses/{ip_id}/release", response_model=IpOut)
def release(
    ip_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> IpOut:
    if not can_manage_network(user):
        raise HTTPException(status_code=403, detail="权限不足")
    ip = _load_ip(db, ip_id)
    if not ip:
        raise HTTPException(status_code=404, detail="地址不存在")
    try:
        ip_service.release_ip(db, ip, user)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    ip = _load_ip(db, ip_id)
    assert ip is not None
    return ip_out(ip)


@router.post("/ip-addresses/{ip_id}/reserve", response_model=IpOut)
def reserve(
    ip_id: int,
    body: ReserveRequest | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> IpOut:
    if not can_manage_network(user):
        raise HTTPException(status_code=403, detail="权限不足")
    ip = _load_ip(db, ip_id)
    if not ip:
        raise HTTPException(status_code=404, detail="地址不存在")
    remark = body.remark if body else "人工预留"
    try:
        ip_service.reserve_ip(db, ip, user, remark=remark)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    ip = _load_ip(db, ip_id)
    assert ip is not None
    return ip_out(ip)


@router.post("/ip-addresses/batch-release", response_model=Message)
def batch_release(
    body: BatchIdsRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Message:
    """批量回收：已分配/预留/禁用 → free。网关等系统地址会跳过。"""
    if not can_manage_network(user):
        raise HTTPException(status_code=403, detail="权限不足")
    ok = 0
    skipped: list[str] = []
    for ip_id in body.ids:
        ip = _load_ip(db, ip_id)
        if not ip:
            skipped.append(f"{ip_id}:不存在")
            continue
        try:
            ip_service.release_ip(db, ip, user)
            ok += 1
        except ValueError as exc:
            skipped.append(f"{ip.address}:{exc}")
    db.commit()
    msg = f"成功回收 {ok} 个"
    if skipped:
        msg += f"，跳过 {len(skipped)} 个"
    return Message(message=msg, data={"ok": ok, "skipped": skipped[:20]})


@router.post("/ip-addresses/{ip_id}/disable", response_model=IpOut)
def disable(
    ip_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> IpOut:
    if not can_manage_network(user):
        raise HTTPException(status_code=403, detail="权限不足")
    ip = _load_ip(db, ip_id)
    if not ip:
        raise HTTPException(status_code=404, detail="地址不存在")
    try:
        ip_service.disable_ip(db, ip, user)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    ip = _load_ip(db, ip_id)
    assert ip is not None
    return ip_out(ip)


@router.post("/ip-addresses/{ip_id}/enable", response_model=IpOut)
def enable(
    ip_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> IpOut:
    if not can_manage_network(user):
        raise HTTPException(status_code=403, detail="权限不足")
    ip = _load_ip(db, ip_id)
    if not ip:
        raise HTTPException(status_code=404, detail="地址不存在")
    try:
        ip_service.enable_ip(db, ip, user)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    ip = _load_ip(db, ip_id)
    assert ip is not None
    return ip_out(ip)


@router.post("/subnets/{subnet_id}/allocate-next", response_model=IpOut)
def allocate_next_free(
    subnet_id: int,
    body: AllocateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> IpOut:
    """在指定子网里自动找第一个 free 地址并分配。"""
    if not can_allocate(user):
        raise HTTPException(status_code=403, detail="权限不足")
    subnet = db.scalar(
        select(Subnet).options(joinedload(Subnet.department)).where(Subnet.id == subnet_id)
    )
    if not subnet:
        raise HTTPException(status_code=404, detail="子网不存在")
    if user.role == "dept_user" and subnet.department_id != user.department_id:
        raise HTTPException(status_code=403, detail="只能分配本部门子网地址")

    candidate = db.scalar(
        select(IpAddress)
        .options(joinedload(IpAddress.subnet))
        .where(
            IpAddress.subnet_id == subnet_id,
            IpAddress.status == "free",
            IpAddress.is_network_or_broadcast.is_(False),
        )
        .order_by(IpAddress.id)
        .limit(1)
    )
    if not candidate:
        raise HTTPException(status_code=400, detail="该子网没有可用空闲地址")

    ip = candidate
    # 重新带全关系，后面锁检查要用 gateway
    ip = _load_ip(db, ip.id)
    assert ip is not None
    try:
        ip_service.allocate_ip(
            db,
            ip,
            user,
            hostname=body.hostname,
            mac=body.mac,
            device_name=body.device_name,
            device_type=body.device_type,
            device_id=body.device_id,
            expire_at=body.expire_at,
            remark=body.remark,
        )
        db.commit()
    except PermissionError as exc:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    ip = _load_ip(db, ip.id)
    assert ip is not None
    return ip_out(ip)


@router.get("/logs", response_model=list[LogOut])
def list_logs(
    address: str | None = Query(default=None, max_length=50),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[LogOut]:
    stmt = select(AllocationLog)
    if user.role == "dept_user":
        stmt = (
            stmt.join(IpAddress, AllocationLog.ip_address_id == IpAddress.id)
            .join(Subnet, IpAddress.subnet_id == Subnet.id)
            .where(Subnet.department_id == user.department_id)
        )
    if address:
        stmt = stmt.where(AllocationLog.address == address)
    stmt = stmt.order_by(AllocationLog.id.desc()).limit(limit)
    logs = db.scalars(stmt).all()
    return [log_out(x) for x in logs]
