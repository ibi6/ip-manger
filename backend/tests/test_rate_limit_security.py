from __future__ import annotations

from pathlib import Path

from starlette.requests import Request

from app.core.config import get_settings
from app.core.rate_limit import client_ip


def _request(*, peer: str, forwarded_for: str) -> Request:
    """Build a real ASGI request carrying a proxy chain for resolver tests."""
    return Request(
        {
            "type": "http",
            "method": "POST",
            "scheme": "http",
            "path": "/api/v1/auth/login",
            "raw_path": b"/api/v1/auth/login",
            "query_string": b"",
            "headers": [(b"x-forwarded-for", forwarded_for.encode("ascii"))],
            "client": (peer, 43123),
            "server": ("testserver", 80),
        }
    )


def test_trusted_proxy_uses_appended_peer_address_not_spoofed_first_hop(monkeypatch):
    """A client-supplied first XFF value must not create a fresh rate-limit bucket."""
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "true")
    get_settings.cache_clear()
    try:
        request = _request(
            peer="172.20.0.3",
            forwarded_for="198.51.100.77, 203.0.113.42",
        )

        assert client_ip(request) == "203.0.113.42"
    finally:
        get_settings.cache_clear()


def test_trusted_proxy_rejects_malformed_forwarded_address(monkeypatch):
    """Malformed forwarding metadata must fall back to the direct peer identity."""
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "true")
    get_settings.cache_clear()
    try:
        request = _request(peer="172.20.0.3", forwarded_for="not-an-ip")

        assert client_ip(request) == "172.20.0.3"
    finally:
        get_settings.cache_clear()


def test_container_does_not_trust_forwarding_headers_from_every_peer():
    """Uvicorn must leave proxy identity handling to the application policy."""
    dockerfile = Path(__file__).resolve().parents[1] / "Dockerfile"
    contents = dockerfile.read_text(encoding="utf-8")

    assert "--forwarded-allow-ips=*" not in contents
    assert "--no-proxy-headers" in contents
