import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AccountStatus, RequestedRole, Shift, SubmissionStatus, Zone
from app.models.app_user import AppUser
from app.models.submission import Submission
from app.repositories.reporting_repository import ReportingRepository
from app.services.reporting_service import ReportingService

pytestmark = pytest.mark.integration


def _build_user(
    *,
    email: str,
    full_name: str,
    requested_role: RequestedRole,
    approved_role: RequestedRole | None,
    account_status: AccountStatus,
) -> AppUser:
    now = datetime.now(UTC)
    return AppUser(
        id=uuid.uuid4(),
        auth_user_id=uuid.uuid4(),
        full_name=full_name,
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
        pending_grids=2 if status == SubmissionStatus.IN_PROGRESS else 0,
        completed_grids=7 if status == SubmissionStatus.IN_PROGRESS else 9,
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


async def test_reporting_dashboard_summary_counts_key_metrics(
    integration_session: AsyncSession,
) -> None:
    selected_date = date(2026, 4, 14)
    admin = _build_user(
        email="admin-summary@example.com",
        full_name="Admin",
        requested_role=RequestedRole.ADMIN,
        approved_role=RequestedRole.ADMIN,
        account_status=AccountStatus.APPROVED,
    )
    tester_with_ongoing = _build_user(
        email="ongoing@example.com",
        full_name="Ongoing Tester",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    tester_without_submission = _build_user(
        email="nosubmit-summary@example.com",
        full_name="No Submit Tester",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    pending_tester = _build_user(
        email="pending-summary@example.com",
        full_name="Pending Tester",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=None,
        account_status=AccountStatus.PENDING_APPROVAL,
    )
    integration_session.add_all([admin, tester_with_ongoing, tester_without_submission, pending_tester])
    await integration_session.flush()
    integration_session.add(
        _build_submission(
            owner=tester_with_ongoing,
            work_date=selected_date,
            status=SubmissionStatus.IN_PROGRESS,
            cluster_suffix="ONGOING",
        )
    )
    await integration_session.commit()

    service = ReportingService(repository=ReportingRepository(integration_session))
    summary = await service.get_dashboard_summary(_auth_payload(admin), work_date=selected_date)

    assert summary.approved_drive_testers == 2
    assert summary.ongoing_submissions == 1
    assert summary.completed_submissions == 0
    assert summary.no_submission_yet == 1
    assert summary.reference_date == selected_date


async def test_reporting_list_no_submission_yet_supports_pagination_and_order(
    integration_session: AsyncSession,
) -> None:
    selected_date = date(2026, 4, 14)
    admin = _build_user(
        email="admin-nosubmit@example.com",
        full_name="Admin",
        requested_role=RequestedRole.ADMIN,
        approved_role=RequestedRole.ADMIN,
        account_status=AccountStatus.APPROVED,
    )
    tester_a = _build_user(
        email="a@example.com",
        full_name="Alice",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    tester_b = _build_user(
        email="b@example.com",
        full_name="Bob",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    tester_c = _build_user(
        email="c@example.com",
        full_name="Charlie",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    integration_session.add_all([admin, tester_a, tester_b, tester_c])
    await integration_session.commit()

    service = ReportingService(repository=ReportingRepository(integration_session))
    page_items, total = await service.list_no_submission_yet(
        _auth_payload(admin),
        work_date=selected_date,
        page=1,
        page_size=2,
    )

    assert total == 3
    assert [item.full_name for item in page_items] == ["Alice", "Bob"]
