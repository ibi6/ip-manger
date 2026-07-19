import logging

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.core.exceptions import register_exception_handlers


def test_api_responses_include_security_headers(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "camera=()" in response.headers["permissions-policy"]
    assert "default-src 'none'" in response.headers["content-security-policy"]
    assert response.headers["x-request-id"]


def test_auth_responses_are_not_cached(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "ChangeMe123!"},
    )

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"


def test_request_id_accepts_safe_values_and_replaces_untrusted_input(client):
    safe = client.get("/health", headers={"X-Request-ID": "trace-123"})
    oversized = client.get("/health", headers={"X-Request-ID": "x" * 200})
    unsafe = client.get("/health", headers={"X-Request-ID": "trace id with spaces"})

    assert safe.headers["x-request-id"] == "trace-123"
    assert oversized.headers["x-request-id"] != "x" * 200
    assert len(oversized.headers["x-request-id"]) == 12
    assert unsafe.headers["x-request-id"] != "trace id with spaces"
    assert len(unsafe.headers["x-request-id"]) == 12


def test_http_exception_handler_preserves_response_headers():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/limited")
    def limited():
        raise HTTPException(status_code=429, detail="请求过多", headers={"Retry-After": "60"})

    response = TestClient(app).get("/limited")

    assert response.status_code == 429
    assert response.headers["retry-after"] == "60"


def test_unhandled_exception_is_logged_without_exposing_details(caplog):
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/explode")
    def explode():
        raise RuntimeError("database password leaked")

    with caplog.at_level(logging.ERROR):
        response = TestClient(app, raise_server_exceptions=False).get("/explode")

    assert response.status_code == 500
    assert response.json()["detail"] == "服务器内部错误，请稍后重试或查看服务日志"
    assert "database password" not in response.text
    assert "未处理的服务器异常" in caplog.text
