import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

import pytest

from app.api.v1.routers.submissions import (
    get_submission_service,
    get_workorder_service_for_submissions,
)
from app.core.enums import Shift, SubmissionStatus
from app.core.security import get_current_auth_payload


@dataclass(frozen=True)
class FakeSubmissionView:
    id: uuid.UUID
    client_generated_id: uuid.UUID
    owner_user_id: uuid.UUID
    submitter_name_snapshot: str
    submitter_email_snapshot: str
    workorder_id: uuid.UUID
    work_date: date
    shift: Shift
    team_number: str | None
    ticket_number: str | None
    skipped_grids: int
    force_tested_grids: int
    completed_grids: int
    status: SubmissionStatus
    version_number: int
    started_at: datetime
    ended_at: datetime | None
    created_at: datetime
    updated_at: datetime
    file_submission_pending: bool


class FakeSubmissionService:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.item = FakeSubmissionView(
            id=uuid.uuid4(),
            client_generated_id=uuid.uuid4(),
            owner_user_id=uuid.uuid4(),
            submitter_name_snapshot="Tester Name",
            submitter_email_snapshot="tester@example.com",
            workorder_id=uuid.uuid4(),
            work_date=date(2026, 4, 14),
            shift=Shift.AM,
            team_number="11",
            ticket_number="TKT-1",
            skipped_grids=1,
            force_tested_grids=0,
            completed_grids=7,
            status=SubmissionStatus.IN_PROGRESS,
            version_number=1,
            started_at=now,
            ended_at=None,
            created_at=now,
            updated_at=now,
            file_submission_pending=False,
        )
        self.last_list_page = 0
        self.last_list_page_size = 0

    async def create_submission(self, _: dict[str, Any], __: Any) -> FakeSubmissionView:
        return self.item

    async def list_my_submissions(
        self,
        _: dict[str, Any],
        *,
        work_date: date | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        status: SubmissionStatus | None = None,
        shift: Shift | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[FakeSubmissionView], int]:
        self.last_list_page = page
        self.last_list_page_size = page_size
        return [self.item], 1

    async def get_submission(self, _: dict[str, Any], submission_id: uuid.UUID) -> FakeSubmissionView:
        if submission_id == self.item.id:
            return self.item
        return self.item

    async def update_submission(
        self,
        _: dict[str, Any],
        __: uuid.UUID,
        ___: Any,
    ) -> FakeSubmissionView:
        return self.item

    async def complete_submission(self, _: dict[str, Any], __: uuid.UUID) -> FakeSubmissionView:
        return FakeSubmissionView(
            **{
                **self.item.__dict__,
                "status": SubmissionStatus.COMPLETED,
                "file_submission_pending": True,
                "version_number": self.item.version_number + 1,
            }
        )


class FakeWorkorderServiceForPost:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.item = FakeSubmissionView(
            id=uuid.uuid4(),
            client_generated_id=uuid.uuid4(),
            owner_user_id=uuid.uuid4(),
            submitter_name_snapshot="Tester Name",
            submitter_email_snapshot="tester@example.com",
            workorder_id=uuid.uuid4(),
            work_date=date(2026, 4, 14),
            shift=Shift.AM,
            team_number="11",
            ticket_number="TKT-1",
            skipped_grids=0,
            force_tested_grids=0,
            completed_grids=0,
            status=SubmissionStatus.IN_PROGRESS,
            version_number=1,
            started_at=now,
            ended_at=None,
            created_at=now,
            updated_at=now,
            file_submission_pending=False,
        )

    async def start_drive(self, _: dict[str, Any], __: Any) -> FakeSubmissionView:
        return self.item


@pytest.fixture
def submission_service() -> FakeSubmissionService:
    return FakeSubmissionService()


def test_list_submissions_requires_auth(client: Any) -> None:
    response = client.get("/api/v1/submissions")
    body = response.json()

    assert response.status_code == 401
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert "request_id" in body["meta"]


def test_create_submission_success_response_envelope(
    client: Any,
    auth_payload_drive_tester: dict[str, Any],
) -> None:
    workorder_service = FakeWorkorderServiceForPost()
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_drive_tester
    app.dependency_overrides[get_workorder_service_for_submissions] = lambda: workorder_service

    response = client.post(
        "/api/v1/submissions",
        json={
            "workorder_code": "WO-001",
            "region": "NE_UP",
            "total_grids": 10,
            "work_date": "2026-04-14",
            "shift": "AM",
            "team_number": "11",
            "ticket_number": "TKT-1",
        },
    )
    body = response.json()

    assert response.status_code == 201
    assert body["success"] is True
    assert body["data"]["status"] == "IN_PROGRESS"
    assert body["data"]["file_submission_pending"] is False
    assert "request_id" in body["meta"]


def test_list_submissions_success_with_default_pagination(
    client: Any,
    auth_payload_drive_tester: dict[str, Any],
    submission_service: FakeSubmissionService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_drive_tester
    app.dependency_overrides[get_submission_service] = lambda: submission_service

    response = client.get("/api/v1/submissions")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["pagination"]["page"] == 1
    assert body["data"]["pagination"]["page_size"] == 20
    assert body["data"]["pagination"]["total"] == 1
    assert body["data"]["items"][0]["id"] == str(submission_service.item.id)
    assert submission_service.last_list_page == 1
    assert submission_service.last_list_page_size == 20


def test_get_submission_detail_invalid_uuid_returns_enveloped_422(
    client: Any,
    auth_payload_drive_tester: dict[str, Any],
    submission_service: FakeSubmissionService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_drive_tester
    app.dependency_overrides[get_submission_service] = lambda: submission_service

    response = client.get("/api/v1/submissions/not-a-uuid")
    body = response.json()

    assert response.status_code == 422
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "request_id" in body["meta"]


def test_patch_submission_rejects_unknown_fields_with_422(
    client: Any,
    auth_payload_drive_tester: dict[str, Any],
    submission_service: FakeSubmissionService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_drive_tester
    app.dependency_overrides[get_submission_service] = lambda: submission_service

    response = client.patch(
        f"/api/v1/submissions/{submission_service.item.id}",
        json={"version_number": 1, "bad_field": "not-allowed"},
    )
    body = response.json()

    assert response.status_code == 422
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "request_id" in body["meta"]


def test_complete_submission_success_response_envelope(
    client: Any,
    auth_payload_drive_tester: dict[str, Any],
    submission_service: FakeSubmissionService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_drive_tester
    app.dependency_overrides[get_submission_service] = lambda: submission_service

    response = client.post(f"/api/v1/submissions/{submission_service.item.id}/complete")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["status"] == "COMPLETED"
    assert body["data"]["file_submission_pending"] is True
    assert "request_id" in body["meta"]
