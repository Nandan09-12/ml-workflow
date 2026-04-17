import uuid
from dataclasses import dataclass
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import Region, Shift, WorkorderStatus


class StartDriveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_generated_id: uuid.UUID | None = None
    workorder_code: str = Field(min_length=1, max_length=255)
    region: Region | None = None
    total_grids: int | None = Field(default=None, gt=0)
    work_date: date
    shift: Shift
    team_number: str | None = Field(default=None, max_length=100)
    ticket_number: str | None = Field(default=None, max_length=100)


class WorkorderLookupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workorder_code: str = Field(min_length=1, max_length=255)


@dataclass(frozen=True)
class WorkorderSummary:
    workorder_code: str
    region: Region
    status: WorkorderStatus
    total_grids: int
    completed_grids: int
    skipped_grids: int
    remaining_grids: int
    progress_percent: float


@dataclass(frozen=True)
class WorkorderView:
    id: uuid.UUID
    workorder_code: str
    region: Region
    status: WorkorderStatus
    total_grids: int
    completed_grids: int
    skipped_grids: int
    remaining_grids: int
    progress_percent: float
    created_at: datetime
    updated_at: datetime


class WorkorderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: uuid.UUID
    workorder_code: str
    region: Region
    status: WorkorderStatus
    total_grids: int
    completed_grids: int
    skipped_grids: int
    remaining_grids: int
    progress_percent: float
    created_at: datetime
    updated_at: datetime


class WorkorderSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    workorder_code: str
    region: Region
    status: WorkorderStatus
    total_grids: int
    completed_grids: int
    skipped_grids: int
    remaining_grids: int
    progress_percent: float
