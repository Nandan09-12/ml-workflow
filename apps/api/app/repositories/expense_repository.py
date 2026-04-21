import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import desc, select

from app.models.app_user import AppUser
from app.models.expense_entry import ExpenseEntry
from app.repositories.base import BaseRepository


class ExpenseRepository(BaseRepository):
    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None:
        query = select(AppUser).where(AppUser.auth_user_id == auth_user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_expense_entry(self, entry: ExpenseEntry) -> ExpenseEntry:
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def list_expenses_for_owner(self, owner_user_id: uuid.UUID) -> list[ExpenseEntry]:
        query = (
            select(ExpenseEntry)
            .where(ExpenseEntry.owner_user_id == owner_user_id)
            .order_by(desc(ExpenseEntry.expense_date), desc(ExpenseEntry.created_at))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        if self.session.in_transaction():
            try:
                yield
                await self.session.commit()
            except Exception:
                await self.session.rollback()
                raise
            return

        async with self.session.begin():
            yield
