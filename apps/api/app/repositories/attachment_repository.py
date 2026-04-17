import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.app_user import AppUser
from app.models.submission import Submission
from app.models.submission_attachment import SubmissionAttachment
from app.models.submission_audit_log import SubmissionAuditLog
from app.models.workorder import Workorder


class AttachmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None:
        query = select(AppUser).where(AppUser.auth_user_id == auth_user_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_submission_by_id(self, submission_id: uuid.UUID) -> Submission | None:
        query = select(Submission).where(Submission.id == submission_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def count_active_attachments(self, submission_id: uuid.UUID) -> int:
        query = select(func.count(SubmissionAttachment.id)).where(
            SubmissionAttachment.submission_id == submission_id,
            SubmissionAttachment.is_active.is_(True),
        )
        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def create_attachment(self, attachment: SubmissionAttachment) -> SubmissionAttachment:
        self._session.add(attachment)
        await self._session.flush()
        return attachment

    async def list_attachments_for_submission(
        self,
        submission_id: uuid.UUID,
        *,
        active_only: bool = True,
    ) -> list[SubmissionAttachment]:
        query = select(SubmissionAttachment).where(SubmissionAttachment.submission_id == submission_id)
        if active_only:
            query = query.where(SubmissionAttachment.is_active.is_(True))
        query = query.order_by(SubmissionAttachment.uploaded_at.desc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_attachment_by_id(self, attachment_id: uuid.UUID) -> SubmissionAttachment | None:
        query = select(SubmissionAttachment).where(SubmissionAttachment.id == attachment_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def save_attachment(self, attachment: SubmissionAttachment) -> SubmissionAttachment:
        self._session.add(attachment)
        await self._session.flush()
        return attachment

    async def get_workorder_by_id(self, workorder_id: uuid.UUID) -> Workorder | None:
        query = select(Workorder).where(Workorder.id == workorder_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def save_workorder(self, workorder: Workorder) -> Workorder:
        self._session.add(workorder)
        await self._session.flush()
        return workorder

    async def create_audit_log(self, log: SubmissionAuditLog) -> SubmissionAuditLog:
        self._session.add(log)
        await self._session.flush()
        return log

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
