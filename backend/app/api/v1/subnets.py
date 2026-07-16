from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import can_manage_network, get_current_user
from app.db.session import get_db
from app.models import IpAddress, Subnet, User
from app.schemas.common import Message, SubnetCreate, SubnetOut
from app.services.serializers import subnet_out, subnets_out
from app.services.subnet_service import create_subnet_with_pool

router = APIRouter(prefix="/subnets")


def _load_subnet(db: Session, subnet_id: int) -> Subnet | None:
    return db.scalar(
        select(Subnet)
        .options(joinedload(Subnet.site), joinedload(Subnet.department))
        .where(Subnet.id == subnet_id)
    )


@router.get("", response_model=list[SubnetOut])
def list_subnets(
    site_id: int | None = Query(default=None, gt=0),
    q: str | None = Query(default=None, max_length=100),
    include_archived: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[SubnetOut]:
    stmt = select(Subnet).options(joinedload(Subnet.site), joinedload(Subnet.department))
    if site_id is not None:
        stmt = stmt.where(Subnet.site_id == site_id)
    if not include_archived:
        stmt = stmt.where(Subnet.status == "active")
    if user.role == "dept_user":
        stmt = stmt.where(Subnet.department_id == user.department_id)
    subnets = db.scalars(stmt.order_by(Subnet.id.desc())).unique().all()
    if q:
        ql = q.lower()
        subnets = [
            s
            for s in subnets
            if ql in s.name.lower()
            or ql in s.cidr.lower()
            or ql in (s.purpose or "").lower()
            or (s.site and ql in s.site.name.lower())
        ]
    return subnets_out(db, list(subnets))


@router.get("/{subnet_id}", response_model=SubnetOut)
def get_subnet(
    subnet_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SubnetOut:
    subnet = _load_subnet(db, subnet_id)
    if not subnet:
        raise HTTPException(status_code=404, detail="子网不存在")
    if user.role == "dept_user" and subnet.department_id != user.department_id:
        raise HTTPException(status_code=403, detail="无权查看该子网")
    return subnet_out(db, subnet)


@router.post("", response_model=SubnetOut, status_code=status.HTTP_201_CREATED)
def create_subnet(
    body: SubnetCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SubnetOut:
    if not can_manage_network(user):
        raise HTTPException(status_code=403, detail="权限不足")
    dept_id = body.department_id or user.department_id
    try:
        subnet = create_subnet_with_pool(
            db,
            name=body.name,
            cidr=body.cidr,
            site_id=body.site_id,
            department_id=dept_id,
            gateway=body.gateway,
            vlan_id=body.vlan_id,
            purpose=body.purpose,
            description=body.description,
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    subnet = _load_subnet(db, subnet.id)
    assert subnet is not None
    return subnet_out(db, subnet)


@router.post("/{subnet_id}/archive", response_model=Message)
def archive_subnet(
    subnet_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Message:
    """软归档：有已分配地址时不允许，避免误操作。"""
    if not can_manage_network(user):
        raise HTTPException(status_code=403, detail="权限不足")
    subnet = _load_subnet(db, subnet_id)
    if not subnet:
        raise HTTPException(status_code=404, detail="子网不存在")
    if subnet.status == "archived":
        return Message(message="子网已是归档状态")
    used = (
        db.scalar(
            select(func.count())
            .select_from(IpAddress)
            .where(IpAddress.subnet_id == subnet_id, IpAddress.status == "allocated")
        )
        or 0
    )
    if used > 0:
        raise HTTPException(
            status_code=400,
            detail=f"该子网还有 {used} 个已分配地址，请先回收再归档",
        )
    subnet.status = "archived"
    db.commit()
    return Message(message="子网已归档（可在 include_archived 中查看）")


@router.post("/{subnet_id}/restore", response_model=Message)
def restore_subnet(
    subnet_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Message:
    if not can_manage_network(user):
        raise HTTPException(status_code=403, detail="权限不足")
    subnet = _load_subnet(db, subnet_id)
    if not subnet:
        raise HTTPException(status_code=404, detail="子网不存在")
    subnet.status = "active"
    db.commit()
    return Message(message="子网已恢复为 active")


@router.delete("/{subnet_id}", response_model=Message)
def delete_subnet(
    subnet_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Message:
    """默认改为归档；仅 archived 且无已分配地址时才允许物理删除。"""
    if not can_manage_network(user):
        raise HTTPException(status_code=403, detail="权限不足")
    subnet = _load_subnet(db, subnet_id)
    if not subnet:
        raise HTTPException(status_code=404, detail="子网不存在")
    used = (
        db.scalar(
            select(func.count())
            .select_from(IpAddress)
            .where(IpAddress.subnet_id == subnet_id, IpAddress.status == "allocated")
        )
        or 0
    )
    if used > 0:
        raise HTTPException(
            status_code=400,
            detail=f"该子网还有 {used} 个已分配地址，请先回收",
        )
    # 第一次点删除：归档；已归档再删：物理删除
    if subnet.status != "archived":
        subnet.status = "archived"
        db.commit()
        return Message(message="子网已归档（再点删除才会永久移除）")
    db.delete(subnet)
    db.commit()
    return Message(message="子网已永久删除")
