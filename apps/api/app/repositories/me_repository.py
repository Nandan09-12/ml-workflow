import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AccountStatus, RequestedRole
from app.models.app_user import AppUser
from app.models.user_approval_audit import UserApprovalAudit


class MeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None:
        query = select(AppUser).where(AppUser.auth_user_id == auth_user_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def count_approved_admins(self) -> int:
        query = (
            select(func.count(AppUser.id))
            .where(AppUser.account_status == AccountStatus.APPROVED)
            .where(AppUser.approved_role == RequestedRole.ADMIN)
        )
        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def create_user(self, user: AppUser) -> AppUser:
        self._session.add(user)
        await self._session.flush()
        return user

    async def create_approval_audit(self, audit: UserApprovalAudit) -> UserApprovalAudit:
        self._session.add(audit)
        await self._session.flush()
        return audit

    async def acquire_bootstrap_lock(self) -> None:
        # Transaction-scoped advisory lock to avoid concurrent first-admin bootstrap races.
        await self._session.execute(text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": 919001})

    async def update_full_name(self, user: AppUser, full_name: str) -> AppUser:
        user.full_name = full_name
        user.updated_at = datetime.now(UTC)
        await self._session.flush()
        return user

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        if self._session.in_transaction():
            try:
                yield
                await self._session.commit()
            except Exception:
                await self._session.rollback()
                raise
            return

        async with self._session.begin():
            yield
