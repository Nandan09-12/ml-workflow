import uuid
from datetime import UTC, datetime
from typing import Any

import pytest

from app.core.enums import AccountStatus, RequestedRole
from app.core.errors import AppError
from app.models.app_user import AppUser
from app.schemas.mobile import MobileSyncRequest
from app.services.mobile_service import MobileService


class FakeMobileRepository:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.user = AppUser(
            id=uuid.uuid4(),
            auth_user_id=uuid.uuid4(),
            full_name="Mobile Tester",
            email="mobile@example.com",
            requested_role=RequestedRole.DRIVE_TESTER,
            approved_role=RequestedRole.DRIVE_TESTER,
            account_status=AccountStatus.APPROVED,
            approved_at=now,
            approved_by_user_id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
        )

    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None:
        if auth_user_id == self.user.auth_user_id:
            return self.user
        return None


def _auth_payload(user: AppUser) -> dict[str, Any]:
    return {"sub": str(user.auth_user_id), "email": user.email}


async def test_mobile_bootstrap_returns_user_and_reference_data() -> None:
    repo = FakeMobileRepository()
    service = MobileService(repository=repo)

    result = await service.get_bootstrap_payload(_auth_payload(repo.user))

    assert result.contract_version == "v1"
    assert result.user.email == "mobile@example.com"
    assert "NORTHEAST" in result.reference_data.zones
    assert "AM" in result.reference_data.shifts
    assert result.offline_sync_enabled is False


async def test_mobile_bootstrap_requires_existing_app_user() -> None:
    repo = FakeMobileRepository()
    service = MobileService(repository=repo)

    with pytest.raises(AppError) as exc:
        await service.get_bootstrap_payload({"sub": str(uuid.uuid4()), "email": "missing@example.com"})

    assert exc.value.code.value == "NOT_FOUND"
    assert exc.value.status_code == 404


async def test_mobile_sync_returns_placeholder_contract() -> None:
    repo = FakeMobileRepository()
    service = MobileService(repository=repo)

    result = await service.sync_placeholder(
        _auth_payload(repo.user),
        MobileSyncRequest(
            client_batch_id=uuid.uuid4(),
            device_id="pixel-1",
            operations=[{"entity": "submission", "action": "upsert"}],
        ),
    )

    assert result.status == "NOT_IMPLEMENTED"
    assert result.accepted is False
    assert result.received_operations_count == 1
    assert result.processed_operations_count == 0


async def test_mobile_service_rejects_invalid_auth_subject() -> None:
    repo = FakeMobileRepository()
    service = MobileService(repository=repo)

    with pytest.raises(AppError) as exc:
        await service.get_bootstrap_payload({"sub": "bad-uuid", "email": "mobile@example.com"})

    assert exc.value.code.value == "UNAUTHORIZED"
    assert exc.value.status_code == 401


# ---------------------------------------------------------------------------
# Wave 2 RED tests — item 55: mobile bootstrap includes workorder_statuses
# ---------------------------------------------------------------------------


async def test_mobile_bootstrap_includes_workorder_statuses() -> None:
    """Bootstrap reference_data must include workorder_statuses list."""
    from app.core.enums import WorkorderStatus
    repo = FakeMobileRepository()
    service = MobileService(repository=repo)

    payload = await service.get_bootstrap_payload(
        {"sub": str(repo.user.auth_user_id), "email": repo.user.email}
    )

    assert hasattr(payload.reference_data, "workorder_statuses")
    statuses = payload.reference_data.workorder_statuses
    assert isinstance(statuses, list)
    assert WorkorderStatus.ACTIVE.value in statuses
    assert WorkorderStatus.COMPLETED.value in statuses

