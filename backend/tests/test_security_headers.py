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
