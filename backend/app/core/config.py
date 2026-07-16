from __future__ import annotations

import logging
import secrets
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("ipam.config")

# Weak / demo keys that must never be used in production
_INSECURE_KEYS = frozenset(
    {
        "",
        "change-me",
        "secret",
        "ipam-dev-secret-key-change-in-production-32c",
        "ipam-docker-change-me-in-production-32chars",
    }
)


def _project_data_dir() -> Path:
    # backend/app/core/config.py -> backend/
    return Path(__file__).resolve().parents[2]


def _load_or_create_dev_secret() -> str:
    """Persist a random secret for local dev so restarts keep tokens valid."""
    path = _project_data_dir() / ".secret_key"
    if path.exists():
        value = path.read_text(encoding="utf-8").strip()
        if len(value) >= 32:
            return value
    value = secrets.token_urlsafe(48)
    try:
        path.write_text(value, encoding="utf-8")
        path.chmod(0o600)
    except OSError:
        logger.warning("无法写入 %s，使用内存临时密钥", path)
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "NetLedger 企业 IP 地址管理"
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    # Empty = auto (dev file / production fail)
    secret_key: str = Field(default="", validation_alias="SECRET_KEY")
    access_token_expire_minutes: int = 480
    algorithm: str = "HS256"
    database_url: str = "sqlite:///./ipam.db"
    cors_origins: str = (
        "http://localhost:5173,http://localhost:5174,http://localhost:5175,"
        "http://127.0.0.1:5173,http://127.0.0.1:5174,http://127.0.0.1:5175,"
        "http://localhost,http://127.0.0.1"
    )
    login_rate_limit: int = 8  # attempts per window
    login_rate_window_seconds: int = 60
    trust_proxy_headers: bool = False
    seed_demo_data: bool | None = None
    bootstrap_admin_username: str = "admin"
    bootstrap_admin_display_name: str = "NetLedger 管理员"
    bootstrap_admin_password: str = ""

    @field_validator("app_env")
    @classmethod
    def normalize_env(cls, v: str) -> str:
        normalized = (v or "development").strip().lower()
        if normalized in {"prod", "production"}:
            return "production"
        if normalized in {"dev", "development"}:
            return "development"
        raise ValueError("APP_ENV 仅支持 development/dev 或 production/prod")

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def demo_seed_enabled(self) -> bool:
        """Enable sample data by default only outside production."""
        if self.is_production:
            return False
        return True if self.seed_demo_data is None else self.seed_demo_data

    def resolve_secret_key(self) -> str:
        key = (self.secret_key or "").strip()
        if key and key not in _INSECURE_KEYS and len(key) >= 32:
            return key

        if self.is_production:
            raise RuntimeError(
                "生产环境必须设置足够长的 SECRET_KEY（≥32 字符），"
                "请通过环境变量 SECRET_KEY 配置，且勿使用示例默认值。"
            )

        # Development: auto-generate stable secret
        if not key or key in _INSECURE_KEYS:
            logger.warning(
                "未配置安全 SECRET_KEY，已使用本地自动密钥（仅限开发/演示）。"
                "生产部署请设置环境变量 SECRET_KEY。"
            )
            return _load_or_create_dev_secret()
        if len(key) < 32:
            raise RuntimeError("SECRET_KEY 长度必须 ≥ 32 字符")
        return key


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_secret_key() -> str:
    """Resolve the signing key once per process to avoid repeated I/O and warning logs."""
    return get_settings().resolve_secret_key()
