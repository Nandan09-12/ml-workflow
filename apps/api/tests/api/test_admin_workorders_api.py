import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import pytest

from app.api.v1.routers.admin_workorders import get_workorder_service
from app.core.enums import Region, WorkorderStatus
from app.core.errors import AppError, ErrorCode
from app.core.security import get_current_auth_payload


@dataclass(frozen=True)
class FakeWorkorderView:
    id: uuid.UUID
    workorder_code: str
    region: Region
    status: WorkorderStatus
    total_grids: int
    completed_grids: int
    skipped_grids: int
    remaining_grids: int
    progress_percent: float
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class FakeWorkorderDetailView:
    id: uuid.UUID
    workorder_code: str
    region: Region
    status: WorkorderStatus
    total_grids: int
    completed_grids: int
    skipped_grids: int
    remaining_grids: int
    progress_percent: float
    created_at: datetime
    updated_at: datetime
    submissions: list = field(default_factory=list)


class FakeWorkorderService:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.view = FakeWorkorderView(
            id=uuid.uuid4(),
            workorder_code="WO-001",
            region=Region.NE_UP,
            status=WorkorderStatus.ACTIVE,
            total_grids=10,
            completed_grids=3,
            skipped_grids=1,
            remaining_grids=6,
            progress_percent=30.0,
            created_at=now,
            updated_at=now,
        )
        self.detail_view = FakeWorkorderDetailView(
            id=self.view.id,
            workorder_code=self.view.workorder_code,
            region=self.view.region,
            status=self.view.status,
            total_grids=self.view.total_grids,
            completed_grids=self.view.completed_grids,
            skipped_grids=self.view.skipped_grids,
            remaining_grids=self.view.remaining_grids,
            progress_percent=self.view.progress_percent,
            created_at=now,
            updated_at=now,
            submissions=[],
        )
        self.raise_admin_only = False
        self.raise_not_found = False
        self.raise_progress_exceeds = False

    async def list_workorders(
        self,
        _: dict[str, Any],
        *,
        region: Any = None,
        status: Any = None,
        workorder_code: Any = None,
        date_from: Any = None,
        date_to: Any = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[FakeWorkorderView], int]:
        if self.raise_admin_only:
            raise AppError(ErrorCode.ADMIN_ONLY, "Admin access required.", status_code=403)
        return [self.view], 1

    async def get_workorder_admin(
        self,
        _: dict[str, Any],
        workorder_id: uuid.UUID,
    ) -> FakeWorkorderDetailView:
        if self.raise_admin_only:
            raise AppError(ErrorCode.ADMIN_ONLY, "Admin access required.", status_code=403)
        if self.raise_not_found:
            raise AppError(ErrorCode.WORKORDER_NOT_FOUND, "Not found.", status_code=404)
        return self.detail_view

    async def update_workorder(
        self,
        _: dict[str, Any],
        workorder_id: uuid.UUID,
        body: Any,
    ) -> FakeWorkorderView:
        if self.raise_admin_only:
            raise AppError(ErrorCode.ADMIN_ONLY, "Admin access required.", status_code=403)
        if self.raise_not_found:
            raise AppError(ErrorCode.WORKORDER_NOT_FOUND, "Not found.", status_code=404)
        if self.raise_progress_exceeds:
            raise AppError(
                ErrorCode.WORKORDER_PROGRESS_EXCEEDS_TOTAL,
                "Progress exceeds total.",
                status_code=422,
            )
        return self.view


@pytest.fixture
def workorder_service() -> FakeWorkorderService:
    return FakeWorkorderService()


# ---------------------------------------------------------------------------
# list_workorders
# ---------------------------------------------------------------------------


def test_list_workorders_requires_auth(client: Any) -> None:
    response = client.get("/api/v1/admin/workorders")
    body = response.json()

    assert response.status_code == 401
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert "request_id" in body["meta"]


def test_list_workorders_success_envelope(
    client: Any,
    auth_payload_admin: dict[str, Any],
    workorder_service: FakeWorkorderService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_workorder_service] = lambda: workorder_service

    response = client.get("/api/v1/admin/workorders")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["total"] == 1
    assert body["data"]["items"][0]["workorder_code"] == "WO-001"
    assert body["data"]["items"][0]["status"] == "ACTIVE"
    assert "page" in body["data"]
    assert "request_id" in body["meta"]


def test_list_workorders_enforces_admin_only(
    client: Any,
    auth_payload_drive_tester: dict[str, Any],
    workorder_service: FakeWorkorderService,
) -> None:
    workorder_service.raise_admin_only = True
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_drive_tester
    app.dependency_overrides[get_workorder_service] = lambda: workorder_service

    response = client.get("/api/v1/admin/workorders")
    body = response.json()

    assert response.status_code == 403
    assert body["success"] is False
    assert body["error"]["code"] == "ADMIN_ONLY"


# ---------------------------------------------------------------------------
# get_workorder_admin (detail)
# ---------------------------------------------------------------------------


def test_get_workorder_requires_auth(client: Any) -> None:
    response = client.get(f"/api/v1/admin/workorders/{uuid.uuid4()}")
    body = response.json()

    assert response.status_code == 401
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_get_workorder_success_envelope(
    client: Any,
    auth_payload_admin: dict[str, Any],
    workorder_service: FakeWorkorderService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_workorder_service] = lambda: workorder_service

    response = client.get(f"/api/v1/admin/workorders/{workorder_service.view.id}")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["id"] == str(workorder_service.view.id)
    assert body["data"]["workorder_code"] == "WO-001"
    assert "submissions" in body["data"]
    assert "request_id" in body["meta"]


def test_get_workorder_not_found(
    client: Any,
    auth_payload_admin: dict[str, Any],
    workorder_service: FakeWorkorderService,
) -> None:
    workorder_service.raise_not_found = True
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_workorder_service] = lambda: workorder_service

    response = client.get(f"/api/v1/admin/workorders/{uuid.uuid4()}")
    body = response.json()

    assert response.status_code == 404
    assert body["success"] is False
    assert body["error"]["code"] == "WORKORDER_NOT_FOUND"


def test_get_workorder_invalid_uuid_422(
    client: Any,
    auth_payload_admin: dict[str, Any],
    workorder_service: FakeWorkorderService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_workorder_service] = lambda: workorder_service

    response = client.get("/api/v1/admin/workorders/not-a-uuid")
    body = response.json()

    assert response.status_code == 422
    assert body["error"]["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# update_workorder (PATCH)
# ---------------------------------------------------------------------------


def test_update_workorder_requires_auth(client: Any) -> None:
    response = client.patch(f"/api/v1/admin/workorders/{uuid.uuid4()}", json={"total_grids": 20})
    body = response.json()

    assert response.status_code == 401
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_update_workorder_success_envelope(
    client: Any,
    auth_payload_admin: dict[str, Any],
    workorder_service: FakeWorkorderService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_workorder_service] = lambda: workorder_service

    response = client.patch(
        f"/api/v1/admin/workorders/{workorder_service.view.id}",
        json={"total_grids": 20},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["workorder_code"] == "WO-001"
    assert "request_id" in body["meta"]


def test_update_workorder_extra_fields_422(
    client: Any,
    auth_payload_admin: dict[str, Any],
    workorder_service: FakeWorkorderService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_workorder_service] = lambda: workorder_service

    response = client.patch(
        f"/api/v1/admin/workorders/{workorder_service.view.id}",
        json={"total_grids": 10, "bad_field": "x"},
    )
    body = response.json()

    assert response.status_code == 422
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_update_workorder_admin_only_error(
    client: Any,
    auth_payload_drive_tester: dict[str, Any],
    workorder_service: FakeWorkorderService,
) -> None:
    workorder_service.raise_admin_only = True
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_drive_tester
    app.dependency_overrides[get_workorder_service] = lambda: workorder_service

    response = client.patch(
        f"/api/v1/admin/workorders/{workorder_service.view.id}",
        json={"total_grids": 5},
    )
    body = response.json()

    assert response.status_code == 403
    assert body["error"]["code"] == "ADMIN_ONLY"


def test_update_workorder_progress_exceeds_total(
    client: Any,
    auth_payload_admin: dict[str, Any],
    workorder_service: FakeWorkorderService,
) -> None:
    workorder_service.raise_progress_exceeds = True
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_workorder_service] = lambda: workorder_service

    response = client.patch(
        f"/api/v1/admin/workorders/{workorder_service.view.id}",
        json={"total_grids": 1},
    )
    body = response.json()

    assert response.status_code == 422
    assert body["error"]["code"] == "WORKORDER_PROGRESS_EXCEEDS_TOTAL"


def test_update_workorder_not_found(
    client: Any,
    auth_payload_admin: dict[str, Any],
    workorder_service: FakeWorkorderService,
) -> None:
    workorder_service.raise_not_found = True
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_workorder_service] = lambda: workorder_service

    response = client.patch(
        f"/api/v1/admin/workorders/{uuid.uuid4()}",
        json={"total_grids": 20},
    )
    body = response.json()

    assert response.status_code == 404
    assert body["error"]["code"] == "WORKORDER_NOT_FOUND"
