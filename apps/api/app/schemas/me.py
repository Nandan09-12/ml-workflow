import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.enums import AccountStatus, RequestedRole


class BootstrapRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(min_length=1, max_length=255)
    requested_role: RequestedRole


class AppUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: uuid.UUID
    auth_user_id: uuid.UUID
    full_name: str
    email: EmailStr
    requested_role: RequestedRole
    approved_role: RequestedRole | None
    account_status: AccountStatus


class UpdateMeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(min_length=1, max_length=255)
