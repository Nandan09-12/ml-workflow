import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.enums import AccountStatus, ApprovalDecision, RequestedRole
from app.core.errors import AppError
from app.models.app_user import AppUser
from app.models.user_approval_audit import UserApprovalAudit
from app.repositories.admin_users_repository import AdminUsersRepository
from app.repositories.me_repository import MeRepository
from app.schemas.me import BootstrapRequest, UpdateMeRequest
from app.services.admin_users_service import AdminUsersService
from app.services.me_service import MeService

pytestmark = pytest.mark.integration


def _settings(*, bootstrap_admin_emails: str = "root@example.com") -> Settings:
    return Settings(
        bootstrap_admin_emails=bootstrap_admin_emails,
        supabase_url="https://example.supabase.co",
        database_url="postgresql+asyncpg://postgres:postgres@localhost/postgres",
    )


def _build_user(
    *,
    email: str,
    requested_role: RequestedRole,
    approved_role: RequestedRole | None,
    account_status: AccountStatus,
) -> AppUser:
    now = datetime.now(UTC)
    return AppUser(
        id=uuid.uuid4(),
        auth_user_id=uuid.uuid4(),
        full_name=email.split("@")[0],
        email=email,
        requested_role=requested_role,
        approved_role=approved_role,
        account_status=account_status,
        approved_at=now if account_status == AccountStatus.APPROVED else None,
        approved_by_user_id=None,
        created_at=now,
        updated_at=now,
    )


def _auth_payload(user: AppUser) -> dict[str, str]:
    return {"sub": str(user.auth_user_id), "email": user.email}


async def test_me_bootstrap_auto_approves_first_allowlisted_admin(
    integration_session: AsyncSession,
) -> None:
    service = MeService(
        repository=MeRepository(integration_session),
        settings=_settings(bootstrap_admin_emails="root@example.com"),
    )

    user, created = await service.bootstrap(
        {"sub": str(uuid.uuid4()), "email": "Root@Example.com"},
        BootstrapRequest(full_name="First Admin", requested_role=RequestedRole.ADMIN),
    )

    assert created is True
    assert user.account_status == AccountStatus.APPROVED
    assert user.approved_role == RequestedRole.ADMIN

    saved_user = (
        await integration_session.execute(select(AppUser).where(AppUser.id == user.id))
    ).scalar_one()
    assert saved_user.account_status == AccountStatus.APPROVED

    audits = (
        await integration_session.execute(
            select(UserApprovalAudit).where(UserApprovalAudit.user_id == user.id)
        )
    ).scalars().all()
    assert len(audits) == 1
    assert audits[0].decision == ApprovalDecision.APPROVED
    assert audits[0].review_notes == "BOOTSTRAP_ADMIN_AUTO_APPROVED"


async def test_me_bootstrap_second_admin_is_pending_when_admin_exists(
    integration_session: AsyncSession,
) -> None:
    integration_session.add(
        _build_user(
            email="existing-admin@example.com",
            requested_role=RequestedRole.ADMIN,
            approved_role=RequestedRole.ADMIN,
            account_status=AccountStatus.APPROVED,
        )
    )
    await integration_session.commit()

    service = MeService(
        repository=MeRepository(integration_session),
        settings=_settings(bootstrap_admin_emails="root@example.com,new-admin@example.com"),
    )

    user, created = await service.bootstrap(
        {"sub": str(uuid.uuid4()), "email": "new-admin@example.com"},
        BootstrapRequest(full_name="Pending Admin", requested_role=RequestedRole.ADMIN),
    )

    assert created is True
    assert user.account_status == AccountStatus.PENDING_APPROVAL
    assert user.approved_role is None

    audits = (
        await integration_session.execute(
            select(UserApprovalAudit).where(UserApprovalAudit.user_id == user.id)
        )
    ).scalars().all()
    assert audits == []


async def test_me_update_persists_full_name(
    integration_session: AsyncSession,
) -> None:
    service = MeService(
        repository=MeRepository(integration_session),
        settings=_settings(),
    )
    auth_payload = {"sub": str(uuid.uuid4()), "email": "tester@example.com"}

    created, _ = await service.bootstrap(
        auth_payload,
        BootstrapRequest(full_name="Old Name", requested_role=RequestedRole.DRIVE_TESTER),
    )

    updated = await service.update_me(auth_payload, UpdateMeRequest(full_name="New Name"))

    assert updated.id == created.id
    assert updated.full_name == "New Name"
    saved = (
        await integration_session.execute(select(AppUser).where(AppUser.id == created.id))
    ).scalar_one()
    assert saved.full_name == "New Name"


async def test_admin_approve_user_persists_state_and_history(
    integration_session: AsyncSession,
) -> None:
    admin = _build_user(
        email="admin@example.com",
        requested_role=RequestedRole.ADMIN,
        approved_role=RequestedRole.ADMIN,
        account_status=AccountStatus.APPROVED,
    )
    pending = _build_user(
        email="pending@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=None,
        account_status=AccountStatus.PENDING_APPROVAL,
    )
    integration_session.add_all([admin, pending])
    await integration_session.commit()

    service = AdminUsersService(repository=AdminUsersRepository(integration_session))

    approved = await service.approve_user(_auth_payload(admin), pending.id)

    assert approved.account_status == AccountStatus.APPROVED
    assert approved.approved_role == RequestedRole.DRIVE_TESTER
    assert approved.approved_by_user_id == admin.id

    history = await service.get_approval_history(_auth_payload(admin), pending.id)
    assert len(history) == 1
    assert history[0].decision == ApprovalDecision.APPROVED
    assert history[0].reviewed_by_user_id == admin.id


async def test_admin_list_pending_requires_admin_role(
    integration_session: AsyncSession,
) -> None:
    tester = _build_user(
        email="tester@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    integration_session.add(tester)
    await integration_session.commit()

    service = AdminUsersService(repository=AdminUsersRepository(integration_session))
    with pytest.raises(AppError) as exc:
        await service.list_pending_users(_auth_payload(tester))

    assert exc.value.code.value == "ADMIN_ONLY"
    assert exc.value.status_code == 403


async def test_admin_suspend_approved_user_persists_state(
    integration_session: AsyncSession,
) -> None:
    admin = _build_user(
        email="admin2@example.com",
        requested_role=RequestedRole.ADMIN,
        approved_role=RequestedRole.ADMIN,
        account_status=AccountStatus.APPROVED,
    )
    target = _build_user(
        email="target@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    integration_session.add_all([admin, target])
    await integration_session.commit()

    service = AdminUsersService(repository=AdminUsersRepository(integration_session))
    suspended = await service.suspend_user(_auth_payload(admin), target.id)

    assert suspended.account_status == AccountStatus.SUSPENDED
    saved = (
        await integration_session.execute(select(AppUser).where(AppUser.id == target.id))
    ).scalar_one()
    assert saved.account_status == AccountStatus.SUSPENDED
