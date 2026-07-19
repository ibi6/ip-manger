import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("ipam.exceptions")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException):
        detail = exc.detail
        if not isinstance(detail, str):
            detail = str(detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": detail},
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError):
        # Pydantic may place a ValueError object in `ctx`, which is not JSON serializable
        # and should not be exposed to API clients. The human-readable `msg` is sufficient.
        errors = [
            {key: value for key, value in error.items() if key != "ctx"} for error in exc.errors()
        ]
        first = errors[0] if errors else {}
        loc = ".".join(str(x) for x in first.get("loc", []) if x != "body")
        msg = first.get("msg", "参数校验失败")
        detail = f"{loc}: {msg}" if loc else msg
        return JSONResponse(status_code=422, content={"detail": detail, "errors": errors})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception):
        # Never swallow HTTPException (subclass of Exception in some stacks)
        if isinstance(exc, StarletteHTTPException):
            detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": detail},
                headers=exc.headers,
            )
        logger.error(
            "未处理的服务器异常",
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "服务器内部错误，请稍后重试或查看服务日志"},
        )
