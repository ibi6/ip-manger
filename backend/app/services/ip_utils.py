from __future__ import annotations

import ipaddress
import re


MAC_RE = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")


def parse_network(cidr: str) -> ipaddress.IPv4Network:
    """把用户输入的 CIDR 转成网络对象，顺便做一点限制。"""
    try:
        net = ipaddress.ip_network(cidr.strip(), strict=False)
    except ValueError as exc:
        raise ValueError(f"无效 CIDR: {cidr}") from exc
    if not isinstance(net, ipaddress.IPv4Network):
        raise ValueError("当前仅支持 IPv4")
    # 太大了 sqlite 插数据会很慢，作业环境先限制一下
    if net.prefixlen < 16 or net.prefixlen > 30:
        raise ValueError("自动展开仅支持前缀 /16–/30，演示建议 /24 或 /28")
    if net.num_addresses > 1024:
        raise ValueError("地址数超过 1024，请用更小网段（比如 /24）")
    return net


def normalize_mac(mac: str | None) -> str | None:
    if not mac:
        return None
    mac = mac.strip()
    if not MAC_RE.match(mac):
        raise ValueError("MAC 格式应为 AA:BB:CC:DD:EE:FF")
    return mac.upper().replace("-", ":")


def host_status_for(addr: ipaddress.IPv4Address, net: ipaddress.IPv4Network, gateway: str | None) -> tuple[str, bool, str | None]:
    """Return (status, is_network_or_broadcast, remark)."""
    if addr == net.network_address:
        return "reserved", True, "网络地址"
    if addr == net.broadcast_address:
        return "reserved", True, "广播地址"
    if gateway:
        try:
            if addr == ipaddress.IPv4Address(gateway):
                return "reserved", False, "默认网关"
        except ValueError:
            pass
    return "free", False, None
