from tests.conftest import auth_header


def _first_free(client, headers, subnet_id: int) -> dict:
    r = client.get(f"/api/v1/ip-addresses?subnet_id={subnet_id}&status=free", headers=headers)
    assert r.status_code == 200
    items = [i for i in r.json() if not i["is_network_or_broadcast"]]
    assert items, "no free ip"
    return items[0]


def test_allocate_and_release(client):
    h = auth_header(client, "admin")
    subs = client.get("/api/v1/subnets", headers=h).json()
    subnet = next(s for s in subs if s["department_name"] == "研发中心")
    ip = _first_free(client, h, subnet["id"])

    r = client.post(
        f"/api/v1/ip-addresses/{ip['id']}/allocate",
        headers=h,
        json={"hostname": "t1", "device_type": "pc", "mac": "AA:BB:CC:DD:EE:FF"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "allocated"
    assert r.json()["hostname"] == "t1"

    r2 = client.post(
        f"/api/v1/ip-addresses/{ip['id']}/allocate",
        headers=h,
        json={"hostname": "t2"},
    )
    assert r2.status_code == 400

    r3 = client.post(f"/api/v1/ip-addresses/{ip['id']}/release", headers=h)
    assert r3.status_code == 200
    assert r3.json()["status"] == "free"


def test_cannot_release_gateway(client):
    h = auth_header(client, "admin")
    subs = client.get("/api/v1/subnets", headers=h).json()
    subnet = subs[0]
    ips = client.get(f"/api/v1/ip-addresses?subnet_id={subnet['id']}", headers=h).json()
    gw = next(i for i in ips if i["address"] == subnet["gateway"])
    r = client.post(f"/api/v1/ip-addresses/{gw['id']}/release", headers=h)
    assert r.status_code == 400


def test_bad_mac(client):
    h = auth_header(client, "admin")
    subs = client.get("/api/v1/subnets", headers=h).json()
    ip = _first_free(client, h, subs[0]["id"])
    r = client.post(
        f"/api/v1/ip-addresses/{ip['id']}/allocate",
        headers=h,
        json={"mac": "not-a-mac"},
    )
    assert r.status_code == 400


def test_ip_numeric_sort(client):
    h = auth_header(client, "admin")
    subs = client.get("/api/v1/subnets", headers=h).json()
    ips = client.get(f"/api/v1/ip-addresses?subnet_id={subs[0]['id']}", headers=h).json()
    octets = [int(i["address"].split(".")[-1]) for i in ips]
    assert octets == sorted(octets)


def test_archive_subnet_blocked_when_allocated(client):
    h = auth_header(client, "admin")
    subs = client.get("/api/v1/subnets", headers=h).json()
    # 种子子网都有已分配地址，归档应失败
    r = client.post(f"/api/v1/subnets/{subs[0]['id']}/archive", headers=h)
    assert r.status_code == 400


def test_batch_release(client):
    h = auth_header(client, "admin")
    subs = client.get("/api/v1/subnets", headers=h).json()
    allocated = client.get(
        f"/api/v1/ip-addresses?subnet_id={subs[0]['id']}&status=allocated&page_size=5",
        headers=h,
    ).json()
    ids = [a["id"] for a in allocated[:2]]
    if not ids:
        return
    r = client.post("/api/v1/ip-addresses/batch-release", headers=h, json={"ids": ids})
    assert r.status_code == 200
    assert "成功回收" in r.json()["message"]


def test_allocate_with_device_id(client):
    h = auth_header(client, "admin")
    dev = client.post(
        "/api/v1/devices",
        headers=h,
        json={"name": "绑定测试机", "device_type": "pc", "mac": "11:22:33:44:55:66"},
    ).json()
    subs = client.get("/api/v1/subnets", headers=h).json()
    free = client.get(
        f"/api/v1/ip-addresses?subnet_id={subs[0]['id']}&status=free", headers=h
    ).json()
    target = next(i for i in free if not i["is_network_or_broadcast"])
    r = client.post(
        f"/api/v1/ip-addresses/{target['id']}/allocate",
        headers=h,
        json={"device_id": dev["id"], "hostname": "bind-host"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["device_id"] == dev["id"]
    assert body["device_name"] == "绑定测试机"
