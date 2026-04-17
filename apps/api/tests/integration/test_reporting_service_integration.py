from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    AccountStatus,
    RequestedRole,
    SubmissionStatus,
    WorkorderStatus,
)
from app.repositories.reporting_repository import ReportingRepository
from app.services.reporting_service import ReportingService
from tests.integration.helpers import (
    auth_payload,
    build_submission,
    build_user,
    build_workorder,
)

pytestmark = pytest.mark.integration


async def test_reporting_dashboard_summary_counts_key_metrics(
    integration_session: AsyncSession,
) -> None:
    selected_date = date(2026, 4, 14)
    admin = build_user(
        email="admin-summary@example.com",
        full_name="Admin",
        requested_role=RequestedRole.ADMIN,
        approved_role=RequestedRole.ADMIN,
        account_status=AccountStatus.APPROVED,
    )
    tester_with_ongoing = build_user(
        email="ongoing@example.com",
        full_name="Ongoing Tester",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    tester_with_completed = build_user(
        email="complete@example.com",
        full_name="Completed Tester",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    tester_without_submission = build_user(
        email="nosubmit-summary@example.com",
        full_name="No Submit Tester",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    pending_tester = build_user(
        email="pending-summary@example.com",
        full_name="Pending Tester",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=None,
        account_status=AccountStatus.PENDING_APPROVAL,
    )
    ongoing_workorder = build_workorder(owner=tester_with_ongoing, workorder_code="WO-ONGOING")
    completed_workorder = build_workorder(
        owner=tester_with_completed,
        workorder_code="WO-COMPLETE",
        status=WorkorderStatus.COMPLETED,
    )
    ongoing_submission = build_submission(
        owner=tester_with_ongoing,
        workorder=ongoing_workorder,
        work_date=selected_date,
        status=SubmissionStatus.IN_PROGRESS,
    )
    completed_submission = build_submission(
        owner=tester_with_completed,
        workorder=completed_workorder,
        work_date=selected_date,
        status=SubmissionStatus.COMPLETED,
        skipped_grids=1,
        completed_grids=9,
    )
    integration_session.add_all(
        [
            admin,
            tester_with_ongoing,
            tester_with_completed,
            tester_without_submission,
            pending_tester,
            ongoing_workorder,
            completed_workorder,
            ongoing_submission,
            completed_submission,
        ]
    )
    await integration_session.commit()

    service = ReportingService(repository=ReportingRepository(integration_session))
    summary = await service.get_dashboard_summary(auth_payload(admin), work_date=selected_date)

    assert summary.approved_drive_testers == 3
    assert summary.ongoing_submissions == 1
    assert summary.completed_submissions == 1
    assert summary.no_submission_yet == 1
    assert summary.active_workorders == 1
    assert summary.completed_workorders == 1
    assert summary.reference_date == selected_date


async def test_reporting_list_no_submission_yet_supports_pagination_and_order(
    integration_session: AsyncSession,
) -> None:
    selected_date = date(2026, 4, 14)
    admin = build_user(
        email="admin-nosubmit@example.com",
        full_name="Admin",
        requested_role=RequestedRole.ADMIN,
        approved_role=RequestedRole.ADMIN,
        account_status=AccountStatus.APPROVED,
    )
    tester_a = build_user(
        email="a@example.com",
        full_name="Alice",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    tester_b = build_user(
        email="b@example.com",
        full_name="Bob",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    tester_c = build_user(
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
        auth_payload(admin),
        work_date=selected_date,
        page=1,
        page_size=2,
    )

    assert total == 3
    assert [item.full_name for item in page_items] == ["Alice", "Bob"]
