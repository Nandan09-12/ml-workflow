import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.enums import (
    AccountStatus,
    AuditActionType,
    RequestedRole,
    Shift,
    SubmissionStatus,
    Zone,
)
from app.core.errors import AppError
from app.models.app_user import AppUser
from app.models.submission import Submission
from app.models.submission_attachment import SubmissionAttachment
from app.models.submission_audit_log import SubmissionAuditLog
from app.repositories.attachment_repository import AttachmentRepository
from app.services.attachment_service import AttachmentService, AttachmentUpload

pytestmark = pytest.mark.integration


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
        return f"https://storage.example.com/{bucket_name}/{object_path}?exp={expires_in_seconds}"


def _settings() -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://postgres:postgres@localhost/postgres",
        supabase_url="https://example.supabase.co",
        supabase_storage_bucket="attachments",
    )


def _build_user(
    *,
    email: str,
    requested_role: RequestedRole,
    approved_role: RequestedRole | None,
    account_status: AccountStatus,
) -> AppUser:
    now = datetime.now(UTC)
    return AppUser(
        id=uuid.uuid4(),
        auth_user_id=uuid.uuid4(),
        full_name=email.split("@")[0],
        email=email,
        requested_role=requested_role,
        approved_role=approved_role,
        account_status=account_status,
        approved_at=now if account_status == AccountStatus.APPROVED else None,
        approved_by_user_id=None,
        created_at=now,
        updated_at=now,
    )


def _build_submission(*, owner: AppUser) -> Submission:
    now = datetime.now(UTC)
    return Submission(
        id=uuid.uuid4(),
        client_generated_id=uuid.uuid4(),
        owner_user_id=owner.id,
        submitter_name_snapshot=owner.full_name,
        submitter_email_snapshot=owner.email,
        zone=Zone.NORTHEAST,
        work_date=date(2026, 4, 14),
        shift=Shift.AM,
        team_number="11",
        ticket_number="TKT-1",
        cluster_name="Attachment Cluster",
        cluster_name_normalized="ATTACHMENT CLUSTER",
        number_of_grids=10,
        skipped_grids=1,
        force_tested_grids=0,
        pending_grids=2,
        completed_grids=7,
        status=SubmissionStatus.IN_PROGRESS,
        created_at=now,
        created_by_user_id=owner.id,
        updated_at=now,
        updated_by_user_id=owner.id,
        version_number=1,
    )


def _auth_payload(user: AppUser) -> dict[str, str]:
    return {"sub": str(user.auth_user_id), "email": user.email}


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


async def test_attachment_upload_list_download_delete_full_flow(
    integration_session: AsyncSession,
) -> None:
    owner = _build_user(
        email="owner-attachment@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    submission = _build_submission(owner=owner)
    integration_session.add_all([owner, submission])
    await integration_session.commit()

    storage = FakeAttachmentStorage()
    service = AttachmentService(
        repository=AttachmentRepository(integration_session),
        storage=storage,
        settings=_settings(),
    )

    uploaded = await service.upload_attachment(_auth_payload(owner), submission.id, _upload())
    listed_before = await service.list_attachments(_auth_payload(owner), submission.id)
    download = await service.create_download_url(_auth_payload(owner), uploaded.id)
    await service.delete_attachment(_auth_payload(owner), uploaded.id)
    listed_after = await service.list_attachments(_auth_payload(owner), submission.id)

    assert uploaded.file_extension == ".csv"
    assert uploaded.mime_type == "text/csv"
    assert len(listed_before) == 1
    assert listed_before[0].id == uploaded.id
    assert "https://storage.example.com/attachments/" in download.url
    assert download.expires_in_seconds == 3600
    assert listed_after == []
    assert len(storage.uploads) == 1

    saved = (
        await integration_session.execute(
            select(SubmissionAttachment).where(SubmissionAttachment.id == uploaded.id)
        )
    ).scalar_one()
    assert saved.is_active is False

    logs = (
        await integration_session.execute(
            select(SubmissionAuditLog)
            .where(SubmissionAuditLog.submission_id == submission.id)
            .order_by(SubmissionAuditLog.created_at.asc())
        )
    ).scalars().all()
    actions = [entry.action_type for entry in logs]
    assert AuditActionType.FILE_UPLOADED in actions
    assert AuditActionType.FILE_REMOVED in actions


async def test_attachment_upload_rejects_when_limit_is_reached(
    integration_session: AsyncSession,
) -> None:
    owner = _build_user(
        email="owner-limit@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    submission = _build_submission(owner=owner)
    integration_session.add_all([owner, submission])
    await integration_session.flush()
    now = datetime.now(UTC)
    for index in range(5):
        integration_session.add(
            SubmissionAttachment(
                id=uuid.uuid4(),
                submission_id=submission.id,
                file_name=f"existing-{index}.csv",
                bucket_name="attachments",
                object_path=f"{submission.id}/existing-{index}.csv",
                mime_type="text/csv",
                file_extension=".csv",
                file_size_bytes=120,
                uploaded_by_user_id=owner.id,
                uploaded_at=now,
                is_active=True,
            )
        )
    await integration_session.commit()

    storage = FakeAttachmentStorage()
    service = AttachmentService(
        repository=AttachmentRepository(integration_session),
        storage=storage,
        settings=_settings(),
    )
    with pytest.raises(AppError) as exc:
        await service.upload_attachment(_auth_payload(owner), submission.id, _upload())

    assert exc.value.code.value == "VALIDATION_ERROR"
    assert exc.value.status_code == 400
    assert storage.uploads == []


async def test_attachment_upload_rejects_non_owner_non_admin(
    integration_session: AsyncSession,
) -> None:
    owner = _build_user(
        email="owner-access@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    other = _build_user(
        email="other-access@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    submission = _build_submission(owner=owner)
    integration_session.add_all([owner, other, submission])
    await integration_session.commit()

    service = AttachmentService(
        repository=AttachmentRepository(integration_session),
        storage=FakeAttachmentStorage(),
        settings=_settings(),
    )

    with pytest.raises(AppError) as exc:
        await service.upload_attachment(_auth_payload(other), submission.id, _upload())

    assert exc.value.code.value == "NOT_OWNER"
    assert exc.value.status_code == 403


async def test_attachment_upload_allows_admin_on_foreign_submission(
    integration_session: AsyncSession,
) -> None:
    owner = _build_user(
        email="owner-admin-upload@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    admin = _build_user(
        email="admin-upload@example.com",
        requested_role=RequestedRole.ADMIN,
        approved_role=RequestedRole.ADMIN,
        account_status=AccountStatus.APPROVED,
    )
    submission = _build_submission(owner=owner)
    integration_session.add_all([owner, admin, submission])
    await integration_session.commit()

    service = AttachmentService(
        repository=AttachmentRepository(integration_session),
        storage=FakeAttachmentStorage(),
        settings=_settings(),
    )
    uploaded = await service.upload_attachment(
        _auth_payload(admin),
        submission.id,
        _upload(filename="admin.csv"),
    )

    assert uploaded.file_name == "admin.csv"
    assert uploaded.uploaded_by_user_id == admin.id


async def test_attachment_upload_rejects_disallowed_extension(
    integration_session: AsyncSession,
) -> None:
    owner = _build_user(
        email="owner-ext@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    submission = _build_submission(owner=owner)
    integration_session.add_all([owner, submission])
    await integration_session.commit()

    service = AttachmentService(
        repository=AttachmentRepository(integration_session),
        storage=FakeAttachmentStorage(),
        settings=_settings(),
    )
    with pytest.raises(AppError) as exc:
        await service.upload_attachment(
            _auth_payload(owner),
            submission.id,
            _upload(filename="legacy.xls", content_type="application/vnd.ms-excel"),
        )

    assert exc.value.code.value == "UNSUPPORTED_FILE_TYPE"
    assert exc.value.status_code == 400
