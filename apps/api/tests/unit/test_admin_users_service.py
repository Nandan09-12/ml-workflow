import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

import pytest

from app.core.enums import AccountStatus, ApprovalDecision, RequestedRole
from app.core.errors import AppError
from app.models.app_user import AppUser
from app.models.user_approval_audit import UserApprovalAudit
from app.services.admin_users_service import AdminUsersService


class FakeAdminUsersRepository:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.admin_user = AppUser(
            id=uuid.uuid4(),
            auth_user_id=uuid.uuid4(),
            full_name="Admin",
            email="admin@example.com",
            requested_role=RequestedRole.ADMIN,
            approved_role=RequestedRole.ADMIN,
            account_status=AccountStatus.APPROVED,
            approved_at=now,
            approved_by_user_id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
        )
        self.tester_user = AppUser(
            id=uuid.uuid4(),
            auth_user_id=uuid.uuid4(),
            full_name="Tester",
            email="tester@example.com",
            requested_role=RequestedRole.DRIVE_TESTER,
            approved_role=RequestedRole.DRIVE_TESTER,
            account_status=AccountStatus.APPROVED,
            approved_at=now,
            approved_by_user_id=self.admin_user.id,
            created_at=now,
            updated_at=now,
        )
        self.pending_user = AppUser(
            id=uuid.uuid4(),
            auth_user_id=uuid.uuid4(),
            full_name="Pending",
            email="pending@example.com",
            requested_role=RequestedRole.DRIVE_TESTER,
            approved_role=None,
            account_status=AccountStatus.PENDING_APPROVAL,
            approved_at=None,
            approved_by_user_id=None,
            created_at=now,
            updated_at=now,
        )
        self.rejected_user = AppUser(
            id=uuid.uuid4(),
            auth_user_id=uuid.uuid4(),
            full_name="Rejected",
            email="rejected@example.com",
            requested_role=RequestedRole.ADMIN,
            approved_role=None,
            account_status=AccountStatus.REJECTED,
            approved_at=None,
            approved_by_user_id=None,
            created_at=now,
            updated_at=now,
        )
        self.users = [
            self.admin_user,
            self.tester_user,
            self.pending_user,
            self.rejected_user,
        ]
        self.approval_audits: list[UserApprovalAudit] = []
        self.transaction_entries = 0

    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None:
        return next((user for user in self.users if user.auth_user_id == auth_user_id), None)

    async def list_pending_users(
        self,
        *,
        requested_role: RequestedRole | None = None,
    ) -> list[AppUser]:
        users = [u for u in self.users if u.account_status == AccountStatus.PENDING_APPROVAL]
        if requested_role is not None:
            users = [u for u in users if u.requested_role == requested_role]
        return users

    async def list_users(
        self,
        *,
        requested_role: RequestedRole | None = None,
        account_status: AccountStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[AppUser], int]:
        users = list(self.users)
        if requested_role is not None:
            users = [u for u in users if u.requested_role == requested_role]
        if account_status is not None:
            users = [u for u in users if u.account_status == account_status]
        total = len(users)
        return users[offset : offset + limit], total

    async def get_by_id(self, user_id: uuid.UUID) -> AppUser | None:
        return next((user for user in self.users if user.id == user_id), None)

    async def save_user(self, user: AppUser) -> AppUser:
        return user

    async def create_approval_audit(self, audit: UserApprovalAudit) -> UserApprovalAudit:
        self.approval_audits.append(audit)
        return audit

    async def get_approval_history(self, user_id: uuid.UUID) -> list[UserApprovalAudit]:
        return [entry for entry in self.approval_audits if entry.user_id == user_id]

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        self.transaction_entries += 1
        yield


def _auth_payload(user: AppUser) -> dict[str, Any]:
    return {"sub": str(user.auth_user_id), "email": user.email}


async def test_pending_list_requires_admin_role() -> None:
    repo = FakeAdminUsersRepository()
    service = AdminUsersService(repository=repo)

    with pytest.raises(AppError) as exc:
        await service.list_pending_users(_auth_payload(repo.tester_user))

    assert exc.value.code.value == "ADMIN_ONLY"
    assert exc.value.status_code == 403


async def test_pending_list_requires_approved_account() -> None:
    repo = FakeAdminUsersRepository()
    service = AdminUsersService(repository=repo)

    with pytest.raises(AppError) as exc:
        await service.list_pending_users(_auth_payload(repo.rejected_user))

    assert exc.value.code.value == "ACCOUNT_NOT_APPROVED"
    assert exc.value.status_code == 403


async def test_list_pending_returns_only_pending_users() -> None:
    repo = FakeAdminUsersRepository()
    service = AdminUsersService(repository=repo)

    results = await service.list_pending_users(_auth_payload(repo.admin_user))

    assert len(results) == 1
    assert results[0].id == repo.pending_user.id


async def test_list_users_respects_pagination_defaults() -> None:
    repo = FakeAdminUsersRepository()
    service = AdminUsersService(repository=repo)

    results, total = await service.list_users(
        _auth_payload(repo.admin_user),
        page=1,
        page_size=20,
    )

    assert total == 4
    assert len(results) == 4


async def test_approve_pending_user_updates_state_and_writes_audit() -> None:
    repo = FakeAdminUsersRepository()
    service = AdminUsersService(repository=repo)

    approved = await service.approve_user(
        _auth_payload(repo.admin_user),
        repo.pending_user.id,
    )

    assert approved.account_status == AccountStatus.APPROVED
    assert approved.approved_role == RequestedRole.DRIVE_TESTER
    assert approved.approved_by_user_id == repo.admin_user.id
    assert approved.approved_at is not None
    assert repo.transaction_entries == 1
    assert len(repo.approval_audits) == 1
    assert repo.approval_audits[0].decision == ApprovalDecision.APPROVED


async def test_reject_pending_user_updates_state_and_writes_audit() -> None:
    repo = FakeAdminUsersRepository()
    service = AdminUsersService(repository=repo)

    rejected = await service.reject_user(
        _auth_payload(repo.admin_user),
        repo.pending_user.id,
    )

    assert rejected.account_status == AccountStatus.REJECTED
    assert rejected.approved_role is None
    assert rejected.approved_at is None
    assert repo.transaction_entries == 1
    assert len(repo.approval_audits) == 1
    assert repo.approval_audits[0].decision == ApprovalDecision.REJECTED


async def test_approve_requires_pending_status() -> None:
    repo = FakeAdminUsersRepository()
    service = AdminUsersService(repository=repo)

    with pytest.raises(AppError) as exc:
        await service.approve_user(_auth_payload(repo.admin_user), repo.tester_user.id)

    assert exc.value.code.value == "INVALID_ACCOUNT_STATE"
    assert exc.value.status_code == 400


async def test_reject_requires_pending_status() -> None:
    repo = FakeAdminUsersRepository()
    service = AdminUsersService(repository=repo)

    with pytest.raises(AppError) as exc:
        await service.reject_user(_auth_payload(repo.admin_user), repo.tester_user.id)

    assert exc.value.code.value == "INVALID_ACCOUNT_STATE"
    assert exc.value.status_code == 400


async def test_suspend_approved_user_sets_suspended_status() -> None:
    repo = FakeAdminUsersRepository()
    service = AdminUsersService(repository=repo)

    suspended = await service.suspend_user(
        _auth_payload(repo.admin_user),
        repo.tester_user.id,
    )

    assert suspended.account_status == AccountStatus.SUSPENDED
    assert repo.transaction_entries == 1


async def test_suspend_requires_approved_status() -> None:
    repo = FakeAdminUsersRepository()
    service = AdminUsersService(repository=repo)

    with pytest.raises(AppError) as exc:
        await service.suspend_user(_auth_payload(repo.admin_user), repo.pending_user.id)

    assert exc.value.code.value == "INVALID_ACCOUNT_STATE"
    assert exc.value.status_code == 400


async def test_get_approval_history_returns_entries() -> None:
    repo = FakeAdminUsersRepository()
    service = AdminUsersService(repository=repo)

    await service.approve_user(_auth_payload(repo.admin_user), repo.pending_user.id)
    history = await service.get_approval_history(
        _auth_payload(repo.admin_user),
        repo.pending_user.id,
    )

    assert len(history) == 1
    assert history[0].decision == ApprovalDecision.APPROVED
