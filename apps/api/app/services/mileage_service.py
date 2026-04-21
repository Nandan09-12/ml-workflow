import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Protocol

from app.core.config import Settings
from app.core.enums import AccountStatus
from app.core.errors import AppError, ErrorCode
from app.integrations.storage.base import (
    StorageIntegrationError,
    StorageProviderProtocol,
)
from app.models.app_user import AppUser
from app.models.mileage_entry import MileageEntry


@dataclass(frozen=True)
class MileageUpload:
    file_name: str
    content_type: str
    content: bytes


@dataclass(frozen=True)
class MileageEntryView:
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


class MileageRepositoryProtocol(Protocol):
    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None: ...

    async def get_mileage_for_owner_and_date(
        self,
        *,
        owner_user_id: uuid.UUID,
        work_date: date,
    ) -> MileageEntry | None: ...

    async def create_mileage_entry(self, entry: MileageEntry) -> MileageEntry: ...

    async def save_mileage_entry(self, entry: MileageEntry) -> MileageEntry: ...

    def transaction(self) -> Any: ...


class MileageService:
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif"}
    ALLOWED_MIME_TYPES = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/heic",
        "image/heif",
    }
    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

    def __init__(
        self,
        *,
        repository: MileageRepositoryProtocol,
        storage: StorageProviderProtocol,
        settings: Settings,
    ) -> None:
        self._repository = repository
        self._storage = storage
        self._settings = settings

    async def get_entry_for_date(
        self,
        auth_payload: dict[str, Any],
        work_date: date,
    ) -> MileageEntryView | None:
        actor = await self._require_approved_user(auth_payload)
        entry = await self._repository.get_mileage_for_owner_and_date(
            owner_user_id=actor.id,
            work_date=work_date,
        )
        if entry is None:
            return None
        return self._to_view(entry)

    async def start_shift(
        self,
        auth_payload: dict[str, Any],
        *,
        work_date: date,
        start_mileage: int,
        started_at: datetime,
        upload: MileageUpload,
    ) -> MileageEntryView:
        actor = await self._require_approved_user(auth_payload)
        if start_mileage < 0:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "Start mileage must be zero or greater.",
                status_code=422,
            )

        existing = await self._repository.get_mileage_for_owner_and_date(
            owner_user_id=actor.id,
            work_date=work_date,
        )
        if existing is not None:
            raise AppError(
                ErrorCode.CONFLICT,
                "A mileage entry already exists for this date. End the existing shift instead.",
                status_code=409,
            )

        start_file_name, start_bucket_name, start_object_path, start_mime_type = await self._upload_image(
            actor_id=actor.id,
            work_date=work_date,
            stage="start",
            upload=upload,
        )

        entry = MileageEntry(
            id=uuid.uuid4(),
            owner_user_id=actor.id,
            work_date=work_date,
            start_mileage=start_mileage,
            end_mileage=None,
            started_at=started_at,
            ended_at=None,
            start_odometer_file_name=start_file_name,
            start_odometer_bucket_name=start_bucket_name,
            start_odometer_object_path=start_object_path,
            start_odometer_mime_type=start_mime_type,
            end_odometer_file_name=None,
            end_odometer_bucket_name=None,
            end_odometer_object_path=None,
            end_odometer_mime_type=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        async with self._repository.transaction():
            created = await self._repository.create_mileage_entry(entry)

        return self._to_view(created)

    async def end_shift(
        self,
        auth_payload: dict[str, Any],
        *,
        work_date: date,
        end_mileage: int,
        ended_at: datetime,
        upload: MileageUpload,
    ) -> MileageEntryView:
        actor = await self._require_approved_user(auth_payload)
        if end_mileage < 0:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "End mileage must be zero or greater.",
                status_code=422,
            )

        entry = await self._repository.get_mileage_for_owner_and_date(
            owner_user_id=actor.id,
            work_date=work_date,
        )
        if entry is None:
            raise AppError(
                ErrorCode.NOT_FOUND,
                "No mileage entry exists for this date. Start the shift first.",
                status_code=404,
            )
        if entry.ended_at is not None:
            raise AppError(
                ErrorCode.CONFLICT,
                "This mileage entry is already completed for the day.",
                status_code=409,
            )
        if end_mileage < entry.start_mileage:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "End mileage cannot be less than start mileage.",
                status_code=422,
            )

        end_file_name, end_bucket_name, end_object_path, end_mime_type = await self._upload_image(
            actor_id=actor.id,
            work_date=work_date,
            stage="end",
            upload=upload,
        )

        now = datetime.now(UTC)
        entry.end_mileage = end_mileage
        entry.ended_at = ended_at
        entry.end_odometer_file_name = end_file_name
        entry.end_odometer_bucket_name = end_bucket_name
        entry.end_odometer_object_path = end_object_path
        entry.end_odometer_mime_type = end_mime_type
        entry.updated_at = now

        async with self._repository.transaction():
            saved = await self._repository.save_mileage_entry(entry)

        return self._to_view(saved)

    async def _require_approved_user(self, auth_payload: dict[str, Any]) -> AppUser:
        raw_sub = auth_payload.get("sub")
        if raw_sub is None:
            raise AppError(
                ErrorCode.UNAUTHORIZED,
                "Authenticated user id is missing from token.",
                status_code=401,
            )

        actor = await self._repository.get_by_auth_user_id(uuid.UUID(str(raw_sub)))
        if actor is None:
            raise AppError(
                ErrorCode.NOT_FOUND,
                "Authenticated app user profile not found.",
                status_code=404,
            )
        if actor.account_status != AccountStatus.APPROVED:
            raise AppError(
                ErrorCode.ACCOUNT_NOT_APPROVED,
                "Account is not approved for mileage actions.",
                status_code=403,
            )
        return actor

    async def _upload_image(
        self,
        *,
        actor_id: uuid.UUID,
        work_date: date,
        stage: str,
        upload: MileageUpload,
    ) -> tuple[str, str, str, str]:
        file_name = self._normalize_file_name(upload.file_name)
        extension = self._extract_extension(file_name)
        mime_type = upload.content_type.strip().lower()
        file_size_bytes = len(upload.content)
        self._validate_file(extension=extension, content_type=mime_type, file_size_bytes=file_size_bytes)

        bucket_name = self._settings.supabase_storage_bucket
        object_path = f"mileage/{actor_id}/{work_date.isoformat()}/{stage}-{uuid.uuid4().hex}{extension}"

        try:
            await self._storage.upload_bytes(
                bucket_name=bucket_name,
                object_path=object_path,
                content_type=mime_type,
                data=upload.content,
            )
        except StorageIntegrationError as exc:
            raise AppError(
                ErrorCode.INTERNAL_SERVER_ERROR,
                "Failed to upload odometer image.",
                status_code=500,
            ) from exc

        return file_name, bucket_name, object_path, mime_type

    def _validate_file(self, *, extension: str, content_type: str, file_size_bytes: int) -> None:
        if extension not in self.ALLOWED_EXTENSIONS:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "Only JPG, JPEG, PNG, HEIC, and HEIF odometer images are allowed.",
                status_code=422,
            )
        if content_type not in self.ALLOWED_MIME_TYPES:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "Unsupported odometer image type.",
                status_code=422,
            )
        if file_size_bytes <= 0 or file_size_bytes > self.MAX_FILE_SIZE_BYTES:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "Odometer image must be between 1 byte and 10 MB.",
                status_code=422,
            )

    @staticmethod
    def _normalize_file_name(file_name: str) -> str:
        normalized = Path(file_name or "odometer-image").name.strip()
        return normalized or "odometer-image"

    @staticmethod
    def _extract_extension(file_name: str) -> str:
        return Path(file_name).suffix.lower()

    @staticmethod
    def _to_view(entry: MileageEntry) -> MileageEntryView:
        return MileageEntryView(
            id=entry.id,
            owner_user_id=entry.owner_user_id,
            work_date=entry.work_date,
            start_mileage=entry.start_mileage,
            end_mileage=entry.end_mileage,
            started_at=entry.started_at,
            ended_at=entry.ended_at,
            start_odometer_file_name=entry.start_odometer_file_name,
            end_odometer_file_name=entry.end_odometer_file_name,
            is_completed=entry.ended_at is not None,
        )
