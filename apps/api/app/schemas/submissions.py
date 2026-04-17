import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import AuditActionType, AuditSource, Shift, SubmissionStatus
from app.schemas.workorders import WorkorderSummaryResponse


class CreateSubmissionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_generated_id: uuid.UUID | None = None
    workorder_id: uuid.UUID
    work_date: date
    shift: Shift
    team_number: str | None = Field(default=None, max_length=100)
    ticket_number: str | None = Field(default=None, max_length=100)
    skipped_grids: int
    force_tested_grids: int
    completed_grids: int


class UpdateSubmissionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version_number: int = Field(ge=1)
    work_date: date | None = None
    shift: Shift | None = None
    team_number: str | None = Field(default=None, max_length=100)
    ticket_number: str | None = Field(default=None, max_length=100)
    skipped_grids: int | None = None
    force_tested_grids: int | None = None
    completed_grids: int | None = None


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: uuid.UUID
    client_generated_id: uuid.UUID
    workorder_id: uuid.UUID
    owner_user_id: uuid.UUID
    submitter_name_snapshot: str
    submitter_email_snapshot: str
    work_date: date
    shift: Shift
    team_number: str | None
    ticket_number: str | None
    skipped_grids: int
    force_tested_grids: int
    completed_grids: int
    status: SubmissionStatus
    version_number: int
    started_at: datetime
    ended_at: datetime | None
    created_at: datetime
    updated_at: datetime
    file_submission_pending: bool
    workorder_summary: WorkorderSummaryResponse | None = None


class SubmissionAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: uuid.UUID
    submission_id: uuid.UUID
    action_type: AuditActionType
    actor_user_id: uuid.UUID
    actor_role: str
    source: AuditSource
    changed_fields_json: dict[str, object] | None
    before_snapshot_json: dict[str, object] | None
    after_snapshot_json: dict[str, object] | None
    created_at: datetime
