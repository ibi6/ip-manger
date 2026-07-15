from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int


class Page(BaseModel, Generic[T]):
    items: list[T]
    meta: PageMeta


class BatchIdsRequest(BaseModel):
    ids: list[int] = Field(min_length=1, max_length=200)


class Message(BaseModel):
    message: str
    data: Any | None = None


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(ORMModel):
    id: int
    username: str
    display_name: str
    role: str
    department_id: int
    department_name: str
    avatar_color: str
    is_active: bool = True


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)
    role: str = "viewer"
    department_id: int


class UserUpdate(BaseModel):
    display_name: str | None = None
    role: str | None = None
    department_id: int | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)


class DepartmentOut(ORMModel):
    id: int
    name: str
    code: str


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=1, max_length=50)


class SiteOut(ORMModel):
    id: int
    name: str
    code: str
    location: str
    remark: str | None = None
    subnet_count: int = 0


class SiteCreate(BaseModel):
    name: str
    code: str
    location: str = ""
    remark: str | None = None


class SubnetOut(ORMModel):
    id: int
    site_id: int
    site_name: str
    name: str
    cidr: str
    gateway: str
    vlan_id: int | None = None
    purpose: str
    department_id: int
    department_name: str
    description: str | None = None
    total_ips: int
    used_ips: int
    free_ips: int
    reserved_ips: int
    disabled_ips: int
    utilization: float
    status: str
    created_at: str | None = None


class SubnetCreate(BaseModel):
    name: str
    cidr: str
    site_id: int
    department_id: int | None = None
    gateway: str = ""
    vlan_id: int | None = None
    purpose: str = "通用"
    description: str | None = None


class IpOut(ORMModel):
    id: int
    subnet_id: int
    subnet_cidr: str
    address: str
    status: str
    hostname: str | None = None
    mac: str | None = None
    device_name: str | None = None
    device_type: str | None = None
    device_id: int | None = None
    owner_name: str | None = None
    owner_user_id: int | None = None
    department_id: int | None = None
    department_name: str | None = None
    allocated_at: str | None = None
    expire_at: str | None = None
    remark: str | None = None
    is_network_or_broadcast: bool = False


class IpListPage(BaseModel):
    """地址列表分页结果。"""

    items: list[IpOut]
    total: int
    page: int
    page_size: int


class AllocateRequest(BaseModel):
    hostname: str | None = None
    mac: str | None = None
    device_name: str | None = None
    device_type: str | None = "pc"
    device_id: int | None = None
    expire_at: str | None = None
    remark: str | None = None


class ReserveRequest(BaseModel):
    remark: str | None = "人工预留"


class DeviceOut(ORMModel):
    id: int
    name: str
    device_type: str
    mac: str | None = None
    location: str | None = None
    department_id: int | None = None
    department_name: str | None = None
    owner_user_id: int | None = None
    owner_name: str | None = None
    remark: str | None = None
    bound_ip: str | None = None
    created_at: str | None = None


class DeviceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    device_type: str = "other"
    mac: str | None = None
    location: str | None = None
    department_id: int | None = None
    owner_user_id: int | None = None
    remark: str | None = None


class DeviceUpdate(BaseModel):
    name: str | None = None
    device_type: str | None = None
    mac: str | None = None
    location: str | None = None
    department_id: int | None = None
    owner_user_id: int | None = None
    remark: str | None = None


class ConflictOut(ORMModel):
    id: int
    ip_address: str
    subnet_cidr: str
    type: str
    detail: str
    status: str
    detected_at: str


class LogOut(ORMModel):
    id: int
    address: str
    action: str
    operator_name: str
    detail: str
    created_at: str


class DashboardOut(BaseModel):
    site_count: int
    subnet_count: int
    total_ips: int
    free_ips: int
    allocated_ips: int
    reserved_ips: int
    disabled_ips: int
    open_conflicts: int
    expiring_soon: int
    top_subnets: list[dict[str, Any]]
    recent_logs: list[LogOut]
