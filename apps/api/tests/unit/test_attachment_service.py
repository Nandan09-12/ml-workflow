import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from typing import Any

import pytest

from app.core.config import Settings
from app.core.enums import (
    AccountStatus,
    AuditActionType,
    RequestedRole,
    Shift,
    SubmissionStatus,
    WorkorderStatus,
)
from app.core.errors import AppError
from app.models.app_user import AppUser
from app.models.submission import Submission
from app.models.submission_attachment import SubmissionAttachment
from app.models.submission_audit_log import SubmissionAuditLog
from app.models.workorder import Workorder
from app.services.attachment_service import AttachmentService, AttachmentUpload


class FakeAttachmentStorage:
    def __init__(self) -> None:
        self.uploads: list[tuple[str, str, str, int]] = []

    async def upload_bytes(
        self,
        *,
        bucket_name: str,
        object_path: str,
        content_type: str,
        data: bytes,
    ) -> None:
        self.uploads.append((bucket_name, object_path, content_type, len(data)))

    async def create_signed_download_url(
        self,
        *,
        bucket_name: str,
        object_path: str,
        expires_in_seconds: int,
    ) -> str:
        return (
            f"https://storage.example.com/{bucket_name}/{object_path}"
            f"?expires_in={expires_in_seconds}"
        )


class FakeAttachmentRepository:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.owner_user = AppUser(
            id=uuid.uuid4(),
            auth_user_id=uuid.uuid4(),
            full_name="Owner",
            email="owner@example.com",
            requested_role=RequestedRole.DRIVE_TESTER,
            approved_role=RequestedRole.DRIVE_TESTER,
            account_status=AccountStatus.APPROVED,
            approved_at=now,
            approved_by_user_id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
        )
        self.admin_user = AppUser(
            id=uuid.uuid4(),
            auth_user_id=uuid.uuid4(),
            full_name="Admin",
            email="admin@example.com",
            requested_role=RequestedRole.ADMIN,
            approved_role=RequestedRole.ADMIN,
            account_status=AccountStatus.APPROVED,
            approved_at=now,
            approved_by_user_id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
        )
        self.other_user = AppUser(
            id=uuid.uuid4(),
            auth_user_id=uuid.uuid4(),
            full_name="Other",
            email="other@example.com",
            requested_role=RequestedRole.DRIVE_TESTER,
            approved_role=RequestedRole.DRIVE_TESTER,
            account_status=AccountStatus.APPROVED,
            approved_at=now,
            approved_by_user_id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
        )
        self.pending_user = AppUser(
            id=uuid.uuid4(),
            auth_user_id=uuid.uuid4(),
            full_name="Pending",
            email="pending@example.com",
            requested_role=RequestedRole.DRIVE_TESTER,
            approved_role=None,
            account_status=AccountStatus.PENDING_APPROVAL,
            approved_at=None,
            approved_by_user_id=None,
            created_at=now,
            updated_at=now,
        )
        self.users = [self.owner_user, self.admin_user, self.other_user, self.pending_user]
        self.submission = Submission(
            id=uuid.uuid4(),
            client_generated_id=uuid.uuid4(),
            owner_user_id=self.owner_user.id,
            submitter_name_snapshot=self.owner_user.full_name,
            submitter_email_snapshot=self.owner_user.email,
            workorder_id=uuid.uuid4(),
            work_date=date(2026, 4, 14),
            shift=Shift.AM,
            team_number="11",
            ticket_number="TKT-1",
            skipped_grids=1,
            force_tested_grids=0,
            completed_grids=7,
            status=SubmissionStatus.IN_PROGRESS,
            started_at=now,
            ended_at=None,
            created_at=now,
            created_by_user_id=self.owner_user.id,
            updated_at=now,
            updated_by_user_id=self.owner_user.id,
            version_number=1,
        )
        self.submissions = [self.submission]
        self.workorders: dict[uuid.UUID, Workorder] = {}
        self.attachments: list[SubmissionAttachment] = []
        self.audit_logs: list[SubmissionAuditLog] = []
        self.transaction_entries = 0

    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None:
        return next((user for user in self.users if user.auth_user_id == auth_user_id), None)

    async def get_submission_by_id(self, submission_id: uuid.UUID) -> Submission | None:
        return next((submission for submission in self.submissions if submission.id == submission_id), None)

    async def count_active_attachments(self, submission_id: uuid.UUID) -> int:
        return sum(
            1
            for attachment in self.attachments
            if attachment.submission_id == submission_id and attachment.is_active
        )

    async def create_attachment(self, attachment: SubmissionAttachment) -> SubmissionAttachment:
        self.attachments.append(attachment)
        return attachment

    async def list_attachments_for_submission(
        self,
        submission_id: uuid.UUID,
        *,
        active_only: bool = True,
    ) -> list[SubmissionAttachment]:
        items = [attachment for attachment in self.attachments if attachment.submission_id == submission_id]
        if active_only:
            items = [attachment for attachment in items if attachment.is_active]
        return items

    async def get_attachment_by_id(self, attachment_id: uuid.UUID) -> SubmissionAttachment | None:
        return next((attachment for attachment in self.attachments if attachment.id == attachment_id), None)

    async def save_attachment(self, attachment: SubmissionAttachment) -> SubmissionAttachment:
        return attachment

    async def get_workorder_by_id(self, workorder_id: uuid.UUID) -> Workorder | None:
        return self.workorders.get(workorder_id)

    async def save_workorder(self, workorder: Workorder) -> Workorder:
        self.workorders[workorder.id] = workorder
        return workorder

    async def create_audit_log(self, log: SubmissionAuditLog) -> SubmissionAuditLog:
        self.audit_logs.append(log)
        return log

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        self.transaction_entries += 1
        yield


def _auth_payload(user: AppUser) -> dict[str, Any]:
    return {"sub": str(user.auth_user_id), "email": user.email}


def _workorder(
    owner_user_id: uuid.UUID,
    *,
    total_grids: int = 20,
    status: WorkorderStatus = WorkorderStatus.ACTIVE,
) -> Workorder:
    now = datetime.now(UTC)
    return Workorder(
        id=uuid.uuid4(),
        workorder_code="WO-UNIT",
        workorder_code_normalized="WO-UNIT",
        region=None,  # not needed for these tests
        total_grids=total_grids,
        status=status,
        created_at=now,
        created_by_user_id=owner_user_id,
        updated_at=now,
        updated_by_user_id=owner_user_id,
        completed_at=None,
        completed_by_user_id=None,
    )


def _settings() -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://postgres:postgres@localhost/postgres",
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="service-role",
        supabase_storage_bucket="attachments",
    )


def _upload(
    *,
    filename: str = "report.csv",
    content_type: str = "text/csv",
    size_bytes: int = 128,
) -> AttachmentUpload:
    return AttachmentUpload(
        file_name=filename,
        content_type=content_type,
        content=b"x" * size_bytes,
    )


async def test_upload_attachment_creates_metadata_and_audit() -> None:
    repo = FakeAttachmentRepository()
    storage = FakeAttachmentStorage()
    service = AttachmentService(repository=repo, storage=storage, settings=_settings())

    uploaded = await service.upload_attachment(
        _auth_payload(repo.owner_user),
        repo.submission.id,
        _upload(),
    )

    assert uploaded.file_extension == ".csv"
    assert uploaded.mime_type == "text/csv"
    assert uploaded.file_size_bytes == 128
    assert uploaded.is_active is True
    assert repo.transaction_entries == 1
    assert len(repo.attachments) == 1
    assert len(repo.audit_logs) == 1
    assert repo.audit_logs[0].action_type == AuditActionType.FILE_UPLOADED
    assert len(storage.uploads) == 1


async def test_upload_attachment_rejects_xls_extension() -> None:
    repo = FakeAttachmentRepository()
    storage = FakeAttachmentStorage()
    service = AttachmentService(repository=repo, storage=storage, settings=_settings())

    with pytest.raises(AppError) as exc:
        await service.upload_attachment(
            _auth_payload(repo.owner_user),
            repo.submission.id,
            _upload(filename="legacy.xls", content_type="application/vnd.ms-excel"),
        )

    assert exc.value.code.value == "UNSUPPORTED_FILE_TYPE"
    assert exc.value.status_code == 400


async def test_upload_attachment_rejects_mime_not_allowlisted() -> None:
    repo = FakeAttachmentRepository()
    storage = FakeAttachmentStorage()
    service = AttachmentService(repository=repo, storage=storage, settings=_settings())

    with pytest.raises(AppError) as exc:
        await service.upload_attachment(
            _auth_payload(repo.owner_user),
            repo.submission.id,
            _upload(content_type="text/plain"),
        )

    assert exc.value.code.value == "UNSUPPORTED_FILE_TYPE"
    assert exc.value.status_code == 400


async def test_upload_attachment_rejects_file_size_over_25mb() -> None:
    repo = FakeAttachmentRepository()
    storage = FakeAttachmentStorage()
    service = AttachmentService(repository=repo, storage=storage, settings=_settings())

    with pytest.raises(AppError) as exc:
        await service.upload_attachment(
            _auth_payload(repo.owner_user),
            repo.submission.id,
            _upload(size_bytes=(25 * 1024 * 1024) + 1),
        )

    assert exc.value.code.value == "VALIDATION_ERROR"
    assert exc.value.status_code == 400


async def test_upload_attachment_rejects_when_active_count_reaches_limit() -> None:
    repo = FakeAttachmentRepository()
    storage = FakeAttachmentStorage()
    service = AttachmentService(repository=repo, storage=storage, settings=_settings())
    now = datetime.now(UTC)
    repo.attachments.append(
        SubmissionAttachment(
            id=uuid.uuid4(),
            submission_id=repo.submission.id,
            file_name="old-0.csv",
            bucket_name="attachments",
            object_path=f"{repo.submission.id}/old-0.csv",
            mime_type="text/csv",
            file_extension=".csv",
            file_size_bytes=128,
            uploaded_by_user_id=repo.owner_user.id,
            uploaded_at=now,
            is_active=True,
        )
    )

    with pytest.raises(AppError) as exc:
        await service.upload_attachment(
            _auth_payload(repo.owner_user),
            repo.submission.id,
            _upload(),
        )

    assert exc.value.code.value == "ACTIVE_ATTACHMENT_ALREADY_EXISTS"
    assert exc.value.status_code == 409


async def test_upload_attachment_allows_admin_on_foreign_submission() -> None:
    repo = FakeAttachmentRepository()
    storage = FakeAttachmentStorage()
    service = AttachmentService(repository=repo, storage=storage, settings=_settings())

    uploaded = await service.upload_attachment(
        _auth_payload(repo.admin_user),
        repo.submission.id,
        _upload(filename="admin.csv"),
    )

    assert uploaded.file_name == "admin.csv"


async def test_upload_attachment_rejects_non_owner_non_admin() -> None:
    repo = FakeAttachmentRepository()
    storage = FakeAttachmentStorage()
    service = AttachmentService(repository=repo, storage=storage, settings=_settings())

    with pytest.raises(AppError) as exc:
        await service.upload_attachment(
            _auth_payload(repo.other_user),
            repo.submission.id,
            _upload(),
        )

    assert exc.value.code.value == "NOT_OWNER"
    assert exc.value.status_code == 403


async def test_list_attachments_returns_active_only() -> None:
    repo = FakeAttachmentRepository()
    storage = FakeAttachmentStorage()
    service = AttachmentService(repository=repo, storage=storage, settings=_settings())
    now = datetime.now(UTC)
    active = SubmissionAttachment(
        id=uuid.uuid4(),
        submission_id=repo.submission.id,
        file_name="active.csv",
        bucket_name="attachments",
        object_path=f"{repo.submission.id}/active.csv",
        mime_type="text/csv",
        file_extension=".csv",
        file_size_bytes=128,
        uploaded_by_user_id=repo.owner_user.id,
        uploaded_at=now,
        is_active=True,
    )
    inactive = SubmissionAttachment(
        id=uuid.uuid4(),
        submission_id=repo.submission.id,
        file_name="inactive.csv",
        bucket_name="attachments",
        object_path=f"{repo.submission.id}/inactive.csv",
        mime_type="text/csv",
        file_extension=".csv",
        file_size_bytes=128,
        uploaded_by_user_id=repo.owner_user.id,
        uploaded_at=now,
        is_active=False,
    )
    repo.attachments.extend([active, inactive])

    listed = await service.list_attachments(
        _auth_payload(repo.owner_user),
        repo.submission.id,
    )

    assert len(listed) == 1
    assert listed[0].id == active.id


async def test_create_download_url_returns_signed_link() -> None:
    repo = FakeAttachmentRepository()
    storage = FakeAttachmentStorage()
    service = AttachmentService(repository=repo, storage=storage, settings=_settings())
    now = datetime.now(UTC)
    attachment = SubmissionAttachment(
        id=uuid.uuid4(),
        submission_id=repo.submission.id,
        file_name="active.csv",
        bucket_name="attachments",
        object_path=f"{repo.submission.id}/active.csv",
        mime_type="text/csv",
        file_extension=".csv",
        file_size_bytes=128,
        uploaded_by_user_id=repo.owner_user.id,
        uploaded_at=now,
        is_active=True,
    )
    repo.attachments.append(attachment)

    result = await service.create_download_url(_auth_payload(repo.owner_user), attachment.id)

    assert result.url.startswith("https://storage.example.com/attachments/")
    assert result.expires_in_seconds == 3600


async def test_delete_attachment_soft_deletes_and_audits() -> None:
    repo = FakeAttachmentRepository()
    storage = FakeAttachmentStorage()
    service = AttachmentService(repository=repo, storage=storage, settings=_settings())
    now = datetime.now(UTC)
    attachment = SubmissionAttachment(
        id=uuid.uuid4(),
        submission_id=repo.submission.id,
        file_name="active.csv",
        bucket_name="attachments",
        object_path=f"{repo.submission.id}/active.csv",
        mime_type="text/csv",
        file_extension=".csv",
        file_size_bytes=128,
        uploaded_by_user_id=repo.owner_user.id,
        uploaded_at=now,
        is_active=True,
    )
    repo.attachments.append(attachment)

    await service.delete_attachment(_auth_payload(repo.owner_user), attachment.id)

    assert attachment.is_active is False
    assert repo.transaction_entries == 1
    assert len(repo.audit_logs) == 1
    assert repo.audit_logs[0].action_type == AuditActionType.FILE_REMOVED


async def test_attachment_actions_require_approved_account() -> None:
    repo = FakeAttachmentRepository()
    storage = FakeAttachmentStorage()
    service = AttachmentService(repository=repo, storage=storage, settings=_settings())

    with pytest.raises(AppError) as exc:
        await service.list_attachments(_auth_payload(repo.pending_user), repo.submission.id)

    assert exc.value.code.value == "ACCOUNT_NOT_APPROVED"
    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# RED tests — upload: use ACTIVE_ATTACHMENT_ALREADY_EXISTS code
# ---------------------------------------------------------------------------


async def test_upload_attachment_rejects_second_active_with_correct_error_code() -> None:
    repo = FakeAttachmentRepository()
    storage = FakeAttachmentStorage()
    service = AttachmentService(repository=repo, storage=storage, settings=_settings())
    existing = SubmissionAttachment(
        id=uuid.uuid4(),
        submission_id=repo.submission.id,
        file_name="existing.csv",
        bucket_name="attachments",
        object_path=f"{repo.submission.id}/existing.csv",
        mime_type="text/csv",
        file_extension=".csv",
        file_size_bytes=128,
        uploaded_by_user_id=repo.owner_user.id,
        uploaded_at=datetime.now(UTC),
        is_active=True,
    )
    repo.attachments.append(existing)

    with pytest.raises(AppError) as exc:
        await service.upload_attachment(
            _auth_payload(repo.owner_user),
            repo.submission.id,
            _upload(),
        )

    assert exc.value.code.value == "ACTIVE_ATTACHMENT_ALREADY_EXISTS"
    assert exc.value.status_code == 409


# ---------------------------------------------------------------------------
# RED tests — delete_attachment: parent workorder cascade
# ---------------------------------------------------------------------------


async def _make_completed_submission_with_attachment(
    repo: FakeAttachmentRepository,
) -> SubmissionAttachment:
    """Set repo.submission to COMPLETED and add one active attachment."""
    now = datetime.now(UTC)
    repo.submission.status = SubmissionStatus.COMPLETED
    attachment = SubmissionAttachment(
        id=uuid.uuid4(),
        submission_id=repo.submission.id,
        file_name="report.csv",
        bucket_name="attachments",
        object_path=f"{repo.submission.id}/report.csv",
        mime_type="text/csv",
        file_extension=".csv",
        file_size_bytes=128,
        uploaded_by_user_id=repo.owner_user.id,
        uploaded_at=now,
        is_active=True,
    )
    repo.attachments.append(attachment)
    return attachment


async def test_delete_last_attachment_reverts_completed_workorder_to_active() -> None:
    repo = FakeAttachmentRepository()
    storage = FakeAttachmentStorage()
    service = AttachmentService(repository=repo, storage=storage, settings=_settings())

    wo = _workorder(repo.owner_user.id, status=WorkorderStatus.COMPLETED)
    repo.submission.workorder_id = wo.id
    repo.workorders[wo.id] = wo
    attachment = await _make_completed_submission_with_attachment(repo)

    await service.delete_attachment(_auth_payload(repo.owner_user), attachment.id)

    assert attachment.is_active is False
    assert wo.status == WorkorderStatus.ACTIVE


async def test_delete_attachment_does_not_revert_workorder_if_still_has_active_file() -> None:
    """If there is a second active file still remaining, parent stays COMPLETED."""
    repo = FakeAttachmentRepository()
    storage = FakeAttachmentStorage()
    service = AttachmentService(repository=repo, storage=storage, settings=_settings())

    wo = _workorder(repo.owner_user.id, status=WorkorderStatus.COMPLETED)
    repo.submission.workorder_id = wo.id
    repo.workorders[wo.id] = wo
    repo.submission.status = SubmissionStatus.COMPLETED

    now = datetime.now(UTC)
    att1 = SubmissionAttachment(
        id=uuid.uuid4(), submission_id=repo.submission.id, file_name="a.csv",
        bucket_name="attachments", object_path=f"{repo.submission.id}/a.csv",
        mime_type="text/csv", file_extension=".csv", file_size_bytes=10,
        uploaded_by_user_id=repo.owner_user.id, uploaded_at=now, is_active=True,
    )
    att2 = SubmissionAttachment(
        id=uuid.uuid4(), submission_id=repo.submission.id, file_name="b.csv",
        bucket_name="attachments", object_path=f"{repo.submission.id}/b.csv",
        mime_type="text/csv", file_extension=".csv", file_size_bytes=10,
        uploaded_by_user_id=repo.owner_user.id, uploaded_at=now, is_active=True,
    )
    repo.attachments.extend([att1, att2])

    await service.delete_attachment(_auth_payload(repo.owner_user), att1.id)

    assert att1.is_active is False
    assert wo.status == WorkorderStatus.COMPLETED  # still has att2


async def test_delete_attachment_on_non_completed_submission_no_workorder_change() -> None:
    """If submission is IN_PROGRESS/CHECKED_OUT, parent workorder status left untouched."""
    repo = FakeAttachmentRepository()
    storage = FakeAttachmentStorage()
    service = AttachmentService(repository=repo, storage=storage, settings=_settings())

    wo = _workorder(repo.owner_user.id, status=WorkorderStatus.ACTIVE)
    repo.submission.workorder_id = wo.id
    repo.workorders[wo.id] = wo
    repo.submission.status = SubmissionStatus.CHECKED_OUT  # not completed

    now = datetime.now(UTC)
    att = SubmissionAttachment(
        id=uuid.uuid4(), submission_id=repo.submission.id, file_name="report.csv",
        bucket_name="attachments", object_path=f"{repo.submission.id}/report.csv",
        mime_type="text/csv", file_extension=".csv", file_size_bytes=10,
        uploaded_by_user_id=repo.owner_user.id, uploaded_at=now, is_active=True,
    )
    repo.attachments.append(att)

    await service.delete_attachment(_auth_payload(repo.owner_user), att.id)

    assert att.is_active is False
    assert wo.status == WorkorderStatus.ACTIVE  # unchanged


# ---------------------------------------------------------------------------
# Wave 2 RED tests — item 51: admin attachment history endpoint
# ---------------------------------------------------------------------------


async def test_get_attachment_history_requires_admin() -> None:
    """Non-admin users cannot access the full attachment history."""
    repo = FakeAttachmentRepository()
    service = AttachmentService(
        repository=repo, storage=FakeAttachmentStorage(), settings=_settings()
    )

    with pytest.raises(AppError) as exc:
        await service.get_attachment_history(
            _auth_payload(repo.owner_user), repo.submission.id
        )

    assert exc.value.code.value == "ADMIN_ONLY"
    assert exc.value.status_code == 403


async def test_get_attachment_history_returns_not_found_for_missing_submission() -> None:
    repo = FakeAttachmentRepository()
    service = AttachmentService(
        repository=repo, storage=FakeAttachmentStorage(), settings=_settings()
    )

    with pytest.raises(AppError) as exc:
        await service.get_attachment_history(_auth_payload(repo.admin_user), uuid.uuid4())

    assert exc.value.code.value == "NOT_FOUND"
    assert exc.value.status_code == 404


async def test_get_attachment_history_returns_all_including_inactive() -> None:
    repo = FakeAttachmentRepository()
    service = AttachmentService(
        repository=repo, storage=FakeAttachmentStorage(), settings=_settings()
    )
    now = datetime.now(UTC)
    active_att = SubmissionAttachment(
        id=uuid.uuid4(), submission_id=repo.submission.id, file_name="active.csv",
        bucket_name="attachments", object_path=f"{repo.submission.id}/active.csv",
        mime_type="text/csv", file_extension=".csv", file_size_bytes=100,
        uploaded_by_user_id=repo.owner_user.id, uploaded_at=now, is_active=True,
    )
    inactive_att = SubmissionAttachment(
        id=uuid.uuid4(), submission_id=repo.submission.id, file_name="old.csv",
        bucket_name="attachments", object_path=f"{repo.submission.id}/old.csv",
        mime_type="text/csv", file_extension=".csv", file_size_bytes=50,
        uploaded_by_user_id=repo.owner_user.id, uploaded_at=now, is_active=False,
    )
    repo.attachments.extend([active_att, inactive_att])

    views = await service.get_attachment_history(_auth_payload(repo.admin_user), repo.submission.id)

    assert len(views) == 2
    is_active_values = {v.is_active for v in views}
    assert True in is_active_values
    assert False in is_active_values


async def test_get_attachment_history_returns_empty_list_when_no_attachments() -> None:
    repo = FakeAttachmentRepository()
    service = AttachmentService(
        repository=repo, storage=FakeAttachmentStorage(), settings=_settings()
    )

    views = await service.get_attachment_history(_auth_payload(repo.admin_user), repo.submission.id)

    assert views == []

