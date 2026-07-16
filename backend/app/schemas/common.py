from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.security import validate_password_strength

T = TypeVar("T")
RoleValue = Literal["admin", "network_admin", "dept_user", "viewer"]
DeviceTypeValue = Literal["server", "pc", "printer", "ap", "camera", "other"]


class APIModel(BaseModel):
    """Base request/response model with consistent whitespace normalization."""

    model_config = ConfigDict(str_strip_whitespace=True)


class ORMModel(APIModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


class PageMeta(APIModel):
    page: int
    page_size: int
    total: int


class Page(APIModel, Generic[T]):
    items: list[T]
    meta: PageMeta


class BatchIdsRequest(APIModel):
    ids: list[int] = Field(min_length=1, max_length=200)


class Message(APIModel):
    message: str
    data: Any | None = None


class LoginRequest(APIModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class ChangePasswordRequest(APIModel):
    old_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return validate_password_strength(value)


class TokenResponse(APIModel):
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


class UserCreate(APIModel):
    username: str = Field(min_length=2, max_length=50, pattern=r"^[A-Za-z0-9._-]+$")
    password: str = Field(min_length=12, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)
    role: RoleValue = "viewer"
    department_id: int = Field(gt=0)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_strength(value)


class UserUpdate(APIModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    role: RoleValue | None = None
    department_id: int | None = Field(default=None, gt=0)
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_optional_password(cls, value: str | None) -> str | None:
        return validate_password_strength(value) if value is not None else None


class DepartmentOut(ORMModel):
    id: int
    name: str
    code: str


class DepartmentCreate(APIModel):
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=1, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")


class SiteOut(ORMModel):
    id: int
    name: str
    code: str
    location: str
    remark: str | None = None
    subnet_count: int = 0


class SiteCreate(APIModel):
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=1, max_length=50, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
    location: str = Field(default="", max_length=200)
    remark: str | None = Field(default=None, max_length=500)


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


class SubnetCreate(APIModel):
    name: str = Field(min_length=1, max_length=100)
    cidr: str = Field(min_length=3, max_length=50)
    site_id: int = Field(gt=0)
    department_id: int | None = Field(default=None, gt=0)
    gateway: str = Field(default="", max_length=50)
    vlan_id: int | None = Field(default=None, ge=1, le=4094)
    purpose: str = Field(default="通用", min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)


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


class IpListPage(APIModel):
    """地址列表分页结果。"""

    items: list[IpOut]
    total: int
    page: int
    page_size: int


class AllocateRequest(APIModel):
    hostname: str | None = Field(default=None, max_length=100)
    mac: str | None = Field(default=None, max_length=30)
    device_name: str | None = Field(default=None, max_length=100)
    device_type: DeviceTypeValue | None = "pc"
    device_id: int | None = Field(default=None, gt=0)
    expire_at: str | None = Field(default=None, max_length=10)
    remark: str | None = Field(default=None, max_length=500)


class ReserveRequest(APIModel):
    remark: str | None = Field(default="人工预留", max_length=500)


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


class DeviceCreate(APIModel):
    name: str = Field(min_length=1, max_length=100)
    device_type: DeviceTypeValue = "other"
    mac: str | None = Field(default=None, max_length=30)
    location: str | None = Field(default=None, max_length=200)
    department_id: int | None = Field(default=None, gt=0)
    owner_user_id: int | None = Field(default=None, gt=0)
    remark: str | None = Field(default=None, max_length=500)


class DeviceUpdate(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    device_type: DeviceTypeValue | None = None
    mac: str | None = Field(default=None, max_length=30)
    location: str | None = Field(default=None, max_length=200)
    department_id: int | None = Field(default=None, gt=0)
    owner_user_id: int | None = Field(default=None, gt=0)
    remark: str | None = Field(default=None, max_length=500)


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


class DashboardOut(APIModel):
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
