from sqlalchemy import event

from app.db.session import get_db
from app.main import app
from tests.conftest import auth_header


def test_ip_page(client):
    h = auth_header(client, "admin")
    r = client.get("/api/v1/ip-addresses/page?page=1&page_size=10", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "total" in body
    assert body["page"] == 1
    assert len(body["items"]) <= 10


def test_ip_page_pushes_limit_and_offset_into_sql(client):
    headers = auth_header(client, "admin")
    override = app.dependency_overrides[get_db]
    session_source = override()
    session = next(session_source)
    engine = session.get_bind()
    session.close()
    session_source.close()
    statements: list[str] = []

    def capture_sql(_conn, _cursor, statement, _parameters, _context, _executemany):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", capture_sql)
    try:
        response = client.get(
            "/api/v1/ip-addresses/page?page=2&page_size=7",
            headers=headers,
        )
    finally:
        event.remove(engine, "before_cursor_execute", capture_sql)

    assert response.status_code == 200
    address_queries = [sql.upper() for sql in statements if "FROM IP_ADDRESSES" in sql.upper()]
    assert any(" LIMIT " in sql and " OFFSET " in sql for sql in address_queries)


def test_ip_page_searches_owner_without_crossing_department_scope(client):
    biz = auth_header(client, "biz")
    biz_user = client.get("/api/v1/auth/me", headers=biz).json()
    own_subnet = client.get("/api/v1/subnets", headers=biz).json()[0]
    free_ips = client.get(
        f"/api/v1/ip-addresses?subnet_id={own_subnet['id']}&status=free",
        headers=biz,
    ).json()
    target = next(ip for ip in free_ips if not ip["is_network_or_broadcast"])
    allocated = client.post(
        f"/api/v1/ip-addresses/{target['id']}/allocate",
        headers=biz,
        json={"hostname": "owner-search"},
    )
    assert allocated.status_code == 200

    result = client.get(
        "/api/v1/ip-addresses/page?q=周景行&page=1&page_size=10",
        headers=biz,
    ).json()

    assert any(item["id"] == target["id"] for item in result["items"])
    assert all(item["department_id"] == biz_user["department_id"] for item in result["items"])


def test_mac_unique(client):
    h = auth_header(client, "admin")
    r1 = client.post(
        "/api/v1/devices",
        headers=h,
        json={"name": "A", "device_type": "pc", "mac": "AA:BB:CC:11:22:33"},
    )
    assert r1.status_code == 201
    r2 = client.post(
        "/api/v1/devices",
        headers=h,
        json={"name": "B", "device_type": "pc", "mac": "AA:BB:CC:11:22:33"},
    )
    assert r2.status_code == 400


def test_create_department(client):
    h = auth_header(client, "admin")
    r = client.post(
        "/api/v1/users/departments",
        headers=h,
        json={"name": "测试部", "code": "TEST"},
    )
    assert r.status_code == 201
    assert r.json()["code"] == "TEST"
