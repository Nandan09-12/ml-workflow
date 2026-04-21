import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date

from sqlalchemy import select

from app.models.app_user import AppUser
from app.models.mileage_entry import MileageEntry
from app.repositories.base import BaseRepository


class MileageRepository(BaseRepository):
    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None:
        query = select(AppUser).where(AppUser.auth_user_id == auth_user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_mileage_for_owner_and_date(
        self,
        *,
        owner_user_id: uuid.UUID,
        work_date: date,
    ) -> MileageEntry | None:
        query = select(MileageEntry).where(
            MileageEntry.owner_user_id == owner_user_id,
            MileageEntry.work_date == work_date,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_mileage_entry(self, entry: MileageEntry) -> MileageEntry:
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def save_mileage_entry(self, entry: MileageEntry) -> MileageEntry:
        self.session.add(entry)
        await self.session.flush()
        return entry

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
