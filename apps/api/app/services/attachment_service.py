import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from app.core.config import Settings
from app.core.enums import AccountStatus, AuditActionType, AuditSource, RequestedRole
from app.core.errors import AppError, ErrorCode
from app.integrations.storage.base import (
    StorageIntegrationError,
    StorageProviderProtocol,
)
from app.models.app_user import AppUser
from app.models.submission import Submission
from app.models.submission_attachment import SubmissionAttachment
from app.models.submission_audit_log import SubmissionAuditLog


@dataclass(frozen=True)
class AttachmentUpload:
    file_name: str
    content_type: str
    content: bytes


@dataclass(frozen=True)
class AttachmentView:
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


@dataclass(frozen=True)
class DownloadUrlView:
    url: str
    expires_in_seconds: int


class AttachmentRepositoryProtocol(Protocol):
    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None: ...

    async def get_submission_by_id(self, submission_id: uuid.UUID) -> Submission | None: ...

    async def count_active_attachments(self, submission_id: uuid.UUID) -> int: ...

    async def create_attachment(self, attachment: SubmissionAttachment) -> SubmissionAttachment: ...

    async def list_attachments_for_submission(
        self,
        submission_id: uuid.UUID,
        *,
        active_only: bool = True,
    ) -> list[SubmissionAttachment]: ...

    async def get_attachment_by_id(self, attachment_id: uuid.UUID) -> SubmissionAttachment | None: ...

    async def save_attachment(self, attachment: SubmissionAttachment) -> SubmissionAttachment: ...

    async def create_audit_log(self, log: SubmissionAuditLog) -> SubmissionAuditLog: ...

    def transaction(self) -> Any: ...


class AttachmentService:
    MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024
    MAX_ACTIVE_ATTACHMENTS = 5
    DOWNLOAD_URL_EXPIRY_SECONDS = 3600

    ALLOWED_EXTENSIONS = {".csv", ".xlsx"}
    ALLOWED_MIME_TYPES = {
        "text/csv",
        "application/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }

    def __init__(
        self,
        *,
        repository: AttachmentRepositoryProtocol,
        storage: StorageProviderProtocol,
        settings: Settings,
    ) -> None:
        self._repository = repository
        self._storage = storage
        self._settings = settings

    async def upload_attachment(
        self,
        auth_payload: dict[str, Any],
        submission_id: uuid.UUID,
        upload: AttachmentUpload,
    ) -> AttachmentView:
        actor = await self._require_approved_user(auth_payload)
        submission = await self._get_submission_or_404(submission_id)
        self._assert_can_access_submission(actor, submission)

        file_name = self._normalize_file_name(upload.file_name)
        extension = self._extract_extension(file_name)
        content_type = upload.content_type.strip().lower()
        file_size_bytes = len(upload.content)

        self._validate_file(extension=extension, content_type=content_type, file_size_bytes=file_size_bytes)

        active_count = await self._repository.count_active_attachments(submission.id)
        if active_count >= self.MAX_ACTIVE_ATTACHMENTS:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "Maximum active attachments reached for this submission.",
                status_code=400,
                details={"max_active_attachments": self.MAX_ACTIVE_ATTACHMENTS},
            )

        object_path = f"{submission.id}/{uuid.uuid4().hex}{extension}"
        bucket_name = self._settings.supabase_storage_bucket
        try:
            await self._storage.upload_bytes(
                bucket_name=bucket_name,
                object_path=object_path,
                content_type=content_type,
                data=upload.content,
            )
        except StorageIntegrationError as exc:
            raise AppError(
                ErrorCode.INTERNAL_SERVER_ERROR,
                "Failed to upload file to storage.",
                status_code=500,
            ) from exc

        now = datetime.now(UTC)
        attachment = SubmissionAttachment(
            id=uuid.uuid4(),
            submission_id=submission.id,
            file_name=file_name,
            bucket_name=bucket_name,
            object_path=object_path,
            mime_type=content_type,
            file_extension=extension,
            file_size_bytes=file_size_bytes,
            uploaded_by_user_id=actor.id,
            uploaded_at=now,
            is_active=True,
        )

        async with self._repository.transaction():
            created = await self._repository.create_attachment(attachment)
            await self._repository.create_audit_log(
                self._build_audit_log(
                    submission_id=submission.id,
                    actor=actor,
                    action_type=AuditActionType.FILE_UPLOADED,
                    changed_fields=["attachment_uploaded"],
                )
            )

        return self._to_view(created)

    async def list_attachments(
        self,
        auth_payload: dict[str, Any],
        submission_id: uuid.UUID,
    ) -> list[AttachmentView]:
        actor = await self._require_approved_user(auth_payload)
        submission = await self._get_submission_or_404(submission_id)
        self._assert_can_access_submission(actor, submission)
        attachments = await self._repository.list_attachments_for_submission(submission.id, active_only=True)
        return [self._to_view(item) for item in attachments]

    async def get_attachment(
        self,
        auth_payload: dict[str, Any],
        attachment_id: uuid.UUID,
    ) -> AttachmentView:
        actor = await self._require_approved_user(auth_payload)
        attachment = await self._get_active_attachment_or_404(attachment_id)
        submission = await self._get_submission_or_404(attachment.submission_id)
        self._assert_can_access_submission(actor, submission)
        return self._to_view(attachment)

    async def create_download_url(
        self,
        auth_payload: dict[str, Any],
        attachment_id: uuid.UUID,
    ) -> DownloadUrlView:
        actor = await self._require_approved_user(auth_payload)
        attachment = await self._get_active_attachment_or_404(attachment_id)
        submission = await self._get_submission_or_404(attachment.submission_id)
        self._assert_can_access_submission(actor, submission)
        try:
            url = await self._storage.create_signed_download_url(
                bucket_name=attachment.bucket_name,
                object_path=attachment.object_path,
                expires_in_seconds=self.DOWNLOAD_URL_EXPIRY_SECONDS,
            )
        except StorageIntegrationError as exc:
            raise AppError(
                ErrorCode.INTERNAL_SERVER_ERROR,
                "Failed to create signed download URL.",
                status_code=500,
            ) from exc

        return DownloadUrlView(url=url, expires_in_seconds=self.DOWNLOAD_URL_EXPIRY_SECONDS)

    async def delete_attachment(
        self,
        auth_payload: dict[str, Any],
        attachment_id: uuid.UUID,
    ) -> None:
        actor = await self._require_approved_user(auth_payload)
        async with self._repository.transaction():
            attachment = await self._repository.get_attachment_by_id(attachment_id)
            if attachment is None:
                raise AppError(ErrorCode.NOT_FOUND, "Attachment was not found.", status_code=404)
            submission = await self._get_submission_or_404(attachment.submission_id)
            self._assert_can_access_submission(actor, submission)
            if not attachment.is_active:
                return
            attachment.is_active = False
            await self._repository.save_attachment(attachment)
            await self._repository.create_audit_log(
                self._build_audit_log(
                    submission_id=submission.id,
                    actor=actor,
                    action_type=AuditActionType.FILE_REMOVED,
                    changed_fields=["attachment_removed"],
                )
            )

    async def _require_approved_user(self, auth_payload: dict[str, Any]) -> AppUser:
        auth_user_id = self._extract_auth_user_id(auth_payload)
        actor = await self._repository.get_by_auth_user_id(auth_user_id)
        if actor is None:
            raise AppError(
                ErrorCode.NOT_FOUND,
                "Authenticated app user profile not found.",
                status_code=404,
            )
        if actor.account_status != AccountStatus.APPROVED:
            raise AppError(
                ErrorCode.ACCOUNT_NOT_APPROVED,
                "Account is not approved for attachment actions.",
                status_code=403,
            )
        return actor

    async def _get_submission_or_404(self, submission_id: uuid.UUID) -> Submission:
        submission = await self._repository.get_submission_by_id(submission_id)
        if submission is None:
            raise AppError(ErrorCode.NOT_FOUND, "Submission was not found.", status_code=404)
        return submission

    async def _get_active_attachment_or_404(self, attachment_id: uuid.UUID) -> SubmissionAttachment:
        attachment = await self._repository.get_attachment_by_id(attachment_id)
        if attachment is None or not attachment.is_active:
            raise AppError(ErrorCode.NOT_FOUND, "Attachment was not found.", status_code=404)
        return attachment

    @staticmethod
    def _extract_auth_user_id(auth_payload: dict[str, Any]) -> uuid.UUID:
        raw_sub = auth_payload.get("sub")
        if raw_sub is None:
            raise AppError(
                ErrorCode.UNAUTHORIZED,
                "Authenticated user id is missing from token.",
                status_code=401,
            )
        try:
            return uuid.UUID(str(raw_sub))
        except (TypeError, ValueError) as exc:
            raise AppError(
                ErrorCode.UNAUTHORIZED,
                "Authenticated user id is invalid.",
                status_code=401,
            ) from exc

    @staticmethod
    def _normalize_file_name(file_name: str) -> str:
        normalized = file_name.strip()
        if not normalized:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "Uploaded file name is required.",
                status_code=400,
            )
        return normalized

    def _validate_file(self, *, extension: str, content_type: str, file_size_bytes: int) -> None:
        if extension not in self.ALLOWED_EXTENSIONS:
            raise AppError(
                ErrorCode.UNSUPPORTED_FILE_TYPE,
                "Unsupported file extension. Only .csv and .xlsx are allowed in v1.",
                status_code=400,
                details={"file_extension": extension, "allowed_extensions": sorted(self.ALLOWED_EXTENSIONS)},
            )
        if content_type not in self.ALLOWED_MIME_TYPES:
            raise AppError(
                ErrorCode.UNSUPPORTED_FILE_TYPE,
                "Unsupported MIME type.",
                status_code=400,
                details={"mime_type": content_type, "allowed_mime_types": sorted(self.ALLOWED_MIME_TYPES)},
            )
        if file_size_bytes > self.MAX_FILE_SIZE_BYTES:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "Attachment exceeds max size of 25 MB.",
                status_code=400,
                details={
                    "max_file_size_bytes": self.MAX_FILE_SIZE_BYTES,
                    "file_size_bytes": file_size_bytes,
                },
            )

    @staticmethod
    def _extract_extension(file_name: str) -> str:
        extension = Path(file_name).suffix.strip().lower()
        if not extension:
            raise AppError(
                ErrorCode.UNSUPPORTED_FILE_TYPE,
                "File extension is required.",
                status_code=400,
            )
        return extension

    @staticmethod
    def _assert_can_access_submission(actor: AppUser, submission: Submission) -> None:
        is_owner = submission.owner_user_id == actor.id
        is_admin = actor.approved_role == RequestedRole.ADMIN
        if not is_owner and not is_admin:
            raise AppError(
                ErrorCode.NOT_OWNER,
                "Submission does not belong to the authenticated user.",
                status_code=403,
            )

    @staticmethod
    def _build_audit_log(
        *,
        submission_id: uuid.UUID,
        actor: AppUser,
        action_type: AuditActionType,
        changed_fields: list[str],
    ) -> SubmissionAuditLog:
        return SubmissionAuditLog(
            id=uuid.uuid4(),
            submission_id=submission_id,
            action_type=action_type,
            actor_user_id=actor.id,
            actor_role=(
                actor.approved_role.value
                if actor.approved_role is not None
                else actor.requested_role.value
            ),
            source=AuditSource.WEB,
            changed_fields_json={"fields": changed_fields},
            before_snapshot_json=None,
            after_snapshot_json=None,
            created_at=datetime.now(UTC),
        )

    @staticmethod
    def _to_view(attachment: SubmissionAttachment) -> AttachmentView:
        return AttachmentView(
            id=attachment.id,
            submission_id=attachment.submission_id,
            file_name=attachment.file_name,
            bucket_name=attachment.bucket_name,
            object_path=attachment.object_path,
            mime_type=attachment.mime_type,
            file_extension=attachment.file_extension,
            file_size_bytes=attachment.file_size_bytes,
            uploaded_by_user_id=attachment.uploaded_by_user_id,
            uploaded_at=attachment.uploaded_at,
            is_active=attachment.is_active,
        )
