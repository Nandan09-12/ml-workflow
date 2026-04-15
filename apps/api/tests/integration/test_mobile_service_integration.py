import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AccountStatus, RequestedRole
from app.core.errors import AppError
from app.models.app_user import AppUser
from app.repositories.mobile_repository import MobileRepository
from app.schemas.mobile import MobileSyncRequest
from app.services.mobile_service import MobileService

pytestmark = pytest.mark.integration


def _build_user(email: str) -> AppUser:
    now = datetime.now(UTC)
    return AppUser(
        id=uuid.uuid4(),
        auth_user_id=uuid.uuid4(),
        full_name="Mobile Integration User",
        email=email,
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
        approved_at=now,
        approved_by_user_id=None,
        created_at=now,
        updated_at=now,
    )


def _auth_payload(user: AppUser) -> dict[str, str]:
    return {"sub": str(user.auth_user_id), "email": user.email}


async def test_mobile_bootstrap_reads_user_from_database(
    integration_session: AsyncSession,
) -> None:
    user = _build_user("mobile-it@example.com")
    integration_session.add(user)
    await integration_session.commit()

    service = MobileService(repository=MobileRepository(integration_session))
    payload = await service.get_bootstrap_payload(_auth_payload(user))

    assert payload.user.email == "mobile-it@example.com"
    assert payload.contract_version == "v1"
    assert payload.offline_sync_enabled is False
    assert "NORTHEAST" in payload.reference_data.zones


async def test_mobile_sync_placeholder_returns_contract_shape(
    integration_session: AsyncSession,
) -> None:
    user = _build_user("mobile-sync-it@example.com")
    integration_session.add(user)
    await integration_session.commit()

    service = MobileService(repository=MobileRepository(integration_session))
    result = await service.sync_placeholder(
        _auth_payload(user),
        MobileSyncRequest(
            client_batch_id=uuid.uuid4(),
            device_id="integration-device",
            operations=[{"entity": "submission", "action": "upsert"}],
        ),
    )

    assert result.status == "NOT_IMPLEMENTED"
    assert result.accepted is False
    assert result.received_operations_count == 1
    assert result.processed_operations_count == 0
    assert result.rejected_operations_count == 1


async def test_mobile_bootstrap_returns_not_found_for_missing_user(
    integration_session: AsyncSession,
) -> None:
    service = MobileService(repository=MobileRepository(integration_session))

    with pytest.raises(AppError) as exc:
        await service.get_bootstrap_payload(
            {"sub": str(uuid.uuid4()), "email": "missing@example.com"}
        )

    assert exc.value.code.value == "NOT_FOUND"
    assert exc.value.status_code == 404

