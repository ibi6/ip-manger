from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import hash_password, validate_password_strength
from app.models import AllocationLog, Conflict, Department, Device, IpAddress, Site, Subnet, User
from app.services.subnet_service import create_subnet_with_pool


def initialize_data(db: Session, settings: Settings) -> None:
    """Initialize an empty database according to explicit environment policy."""
    if db.scalar(select(User.id).limit(1)):
        return

    if settings.is_production and settings.seed_demo_data:
        raise RuntimeError("生产环境禁止启用 SEED_DEMO_DATA，请改用 BOOTSTRAP_ADMIN_PASSWORD")

    if settings.demo_seed_enabled:
        seed_if_empty(db)
        return

    password = settings.bootstrap_admin_password
    if not password:
        raise RuntimeError(
            "空数据库必须设置 BOOTSTRAP_ADMIN_PASSWORD；生产环境不会创建默认演示账号"
        )
    try:
        validate_password_strength(password)
    except ValueError as exc:
        raise RuntimeError(f"BOOTSTRAP_ADMIN_PASSWORD 不符合安全策略：{exc}") from exc

    username = settings.bootstrap_admin_username.strip()
    display_name = settings.bootstrap_admin_display_name.strip()
    if not username or len(username) > 50:
        raise RuntimeError("BOOTSTRAP_ADMIN_USERNAME 必须为 1–50 个字符")
    if not display_name or len(display_name) > 100:
        raise RuntimeError("BOOTSTRAP_ADMIN_DISPLAY_NAME 必须为 1–100 个字符")

    department = Department(name="信息中心", code="IT")
    db.add(department)
    db.flush()
    db.add(
        User(
            username=username,
            display_name=display_name,
            password_hash=hash_password(password),
            role="admin",
            department_id=department.id,
            avatar_color="#0b9185",
            is_active=True,
            auth_version=0,
        )
    )
    db.commit()


def seed_if_empty(db: Session) -> None:
    if db.scalar(select(User.id).limit(1)):
        return

    depts = [
        Department(name="信息中心", code="IT"),
        Department(name="研发中心", code="RD"),
        Department(name="行政人事部", code="HR"),
    ]
    db.add_all(depts)
    db.flush()

    users = [
        User(
            username="admin",
            display_name="陈启明",
            password_hash=hash_password("ChangeMe123!"),
            role="admin",
            department_id=depts[0].id,
            avatar_color="#0d9488",
        ),
        User(
            username="netadmin",
            display_name="林知微",
            password_hash=hash_password("ChangeMe123!"),
            role="network_admin",
            department_id=depts[0].id,
            avatar_color="#1a4263",
        ),
        User(
            username="biz",
            display_name="周景行",
            password_hash=hash_password("ChangeMe123!"),
            role="dept_user",
            department_id=depts[1].id,
            avatar_color="#b45309",
        ),
        User(
            username="viewer",
            display_name="苏晚晴",
            password_hash=hash_password("ChangeMe123!"),
            role="viewer",
            department_id=depts[2].id,
            avatar_color="#7c3aed",
        ),
    ]
    db.add_all(users)
    db.flush()

    sites = [
        Site(name="总部园区", code="HQ", location="市高新区 A 座", remark="核心机房与办公网"),
        Site(name="研发分园区", code="RD", location="软件园 B2", remark="研发与测试网"),
        Site(name="分支办事处", code="BR", location="城南写字楼 18F"),
    ]
    db.add_all(sites)
    db.flush()

    # 用较小网段加快种子速度，同时覆盖完整池逻辑：/28 = 16 地址
    specs = [
        {
            "name": "办公网-A",
            "cidr": "10.10.1.0/28",
            "site_id": sites[0].id,
            "department_id": depts[0].id,
            "gateway": "10.10.1.1",
            "vlan_id": 10,
            "purpose": "办公终端",
            "description": "总部办公 VLAN10（演示 /28）",
        },
        {
            "name": "服务器区",
            "cidr": "10.10.20.0/28",
            "site_id": sites[0].id,
            "department_id": depts[0].id,
            "gateway": "10.10.20.1",
            "vlan_id": 20,
            "purpose": "生产服务器",
        },
        {
            "name": "研发终端网",
            "cidr": "10.20.5.0/28",
            "site_id": sites[1].id,
            "department_id": depts[1].id,
            "gateway": "10.20.5.1",
            "vlan_id": 105,
            "purpose": "研发办公",
        },
        {
            "name": "测试隔离网",
            "cidr": "10.20.88.0/28",
            "site_id": sites[1].id,
            "department_id": depts[1].id,
            "gateway": "10.20.88.1",
            "vlan_id": 188,
            "purpose": "测试环境",
        },
        {
            "name": "分支办公网",
            "cidr": "192.168.30.0/28",
            "site_id": sites[2].id,
            "department_id": depts[2].id,
            "gateway": "192.168.30.1",
            "vlan_id": 30,
            "purpose": "分支办公",
        },
    ]

    subnets: list[Subnet] = []
    for sp in specs:
        subnets.append(create_subnet_with_pool(db, **sp))

    def pick(subnet: Subnet, last_octet_or_suffix: str) -> IpAddress | None:
        # match by full address ending
        for ip in db.scalars(select(IpAddress).where(IpAddress.subnet_id == subnet.id)).all():
            if ip.address.endswith(last_octet_or_suffix):
                return ip
        return None

    now = datetime.now(UTC)
    admin, netadmin, biz, viewer = users

    samples = [
        (
            subnets[0],
            ".2",
            "allocated",
            "pc-hq-012",
            "AA:BB:CC:11:22:01",
            "行政办电脑",
            "pc",
            viewer,
            date.today() + timedelta(days=120),
        ),
        (
            subnets[0],
            ".3",
            "allocated",
            "print-hq-01",
            "AA:BB:CC:11:22:15",
            "一楼打印机",
            "printer",
            netadmin,
            None,
        ),
        (
            subnets[0],
            ".4",
            "allocated",
            "ap-floor3",
            "AA:BB:CC:33:01:80",
            "3F-AP",
            "ap",
            netadmin,
            date.today() + timedelta(days=5),
        ),
        (subnets[0], ".5", "disabled", None, None, None, None, None, None),
        (
            subnets[1],
            ".2",
            "allocated",
            "erp-app-01",
            "52:54:00:AB:01:10",
            "ERP 应用节点",
            "server",
            admin,
            None,
        ),
        (
            subnets[1],
            ".3",
            "allocated",
            "erp-db-01",
            "52:54:00:AB:01:11",
            "ERP 数据库",
            "server",
            admin,
            None,
        ),
        (subnets[1], ".4", "reserved", "vip-erp", None, None, None, admin, None),
        (
            subnets[2],
            ".2",
            "allocated",
            "dev-zhou-nb",
            "3C:22:FB:10:20:32",
            "周景行笔记本",
            "pc",
            biz,
            date.today() + timedelta(days=20),
        ),
        (
            subnets[2],
            ".3",
            "allocated",
            "dev-build-02",
            "3C:22:FB:10:20:40",
            "编译机",
            "server",
            biz,
            None,
        ),
        (
            subnets[3],
            ".2",
            "allocated",
            "qa-web-01",
            None,
            "测试 Web",
            "server",
            netadmin,
            date.today() + timedelta(days=3),
        ),
        (
            subnets[4],
            ".2",
            "allocated",
            "br-cam-01",
            "B0:BE:76:30:00:25",
            "前台摄像头",
            "camera",
            viewer,
            None,
        ),
    ]

    for subnet, suffix, status, hostname, mac, device_name, device_type, owner, exp in samples:
        ip = pick(subnet, suffix)
        if not ip or ip.is_network_or_broadcast:
            continue
        if status == "allocated" and owner:
            # 同时往设备台账插一条，方便演示“先有设备再绑 IP”
            dev = None
            if device_name:
                dev = Device(
                    name=device_name,
                    device_type=device_type or "other",
                    mac=mac,
                    location=getattr(getattr(subnet, "site", None), "name", None),
                    department_id=owner.department_id,
                    owner_user_id=owner.id,
                )
                db.add(dev)
                db.flush()
            ip.status = "allocated"
            ip.hostname = hostname
            ip.mac = mac
            ip.device_name = device_name
            ip.device_type = device_type
            ip.device_id = dev.id if dev else None
            ip.owner_user_id = owner.id
            ip.department_id = owner.department_id
            ip.allocated_at = now - timedelta(days=30)
            ip.expire_at = exp
        elif status == "reserved":
            ip.status = "reserved"
            ip.hostname = hostname
            ip.remark = "VIP 预留"
            ip.owner_user_id = owner.id if owner else None
        elif status == "disabled":
            ip.status = "disabled"
            ip.remark = "端口故障隔离"

    # 再放两台未绑定 IP 的设备，演示“空闲设备”
    db.add_all(
        [
            Device(
                name="备用笔记本-01",
                device_type="pc",
                mac="AA:BB:CC:00:00:01",
                location="研发分园区",
                department_id=depts[1].id,
                owner_user_id=biz.id,
                remark="还没分配地址",
            ),
            Device(
                name="会议室电视",
                device_type="other",
                location="总部园区 3F",
                department_id=depts[0].id,
                owner_user_id=netadmin.id,
            ),
        ]
    )

    db.add_all(
        [
            AllocationLog(
                address="10.20.5.2",
                action="allocate",
                operator_id=netadmin.id,
                operator_name=netadmin.display_name,
                detail="分配给 周景行 / 研发笔记本",
            ),
            AllocationLog(
                address="10.10.1.4",
                action="allocate",
                operator_id=netadmin.id,
                operator_name=netadmin.display_name,
                detail="无线 AP 上线",
            ),
            AllocationLog(
                address="10.10.20.4",
                action="reserve",
                operator_id=admin.id,
                operator_name=admin.display_name,
                detail="ERP VIP 预留",
            ),
        ]
    )

    # conflicts
    ip_print = pick(subnets[0], ".3")
    free_ip = next(
        (
            x
            for x in db.scalars(select(IpAddress).where(IpAddress.subnet_id == subnets[0].id)).all()
            if x.status == "free"
        ),
        None,
    )
    db.add(
        Conflict(
            ip_address_id=ip_print.id if ip_print else None,
            ip_address=ip_print.address if ip_print else "10.10.1.3",
            subnet_cidr=subnets[0].cidr,
            conflict_type="duplicate_mac",
            detail="探测到 MAC AA:BB:CC:11:22:99 与台账不一致（种子数据）",
            status="open",
        )
    )
    if free_ip:
        db.add(
            Conflict(
                ip_address_id=free_ip.id,
                ip_address=free_ip.address,
                subnet_cidr=subnets[0].cidr,
                conflict_type="rogue_host",
                detail="扫描发现主机 online，但地址池中状态为空闲（种子数据）",
                status="open",
            )
        )
    db.add(
        Conflict(
            ip_address="10.10.20.8",
            subnet_cidr=subnets[1].cidr,
            conflict_type="status_mismatch",
            detail="台账 free，交换机 ARP 仍有残留条目（已解决示例）",
            status="resolved",
        )
    )

    db.commit()
