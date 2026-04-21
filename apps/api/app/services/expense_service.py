import uuid
from dataclasses import dataclass
from datetime import date, datetime
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
from app.models.expense_entry import ExpenseEntry


@dataclass(frozen=True)
class ExpenseUpload:
    file_name: str
    content_type: str
    content: bytes


@dataclass(frozen=True)
class ExpenseEntryView:
    id: uuid.UUID
    owner_user_id: uuid.UUID
    expense_date: date
    amount: float
    category: str
    receipt_file_name: str
    created_at: datetime


class ExpenseRepositoryProtocol(Protocol):
    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None: ...
    async def create_expense_entry(self, entry: ExpenseEntry) -> ExpenseEntry: ...
    async def list_expenses_for_owner(self, owner_user_id: uuid.UUID) -> list[ExpenseEntry]: ...
    def transaction(self) -> Any: ...


class ExpenseService:
    ALLOWED_CATEGORIES = {"gas", "food", "room", "other"}
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".pdf"}
    ALLOWED_MIME_TYPES = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/heic",
        "image/heif",
        "application/pdf",
    }
    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

    def __init__(
        self,
        *,
        repository: ExpenseRepositoryProtocol,
        storage: StorageProviderProtocol,
        settings: Settings,
    ) -> None:
        self._repository = repository
        self._storage = storage
        self._settings = settings

    async def create_expense(
        self,
        auth_payload: dict[str, Any],
        *,
        expense_date: date,
        amount: float,
        category: str,
        upload: ExpenseUpload,
    ) -> ExpenseEntryView:
        actor = await self._require_approved_user(auth_payload)
        normalized_category = category.strip().lower()
        if normalized_category not in self.ALLOWED_CATEGORIES:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "Expense category must be one of gas, food, room, or other.",
                status_code=422,
            )
        if amount <= 0:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "Expense amount must be greater than zero.",
                status_code=422,
            )

        receipt_file_name, receipt_bucket_name, receipt_object_path, receipt_mime_type = await self._upload_receipt(
            actor_id=actor.id,
            expense_date=expense_date,
            upload=upload,
        )

        entry = ExpenseEntry(
            id=uuid.uuid4(),
            owner_user_id=actor.id,
            expense_date=expense_date,
            amount=amount,
            category=normalized_category,
            receipt_file_name=receipt_file_name,
            receipt_bucket_name=receipt_bucket_name,
            receipt_object_path=receipt_object_path,
            receipt_mime_type=receipt_mime_type,
        )
        async with self._repository.transaction():
            created = await self._repository.create_expense_entry(entry)
        return self._to_view(created)

    async def list_expenses(self, auth_payload: dict[str, Any]) -> list[ExpenseEntryView]:
        actor = await self._require_approved_user(auth_payload)
        items = await self._repository.list_expenses_for_owner(actor.id)
        return [self._to_view(item) for item in items]

    async def _require_approved_user(self, auth_payload: dict[str, Any]) -> AppUser:
        raw_sub = auth_payload.get("sub")
        if raw_sub is None:
            raise AppError(
                ErrorCode.AUTHENTICATION_FAILED,
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
                "Account is not approved for expense actions.",
                status_code=403,
            )
        return actor

    async def _upload_receipt(
        self,
        *,
        actor_id: uuid.UUID,
        expense_date: date,
        upload: ExpenseUpload,
    ) -> tuple[str, str, str, str]:
        file_name = self._normalize_file_name(upload.file_name)
        extension = self._extract_extension(file_name)
        mime_type = upload.content_type.strip().lower()
        file_size_bytes = len(upload.content)
        self._validate_file(extension=extension, content_type=mime_type, file_size_bytes=file_size_bytes)

        bucket_name = self._settings.supabase_storage_bucket
        object_path = f"expenses/{actor_id}/{expense_date.isoformat()}/{uuid.uuid4().hex}{extension}"
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
                "Failed to upload expense receipt.",
                status_code=500,
            ) from exc

        return file_name, bucket_name, object_path, mime_type

    def _validate_file(self, *, extension: str, content_type: str, file_size_bytes: int) -> None:
        if extension not in self.ALLOWED_EXTENSIONS:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "Only JPG, JPEG, PNG, HEIC, HEIF, and PDF receipts are allowed.",
                status_code=422,
            )
        if content_type not in self.ALLOWED_MIME_TYPES:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "Unsupported receipt file type.",
                status_code=422,
            )
        if file_size_bytes <= 0 or file_size_bytes > self.MAX_FILE_SIZE_BYTES:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "Receipt file must be between 1 byte and 10 MB.",
                status_code=422,
            )

    @staticmethod
    def _normalize_file_name(file_name: str) -> str:
        normalized = Path(file_name or "receipt").name.strip()
        return normalized or "receipt"

    @staticmethod
    def _extract_extension(file_name: str) -> str:
        return Path(file_name).suffix.lower()

    @staticmethod
    def _to_view(entry: ExpenseEntry) -> ExpenseEntryView:
        return ExpenseEntryView(
            id=entry.id,
            owner_user_id=entry.owner_user_id,
            expense_date=entry.expense_date,
            amount=float(entry.amount),
            category=entry.category,
            receipt_file_name=entry.receipt_file_name,
            created_at=entry.created_at,
        )
