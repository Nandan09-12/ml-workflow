import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AccountStatus, RequestedRole
from app.models.app_user import AppUser
from app.models.user_approval_audit import UserApprovalAudit


class AdminUsersRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None:
        query = select(AppUser).where(AppUser.auth_user_id == auth_user_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def list_pending_users(
        self,
        *,
        requested_role: RequestedRole | None = None,
    ) -> list[AppUser]:
        query = select(AppUser).where(AppUser.account_status == AccountStatus.PENDING_APPROVAL)
        if requested_role is not None:
            query = query.where(AppUser.requested_role == requested_role)
        query = query.order_by(AppUser.created_at.asc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def list_users(
        self,
        *,
        requested_role: RequestedRole | None = None,
        account_status: AccountStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[AppUser], int]:
        base_query = select(AppUser)
        count_query = select(func.count(AppUser.id))
        if requested_role is not None:
            base_query = base_query.where(AppUser.requested_role == requested_role)
            count_query = count_query.where(AppUser.requested_role == requested_role)
        if account_status is not None:
            base_query = base_query.where(AppUser.account_status == account_status)
            count_query = count_query.where(AppUser.account_status == account_status)

        users_query = base_query.order_by(AppUser.created_at.desc()).offset(offset).limit(limit)
        users_result = await self._session.execute(users_query)
        total_result = await self._session.execute(count_query)
        users = list(users_result.scalars().all())
        total = int(total_result.scalar_one())
        return users, total

    async def get_by_id(self, user_id: uuid.UUID) -> AppUser | None:
        query = select(AppUser).where(AppUser.id == user_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def save_user(self, user: AppUser) -> AppUser:
        self._session.add(user)
        await self._session.flush()
        return user

    async def create_approval_audit(self, audit: UserApprovalAudit) -> UserApprovalAudit:
        self._session.add(audit)
        await self._session.flush()
        return audit

    async def get_approval_history(self, user_id: uuid.UUID) -> list[UserApprovalAudit]:
        query = (
            select(UserApprovalAudit)
            .where(UserApprovalAudit.user_id == user_id)
            .order_by(UserApprovalAudit.created_at.desc())
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())

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
