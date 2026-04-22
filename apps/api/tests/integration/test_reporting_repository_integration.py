import csv
import io
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AccountStatus, RequestedRole, SubmissionStatus
from app.repositories.reporting_repository import ReportingRepository
from app.services.reporting_service import ReportingService
from tests.integration.helpers import (
    auth_payload,
    build_attachment,
    build_submission,
    build_user,
    build_workorder,
)

pytestmark = pytest.mark.integration


async def test_no_submission_yet_uses_approved_tester_set(
    integration_session: AsyncSession,
) -> None:
    repo = ReportingRepository(integration_session)
    selected_date = date(2026, 4, 14)
    admin = build_user(
        email="admin@example.com",
        requested_role=RequestedRole.ADMIN,
        approved_role=RequestedRole.ADMIN,
        account_status=AccountStatus.APPROVED,
    )
    tester_with_submission = build_user(
        email="submitted@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    tester_without_submission = build_user(
        email="nosubmit@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    pending_tester = build_user(
        email="pending@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=None,
        account_status=AccountStatus.PENDING_APPROVAL,
    )
    workorder = build_workorder(owner=tester_with_submission, workorder_code="WO-A")
    submission = build_submission(
        owner=tester_with_submission,
        workorder=workorder,
        work_date=selected_date,
        status=SubmissionStatus.IN_PROGRESS,
    )
    integration_session.add_all(
        [
            admin,
            tester_with_submission,
            tester_without_submission,
            pending_tester,
            workorder,
            submission,
        ]
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
    admin = build_user(
        email="admin2@example.com",
        requested_role=RequestedRole.ADMIN,
        approved_role=RequestedRole.ADMIN,
        account_status=AccountStatus.APPROVED,
    )
    owner = build_user(
        email="owner@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    pending_workorder = build_workorder(owner=owner, workorder_code="WO-PENDING")
    with_file_workorder = build_workorder(owner=owner, workorder_code="WO-WITHFILE")
    pending_submission = build_submission(
        owner=owner,
        workorder=pending_workorder,
        work_date=selected_date,
        status=SubmissionStatus.CHECKED_OUT,
        ticket_number="TKT-PENDING",
    )
    with_file_submission = build_submission(
        owner=owner,
        workorder=with_file_workorder,
        work_date=selected_date,
        status=SubmissionStatus.CHECKED_OUT,
        ticket_number="TKT-WITHFILE",
    )
    attachment = build_attachment(submission=with_file_submission, uploader=owner, file_name="data.csv")
    integration_session.add_all(
        [
            admin,
            owner,
            pending_workorder,
            with_file_workorder,
            pending_submission,
            with_file_submission,
            attachment,
        ]
    )
    await integration_session.commit()

    csv_text = await service.export_submissions_csv(
        auth_payload(admin),
        work_date=selected_date,
        file_submission_pending=True,
    )
    rows = list(csv.DictReader(io.StringIO(csv_text)))

    assert len(rows) == 1
    assert rows[0]["ticket_number"] == "TKT-PENDING"
    assert rows[0]["status"] == "CHECKED_OUT"
    assert rows[0]["file_submission_pending"] == "true"
    assert rows[0]["workorder_code"] == "WO-PENDING"


async def test_reporting_service_export_csv_supports_no_filters_and_status_filter(
    integration_session: AsyncSession,
) -> None:
    repo = ReportingRepository(integration_session)
    service = ReportingService(repository=repo)
    selected_date = date(2026, 4, 14)
    admin = build_user(
        email="admin3@example.com",
        requested_role=RequestedRole.ADMIN,
        approved_role=RequestedRole.ADMIN,
        account_status=AccountStatus.APPROVED,
    )
    owner = build_user(
        email="owner3@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    completed_workorder = build_workorder(owner=owner, workorder_code="WO-COMP")
    in_progress_workorder = build_workorder(owner=owner, workorder_code="WO-IP")
    completed_submission = build_submission(
        owner=owner,
        workorder=completed_workorder,
        work_date=selected_date,
        status=SubmissionStatus.COMPLETED,
        ticket_number="TKT-COMP",
    )
    in_progress_submission = build_submission(
        owner=owner,
        workorder=in_progress_workorder,
        work_date=selected_date,
        status=SubmissionStatus.IN_PROGRESS,
        ticket_number="TKT-IP",
    )

    integration_session.add_all(
        [
            admin,
            owner,
            completed_workorder,
            in_progress_workorder,
            completed_submission,
            in_progress_submission,
        ]
    )
    await integration_session.commit()

    unfiltered_csv = await service.export_submissions_csv(auth_payload(admin))
    unfiltered_rows = list(csv.DictReader(io.StringIO(unfiltered_csv)))
    completed_csv = await service.export_submissions_csv(
        auth_payload(admin),
        status=SubmissionStatus.COMPLETED,
    )
    completed_rows = list(csv.DictReader(io.StringIO(completed_csv)))

    assert len(unfiltered_rows) >= 2
    assert {row["ticket_number"] for row in unfiltered_rows} >= {"TKT-COMP", "TKT-IP"}
    assert len(completed_rows) == 1
    assert completed_rows[0]["ticket_number"] == "TKT-COMP"
    assert completed_rows[0]["status"] == "COMPLETED"

