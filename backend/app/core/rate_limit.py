from __future__ import annotations

import threading
import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

from app.core.config import get_settings

_lock = threading.Lock()
_attempts: dict[str, list[float]] = defaultdict(list)


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def check_login_rate_limit(request: Request) -> None:
    """Simple in-memory sliding window. Sufficient for single-process demo/prod small deploy."""
    settings = get_settings()
    ip = client_ip(request)
    now = time.time()
    window = settings.login_rate_window_seconds
    limit = settings.login_rate_limit

    with _lock:
        bucket = [t for t in _attempts[ip] if now - t < window]
        if len(bucket) >= limit:
            _attempts[ip] = bucket
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"登录尝试过于频繁，请 {window} 秒后再试",
            )
        bucket.append(now)
        _attempts[ip] = bucket


def reset_rate_limits() -> None:
    """Test helper."""
    with _lock:
        _attempts.clear()
