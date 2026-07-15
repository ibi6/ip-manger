from tests.conftest import auth_header


def test_viewer_cannot_create_subnet(client):
    h = auth_header(client, "viewer")
    r = client.post(
        "/api/v1/subnets",
        headers=h,
        json={"name": "x", "cidr": "10.77.1.0/28", "site_id": 1, "gateway": "10.77.1.1"},
    )
    assert r.status_code == 403


def test_biz_cannot_allocate_other_dept(client):
    admin = auth_header(client, "admin")
    biz = auth_header(client, "biz")
    subs = client.get("/api/v1/subnets", headers=admin).json()
    other = next(s for s in subs if s["department_name"] != "研发中心")
    free = client.get(
        f"/api/v1/ip-addresses?subnet_id={other['id']}&status=free", headers=admin
    ).json()
    target = next(i for i in free if not i["is_network_or_broadcast"])
    r = client.post(
        f"/api/v1/ip-addresses/{target['id']}/allocate",
        headers=biz,
        json={"hostname": "hack"},
    )
    assert r.status_code == 403


def test_biz_can_allocate_own_dept(client):
    admin = auth_header(client, "admin")
    biz = auth_header(client, "biz")
    subs = client.get("/api/v1/subnets", headers=admin).json()
    own = next(s for s in subs if s["department_name"] == "研发中心")
    free = client.get(
        f"/api/v1/ip-addresses?subnet_id={own['id']}&status=free", headers=admin
    ).json()
    target = next(i for i in free if not i["is_network_or_broadcast"])
    r = client.post(
        f"/api/v1/ip-addresses/{target['id']}/allocate",
        headers=biz,
        json={"hostname": "biz-ok"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "allocated"

    r2 = client.post(f"/api/v1/ip-addresses/{target['id']}/release", headers=biz)
    assert r2.status_code == 403


def test_dashboard_requires_auth(client):
    r = client.get("/api/v1/dashboard/overview")
    assert r.status_code == 401


def test_dashboard_ok(client):
    h = auth_header(client)
    r = client.get("/api/v1/dashboard/overview", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["subnet_count"] >= 1
    assert body["total_ips"] > 0
