import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class MileageEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_user_id: uuid.UUID
    work_date: date
    start_mileage: int
    end_mileage: int | None
    started_at: datetime
    ended_at: datetime | None
    start_odometer_file_name: str
    end_odometer_file_name: str | None
    is_completed: bool
