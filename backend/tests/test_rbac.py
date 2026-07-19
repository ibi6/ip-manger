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


def test_biz_cannot_bind_another_departments_device(client):
    admin = auth_header(client, "admin")
    biz = auth_header(client, "biz")
    biz_user = client.get("/api/v1/auth/me", headers=biz).json()
    departments = client.get("/api/v1/users/departments", headers=admin).json()
    other_department = next(d for d in departments if d["id"] != biz_user["department_id"])
    device = client.post(
        "/api/v1/devices",
        headers=admin,
        json={
            "name": "Other department device",
            "device_type": "pc",
            "department_id": other_department["id"],
        },
    ).json()
    own_subnet = client.get("/api/v1/subnets", headers=biz).json()[0]
    free_ips = client.get(
        f"/api/v1/ip-addresses?subnet_id={own_subnet['id']}&status=free",
        headers=biz,
    ).json()
    target = next(ip for ip in free_ips if not ip["is_network_or_broadcast"])

    response = client.post(
        f"/api/v1/ip-addresses/{target['id']}/allocate",
        headers=biz,
        json={"hostname": "cross-device", "device_id": device["id"]},
    )

    assert response.status_code == 403
    current = client.get(f"/api/v1/ip-addresses/{target['id']}", headers=biz).json()
    assert current["status"] == "free"

    allocate_next = client.post(
        f"/api/v1/subnets/{own_subnet['id']}/allocate-next",
        headers=biz,
        json={"hostname": "cross-device-next", "device_id": device["id"]},
    )
    assert allocate_next.status_code == 403


def test_biz_dashboard_only_counts_own_department(client):
    biz = auth_header(client, "biz")
    own_subnets = client.get("/api/v1/subnets", headers=biz).json()

    dashboard = client.get("/api/v1/dashboard/overview", headers=biz).json()

    assert dashboard["subnet_count"] == len(own_subnets)
    assert dashboard["total_ips"] == sum(subnet["total_ips"] for subnet in own_subnets)


def test_biz_logs_hide_other_department_activity(client):
    admin = auth_header(client, "admin")
    biz = auth_header(client, "biz")
    subnets = client.get("/api/v1/subnets", headers=admin).json()
    other = next(subnet for subnet in subnets if subnet["department_name"] != "研发中心")
    free_ips = client.get(
        f"/api/v1/ip-addresses?subnet_id={other['id']}&status=free",
        headers=admin,
    ).json()
    target = next(ip for ip in free_ips if not ip["is_network_or_broadcast"])
    allocated = client.post(
        f"/api/v1/ip-addresses/{target['id']}/allocate",
        headers=admin,
        json={"hostname": "other-department-host"},
    )
    assert allocated.status_code == 200

    logs = client.get("/api/v1/logs", headers=biz).json()

    assert all(log["address"] != target["address"] for log in logs)


def test_biz_conflicts_follow_department_scope(client):
    admin = auth_header(client, "admin")
    biz = auth_header(client, "biz")
    scan = client.post("/api/v1/conflicts/simulate-scan", headers=admin)
    assert scan.status_code == 200
    created = client.get("/api/v1/conflicts?status=all", headers=admin).json()[0]
    own_cidrs = {subnet["cidr"] for subnet in client.get("/api/v1/subnets", headers=biz).json()}

    visible_ids = {
        conflict["id"]
        for conflict in client.get("/api/v1/conflicts?status=all", headers=biz).json()
    }

    assert (created["id"] in visible_ids) is (created["subnet_cidr"] in own_cidrs)


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
