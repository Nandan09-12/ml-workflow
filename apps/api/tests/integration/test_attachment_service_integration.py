from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.enums import (
    AccountStatus,
    AuditActionType,
    RequestedRole,
    SubmissionStatus,
    WorkorderStatus,
)
from app.core.errors import AppError
from app.models.submission_attachment import SubmissionAttachment
from app.models.submission_audit_log import SubmissionAuditLog
from app.models.workorder import Workorder
from app.repositories.attachment_repository import AttachmentRepository
from app.services.attachment_service import AttachmentService, AttachmentUpload
from tests.integration.helpers import (
    auth_payload,
    build_attachment,
    build_submission,
    build_user,
    build_workorder,
)

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
        database_url="postgresql+asyncpg://postgres:postgres@localhost:5433/ml_workflow_integration",
        supabase_url="https://example.supabase.co",
        supabase_storage_bucket="attachments",
    )


def _upload(
    *,
    filename: str = "report.csv",
    content_type: str = "text/csv",
    size_bytes: int = 128,
) -> AttachmentUpload:
    return AttachmentUpload(file_name=filename, content_type=content_type, content=b"x" * size_bytes)


async def test_attachment_upload_list_download_delete_full_flow(
    integration_session: AsyncSession,
) -> None:
    owner = build_user(
        email="owner-attachment@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    workorder = build_workorder(owner=owner, workorder_code="WO-ATTACH")
    submission = build_submission(
        owner=owner,
        workorder=workorder,
        work_date=date(2026, 4, 14),
        status=SubmissionStatus.CHECKED_OUT,
    )
    integration_session.add_all([owner, workorder, submission])
    await integration_session.commit()

    storage = FakeAttachmentStorage()
    service = AttachmentService(
        repository=AttachmentRepository(integration_session),
        storage=storage,
        settings=_settings(),
    )

    uploaded = await service.upload_attachment(auth_payload(owner), submission.id, _upload())
    listed_before = await service.list_attachments(auth_payload(owner), submission.id)
    download = await service.create_download_url(auth_payload(owner), uploaded.id)
    await service.delete_attachment(auth_payload(owner), uploaded.id)
    listed_after = await service.list_attachments(auth_payload(owner), submission.id)

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
    assert [entry.action_type for entry in logs] == [
        AuditActionType.FILE_UPLOADED,
        AuditActionType.FILE_REMOVED,
    ]


async def test_attachment_upload_rejects_when_active_attachment_exists(
    integration_session: AsyncSession,
) -> None:
    owner = build_user(
        email="owner-limit@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    workorder = build_workorder(owner=owner, workorder_code="WO-LIMIT")
    submission = build_submission(owner=owner, workorder=workorder, work_date=date(2026, 4, 14))
    existing = build_attachment(submission=submission, uploader=owner)
    integration_session.add_all([owner, workorder, submission, existing])
    await integration_session.commit()

    storage = FakeAttachmentStorage()
    service = AttachmentService(
        repository=AttachmentRepository(integration_session),
        storage=storage,
        settings=_settings(),
    )
    with pytest.raises(AppError) as exc:
        await service.upload_attachment(auth_payload(owner), submission.id, _upload())

    assert exc.value.code.value == "ACTIVE_ATTACHMENT_ALREADY_EXISTS"
    assert exc.value.status_code == 409
    assert storage.uploads == []


async def test_attachment_upload_rejects_non_owner_non_admin(
    integration_session: AsyncSession,
) -> None:
    owner = build_user(
        email="owner-access@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    other = build_user(
        email="other-access@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    workorder = build_workorder(owner=owner, workorder_code="WO-ACCESS")
    submission = build_submission(owner=owner, workorder=workorder, work_date=date(2026, 4, 14))
    integration_session.add_all([owner, other, workorder, submission])
    await integration_session.commit()

    service = AttachmentService(
        repository=AttachmentRepository(integration_session),
        storage=FakeAttachmentStorage(),
        settings=_settings(),
    )

    with pytest.raises(AppError) as exc:
        await service.upload_attachment(auth_payload(other), submission.id, _upload())

    assert exc.value.code.value == "NOT_OWNER"
    assert exc.value.status_code == 403


async def test_attachment_upload_allows_admin_on_foreign_submission(
    integration_session: AsyncSession,
) -> None:
    owner = build_user(
        email="owner-admin-upload@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    admin = build_user(
        email="admin-upload@example.com",
        requested_role=RequestedRole.ADMIN,
        approved_role=RequestedRole.ADMIN,
        account_status=AccountStatus.APPROVED,
    )
    workorder = build_workorder(owner=owner, workorder_code="WO-ADMIN-UP")
    submission = build_submission(owner=owner, workorder=workorder, work_date=date(2026, 4, 14))
    integration_session.add_all([owner, admin, workorder, submission])
    await integration_session.commit()

    service = AttachmentService(
        repository=AttachmentRepository(integration_session),
        storage=FakeAttachmentStorage(),
        settings=_settings(),
    )
    uploaded = await service.upload_attachment(
        auth_payload(admin),
        submission.id,
        _upload(filename="admin.csv"),
    )

    assert uploaded.file_name == "admin.csv"
    assert uploaded.uploaded_by_user_id == admin.id


async def test_attachment_upload_rejects_disallowed_extension(
    integration_session: AsyncSession,
) -> None:
    owner = build_user(
        email="owner-ext@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    workorder = build_workorder(owner=owner, workorder_code="WO-EXT")
    submission = build_submission(owner=owner, workorder=workorder, work_date=date(2026, 4, 14))
    integration_session.add_all([owner, workorder, submission])
    await integration_session.commit()

    service = AttachmentService(
        repository=AttachmentRepository(integration_session),
        storage=FakeAttachmentStorage(),
        settings=_settings(),
    )
    with pytest.raises(AppError) as exc:
        await service.upload_attachment(
            auth_payload(owner),
            submission.id,
            _upload(filename="legacy.xls", content_type="application/vnd.ms-excel"),
        )

    assert exc.value.code.value == "UNSUPPORTED_FILE_TYPE"
    assert exc.value.status_code == 400


async def test_delete_last_attachment_reverts_completed_workorder_to_active(
    integration_session: AsyncSession,
) -> None:
    owner = build_user(
        email="owner-delete@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    workorder = build_workorder(
        owner=owner,
        workorder_code="WO-DELETE",
        status=WorkorderStatus.COMPLETED,
    )
    submission = build_submission(
        owner=owner,
        workorder=workorder,
        work_date=date(2026, 4, 14),
        status=SubmissionStatus.COMPLETED,
        skipped_grids=1,
        completed_grids=9,
    )
    attachment = build_attachment(submission=submission, uploader=owner)
    integration_session.add_all([owner, workorder, submission, attachment])
    await integration_session.commit()

    service = AttachmentService(
        repository=AttachmentRepository(integration_session),
        storage=FakeAttachmentStorage(),
        settings=_settings(),
    )
    await service.delete_attachment(auth_payload(owner), attachment.id)

    saved_workorder = (
        await integration_session.execute(select(Workorder).where(Workorder.id == workorder.id))
    ).scalar_one()
    assert saved_workorder.status == WorkorderStatus.ACTIVE


async def test_delete_last_attachment_keeps_active_parent_active(
    integration_session: AsyncSession,
) -> None:
    owner = build_user(
        email="owner-delete-active@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    workorder = build_workorder(
        owner=owner,
        workorder_code="WO-DELETE-ACTIVE",
        status=WorkorderStatus.ACTIVE,
    )
    submission = build_submission(
        owner=owner,
        workorder=workorder,
        work_date=date(2026, 4, 14),
        status=SubmissionStatus.COMPLETED,
        skipped_grids=1,
        completed_grids=9,
    )
    attachment = build_attachment(submission=submission, uploader=owner)
    integration_session.add_all([owner, workorder, submission, attachment])
    await integration_session.commit()

    service = AttachmentService(
        repository=AttachmentRepository(integration_session),
        storage=FakeAttachmentStorage(),
        settings=_settings(),
    )
    await service.delete_attachment(auth_payload(owner), attachment.id)

    saved_workorder = (
        await integration_session.execute(
            select(Workorder).where(Workorder.id == workorder.id)
        )
    ).scalar_one()
    assert saved_workorder.status == WorkorderStatus.ACTIVE
    assert saved_workorder.completed_at is None
