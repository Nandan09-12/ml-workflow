import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

import pytest

from app.api.v1.routers.admin_submissions import get_admin_submission_service
from app.core.enums import Shift, SubmissionStatus, Zone
from app.core.errors import AppError, ErrorCode
from app.core.security import get_current_auth_payload


@dataclass(frozen=True)
class FakeSubmissionView:
    id: uuid.UUID
    client_generated_id: uuid.UUID
    owner_user_id: uuid.UUID
    submitter_name_snapshot: str
    submitter_email_snapshot: str
    zone: Zone
    work_date: date
    shift: Shift
    team_number: str | None
    ticket_number: str | None
    cluster_name: str
    cluster_name_normalized: str
    number_of_grids: int
    skipped_grids: int
    force_tested_grids: int
    pending_grids: int
    completed_grids: int
    status: SubmissionStatus
    version_number: int
    created_at: datetime
    updated_at: datetime
    file_submission_pending: bool


@dataclass(frozen=True)
class FakeSubmissionAuditView:
    id: uuid.UUID
    submission_id: uuid.UUID
    action_type: str
    actor_user_id: uuid.UUID
    actor_role: str
    source: str
    changed_fields_json: dict[str, Any] | None
    before_snapshot_json: dict[str, Any] | None
    after_snapshot_json: dict[str, Any] | None
    created_at: datetime


class FakeAdminSubmissionService:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.item = FakeSubmissionView(
            id=uuid.uuid4(),
            client_generated_id=uuid.uuid4(),
            owner_user_id=uuid.uuid4(),
            submitter_name_snapshot="Tester Name",
            submitter_email_snapshot="tester@example.com",
            zone=Zone.NORTHEAST,
            work_date=date(2026, 4, 14),
            shift=Shift.AM,
            team_number="11",
            ticket_number="TKT-1",
            cluster_name="North-1",
            cluster_name_normalized="NORTH 1",
            number_of_grids=10,
            skipped_grids=1,
            force_tested_grids=0,
            pending_grids=0,
            completed_grids=9,
            status=SubmissionStatus.COMPLETED,
            version_number=3,
            created_at=now,
            updated_at=now,
            file_submission_pending=True,
        )
        self.audit_item = FakeSubmissionAuditView(
            id=uuid.uuid4(),
            submission_id=self.item.id,
            action_type="UPDATED",
            actor_user_id=uuid.uuid4(),
            actor_role="ADMIN",
            source="ADMIN_CONSOLE",
            changed_fields_json={"fields": ["cluster_name"]},
            before_snapshot_json=None,
            after_snapshot_json=None,
            created_at=now,
        )
        self.raise_admin_only = False
        self.last_file_submission_pending: bool | None = None

    async def reopen_submission(self, _: dict[str, Any], __: uuid.UUID) -> FakeSubmissionView:
        if self.raise_admin_only:
            raise AppError(ErrorCode.ADMIN_ONLY, "Admin access required.", status_code=403)
        return FakeSubmissionView(
            **{
                **self.item.__dict__,
                "status": SubmissionStatus.ONGOING,
                "file_submission_pending": False,
                "version_number": self.item.version_number + 1,
            }
        )

    async def list_admin_submissions(
        self,
        _: dict[str, Any],
        *,
        work_date: date | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        status: SubmissionStatus | None = None,
        zone: Zone | None = None,
        shift: Shift | None = None,
        owner_user_id: uuid.UUID | None = None,
        cluster_name: str | None = None,
        ticket_number: str | None = None,
        file_submission_pending: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[FakeSubmissionView], int]:
        if self.raise_admin_only:
            raise AppError(ErrorCode.ADMIN_ONLY, "Admin access required.", status_code=403)
        self.last_file_submission_pending = file_submission_pending
        return [self.item], 1

    async def get_admin_submission(self, _: dict[str, Any], __: uuid.UUID) -> FakeSubmissionView:
        if self.raise_admin_only:
            raise AppError(ErrorCode.ADMIN_ONLY, "Admin access required.", status_code=403)
        return self.item

    async def update_admin_submission(
        self,
        _: dict[str, Any],
        __: uuid.UUID,
        ___: Any,
    ) -> FakeSubmissionView:
        if self.raise_admin_only:
            raise AppError(ErrorCode.ADMIN_ONLY, "Admin access required.", status_code=403)
        return self.item

    async def get_submission_audit(
        self,
        _: dict[str, Any],
        __: uuid.UUID,
    ) -> list[FakeSubmissionAuditView]:
        if self.raise_admin_only:
            raise AppError(ErrorCode.ADMIN_ONLY, "Admin access required.", status_code=403)
        return [self.audit_item]


@pytest.fixture
def admin_submission_service() -> FakeAdminSubmissionService:
    return FakeAdminSubmissionService()


def test_admin_reopen_requires_auth(client: Any) -> None:
    response = client.post(f"/api/v1/admin/submissions/{uuid.uuid4()}/reopen")
    body = response.json()

    assert response.status_code == 401
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert "request_id" in body["meta"]


def test_admin_reopen_success_envelope(
    client: Any,
    auth_payload_admin: dict[str, Any],
    admin_submission_service: FakeAdminSubmissionService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_admin_submission_service] = lambda: admin_submission_service

    response = client.post(f"/api/v1/admin/submissions/{admin_submission_service.item.id}/reopen")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["status"] == "ONGOING"
    assert body["data"]["file_submission_pending"] is False
    assert "request_id" in body["meta"]


def test_admin_reopen_invalid_uuid_returns_enveloped_422(
    client: Any,
    auth_payload_admin: dict[str, Any],
    admin_submission_service: FakeAdminSubmissionService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_admin_submission_service] = lambda: admin_submission_service

    response = client.post("/api/v1/admin/submissions/not-a-uuid/reopen")
    body = response.json()

    assert response.status_code == 422
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "request_id" in body["meta"]


def test_admin_submissions_list_success_with_file_pending_filter(
    client: Any,
    auth_payload_admin: dict[str, Any],
    admin_submission_service: FakeAdminSubmissionService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_admin_submission_service] = lambda: admin_submission_service

    response = client.get("/api/v1/admin/submissions?file_submission_pending=true")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["items"][0]["file_submission_pending"] is True
    assert body["data"]["pagination"]["page"] == 1
    assert admin_submission_service.last_file_submission_pending is True


def test_admin_submissions_list_enforces_admin_only_error_envelope(
    client: Any,
    auth_payload_drive_tester: dict[str, Any],
    admin_submission_service: FakeAdminSubmissionService,
) -> None:
    admin_submission_service.raise_admin_only = True
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_drive_tester
    app.dependency_overrides[get_admin_submission_service] = lambda: admin_submission_service

    response = client.get("/api/v1/admin/submissions")
    body = response.json()

    assert response.status_code == 403
    assert body["success"] is False
    assert body["error"]["code"] == "ADMIN_ONLY"
    assert "request_id" in body["meta"]


def test_admin_submission_detail_success(
    client: Any,
    auth_payload_admin: dict[str, Any],
    admin_submission_service: FakeAdminSubmissionService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_admin_submission_service] = lambda: admin_submission_service

    response = client.get(f"/api/v1/admin/submissions/{admin_submission_service.item.id}")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["id"] == str(admin_submission_service.item.id)
    assert body["data"]["file_submission_pending"] is True


def test_admin_submission_patch_unknown_field_422(
    client: Any,
    auth_payload_admin: dict[str, Any],
    admin_submission_service: FakeAdminSubmissionService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_admin_submission_service] = lambda: admin_submission_service

    response = client.patch(
        f"/api/v1/admin/submissions/{admin_submission_service.item.id}",
        json={"version_number": 1, "bad_field": "x"},
    )
    body = response.json()

    assert response.status_code == 422
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_admin_submission_audit_success(
    client: Any,
    auth_payload_admin: dict[str, Any],
    admin_submission_service: FakeAdminSubmissionService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_admin_submission_service] = lambda: admin_submission_service

    response = client.get(f"/api/v1/admin/submissions/{admin_submission_service.item.id}/audit")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["count"] == 1
    assert body["data"]["items"][0]["action_type"] == "UPDATED"
