"""Request tracing, access logs, and response security headers."""

from __future__ import annotations

import logging
import re
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("ipam.access")
_REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")


def _safe_request_id(raw_value: str | None) -> str:
    """Return a bounded trace id that cannot inject fields into logs or headers."""
    if raw_value and _REQUEST_ID_PATTERN.fullmatch(raw_value):
        return raw_value
    return uuid.uuid4().hex[:12]


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Attach a request id, log latency, and apply API-safe browser headers."""

    async def dispatch(self, request: Request, call_next) -> Response:
        req_id = _safe_request_id(request.headers.get("x-request-id"))
        start = time.perf_counter()
        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            ms = (time.perf_counter() - start) * 1000
            status = response.status_code if response is not None else 500
            # 健康检查太吵，跳过
            if request.url.path != "/health":
                logger.info(
                    "%s %s %s -> %s (%.1fms)",
                    req_id,
                    request.method,
                    request.url.path,
                    status,
                    ms,
                )
            if response is not None:
                response.headers["X-Request-ID"] = req_id
                response.headers["X-Content-Type-Options"] = "nosniff"
                response.headers["X-Frame-Options"] = "DENY"
                response.headers["Referrer-Policy"] = "no-referrer"
                response.headers["Permissions-Policy"] = (
                    "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
                )
                if request.url.path == "/docs":
                    response.headers["Content-Security-Policy"] = (
                        "default-src 'self' https://cdn.jsdelivr.net; "
                        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                        "img-src 'self' data: https://fastapi.tiangolo.com"
                    )
                else:
                    response.headers["Content-Security-Policy"] = (
                        "default-src 'none'; frame-ancestors 'none'"
                    )
                if request.url.path.startswith("/api/v1/auth/"):
                    response.headers["Cache-Control"] = "no-store"
