import uuid
from typing import Any

import pytest

from app.api.v1.routers.me import get_me_service
from app.core.enums import AccountStatus, RequestedRole
from app.core.security import get_current_auth_payload
from app.services.me_service import MeUserView


class FakeMeService:
    def __init__(self, me_user: MeUserView) -> None:
        self.me_user = me_user

    async def get_me(self, _: dict[str, Any]) -> MeUserView:
        return self.me_user

    async def bootstrap(self, __: dict[str, Any], ___: Any) -> tuple[MeUserView, bool]:
        return self.me_user, True

    async def update_me(self, _: dict[str, Any], __: Any) -> MeUserView:
        return self.me_user


@pytest.fixture
def me_user() -> MeUserView:
    return MeUserView(
        id=uuid.uuid4(),
        auth_user_id=uuid.uuid4(),
        full_name="Jane Doe",
        email="jane@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=None,
        account_status=AccountStatus.PENDING_APPROVAL,
        approved_at=None,
        approved_by_user_id=None,
    )


def test_get_me_unauthenticated_returns_enveloped_401(client: Any) -> None:
    response = client.get("/api/v1/me")
    body = response.json()

    assert response.status_code == 401
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert "request_id" in body["meta"]


def test_get_me_success_response_envelope(
    client: Any,
    auth_payload_drive_tester: dict[str, Any],
    me_user: MeUserView,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_drive_tester
    app.dependency_overrides[get_me_service] = lambda: FakeMeService(me_user)

    response = client.get("/api/v1/me")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["full_name"] == "Jane Doe"
    assert body["data"]["requested_role"] == "DRIVE_TESTER"
    assert "request_id" in body["meta"]


def test_bootstrap_validation_error_is_enveloped_422(
    client: Any,
    auth_payload_admin: dict[str, Any],
    me_user: MeUserView,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_me_service] = lambda: FakeMeService(me_user)

    response = client.post(
        "/api/v1/me/bootstrap",
        json={"full_name": "Only Name"},
    )
    body = response.json()

    assert response.status_code == 422
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert isinstance(body["error"]["details"], list)
    assert "request_id" in body["meta"]


def test_patch_me_rejects_unknown_fields_with_422(
    client: Any,
    auth_payload_drive_tester: dict[str, Any],
    me_user: MeUserView,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_drive_tester
    app.dependency_overrides[get_me_service] = lambda: FakeMeService(me_user)

    response = client.patch(
        "/api/v1/me",
        json={"full_name": "New Name", "email": "not-allowed@example.com"},
    )
    body = response.json()

    assert response.status_code == 422
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "request_id" in body["meta"]
