"""API smoke / regression tests. Run with backend up on :8000."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"


def req(method: str, path: str, token: str | None = None, body: dict | None = None):
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            detail = json.loads(raw)
        except Exception:
            detail = raw
        return e.code, detail


def login(user: str) -> str:
    code, data = req("POST", "/api/v1/auth/login", body={"username": user, "password": "ChangeMe123!"})
    assert code == 200, data
    return data["access_token"]


def main() -> int:
    fails: list[str] = []

    def check(name: str, cond: bool, detail: object = ""):
        if cond:
            print(f"OK  {name}")
        else:
            print(f"FAIL {name}: {detail}")
            fails.append(name)

    admin = login("admin")
    biz = login("biz")
    viewer = login("viewer")

    code, _ = req("POST", "/api/v1/subnets", viewer, {"name": "x", "cidr": "10.77.1.0/28", "site_id": 1})
    check("viewer cannot create subnet", code == 403, code)

    code, subs = req("GET", "/api/v1/subnets", admin)
    check("list subnets", code == 200 and isinstance(subs, list) and len(subs) > 0, code)
    own = next(s for s in subs if s["department_name"] == "研发中心")
    other = next(s for s in subs if s["department_name"] != "研发中心")

    code, free_other = req("GET", f"/api/v1/ip-addresses?subnet_id={other['id']}&status=free", admin)
    target_other = next(i for i in free_other if not i["is_network_or_broadcast"])
    code, _ = req(
        "POST",
        f"/api/v1/ip-addresses/{target_other['id']}/allocate",
        biz,
        {"hostname": "hack"},
    )
    check("biz cannot allocate other dept", code == 403, code)

    code, free_own = req("GET", f"/api/v1/ip-addresses?subnet_id={own['id']}&status=free", admin)
    target_own = next(i for i in free_own if not i["is_network_or_broadcast"])
    code, alloc = req(
        "POST",
        f"/api/v1/ip-addresses/{target_own['id']}/allocate",
        biz,
        {"hostname": "biz-ok", "device_name": "nb"},
    )
    check("biz can allocate own dept", code == 200 and alloc["status"] == "allocated", (code, alloc))

    code, _ = req("POST", f"/api/v1/ip-addresses/{target_own['id']}/release", biz)
    check("biz cannot release", code == 403, code)

    code, ips = req("GET", f"/api/v1/ip-addresses?subnet_id={own['id']}", admin)
    gateway = next(i for i in ips if i["address"] == own["gateway"])
    network = next(i for i in ips if i["is_network_or_broadcast"])
    code, data = req("POST", f"/api/v1/ip-addresses/{network['id']}/release", admin)
    check("cannot release network/broadcast", code == 400, (code, data))
    code, data = req("POST", f"/api/v1/ip-addresses/{gateway['id']}/release", admin)
    check("cannot release gateway", code == 400, (code, data))

    code, data = req(
        "POST",
        f"/api/v1/ip-addresses/{target_own['id']}/allocate",
        admin,
        {"mac": "bad"},
    )
    # already allocated from biz — either 400 not free or if released...
    if alloc and alloc.get("status") == "allocated":
        # still allocated; release first as admin
        req("POST", f"/api/v1/ip-addresses/{target_own['id']}/release", admin)
    free2 = next(
        i
        for i in req("GET", f"/api/v1/ip-addresses?subnet_id={own['id']}&status=free", admin)[1]
        if not i["is_network_or_broadcast"]
    )
    code, data = req("POST", f"/api/v1/ip-addresses/{free2['id']}/allocate", admin, {"mac": "bad"})
    check("reject bad mac", code == 400, (code, data))

    code, data = req(
        "POST",
        f"/api/v1/ip-addresses/{free2['id']}/allocate",
        admin,
        {"expire_at": "nope"},
    )
    check("reject bad expire", code == 400, (code, data))

    code, data = req("POST", f"/api/v1/ip-addresses/{free2['id']}/allocate", admin, {"hostname": "once"})
    check("allocate once", code == 200, (code, data))
    code, data = req("POST", f"/api/v1/ip-addresses/{free2['id']}/allocate", admin, {"hostname": "twice"})
    check("reject double allocate", code == 400, (code, data))
    req("POST", f"/api/v1/ip-addresses/{free2['id']}/release", admin)

    # sort: last octet numeric order preferred
    code, ordered = req("GET", f"/api/v1/ip-addresses?subnet_id={own['id']}", admin)
    addrs = [i["address"] for i in ordered]
    octets = [int(a.split(".")[-1]) for a in addrs]
    check("ip order by last octet", octets == sorted(octets), addrs[:8])

    print("---")
    if fails:
        print(f"{len(fails)} failed: {fails}")
        return 1
    print("all passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
