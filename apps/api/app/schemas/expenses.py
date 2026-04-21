import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ExpenseEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_user_id: uuid.UUID
    expense_date: date
    amount: float
    category: str
    receipt_file_name: str
    created_at: datetime
