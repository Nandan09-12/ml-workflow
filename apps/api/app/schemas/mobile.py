import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.enums import AccountStatus, RequestedRole


class MobileSyncRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_batch_id: uuid.UUID
    device_id: str = Field(min_length=1, max_length=255)
    operations: list[dict[str, Any]] = Field(default_factory=list)


class MobileUserStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: uuid.UUID
    auth_user_id: uuid.UUID
    full_name: str
    email: EmailStr
    requested_role: RequestedRole
    approved_role: RequestedRole | None
    account_status: AccountStatus


class MobileReferenceDataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    zones: list[str]
    shifts: list[str]
    submission_statuses: list[str]


class MobileBootstrapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    contract_version: str
    offline_sync_enabled: bool
    server_time_utc: datetime
    user: MobileUserStateResponse
    reference_data: MobileReferenceDataResponse


class MobileSyncResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    contract_version: str
    accepted: bool
    status: str
    message: str
    received_operations_count: int
    processed_operations_count: int
    rejected_operations_count: int
    server_time_utc: datetime
