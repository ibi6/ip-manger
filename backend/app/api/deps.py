from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.constants import ALLOCATE_ROLES, MANAGE_NETWORK_ROLES, VALID_ROLES
from app.core.security import decode_token
from app.db.session import get_db
from app.models import User

security = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    try:
        payload = decode_token(creds.credentials)
        username = payload.get("sub")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌无效或已过期",
        ) from None
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌无效")

    user = db.scalar(
        select(User).options(joinedload(User.department)).where(User.username == username)
    )
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已禁用")
    token_version = payload.get("ver")
    if not isinstance(token_version, int) or token_version != user.auth_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌已失效，请重新登录"
        )
    if user.role not in VALID_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户角色无效")
    return user


def require_roles(*roles: str) -> Callable:
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role == "admin" or user.role in roles:
            return user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")

    return checker


def can_manage_network(user: User) -> bool:
    return user.role in MANAGE_NETWORK_ROLES


def can_allocate(user: User) -> bool:
    return user.role in ALLOCATE_ROLES


def assert_subnet_readable(user: User, department_id: int) -> None:
    """dept_user 仅本部门；admin/network_admin/viewer 可读全局（viewer 只读由写接口限制）。"""
    if user.role == "dept_user" and department_id != user.department_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该部门资源")
