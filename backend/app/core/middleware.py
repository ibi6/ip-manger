"""简单请求日志，方便答辩时说明“有日志”。"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("ipam.access")


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        req_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
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
