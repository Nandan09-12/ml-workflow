import uuid

from sqlalchemy import select

from app.models.app_user import AppUser
from app.repositories.base import BaseRepository


class MobileRepository(BaseRepository):
    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None:
        query = select(AppUser).where(AppUser.auth_user_id == auth_user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

