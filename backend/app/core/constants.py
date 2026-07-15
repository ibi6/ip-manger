"""Domain constants and validation helpers."""

from __future__ import annotations

VALID_ROLES = frozenset({"admin", "network_admin", "dept_user", "viewer"})
VALID_IP_STATUS = frozenset({"free", "allocated", "reserved", "disabled"})
VALID_SUBNET_STATUS = frozenset({"active", "archived"})
VALID_DEVICE_TYPES = frozenset({"server", "pc", "printer", "ap", "camera", "other"})
VALID_CONFLICT_STATUS = frozenset({"open", "resolved"})
VALID_CONFLICT_TYPES = frozenset({"duplicate_mac", "rogue_host", "status_mismatch"})

MANAGE_NETWORK_ROLES = frozenset({"admin", "network_admin"})
ALLOCATE_ROLES = frozenset({"admin", "network_admin", "dept_user"})
