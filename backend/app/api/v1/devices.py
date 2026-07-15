"""设备台账：先登记设备，再在分配 IP 时绑定。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import can_manage_network, get_current_user
from app.core.constants import VALID_DEVICE_TYPES
from app.db.session import get_db
from app.models import Department, Device, User
from app.schemas.common import DeviceCreate, DeviceOut, DeviceUpdate
from app.services.ip_utils import normalize_mac
from app.services.serializers import device_out

router = APIRouter(prefix="/devices", tags=["devices"])


def _load(db: Session, device_id: int) -> Device | None:
    return db.scalar(
        select(Device)
        .options(
            joinedload(Device.department),
            joinedload(Device.owner),
            joinedload(Device.addresses),
        )
        .where(Device.id == device_id)
    )


@router.get("", response_model=list[DeviceOut])
def list_devices(
    q: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[DeviceOut]:
    stmt = select(Device).options(
        joinedload(Device.department),
        joinedload(Device.owner),
        joinedload(Device.addresses),
    )
    if user.role == "dept_user":
        stmt = stmt.where(Device.department_id == user.department_id)
    devices = list(db.scalars(stmt.order_by(Device.id.desc())).unique().all())
    if q:
        ql = q.lower()
        devices = [
            d
            for d in devices
            if ql in d.name.lower()
            or ql in (d.mac or "").lower()
            or ql in (d.location or "").lower()
        ]
    return [device_out(d) for d in devices]


@router.post("", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
def create_device(
    body: DeviceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DeviceOut:
    if not can_manage_network(user) and user.role != "dept_user":
        raise HTTPException(status_code=403, detail="权限不足")
    dtype = body.device_type or "other"
    if dtype not in VALID_DEVICE_TYPES:
        raise HTTPException(status_code=400, detail="设备类型不合法")
    dept_id = body.department_id or user.department_id
    if body.department_id and not db.get(Department, body.department_id):
        raise HTTPException(status_code=400, detail="部门不存在")
    try:
        mac = normalize_mac(body.mac)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if mac:
        exists = db.scalar(select(Device).where(Device.mac == mac))
        if exists:
            raise HTTPException(status_code=400, detail=f"MAC 已被设备「{exists.name}」使用")

    dev = Device(
        name=body.name.strip(),
        device_type=dtype,
        mac=mac,
        location=body.location,
        department_id=dept_id,
        owner_user_id=body.owner_user_id or user.id,
        remark=body.remark,
    )
    db.add(dev)
    db.commit()
    dev = _load(db, dev.id)
    assert dev is not None
    return device_out(dev)


@router.patch("/{device_id}", response_model=DeviceOut)
def update_device(
    device_id: int,
    body: DeviceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DeviceOut:
    if not can_manage_network(user):
        raise HTTPException(status_code=403, detail="权限不足")
    dev = _load(db, device_id)
    if not dev:
        raise HTTPException(status_code=404, detail="设备不存在")
    if body.name is not None:
        dev.name = body.name.strip()
    if body.device_type is not None:
        if body.device_type not in VALID_DEVICE_TYPES:
            raise HTTPException(status_code=400, detail="设备类型不合法")
        dev.device_type = body.device_type
    if body.mac is not None:
        try:
            new_mac = normalize_mac(body.mac) if body.mac else None
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if new_mac:
            clash = db.scalar(
                select(Device).where(Device.mac == new_mac, Device.id != device_id)
            )
            if clash:
                raise HTTPException(status_code=400, detail=f"MAC 已被设备「{clash.name}」使用")
        dev.mac = new_mac
    if body.location is not None:
        dev.location = body.location
    if body.department_id is not None:
        dev.department_id = body.department_id
    if body.owner_user_id is not None:
        dev.owner_user_id = body.owner_user_id
    if body.remark is not None:
        dev.remark = body.remark
    db.commit()
    dev = _load(db, device_id)
    assert dev is not None
    return device_out(dev)


@router.delete("/{device_id}")
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    if not can_manage_network(user):
        raise HTTPException(status_code=403, detail="权限不足")
    dev = _load(db, device_id)
    if not dev:
        raise HTTPException(status_code=404, detail="设备不存在")
    # 有绑定中的 IP 就不让删，免得台账对不上
    if any(a.status == "allocated" for a in (dev.addresses or [])):
        raise HTTPException(status_code=400, detail="设备仍绑定已分配 IP，请先回收地址")
    db.delete(dev)
    db.commit()
    return {"message": "已删除"}
