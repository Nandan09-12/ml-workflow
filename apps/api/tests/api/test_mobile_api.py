import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.api.v1.routers.mobile import get_mobile_service
from app.core.errors import AppError, ErrorCode
from app.core.security import get_current_auth_payload


@dataclass(frozen=True)
class FakeMobileUserView:
    id: uuid.UUID
    auth_user_id: uuid.UUID
    full_name: str
    email: str
    requested_role: str
    approved_role: str | None
    account_status: str


@dataclass(frozen=True)
class FakeMobileReferenceDataView:
    zones: list[str]
    shifts: list[str]
    submission_statuses: list[str]


@dataclass(frozen=True)
class FakeMobileBootstrapView:
    contract_version: str
    offline_sync_enabled: bool
    server_time_utc: datetime
    user: FakeMobileUserView
    reference_data: FakeMobileReferenceDataView


@dataclass(frozen=True)
class FakeMobileSyncResultView:
    contract_version: str
    accepted: bool
    status: str
    message: str
    received_operations_count: int
    processed_operations_count: int
    rejected_operations_count: int
    server_time_utc: datetime


class FakeMobileService:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.bootstrap = FakeMobileBootstrapView(
            contract_version="v1",
            offline_sync_enabled=False,
            server_time_utc=now,
            user=FakeMobileUserView(
                id=uuid.uuid4(),
                auth_user_id=uuid.uuid4(),
                full_name="Mobile User",
                email="mobile@example.com",
                requested_role="DRIVE_TESTER",
                approved_role="DRIVE_TESTER",
                account_status="APPROVED",
            ),
            reference_data=FakeMobileReferenceDataView(
                zones=["NORTHEAST", "CENTRAL", "SOUTH_FLORIDA"],
                shifts=["AM", "PM"],
                submission_statuses=["ONGOING", "COMPLETED"],
            ),
        )
        self.sync_result = FakeMobileSyncResultView(
            contract_version="v1",
            accepted=False,
            status="NOT_IMPLEMENTED",
            message="Mobile sync placeholder",
            received_operations_count=2,
            processed_operations_count=0,
            rejected_operations_count=2,
            server_time_utc=now,
        )
        self.raise_not_found = False

    async def get_bootstrap_payload(self, _: dict[str, Any]) -> FakeMobileBootstrapView:
        if self.raise_not_found:
            raise AppError(ErrorCode.NOT_FOUND, "User profile not found.", status_code=404)
        return self.bootstrap

    async def sync_placeholder(
        self,
        _: dict[str, Any],
        __: Any,
    ) -> FakeMobileSyncResultView:
        if self.raise_not_found:
            raise AppError(ErrorCode.NOT_FOUND, "User profile not found.", status_code=404)
        return self.sync_result


def test_mobile_bootstrap_requires_auth(client: Any) -> None:
    response = client.get("/api/v1/mobile/bootstrap")
    body = response.json()

    assert response.status_code == 401
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_mobile_bootstrap_success_envelope(
    client: Any,
    auth_payload_drive_tester: dict[str, Any],
) -> None:
    service = FakeMobileService()
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_drive_tester
    app.dependency_overrides[get_mobile_service] = lambda: service

    response = client.get("/api/v1/mobile/bootstrap")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["contract_version"] == "v1"
    assert body["data"]["offline_sync_enabled"] is False
    assert body["data"]["user"]["email"] == "mobile@example.com"
    assert "NORTHEAST" in body["data"]["reference_data"]["zones"]


def test_mobile_sync_placeholder_success(
    client: Any,
    auth_payload_drive_tester: dict[str, Any],
) -> None:
    service = FakeMobileService()
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_drive_tester
    app.dependency_overrides[get_mobile_service] = lambda: service

    response = client.post(
        "/api/v1/mobile/sync",
        json={
            "client_batch_id": str(uuid.uuid4()),
            "device_id": "pixel-1",
            "operations": [{"entity": "submission", "action": "upsert"}],
        },
    )
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["status"] == "NOT_IMPLEMENTED"
    assert body["data"]["received_operations_count"] == 2


def test_mobile_sync_validation_error_enveloped_422(
    client: Any,
    auth_payload_drive_tester: dict[str, Any],
) -> None:
    service = FakeMobileService()
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_drive_tester
    app.dependency_overrides[get_mobile_service] = lambda: service

    response = client.post(
        "/api/v1/mobile/sync",
        json={
            "client_batch_id": str(uuid.uuid4()),
            "operations": [],
            "bad_field": "not-allowed",
        },
    )
    body = response.json()

    assert response.status_code == 422
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"

