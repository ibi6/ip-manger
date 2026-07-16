from __future__ import annotations

import threading
import time
from collections import defaultdict
from ipaddress import ip_address

from fastapi import HTTPException, Request, status

from app.core.config import get_settings

_lock = threading.Lock()
_failures: dict[str, list[float]] = defaultdict(list)


def client_ip(request: Request) -> str:
    """Resolve the rate-limit key without trusting spoofable proxy headers by default."""
    settings = get_settings()
    peer = request.client.host if request.client else "unknown"
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # A controlled proxy appends or overwrites the real client address at
            # the right edge. Never trust a client-supplied first entry.
            candidate = forwarded.rsplit(",", maxsplit=1)[-1].strip()
            try:
                return str(ip_address(candidate))
            except ValueError:
                pass
    return peer


def _prune_locked(now: float, window: int) -> None:
    """Remove expired timestamps and empty client buckets while holding `_lock`."""
    expired_keys: list[str] = []
    for key, values in _failures.items():
        active = [timestamp for timestamp in values if now - timestamp < window]
        if active:
            _failures[key] = active
        else:
            expired_keys.append(key)
    for key in expired_keys:
        _failures.pop(key, None)


def assert_login_allowed(request: Request) -> None:
    """Reject a login attempt only when prior failed attempts exhausted the window."""
    settings = get_settings()
    key = client_ip(request)
    now = time.monotonic()
    with _lock:
        _prune_locked(now, settings.login_rate_window_seconds)
        if len(_failures.get(key, [])) >= settings.login_rate_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"登录失败次数过多，请 {settings.login_rate_window_seconds} 秒后再试",
            )


def record_login_failure(request: Request) -> None:
    """Record one invalid-credential event for the resolved client."""
    settings = get_settings()
    key = client_ip(request)
    now = time.monotonic()
    with _lock:
        _prune_locked(now, settings.login_rate_window_seconds)
        _failures[key].append(now)


def clear_login_failures(request: Request) -> None:
    """Reset the client failure budget after successful credential verification."""
    key = client_ip(request)
    with _lock:
        _failures.pop(key, None)


def reset_rate_limits() -> None:
    """Clear all in-memory buckets for deterministic tests."""
    with _lock:
        _failures.clear()
