from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import can_manage_network, get_current_user
from app.db.session import get_db
from app.models import Conflict, IpAddress, User
from app.schemas.common import ConflictOut, Message
from app.services.serializers import conflict_out

router = APIRouter(prefix="/conflicts")


@router.get("", response_model=list[ConflictOut])
def list_conflicts(
    status: str | None = "open",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ConflictOut]:
    stmt = select(Conflict).order_by(Conflict.id.desc())
    if status and status != "all":
        stmt = stmt.where(Conflict.status == status)
    return [conflict_out(c) for c in db.scalars(stmt).all()]


@router.post("/{conflict_id}/resolve", response_model=ConflictOut)
def resolve_conflict(
    conflict_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ConflictOut:
    if not can_manage_network(user):
        raise HTTPException(status_code=403, detail="权限不足")
    c = db.get(Conflict, conflict_id)
    if not c:
        raise HTTPException(status_code=404, detail="冲突不存在")
    c.status = "resolved"
    db.commit()
    db.refresh(c)
    return conflict_out(c)


@router.post("/simulate-scan", response_model=Message)
@router.post("/scan", response_model=Message, include_in_schema=False)  # alias
def simulate_scan_conflicts(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Message:
    """演示用模拟扫描（非真实 ARP/Nmap），在空闲地址上生成一条 rogue_host 冲突。"""
    if not can_manage_network(user):
        raise HTTPException(status_code=403, detail="权限不足")

    free_ip = db.scalar(
        select(IpAddress)
        .options(joinedload(IpAddress.subnet))
        .where(IpAddress.status == "free", IpAddress.is_network_or_broadcast.is_(False))
        .limit(1)
    )
    if not free_ip:
        return Message(message="模拟扫描完成：未找到可用于演示的空闲地址")

    c = Conflict(
        ip_address_id=free_ip.id,
        ip_address=free_ip.address,
        subnet_cidr=free_ip.subnet.cidr if free_ip.subnet else "",
        conflict_type="rogue_host",
        detail=f"【模拟】发现未登记主机尝试使用空闲地址 {free_ip.address}（非真实探测）",
        status="open",
        detected_at=datetime.now(timezone.utc),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return Message(
        message=f"模拟扫描完成：新增冲突 {c.ip_address}",
        data={"conflict_id": c.id, "mode": "simulate"},
    )
