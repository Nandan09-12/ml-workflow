import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

import pytest

from app.api.v1.routers.admin_submissions import (
    get_admin_submission_service,
    get_attachment_service,
)
from app.core.enums import Shift, SubmissionStatus, WorkorderStatus
from app.core.errors import AppError, ErrorCode
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
            workorder_id=uuid.uuid4(),
            work_date=date(2026, 4, 14),
            shift=Shift.AM,
            team_number="11",
            ticket_number="TKT-1",
            skipped_grids=1,
            force_tested_grids=0,
            completed_grids=9,
            status=SubmissionStatus.COMPLETED,
            version_number=3,
            started_at=now,
            ended_at=now,
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
        self.last_workorder_status: WorkorderStatus | None = None

    async def reopen_submission(self, _: dict[str, Any], __: uuid.UUID) -> FakeSubmissionView:
        if self.raise_admin_only:
            raise AppError(ErrorCode.ADMIN_ONLY, "Admin access required.", status_code=403)
        return FakeSubmissionView(
            **{
                **self.item.__dict__,
                "status": SubmissionStatus.IN_PROGRESS,
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
        shift: Shift | None = None,
        workorder_status: WorkorderStatus | None = None,
        owner_user_id: uuid.UUID | None = None,
        ticket_number: str | None = None,
        file_submission_pending: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[FakeSubmissionView], int]:
        if self.raise_admin_only:
            raise AppError(ErrorCode.ADMIN_ONLY, "Admin access required.", status_code=403)
        self.last_workorder_status = workorder_status
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
    assert body["data"]["status"] == "IN_PROGRESS"
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


def test_admin_submissions_list_success_with_workorder_status_filter(
    client: Any,
    auth_payload_admin: dict[str, Any],
    admin_submission_service: FakeAdminSubmissionService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_admin_submission_service] = lambda: admin_submission_service

    response = client.get("/api/v1/admin/submissions?workorder_status=COMPLETED")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert admin_submission_service.last_workorder_status == WorkorderStatus.COMPLETED


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


# ---------------------------------------------------------------------------
# attachment history endpoint
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FakeAttachmentView:
    id: uuid.UUID
    submission_id: uuid.UUID
    file_name: str
    bucket_name: str
    object_path: str
    mime_type: str
    file_extension: str
    file_size_bytes: int
    uploaded_by_user_id: uuid.UUID
    uploaded_at: datetime
    is_active: bool


class FakeAdminAttachmentService:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.history_item = FakeAttachmentView(
            id=uuid.uuid4(),
            submission_id=uuid.uuid4(),
            file_name="old_report.csv",
            bucket_name="attachments",
            object_path="submission/old_report.csv",
            mime_type="text/csv",
            file_extension=".csv",
            file_size_bytes=200,
            uploaded_by_user_id=uuid.uuid4(),
            uploaded_at=now,
            is_active=False,
        )
        self.raise_admin_only = False

    async def get_attachment_history(
        self,
        _: dict[str, Any],
        submission_id: uuid.UUID,
    ) -> list[FakeAttachmentView]:
        if self.raise_admin_only:
            raise AppError(ErrorCode.ADMIN_ONLY, "Admin access required.", status_code=403)
        return [self.history_item]


@pytest.fixture
def admin_attachment_service() -> FakeAdminAttachmentService:
    return FakeAdminAttachmentService()


def test_attachment_history_requires_auth(client: Any) -> None:
    response = client.get(f"/api/v1/admin/submissions/{uuid.uuid4()}/attachments/history")
    body = response.json()

    assert response.status_code == 401
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_attachment_history_success_envelope(
    client: Any,
    auth_payload_admin: dict[str, Any],
    admin_attachment_service: FakeAdminAttachmentService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_attachment_service] = lambda: admin_attachment_service

    sid = admin_attachment_service.history_item.submission_id
    response = client.get(f"/api/v1/admin/submissions/{sid}/attachments/history")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["count"] == 1
    assert body["data"]["items"][0]["file_name"] == "old_report.csv"
    assert body["data"]["items"][0]["is_active"] is False
    assert "request_id" in body["meta"]


def test_attachment_history_admin_only_error(
    client: Any,
    auth_payload_drive_tester: dict[str, Any],
    admin_attachment_service: FakeAdminAttachmentService,
) -> None:
    admin_attachment_service.raise_admin_only = True
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_drive_tester
    app.dependency_overrides[get_attachment_service] = lambda: admin_attachment_service

    response = client.get(f"/api/v1/admin/submissions/{uuid.uuid4()}/attachments/history")
    body = response.json()

    assert response.status_code == 403
    assert body["error"]["code"] == "ADMIN_ONLY"


def test_attachment_history_invalid_uuid_422(
    client: Any,
    auth_payload_admin: dict[str, Any],
    admin_attachment_service: FakeAdminAttachmentService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_attachment_service] = lambda: admin_attachment_service

    response = client.get("/api/v1/admin/submissions/not-a-uuid/attachments/history")
    body = response.json()

    assert response.status_code == 422
    assert body["error"]["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# SubmissionResponse includes workorder_summary field
# ---------------------------------------------------------------------------


def test_admin_submission_detail_includes_workorder_summary_key(
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
    assert "workorder_summary" in body["data"]
