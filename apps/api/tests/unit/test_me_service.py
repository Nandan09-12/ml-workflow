import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from app.core.config import Settings
from app.core.enums import AccountStatus, ApprovalDecision, RequestedRole
from app.models.app_user import AppUser
from app.models.user_approval_audit import UserApprovalAudit
from app.schemas.me import BootstrapRequest, UpdateMeRequest
from app.services.me_service import MeService


class FakeMeRepository:
    def __init__(self) -> None:
        self.users: list[AppUser] = []
        self.approval_audits: list[UserApprovalAudit] = []
        self.transaction_entries = 0

    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None:
        for user in self.users:
            if user.auth_user_id == auth_user_id:
                return user
        return None

    async def count_approved_admins(self) -> int:
        return sum(
            1
            for user in self.users
            if user.account_status == AccountStatus.APPROVED
            and user.approved_role == RequestedRole.ADMIN
        )

    async def create_user(self, user: AppUser) -> AppUser:
        self.users.append(user)
        return user

    async def create_approval_audit(self, audit: UserApprovalAudit) -> UserApprovalAudit:
        self.approval_audits.append(audit)
        return audit

    async def acquire_bootstrap_lock(self) -> None:
        return None

    async def update_full_name(self, user: AppUser, full_name: str) -> AppUser:
        user.full_name = full_name
        return user

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        self.transaction_entries += 1
        yield


def _settings() -> Settings:
    return Settings(
        bootstrap_admin_emails="  ROOT@example.com, other@example.com ",
        supabase_url="https://example.supabase.co",
        database_url="postgresql+asyncpg://postgres:postgres@localhost/postgres",
    )


def _auth_payload(email: str = "root@example.com") -> dict[str, Any]:
    return {"sub": str(uuid.uuid4()), "email": email}


async def test_bootstrap_auto_approves_first_allowlisted_admin() -> None:
    repo = FakeMeRepository()
    service = MeService(repository=repo, settings=_settings())

    user, created = await service.bootstrap(
        _auth_payload("Root@Example.com"),
        BootstrapRequest(full_name="First Admin", requested_role=RequestedRole.ADMIN),
    )

    assert created is True
    assert user.account_status == AccountStatus.APPROVED
    assert user.approved_role == RequestedRole.ADMIN
    assert user.approved_by_user_id is None
    assert user.approved_at is not None
    assert len(repo.approval_audits) == 1
    assert repo.approval_audits[0].decision == ApprovalDecision.APPROVED
    assert repo.approval_audits[0].reviewed_by_user_id is None
    assert repo.approval_audits[0].review_notes == "BOOTSTRAP_ADMIN_AUTO_APPROVED"
    assert repo.transaction_entries == 1


async def test_bootstrap_non_admin_when_no_approved_admin_stays_pending() -> None:
    repo = FakeMeRepository()
    service = MeService(repository=repo, settings=_settings())

    user, created = await service.bootstrap(
        _auth_payload("allowlisted@example.com"),
        BootstrapRequest(full_name="Drive Tester", requested_role=RequestedRole.DRIVE_TESTER),
    )

    assert created is True
    assert user.account_status == AccountStatus.PENDING_APPROVAL
    assert user.approved_role is None
    assert user.approved_at is None
    assert len(repo.approval_audits) == 0


async def test_bootstrap_admin_not_allowlisted_stays_pending() -> None:
    repo = FakeMeRepository()
    service = MeService(repository=repo, settings=_settings())

    user, created = await service.bootstrap(
        _auth_payload("not-allowed@example.com"),
        BootstrapRequest(full_name="Pending Admin", requested_role=RequestedRole.ADMIN),
    )

    assert created is True
    assert user.account_status == AccountStatus.PENDING_APPROVAL
    assert user.approved_role is None
    assert user.approved_at is None
    assert len(repo.approval_audits) == 0


async def test_bootstrap_is_idempotent_by_auth_user_id() -> None:
    repo = FakeMeRepository()
    service = MeService(repository=repo, settings=_settings())
    payload = _auth_payload("root@example.com")
    request = BootstrapRequest(full_name="First", requested_role=RequestedRole.ADMIN)

    first_user, first_created = await service.bootstrap(payload, request)
    second_user, second_created = await service.bootstrap(payload, request)

    assert first_created is True
    assert second_created is False
    assert first_user.id == second_user.id
    assert len(repo.users) == 1
    assert len(repo.approval_audits) == 1


async def test_update_me_updates_full_name_only() -> None:
    repo = FakeMeRepository()
    service = MeService(repository=repo, settings=_settings())
    payload = _auth_payload("tester@example.com")

    user, _ = await service.bootstrap(
        payload,
        BootstrapRequest(full_name="Old Name", requested_role=RequestedRole.DRIVE_TESTER),
    )

    updated = await service.update_me(payload, UpdateMeRequest(full_name="New Name"))

    assert updated.id == user.id
    assert updated.full_name == "New Name"
