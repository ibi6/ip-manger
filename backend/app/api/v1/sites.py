from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import can_manage_network, get_current_user
from app.db.session import get_db
from app.models import Site, Subnet, User
from app.schemas.common import SiteCreate, SiteOut
from app.services.serializers import site_out

router = APIRouter(prefix="/sites")


@router.get("", response_model=list[SiteOut])
def list_sites(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[SiteOut]:
    sites = db.scalars(select(Site).order_by(Site.id)).all()
    result: list[SiteOut] = []
    for s in sites:
        cnt = db.scalar(select(func.count()).select_from(Subnet).where(Subnet.site_id == s.id)) or 0
        result.append(site_out(s, subnet_count=cnt))
    return result


@router.post("", response_model=SiteOut, status_code=status.HTTP_201_CREATED)
def create_site(
    body: SiteCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SiteOut:
    if not can_manage_network(user):
        raise HTTPException(status_code=403, detail="权限不足")
    if db.scalar(select(Site).where(Site.code == body.code)):
        raise HTTPException(status_code=400, detail="站点编码已存在")
    site = Site(name=body.name, code=body.code, location=body.location, remark=body.remark)
    db.add(site)
    db.commit()
    db.refresh(site)
    return site_out(site, 0)
