"""
RED API tests for GET /api/v1/workorders/lookup.
"""
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest

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


class FakeWorkorderService:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.workorder = FakeWorkorderView(
            id=uuid.uuid4(),
            workorder_code="WO-001",
            region=Region.NE_UP,
            status=WorkorderStatus.ACTIVE,
            total_grids=10,
            completed_grids=3,
            skipped_grids=1,
            remaining_grids=6,
            progress_percent=40.0,
            created_at=now,
            updated_at=now,
        )
        self.raise_not_found = False

    async def lookup_workorder(self, _: dict[str, Any], workorder_code: str) -> FakeWorkorderView:
        if self.raise_not_found:
            raise AppError(ErrorCode.WORKORDER_NOT_FOUND, "Workorder not found.", status_code=404)
        return self.workorder


@pytest.fixture
def workorder_service() -> FakeWorkorderService:
    return FakeWorkorderService()


def test_lookup_workorder_requires_auth(client: Any) -> None:
    response = client.get("/api/v1/workorders/lookup?workorder_code=WO-001")
    body = response.json()

    assert response.status_code == 401
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert "request_id" in body["meta"]


def test_lookup_workorder_success_envelope(
    client: Any,
    auth_payload_drive_tester: dict[str, Any],
    workorder_service: FakeWorkorderService,
) -> None:
    from app.api.v1.routers.workorders import get_workorder_service

    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_drive_tester
    app.dependency_overrides[get_workorder_service] = lambda: workorder_service

    response = client.get("/api/v1/workorders/lookup?workorder_code=WO-001")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["workorder_code"] == "WO-001"
    assert body["data"]["region"] == "NE_UP"
    assert body["data"]["total_grids"] == 10
    assert body["data"]["completed_grids"] == 3
    assert body["data"]["remaining_grids"] == 6
    assert body["data"]["progress_percent"] == 40.0
    assert "request_id" in body["meta"]


def test_lookup_workorder_missing_query_param_returns_422(
    client: Any,
    auth_payload_drive_tester: dict[str, Any],
    workorder_service: FakeWorkorderService,
) -> None:
    from app.api.v1.routers.workorders import get_workorder_service

    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_drive_tester
    app.dependency_overrides[get_workorder_service] = lambda: workorder_service

    response = client.get("/api/v1/workorders/lookup")
    body = response.json()

    assert response.status_code == 422
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_lookup_workorder_not_found_returns_404_envelope(
    client: Any,
    auth_payload_drive_tester: dict[str, Any],
    workorder_service: FakeWorkorderService,
) -> None:
    from app.api.v1.routers.workorders import get_workorder_service

    workorder_service.raise_not_found = True
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_drive_tester
    app.dependency_overrides[get_workorder_service] = lambda: workorder_service

    response = client.get("/api/v1/workorders/lookup?workorder_code=GHOST-WO")
    body = response.json()

    assert response.status_code == 404
    assert body["success"] is False
    assert body["error"]["code"] == "WORKORDER_NOT_FOUND"
    assert "request_id" in body["meta"]
