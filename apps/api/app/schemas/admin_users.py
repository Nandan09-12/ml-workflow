import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.core.enums import AccountStatus, ApprovalDecision, RequestedRole


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: uuid.UUID
    auth_user_id: uuid.UUID
    full_name: str
    email: EmailStr
    requested_role: RequestedRole
    approved_role: RequestedRole | None
    account_status: AccountStatus
    approved_at: datetime | None
    approved_by_user_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class ApprovalAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: uuid.UUID
    user_id: uuid.UUID
    requested_role: RequestedRole
    decision: ApprovalDecision
    reviewed_by_user_id: uuid.UUID | None
    reviewed_at: datetime | None
    review_notes: str | None
    created_at: datetime
