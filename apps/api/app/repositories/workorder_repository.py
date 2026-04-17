import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date

from sqlalchemy import func, select

from app.models.app_user import AppUser
from app.models.submission import Submission
from app.models.submission_audit_log import SubmissionAuditLog
from app.models.workorder import Workorder
from app.repositories.base import BaseRepository


class WorkorderRepository(BaseRepository):
    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None:
        query = select(AppUser).where(AppUser.auth_user_id == auth_user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_workorder_by_normalized_code(self, code: str) -> Workorder | None:
        query = select(Workorder).where(Workorder.workorder_code_normalized == code)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_workorder(self, workorder: Workorder) -> Workorder:
        self.session.add(workorder)
        await self.session.flush()
        return workorder

    async def get_workorder_by_id(self, workorder_id: uuid.UUID) -> Workorder | None:
        query = select(Workorder).where(Workorder.id == workorder_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def save_workorder(self, workorder: Workorder) -> Workorder:
        self.session.add(workorder)
        await self.session.flush()
        return workorder

    async def create_submission(self, submission: Submission) -> Submission:
        self.session.add(submission)
        await self.session.flush()
        return submission

    async def get_submission_by_workorder_date(
        self,
        *,
        workorder_id: uuid.UUID,
        work_date: date,
        exclude_submission_id: uuid.UUID | None = None,
    ) -> Submission | None:
        query = select(Submission).where(
            Submission.workorder_id == workorder_id,
            Submission.work_date == work_date,
        )
        if exclude_submission_id is not None:
            query = query.where(Submission.id != exclude_submission_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_audit_log(self, log: SubmissionAuditLog) -> SubmissionAuditLog:
        self.session.add(log)
        await self.session.flush()
        return log

    async def get_aggregate_progress(self, workorder_id: uuid.UUID) -> tuple[int, int]:
        """Return (sum_completed_grids, sum_skipped_grids) across all child submissions."""
        query = select(
            func.coalesce(func.sum(Submission.completed_grids), 0),
            func.coalesce(func.sum(Submission.skipped_grids), 0),
        ).where(Submission.workorder_id == workorder_id)
        result = await self.session.execute(query)
        row = result.one()
        return int(row[0]), int(row[1])

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
