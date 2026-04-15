import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AccountStatus, RequestedRole, Shift, SubmissionStatus, Zone
from app.models.app_user import AppUser
from app.models.submission import Submission
from app.models.submission_attachment import SubmissionAttachment
from app.repositories.reporting_repository import ReportingRepository
from app.services.reporting_service import ReportingService

pytestmark = pytest.mark.integration


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


def _build_submission(
    *,
    owner: AppUser,
    work_date: date,
    status: SubmissionStatus,
    cluster_suffix: str,
) -> Submission:
    now = datetime.now(UTC)
    return Submission(
        id=uuid.uuid4(),
        client_generated_id=uuid.uuid4(),
        owner_user_id=owner.id,
        submitter_name_snapshot=owner.full_name,
        submitter_email_snapshot=owner.email,
        zone=Zone.NORTHEAST,
        work_date=work_date,
        shift=Shift.AM,
        team_number="11",
        ticket_number=f"TKT-{cluster_suffix}",
        cluster_name=f"Cluster {cluster_suffix}",
        cluster_name_normalized=f"CLUSTER {cluster_suffix}",
        number_of_grids=10,
        skipped_grids=1,
        force_tested_grids=0,
        pending_grids=0 if status == SubmissionStatus.COMPLETED else 2,
        completed_grids=9 if status == SubmissionStatus.COMPLETED else 7,
        status=status,
        created_at=now,
        created_by_user_id=owner.id,
        updated_at=now,
        updated_by_user_id=owner.id,
        completed_at=now if status == SubmissionStatus.COMPLETED else None,
        completed_by_user_id=owner.id if status == SubmissionStatus.COMPLETED else None,
        reopened_at=None,
        reopened_by_user_id=None,
        version_number=1,
    )


def _auth_payload(user: AppUser) -> dict[str, str]:
    return {"sub": str(user.auth_user_id), "email": user.email}


async def test_no_submission_yet_uses_approved_tester_set(
    integration_session: AsyncSession,
) -> None:
    repo = ReportingRepository(integration_session)
    selected_date = date(2026, 4, 14)
    admin = _build_user(
        email="admin@example.com",
        requested_role=RequestedRole.ADMIN,
        approved_role=RequestedRole.ADMIN,
        account_status=AccountStatus.APPROVED,
    )
    tester_with_submission = _build_user(
        email="submitted@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    tester_without_submission = _build_user(
        email="nosubmit@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    pending_tester = _build_user(
        email="pending@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=None,
        account_status=AccountStatus.PENDING_APPROVAL,
    )
    integration_session.add_all([admin, tester_with_submission, tester_without_submission, pending_tester])
    await integration_session.flush()

    integration_session.add(
        _build_submission(
            owner=tester_with_submission,
            work_date=selected_date,
            status=SubmissionStatus.ONGOING,
            cluster_suffix="A",
        )
    )
    await integration_session.commit()

    users, total = await repo.list_approved_drive_testers_without_submission(
        work_date=selected_date,
        offset=0,
        limit=20,
    )

    assert total == 1
    assert len(users) == 1
    assert users[0].email == "nosubmit@example.com"


async def test_reporting_service_export_csv_respects_file_submission_pending_filter(
    integration_session: AsyncSession,
) -> None:
    repo = ReportingRepository(integration_session)
    service = ReportingService(repository=repo)
    selected_date = date(2026, 4, 14)
    admin = _build_user(
        email="admin2@example.com",
        requested_role=RequestedRole.ADMIN,
        approved_role=RequestedRole.ADMIN,
        account_status=AccountStatus.APPROVED,
    )
    owner = _build_user(
        email="owner@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    integration_session.add_all([admin, owner])
    await integration_session.flush()

    pending_submission = _build_submission(
        owner=owner,
        work_date=selected_date,
        status=SubmissionStatus.COMPLETED,
        cluster_suffix="PENDING",
    )
    with_file_submission = _build_submission(
        owner=owner,
        work_date=selected_date,
        status=SubmissionStatus.COMPLETED,
        cluster_suffix="WITHFILE",
    )
    integration_session.add_all([pending_submission, with_file_submission])
    await integration_session.flush()

    integration_session.add(
        SubmissionAttachment(
            id=uuid.uuid4(),
            submission_id=with_file_submission.id,
            file_name="data.csv",
            bucket_name="attachments",
            object_path=f"{with_file_submission.id}/data.csv",
            mime_type="text/csv",
            file_extension=".csv",
            file_size_bytes=512,
            uploaded_by_user_id=owner.id,
            uploaded_at=datetime.now(UTC),
            is_active=True,
        )
    )
    await integration_session.commit()

    csv_text = await service.export_submissions_csv(
        _auth_payload(admin),
        work_date=selected_date,
        file_submission_pending=True,
    )

    assert "CLUSTER PENDING" in csv_text
    assert "CLUSTER WITHFILE" not in csv_text
    assert ",true" in csv_text

