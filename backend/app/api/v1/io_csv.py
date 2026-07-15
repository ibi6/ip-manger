from __future__ import annotations

import csv
import io
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import can_manage_network, get_current_user
from app.db.session import get_db
from app.models import Device, IpAddress, Site, Subnet, User
from app.schemas.common import Message
from app.services.subnet_service import create_subnet_with_pool

router = APIRouter(prefix="/io", tags=["import-export"])


def _csv_response(filename: str, rows: list[list[str]]) -> StreamingResponse:
    buf = io.StringIO()
    writer = csv.writer(buf)
    for row in rows:
        writer.writerow(row)
    # UTF-8 BOM for Excel
    content = "\ufeff" + buf.getvalue()
    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/subnets")
def export_subnets(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    subnets = db.scalars(
        select(Subnet).options(joinedload(Subnet.site), joinedload(Subnet.department)).order_by(Subnet.id)
    ).unique().all()
    rows: list[list[str]] = [
        [
            "id",
            "name",
            "cidr",
            "gateway",
            "vlan_id",
            "purpose",
            "site_code",
            "site_name",
            "department",
            "status",
            "description",
        ]
    ]
    for s in subnets:
        rows.append(
            [
                str(s.id),
                s.name,
                s.cidr,
                s.gateway or "",
                str(s.vlan_id or ""),
                s.purpose or "",
                s.site.code if s.site else "",
                s.site.name if s.site else "",
                s.department.name if s.department else "",
                s.status,
                (s.description or "").replace("\n", " "),
            ]
        )
    return _csv_response("subnets.csv", rows)


@router.get("/export/ip-addresses")
def export_ips(
    subnet_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> StreamingResponse:
    stmt = (
        select(IpAddress)
        .options(
            joinedload(IpAddress.subnet),
            joinedload(IpAddress.owner),
            joinedload(IpAddress.department),
        )
        .order_by(IpAddress.address)
    )
    if subnet_id is not None:
        stmt = stmt.where(IpAddress.subnet_id == subnet_id)
    ips = db.scalars(stmt).unique().all()
    rows: list[list[str]] = [
        [
            "id",
            "address",
            "status",
            "subnet_cidr",
            "hostname",
            "mac",
            "device_name",
            "device_type",
            "owner",
            "department",
            "allocated_at",
            "expire_at",
            "remark",
        ]
    ]
    for ip in ips:
        rows.append(
            [
                str(ip.id),
                ip.address,
                ip.status,
                ip.subnet.cidr if ip.subnet else "",
                ip.hostname or "",
                ip.mac or "",
                ip.device_name or "",
                ip.device_type or "",
                ip.owner.display_name if ip.owner else "",
                ip.department.name if ip.department else "",
                ip.allocated_at.isoformat() if ip.allocated_at else "",
                ip.expire_at.isoformat() if ip.expire_at else "",
                (ip.remark or "").replace("\n", " "),
            ]
        )
    return _csv_response("ip_addresses.csv", rows)


@router.get("/export/devices")
def export_devices(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    stmt = select(Device).options(
        joinedload(Device.department),
        joinedload(Device.owner),
        joinedload(Device.addresses),
    )
    if user.role == "dept_user":
        stmt = stmt.where(Device.department_id == user.department_id)
    devices = db.scalars(stmt.order_by(Device.id)).unique().all()
    rows: list[list[str]] = [
        ["id", "name", "device_type", "mac", "location", "department", "owner", "bound_ip", "remark"]
    ]
    for d in devices:
        bound = ""
        for a in d.addresses or []:
            if a.status == "allocated":
                bound = a.address
                break
        rows.append(
            [
                str(d.id),
                d.name,
                d.device_type,
                d.mac or "",
                d.location or "",
                d.department.name if d.department else "",
                d.owner.display_name if d.owner else "",
                bound,
                (d.remark or "").replace("\n", " "),
            ]
        )
    return _csv_response("devices.csv", rows)


@router.post("/import/subnets", response_model=Message)
async def import_subnets(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Message:
    """
    CSV 表头（至少）：name,cidr,site_code
    可选：gateway,vlan_id,purpose,description
    """
    if not can_manage_network(user):
        raise HTTPException(status_code=403, detail="权限不足")
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="请上传 .csv 文件")

    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("gbk", errors="ignore")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV 为空或缺少表头")

    created = 0
    skipped = 0
    errors: list[str] = []

    for i, row in enumerate(reader, start=2):
        name = (row.get("name") or "").strip()
        cidr = (row.get("cidr") or "").strip()
        site_code = (row.get("site_code") or row.get("site") or "").strip()
        if not name or not cidr or not site_code:
            errors.append(f"第{i}行：name/cidr/site_code 必填")
            skipped += 1
            continue
        site = db.scalar(select(Site).where(Site.code == site_code))
        if not site:
            errors.append(f"第{i}行：站点编码不存在 {site_code}")
            skipped += 1
            continue
        vlan_raw = (row.get("vlan_id") or "").strip()
        vlan_id = int(vlan_raw) if vlan_raw.isdigit() else None
        try:
            create_subnet_with_pool(
                db,
                name=name,
                cidr=cidr,
                site_id=site.id,
                department_id=user.department_id,
                gateway=(row.get("gateway") or "").strip(),
                vlan_id=vlan_id,
                purpose=(row.get("purpose") or "导入").strip() or "导入",
                description=(row.get("description") or "").strip() or None,
            )
            db.commit()
            created += 1
        except ValueError as exc:
            db.rollback()
            errors.append(f"第{i}行：{exc}")
            skipped += 1
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            errors.append(f"第{i}行：{exc}")
            skipped += 1

    msg = f"导入完成：成功 {created}，跳过 {skipped}"
    if errors:
        msg += "；部分错误：" + " | ".join(errors[:5])
    return Message(message=msg, data={"created": created, "skipped": skipped, "errors": errors[:20]})


@router.get("/template/subnets")
def subnet_import_template(_: User = Depends(get_current_user)) -> StreamingResponse:
    rows = [
        ["name", "cidr", "site_code", "gateway", "vlan_id", "purpose", "description"],
        ["演示导入网", "10.99.1.0/28", "HQ", "10.99.1.1", "99", "导入测试", "CSV 模板示例"],
    ]
    return _csv_response("subnet_import_template.csv", rows)
