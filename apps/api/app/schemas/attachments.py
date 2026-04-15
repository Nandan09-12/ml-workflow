import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    submission_id: uuid.UUID
    file_name: str
    bucket_name: str
    object_path: str
    mime_type: str
    file_extension: str
    file_size_bytes: int
    uploaded_by_user_id: uuid.UUID
    uploaded_at: datetime
    is_active: bool


class DownloadUrlResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    url: str
    expires_in_seconds: int
