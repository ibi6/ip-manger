from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.common import DashboardOut
from app.services.serializers import dashboard_out

router = APIRouter()


@router.get("/dashboard/overview", response_model=DashboardOut)
def overview(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DashboardOut:
    return dashboard_out(db)
