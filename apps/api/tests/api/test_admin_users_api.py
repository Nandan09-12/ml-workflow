import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest

from app.api.v1.routers.admin_users import get_admin_users_service
from app.core.enums import AccountStatus, ApprovalDecision, RequestedRole
from app.core.errors import AppError, ErrorCode
from app.core.security import get_current_auth_payload


@dataclass(frozen=True)
class FakeAdminUserView:
    id: uuid.UUID
    auth_user_id: uuid.UUID
    full_name: str
    email: str
    requested_role: RequestedRole
    approved_role: RequestedRole | None
    account_status: AccountStatus
    approved_at: datetime | None
    approved_by_user_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class FakeApprovalAuditView:
    id: uuid.UUID
    user_id: uuid.UUID
    requested_role: RequestedRole
    decision: ApprovalDecision
    reviewed_by_user_id: uuid.UUID | None
    reviewed_at: datetime | None
    review_notes: str | None
    created_at: datetime


class FakeAdminUsersService:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.admin_user = FakeAdminUserView(
            id=uuid.uuid4(),
            auth_user_id=uuid.uuid4(),
            full_name="Admin User",
            email="admin@example.com",
            requested_role=RequestedRole.ADMIN,
            approved_role=RequestedRole.ADMIN,
            account_status=AccountStatus.APPROVED,
            approved_at=now,
            approved_by_user_id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
        )
        self.pending_user = FakeAdminUserView(
            id=uuid.uuid4(),
            auth_user_id=uuid.uuid4(),
            full_name="Pending User",
            email="pending@example.com",
            requested_role=RequestedRole.DRIVE_TESTER,
            approved_role=None,
            account_status=AccountStatus.PENDING_APPROVAL,
            approved_at=None,
            approved_by_user_id=None,
            created_at=now,
            updated_at=now,
        )
        self.history = [
            FakeApprovalAuditView(
                id=uuid.uuid4(),
                user_id=self.pending_user.id,
                requested_role=RequestedRole.DRIVE_TESTER,
                decision=ApprovalDecision.REJECTED,
                reviewed_by_user_id=self.admin_user.id,
                reviewed_at=now,
                review_notes="Insufficient info",
                created_at=now,
            )
        ]
        self.raise_admin_only = False

    async def list_pending_users(
        self,
        _: dict[str, Any],
        *,
        requested_role: RequestedRole | None = None,
    ) -> list[FakeAdminUserView]:
        if self.raise_admin_only:
            raise AppError(ErrorCode.ADMIN_ONLY, "Admin access required.", status_code=403)
        if requested_role is None:
            return [self.pending_user]
        if self.pending_user.requested_role == requested_role:
            return [self.pending_user]
        return []

    async def list_users(
        self,
        _: dict[str, Any],
        *,
        requested_role: RequestedRole | None = None,
        account_status: AccountStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[FakeAdminUserView], int]:
        if self.raise_admin_only:
            raise AppError(ErrorCode.ADMIN_ONLY, "Admin access required.", status_code=403)
        users = [self.admin_user, self.pending_user]
        if requested_role is not None:
            users = [user for user in users if user.requested_role == requested_role]
        if account_status is not None:
            users = [user for user in users if user.account_status == account_status]
        start = (page - 1) * page_size
        return users[start : start + page_size], len(users)

    async def get_user(self, _: dict[str, Any], user_id: uuid.UUID) -> FakeAdminUserView:
        if self.raise_admin_only:
            raise AppError(ErrorCode.ADMIN_ONLY, "Admin access required.", status_code=403)
        if user_id == self.pending_user.id:
            return self.pending_user
        return self.admin_user

    async def approve_user(self, _: dict[str, Any], user_id: uuid.UUID) -> FakeAdminUserView:
        if self.raise_admin_only:
            raise AppError(ErrorCode.ADMIN_ONLY, "Admin access required.", status_code=403)
        if user_id == self.pending_user.id:
            now = datetime.now(UTC)
            self.pending_user = FakeAdminUserView(
                **{
                    **self.pending_user.__dict__,
                    "account_status": AccountStatus.APPROVED,
                    "approved_role": self.pending_user.requested_role,
                    "approved_at": now,
                    "updated_at": now,
                }
            )
        return self.pending_user

    async def reject_user(self, _: dict[str, Any], user_id: uuid.UUID) -> FakeAdminUserView:
        if self.raise_admin_only:
            raise AppError(ErrorCode.ADMIN_ONLY, "Admin access required.", status_code=403)
        if user_id == self.pending_user.id:
            now = datetime.now(UTC)
            self.pending_user = FakeAdminUserView(
                **{
                    **self.pending_user.__dict__,
                    "account_status": AccountStatus.REJECTED,
                    "approved_role": None,
                    "approved_at": None,
                    "updated_at": now,
                }
            )
        return self.pending_user

    async def suspend_user(self, _: dict[str, Any], user_id: uuid.UUID) -> FakeAdminUserView:
        if self.raise_admin_only:
            raise AppError(ErrorCode.ADMIN_ONLY, "Admin access required.", status_code=403)
        if user_id == self.admin_user.id:
            now = datetime.now(UTC)
            self.admin_user = FakeAdminUserView(
                **{
                    **self.admin_user.__dict__,
                    "account_status": AccountStatus.SUSPENDED,
                    "updated_at": now,
                }
            )
            return self.admin_user
        return self.pending_user

    async def get_approval_history(
        self,
        _: dict[str, Any],
        user_id: uuid.UUID,
    ) -> list[FakeApprovalAuditView]:
        if self.raise_admin_only:
            raise AppError(ErrorCode.ADMIN_ONLY, "Admin access required.", status_code=403)
        if user_id == self.pending_user.id:
            return self.history
        return []


@pytest.fixture
def admin_users_service() -> FakeAdminUsersService:
    return FakeAdminUsersService()


def test_admin_users_pending_requires_auth(client: Any) -> None:
    response = client.get("/api/v1/admin/users/pending")
    body = response.json()

    assert response.status_code == 401
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert "request_id" in body["meta"]


def test_admin_users_pending_success_envelope(
    client: Any,
    auth_payload_admin: dict[str, Any],
    admin_users_service: FakeAdminUsersService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_admin_users_service] = lambda: admin_users_service

    response = client.get("/api/v1/admin/users/pending")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert len(body["data"]["items"]) == 1
    assert body["data"]["items"][0]["account_status"] == "PENDING_APPROVAL"
    assert "request_id" in body["meta"]


def test_admin_users_list_enforces_admin_only_error_envelope(
    client: Any,
    auth_payload_drive_tester: dict[str, Any],
    admin_users_service: FakeAdminUsersService,
) -> None:
    admin_users_service.raise_admin_only = True
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_drive_tester
    app.dependency_overrides[get_admin_users_service] = lambda: admin_users_service

    response = client.get("/api/v1/admin/users")
    body = response.json()

    assert response.status_code == 403
    assert body["success"] is False
    assert body["error"]["code"] == "ADMIN_ONLY"
    assert "request_id" in body["meta"]


def test_admin_users_detail_invalid_uuid_returns_enveloped_422(
    client: Any,
    auth_payload_admin: dict[str, Any],
    admin_users_service: FakeAdminUsersService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_admin_users_service] = lambda: admin_users_service

    response = client.get("/api/v1/admin/users/not-a-uuid")
    body = response.json()

    assert response.status_code == 422
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert isinstance(body["error"]["details"], list)
    assert "request_id" in body["meta"]


def test_admin_users_approve_endpoint_success(
    client: Any,
    auth_payload_admin: dict[str, Any],
    admin_users_service: FakeAdminUsersService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_admin_users_service] = lambda: admin_users_service

    response = client.post(f"/api/v1/admin/users/{admin_users_service.pending_user.id}/approve")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["account_status"] == "APPROVED"
    assert body["data"]["approved_role"] == "DRIVE_TESTER"


def test_admin_users_reject_endpoint_success(
    client: Any,
    auth_payload_admin: dict[str, Any],
    admin_users_service: FakeAdminUsersService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_admin_users_service] = lambda: admin_users_service

    response = client.post(f"/api/v1/admin/users/{admin_users_service.pending_user.id}/reject")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["account_status"] == "REJECTED"


def test_admin_users_suspend_endpoint_success(
    client: Any,
    auth_payload_admin: dict[str, Any],
    admin_users_service: FakeAdminUsersService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_admin_users_service] = lambda: admin_users_service

    response = client.post(f"/api/v1/admin/users/{admin_users_service.admin_user.id}/suspend")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["account_status"] == "SUSPENDED"


def test_admin_users_approval_history_success(
    client: Any,
    auth_payload_admin: dict[str, Any],
    admin_users_service: FakeAdminUsersService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_admin
    app.dependency_overrides[get_admin_users_service] = lambda: admin_users_service

    response = client.get(
        f"/api/v1/admin/users/{admin_users_service.pending_user.id}/approval-history"
    )
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert len(body["data"]["items"]) == 1
    assert body["data"]["items"][0]["decision"] == "REJECTED"
