import uuid
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.api.v1.routers.reporting import get_reporting_service
from app.core.errors import AppError, ErrorCode
from app.core.security import get_current_auth_payload


@dataclass(frozen=True)
class FakeDashboardSummaryView:
    approved_drive_testers: int
    ongoing_submissions: int
    completed_submissions: int
    no_submission_yet: int
    active_workorders: int
    completed_workorders: int
    reference_date: date
    date_from: date | None
    date_to: date | None


@dataclass(frozen=True)
class FakeNoSubmissionUserView:
    id: uuid.UUID
    full_name: str
    email: str


class FakeReportingService:
    def __init__(self) -> None:
        self.summary = FakeDashboardSummaryView(
            approved_drive_testers=12,
            ongoing_submissions=5,
            completed_submissions=7,
            no_submission_yet=3,
            active_workorders=4,
            completed_workorders=2,
            reference_date=date(2026, 4, 14),
            date_from=None,
            date_to=None,
        )
        self.no_submission_item = FakeNoSubmissionUserView(
            id=uuid.uuid4(),
            full_name="No Submit Tester",
            email="nosubmit@example.com",
        )
        self.csv_content = (
            "submission_id,submitter_email,status,file_submission_pending\n"
            "11111111-1111-1111-1111-111111111111,tester@example.com,COMPLETED,true\n"
        )
        self.raise_admin_only = False
        self.last_export_filters: dict[str, Any] | None = None
        self.last_work_date: date | None = None

    async def get_dashboard_summary(
        self,
        _: dict[str, Any],
        *,
        work_date: date | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> FakeDashboardSummaryView:
        if self.raise_admin_only:
            raise AppError(ErrorCode.ADMIN_ONLY, "Admin access required.", status_code=403)
        self.last_work_date = work_date
        return self.summary

    async def list_no_submission_yet(
        self,
        _: dict[str, Any],
        *,
        work_date: date,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[FakeNoSubmissionUserView], int]:
        if self.raise_admin_only:
            raise AppError(ErrorCode.ADMIN_ONLY, "Admin access required.", status_code=403)
        self.last_work_date = work_date
        return [self.no_submission_item], 1

    async def export_submissions_csv(
        self,
        _: dict[str, Any],
        *,
        work_date: date | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        status: str | None = None,
        zone: str | None = None,
        shift: str | None = None,
        owner_user_id: uuid.UUID | None = None,
        cluster_name: str | None = None,
        ticket_number: str | None = None,
        file_submission_pending: bool | None = None,
    ) -> str:
        if self.raise_admin_only:
            raise AppError(ErrorCode.ADMIN_ONLY, "Admin access required.", status_code=403)
        self.last_export_filters = {
            "work_date": work_date,
            "date_from": date_from,
            "date_to": date_to,
            "status": status,
            "zone": zone,
            "shift": shift,
            "owner_user_id": owner_user_id,
            "cluster_name": cluster_name,
            "ticket_number": ticket_number,
            "file_submission_pending": file_submission_pending,
        }
        return self.csv_content


def test_dashboard_summary_requires_auth(client: Any) -> None:
    response = client.get("/api/v1/admin/dashboard/summary")
    body = response.json()

    assert response.status_code == 401
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_dashboard_summary_success_envelope(
    client: Any,
    auth_payload_admin: dict[str, Any],
) -> None:
    service = FakeReportingService()
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_reporting_service] = lambda: service

    response = client.get("/api/v1/admin/dashboard/summary?work_date=2026-04-14")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["approved_drive_testers"] == 12
    assert body["data"]["no_submission_yet"] == 3
    assert body["data"]["active_workorders"] == 4
    assert body["data"]["completed_workorders"] == 2
    assert service.last_work_date == date(2026, 4, 14)


def test_no_submission_yet_success_response(
    client: Any,
    auth_payload_admin: dict[str, Any],
) -> None:
    service = FakeReportingService()
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_reporting_service] = lambda: service

    response = client.get("/api/v1/admin/dashboard/no-submission-yet?work_date=2026-04-14")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["work_date"] == "2026-04-14"
    assert body["data"]["count"] == 1
    assert body["data"]["items"][0]["email"] == "nosubmit@example.com"
    assert "not assignment-based" in body["data"]["note"].lower()


def test_no_submission_yet_admin_only_error_envelope(
    client: Any,
    auth_payload_drive_tester: dict[str, Any],
) -> None:
    service = FakeReportingService()
    service.raise_admin_only = True
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_drive_tester
    app.dependency_overrides[get_reporting_service] = lambda: service

    response = client.get("/api/v1/admin/dashboard/no-submission-yet?work_date=2026-04-14")
    body = response.json()

    assert response.status_code == 403
    assert body["success"] is False
    assert body["error"]["code"] == "ADMIN_ONLY"


def test_export_submissions_csv_returns_stream_response(
    client: Any,
    auth_payload_admin: dict[str, Any],
) -> None:
    service = FakeReportingService()
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_reporting_service] = lambda: service

    response = client.get("/api/v1/admin/reports/submissions/export?file_submission_pending=true")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment;" in response.headers.get("content-disposition", "")
    assert "submission_id,submitter_email,status,file_submission_pending" in response.text
    assert service.last_export_filters is not None
    assert service.last_export_filters["file_submission_pending"] is True

