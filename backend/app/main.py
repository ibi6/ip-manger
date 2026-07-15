from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import get_secret_key, get_settings
from app.core.exceptions import register_exception_handlers
from app.core.middleware import RequestLogMiddleware
from app.db.base import Base
from app.db.migrate_sqlite import ensure_sqlite_schema
from app.db.session import SessionLocal, engine
from app.seed import seed_if_empty

import app.models  # noqa: F401

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ipam")

APP_VERSION = "1.5.0"


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Fail fast on bad production secrets
    get_secret_key()
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_schema()
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
    logger.info("IPAM API %s ready", APP_VERSION)
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=APP_VERSION,
    description="企业IP地址管理系统 API（毕业设计）",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLogMiddleware)

register_exception_handlers(app)
app.include_router(api_router)


@app.get("/health")
def health():
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_ok = True
    except Exception:  # noqa: BLE001
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "app": settings.app_name,
        "version": APP_VERSION,
        "env": settings.app_env,
        "database": "up" if db_ok else "down",
        "time": datetime.now(timezone.utc).isoformat(),
    }
