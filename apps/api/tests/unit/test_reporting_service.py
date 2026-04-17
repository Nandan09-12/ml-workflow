import csv
import io
import uuid
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Any

import pytest

from app.core.enums import (
    AccountStatus,
    RequestedRole,
    Shift,
    SubmissionStatus,
    WorkorderStatus,
)
from app.core.errors import AppError
from app.models.app_user import AppUser
from app.services.reporting_service import ReportingService

if TYPE_CHECKING:
    pass


class FakeReportingRepository:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.admin_user = AppUser(
            id=uuid.uuid4(),
            auth_user_id=uuid.uuid4(),
            full_name="Admin User",
            email="admin@example.com",
            requested_role=RequestedRole.ADMIN,
            approved_role=RequestedRole.ADMIN,
            account_status=AccountStatus.APPROVED,
            approved_at=now,
            approved_by_user_id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
        )
        self.tester_user = AppUser(
            id=uuid.uuid4(),
            auth_user_id=uuid.uuid4(),
            full_name="Tester User",
            email="tester@example.com",
            requested_role=RequestedRole.DRIVE_TESTER,
            approved_role=RequestedRole.DRIVE_TESTER,
            account_status=AccountStatus.APPROVED,
            approved_at=now,
            approved_by_user_id=self.admin_user.id,
            created_at=now,
            updated_at=now,
        )
        self.users = [self.admin_user, self.tester_user]

        self.last_summary_filters: dict[str, Any] | None = None
        self.last_no_submission_call: dict[str, Any] | None = None
        self.last_export_filters: dict[str, Any] | None = None

    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None:
        return next((user for user in self.users if user.auth_user_id == auth_user_id), None)

    async def count_approved_drive_testers(self) -> int:
        return 5

    async def count_submissions_by_status(
        self,
        *,
        status: SubmissionStatus,
        work_date: date | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> int:
        self.last_summary_filters = {
            "work_date": work_date,
            "date_from": date_from,
            "date_to": date_to,
        }
        if status == SubmissionStatus.IN_PROGRESS:
            return 2
        return 3

    async def count_approved_drive_testers_without_submission(self, *, work_date: date) -> int:
        self.last_no_submission_call = {"work_date": work_date}
        return 1

    async def list_approved_drive_testers_without_submission(
        self,
        *,
        work_date: date,
        offset: int,
        limit: int,
    ) -> tuple[list[AppUser], int]:
        self.last_no_submission_call = {
            "work_date": work_date,
            "offset": offset,
            "limit": limit,
        }
        users = [self.tester_user]
        return users[offset : offset + limit], len(users)

    async def list_admin_submissions_for_export(
        self,
        *,
        work_date: date | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        status: SubmissionStatus | None = None,
        shift: Shift | None = None,
        owner_user_id: uuid.UUID | None = None,
        ticket_number: str | None = None,
        file_submission_pending: bool | None = None,
    ) -> list[Any]:
        self.last_export_filters = {
            "work_date": work_date,
            "date_from": date_from,
            "date_to": date_to,
            "status": status,
            "shift": shift,
            "owner_user_id": owner_user_id,
            "ticket_number": ticket_number,
            "file_submission_pending": file_submission_pending,
        }
        now = datetime.now(UTC)
        return [
            type(
                "SubmissionStub",
                (),
                {
                    "id": uuid.uuid4(),
                    "client_generated_id": uuid.uuid4(),
                    "owner_user_id": self.tester_user.id,
                    "submitter_name_snapshot": "Tester User",
                    "submitter_email_snapshot": "tester@example.com",
                    "workorder_id": uuid.uuid4(),
                    "work_date": date(2026, 4, 14),
                    "shift": Shift.AM,
                    "team_number": "11",
                    "ticket_number": "TKT-1",
                    "skipped_grids": 1,
                    "force_tested_grids": 0,
                    "completed_grids": 9,
                    "status": SubmissionStatus.CHECKED_OUT,
                    "version_number": 2,
                    "started_at": now,
                    "ended_at": now,
                    "created_at": now,
                    "updated_at": now,
                },
            )(),
        ]

    async def count_active_attachments_for_submissions(
        self,
        submission_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, int]:
        return dict.fromkeys(submission_ids, 0)

    async def count_workorders_by_status(self, *, status: "WorkorderStatus") -> int:
        from app.core.enums import WorkorderStatus
        if status == WorkorderStatus.ACTIVE:
            return 3
        return 1

    async def get_workorders_by_submission_ids(
        self, submission_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, Any]:
        # Returns empty — CSV workorder columns will be blank in tests
        return {}


def _auth_payload(user: AppUser) -> dict[str, Any]:
    return {"sub": str(user.auth_user_id), "email": user.email}


async def test_dashboard_summary_requires_admin_role() -> None:
    repo = FakeReportingRepository()
    service = ReportingService(repository=repo)

    with pytest.raises(AppError) as exc:
        await service.get_dashboard_summary(_auth_payload(repo.tester_user), work_date=date(2026, 4, 14))

    assert exc.value.code.value == "ADMIN_ONLY"
    assert exc.value.status_code == 403


async def test_dashboard_summary_returns_expected_counts() -> None:
    repo = FakeReportingRepository()
    service = ReportingService(repository=repo)

    result = await service.get_dashboard_summary(
        _auth_payload(repo.admin_user),
        work_date=date(2026, 4, 14),
    )

    assert result.approved_drive_testers == 5
    assert result.ongoing_submissions == 2
    assert result.completed_submissions == 3
    assert result.no_submission_yet == 1
    assert result.reference_date == date(2026, 4, 14)
    assert repo.last_summary_filters == {
        "work_date": date(2026, 4, 14),
        "date_from": None,
        "date_to": None,
    }


async def test_no_submission_yet_returns_paginated_items() -> None:
    repo = FakeReportingRepository()
    service = ReportingService(repository=repo)

    items, total = await service.list_no_submission_yet(
        _auth_payload(repo.admin_user),
        work_date=date(2026, 4, 14),
        page=1,
        page_size=20,
    )

    assert total == 1
    assert len(items) == 1
    assert items[0].email == "tester@example.com"
    assert repo.last_no_submission_call == {
        "work_date": date(2026, 4, 14),
        "offset": 0,
        "limit": 20,
    }


async def test_export_submissions_csv_uses_filter_model() -> None:
    repo = FakeReportingRepository()
    service = ReportingService(repository=repo)

    csv_text = await service.export_submissions_csv(
        _auth_payload(repo.admin_user),
        work_date=date(2026, 4, 14),
        status=SubmissionStatus.CHECKED_OUT,
        shift=Shift.AM,
        owner_user_id=repo.tester_user.id,
        ticket_number="TKT",
        file_submission_pending=True,
    )

    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["status"] == "CHECKED_OUT"
    assert rows[0]["file_submission_pending"] == "true"
    assert repo.last_export_filters is not None
    assert repo.last_export_filters["file_submission_pending"] is True
    assert repo.last_export_filters["owner_user_id"] == repo.tester_user.id


# ---------------------------------------------------------------------------
# Wave 2 RED tests — item 52: dashboard includes workorder counts
# ---------------------------------------------------------------------------


async def test_dashboard_summary_includes_workorder_counts() -> None:
    repo = FakeReportingRepository()
    service = ReportingService(repository=repo)

    result = await service.get_dashboard_summary(
        _auth_payload(repo.admin_user),
        work_date=date(2026, 4, 14),
    )

    assert hasattr(result, "active_workorders")
    assert hasattr(result, "completed_workorders")
    assert result.active_workorders == 3   # per FakeReportingRepository stub
    assert result.completed_workorders == 1


# ---------------------------------------------------------------------------
# Wave 2 RED tests — item 54: CSV export includes workorder fields
# ---------------------------------------------------------------------------


async def test_export_csv_includes_workorder_fields() -> None:
    repo = FakeReportingRepository()
    service = ReportingService(repository=repo)

    csv_text = await service.export_submissions_csv(
        _auth_payload(repo.admin_user),
        work_date=date(2026, 4, 14),
    )

    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)
    assert len(rows) >= 1
    # These columns must be present in the CSV header
    headers = reader.fieldnames or []
    assert "workorder_code" in headers
    assert "workorder_region" in headers
    assert "workorder_status" in headers
    assert "workorder_progress_percent" in headers


# ---------------------------------------------------------------------------
# Wave 2 RED tests — item 55: mobile bootstrap includes workorder_statuses
# ---------------------------------------------------------------------------


async def test_dashboard_summary_no_submission_count_is_still_int() -> None:
    """Regression guard: no_submission_yet is still present in summary."""
    repo = FakeReportingRepository()
    service = ReportingService(repository=repo)

    result = await service.get_dashboard_summary(
        _auth_payload(repo.admin_user),
        work_date=date(2026, 4, 14),
    )

    assert isinstance(result.no_submission_yet, int)
