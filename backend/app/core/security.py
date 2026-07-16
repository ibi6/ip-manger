from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_secret_key, get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def validate_password_strength(password: str) -> str:
    """Validate passwords against the application and bcrypt safety boundaries."""
    if len(password) < 12:
        raise ValueError("密码至少需要 12 个字符")
    if len(password) > 128:
        raise ValueError("密码不能超过 128 个字符")
    if len(password.encode("utf-8")) > 72:
        raise ValueError("密码的 UTF-8 长度不能超过 72 字节")
    if not any(character.isalpha() for character in password):
        raise ValueError("密码必须包含字母")
    if not any(character.isdigit() for character in password):
        raise ValueError("密码必须包含数字")
    if not any(not character.isalnum() and not character.isspace() for character in password):
        raise ValueError("密码必须包含特殊字符")
    return password


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, get_secret_key(), algorithm=settings.algorithm)


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, get_secret_key(), algorithms=[settings.algorithm])
    except JWTError as exc:
        raise ValueError("invalid token") from exc
