"""用户管理：目前只给管理员用，功能比较基础。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.core.constants import VALID_ROLES
from app.core.security import hash_password
from app.db.session import get_db
from app.models import Department, User
from app.schemas.common import (
    DepartmentCreate,
    DepartmentOut,
    UserCreate,
    UserOut,
    UserUpdate,
)
from app.services.serializers import user_out

router = APIRouter(prefix="/users", tags=["users"])


def _require_admin(user: User) -> None:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可管理用户")


@router.get("/departments", response_model=list[DepartmentOut])
def list_departments(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[DepartmentOut]:
    rows = db.scalars(select(Department).order_by(Department.id)).all()
    return [DepartmentOut(id=d.id, name=d.name, code=d.code) for d in rows]


@router.post("/departments", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(
    body: DepartmentCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> DepartmentOut:
    _require_admin(current)
    code = body.code.strip().upper()
    name = body.name.strip()
    if db.scalar(select(Department).where((Department.code == code) | (Department.name == name))):
        raise HTTPException(status_code=400, detail="部门名称或编码已存在")
    d = Department(name=name, code=code)
    db.add(d)
    db.commit()
    db.refresh(d)
    return DepartmentOut(id=d.id, name=d.name, code=d.code)


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> list[UserOut]:
    _require_admin(current)
    users = db.scalars(
        select(User).options(joinedload(User.department)).order_by(User.id)
    ).unique().all()
    return [user_out(u) for u in users]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> UserOut:
    _require_admin(current)
    if body.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="角色不合法")
    if not db.get(Department, body.department_id):
        raise HTTPException(status_code=400, detail="部门不存在")
    if db.scalar(select(User).where(User.username == body.username.strip())):
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(
        username=body.username.strip(),
        display_name=body.display_name.strip(),
        password_hash=hash_password(body.password),
        role=body.role,
        department_id=body.department_id,
        avatar_color="#334155",
        is_active=True,
    )
    db.add(user)
    db.commit()
    user = db.scalar(
        select(User).options(joinedload(User.department)).where(User.id == user.id)
    )
    assert user is not None
    return user_out(user)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> UserOut:
    _require_admin(current)
    user = db.scalar(
        select(User).options(joinedload(User.department)).where(User.id == user_id)
    )
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 防止管理员把自己停用后锁死系统（至少留一个可用 admin）
    if user.id == current.id and body.is_active is False:
        raise HTTPException(status_code=400, detail="不能停用当前登录的管理员账号")

    if body.role is not None:
        if body.role not in VALID_ROLES:
            raise HTTPException(status_code=400, detail="角色不合法")
        if user.id == current.id and body.role != "admin":
            raise HTTPException(status_code=400, detail="不能取消自己的管理员角色")
        user.role = body.role

    if body.display_name is not None:
        user.display_name = body.display_name.strip()
    if body.department_id is not None:
        if not db.get(Department, body.department_id):
            raise HTTPException(status_code=400, detail="部门不存在")
        user.department_id = body.department_id
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.password:
        user.password_hash = hash_password(body.password)

    db.commit()
    user = db.scalar(
        select(User).options(joinedload(User.department)).where(User.id == user_id)
    )
    assert user is not None
    return user_out(user)
