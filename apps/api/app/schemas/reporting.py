import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr


class DashboardSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    approved_drive_testers: int
    ongoing_submissions: int
    completed_submissions: int
    no_submission_yet: int
    active_workorders: int
    completed_workorders: int
    reference_date: date
    date_from: date | None
    date_to: date | None


class NoSubmissionYetUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: EmailStr

