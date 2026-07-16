from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.core.rate_limit import (
    assert_login_allowed,
    clear_login_failures,
    record_login_failure,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import User
from app.schemas.common import ChangePasswordRequest, LoginRequest, Message, TokenResponse, UserOut
from app.services.serializers import user_out

router = APIRouter(prefix="/auth")


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    assert_login_allowed(request)
    user = db.scalar(
        select(User).options(joinedload(User.department)).where(User.username == body.username)
    )
    if not user or not verify_password(body.password, user.password_hash):
        record_login_failure(request)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    clear_login_failures(request)
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="用户已禁用")
    token = create_access_token(
        user.username,
        extra={"role": user.role, "uid": user.id, "ver": user.auth_version},
    )
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return user_out(user)


@router.post("/change-password", response_model=Message)
def change_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Message:
    # 重新查一次，避免 session 里对象状态不对
    db_user = db.get(User, user.id)
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if not verify_password(body.old_password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码不正确")
    if body.old_password == body.new_password:
        raise HTTPException(status_code=400, detail="新密码不能与原密码相同")
    db_user.password_hash = hash_password(body.new_password)
    db_user.auth_version += 1
    db.commit()
    return Message(message="密码已修改，请使用新密码重新登录")
