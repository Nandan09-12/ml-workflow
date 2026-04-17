import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date

from sqlalchemy import and_, func, not_, select

from app.core.enums import Shift, SubmissionStatus
from app.models.app_user import AppUser
from app.models.submission import Submission
from app.models.submission_attachment import SubmissionAttachment
from app.models.submission_audit_log import SubmissionAuditLog
from app.models.workorder import Workorder
from app.repositories.base import BaseRepository


class SubmissionRepository(BaseRepository):
    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None:
        query = select(AppUser).where(AppUser.auth_user_id == auth_user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

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

    async def create_submission(self, submission: Submission) -> Submission:
        self.session.add(submission)
        await self.session.flush()
        return submission

    async def list_submissions(
        self,
        *,
        owner_user_id: uuid.UUID,
        work_date: date | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        status: SubmissionStatus | None = None,
        shift: Shift | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Submission], int]:
        users_query = select(Submission).where(Submission.owner_user_id == owner_user_id)
        count_query = select(func.count(Submission.id)).where(Submission.owner_user_id == owner_user_id)

        if work_date is not None:
            users_query = users_query.where(Submission.work_date == work_date)
            count_query = count_query.where(Submission.work_date == work_date)
        if date_from is not None:
            users_query = users_query.where(Submission.work_date >= date_from)
            count_query = count_query.where(Submission.work_date >= date_from)
        if date_to is not None:
            users_query = users_query.where(Submission.work_date <= date_to)
            count_query = count_query.where(Submission.work_date <= date_to)
        if status is not None:
            users_query = users_query.where(Submission.status == status)
            count_query = count_query.where(Submission.status == status)
        if shift is not None:
            users_query = users_query.where(Submission.shift == shift)
            count_query = count_query.where(Submission.shift == shift)

        users_query = users_query.order_by(Submission.work_date.desc(), Submission.created_at.desc())
        users_query = users_query.offset(offset).limit(limit)

        users_result = await self.session.execute(users_query)
        total_result = await self.session.execute(count_query)
        users = list(users_result.scalars().all())
        total = int(total_result.scalar_one())
        return users, total

    async def list_admin_submissions(
        self,
        *,
        work_date: date | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        status: SubmissionStatus | None = None,
        shift: Shift | None = None,
        owner_user_id: uuid.UUID | None = None,
        ticket_number: str | None = None,
        file_submission_pending: bool | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Submission], int]:
        items_query = select(Submission)
        count_query = select(func.count(Submission.id))

        items_query, count_query = self._apply_admin_filters(
            items_query,
            count_query,
            work_date=work_date,
            date_from=date_from,
            date_to=date_to,
            status=status,
            shift=shift,
            owner_user_id=owner_user_id,
            ticket_number=ticket_number,
            file_submission_pending=file_submission_pending,
        )

        items_query = items_query.order_by(Submission.work_date.desc(), Submission.created_at.desc())
        items_query = items_query.offset(offset).limit(limit)

        items_result = await self.session.execute(items_query)
        total_result = await self.session.execute(count_query)
        items = list(items_result.scalars().all())
        total = int(total_result.scalar_one())
        return items, total

    async def get_submission_by_id(self, submission_id: uuid.UUID) -> Submission | None:
        query = select(Submission).where(Submission.id == submission_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def save_submission(self, submission: Submission) -> Submission:
        self.session.add(submission)
        await self.session.flush()
        return submission

    async def create_audit_log(self, log: SubmissionAuditLog) -> SubmissionAuditLog:
        self.session.add(log)
        await self.session.flush()
        return log

    async def get_submission_audit_logs(self, submission_id: uuid.UUID) -> list[SubmissionAuditLog]:
        query = (
            select(SubmissionAuditLog)
            .where(SubmissionAuditLog.submission_id == submission_id)
            .order_by(SubmissionAuditLog.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_active_attachments(self, submission_id: uuid.UUID) -> int:
        query = select(func.count(SubmissionAttachment.id)).where(
            SubmissionAttachment.submission_id == submission_id,
            SubmissionAttachment.is_active.is_(True),
        )
        result = await self.session.execute(query)
        return int(result.scalar_one())

    async def count_active_attachments_for_submissions(
        self,
        submission_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, int]:
        if not submission_ids:
            return {}

        query = (
            select(
                SubmissionAttachment.submission_id,
                func.count(SubmissionAttachment.id),
            )
            .where(
                SubmissionAttachment.submission_id.in_(submission_ids),
                SubmissionAttachment.is_active.is_(True),
            )
            .group_by(SubmissionAttachment.submission_id)
        )
        result = await self.session.execute(query)
        counts: dict[uuid.UUID, int] = dict.fromkeys(submission_ids, 0)
        for submission_id, count in result.all():
            counts[submission_id] = int(count)
        return counts

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

    @staticmethod
    def _apply_admin_filters(
        items_query: object,
        count_query: object,
        *,
        work_date: date | None,
        date_from: date | None,
        date_to: date | None,
        status: SubmissionStatus | None,
        shift: Shift | None,
        owner_user_id: uuid.UUID | None,
        ticket_number: str | None,
        file_submission_pending: bool | None,
    ) -> tuple[object, object]:
        if work_date is not None:
            items_query = items_query.where(Submission.work_date == work_date)
            count_query = count_query.where(Submission.work_date == work_date)
        if date_from is not None:
            items_query = items_query.where(Submission.work_date >= date_from)
            count_query = count_query.where(Submission.work_date >= date_from)
        if date_to is not None:
            items_query = items_query.where(Submission.work_date <= date_to)
            count_query = count_query.where(Submission.work_date <= date_to)
        if status is not None:
            items_query = items_query.where(Submission.status == status)
            count_query = count_query.where(Submission.status == status)
        if shift is not None:
            items_query = items_query.where(Submission.shift == shift)
            count_query = count_query.where(Submission.shift == shift)
        if owner_user_id is not None:
            items_query = items_query.where(Submission.owner_user_id == owner_user_id)
            count_query = count_query.where(Submission.owner_user_id == owner_user_id)
        if ticket_number:
            pattern = f"%{ticket_number.strip()}%"
            items_query = items_query.where(Submission.ticket_number.ilike(pattern))
            count_query = count_query.where(Submission.ticket_number.ilike(pattern))

        if file_submission_pending is not None:
            active_attachment_count = (
                select(func.count(SubmissionAttachment.id))
                .where(
                    SubmissionAttachment.submission_id == Submission.id,
                    SubmissionAttachment.is_active.is_(True),
                )
                .correlate(Submission)
                .scalar_subquery()
            )
            pending_predicate = and_(
                Submission.status == SubmissionStatus.CHECKED_OUT,
                active_attachment_count == 0,
            )
            if file_submission_pending:
                items_query = items_query.where(pending_predicate)
                count_query = count_query.where(pending_predicate)
            else:
                items_query = items_query.where(not_(pending_predicate))
                count_query = count_query.where(not_(pending_predicate))

        return items_query, count_query

    async def get_workorder_by_id(self, workorder_id: uuid.UUID) -> Workorder | None:
        query = select(Workorder).where(Workorder.id == workorder_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def save_workorder(self, workorder: Workorder) -> Workorder:
        self.session.add(workorder)
        await self.session.flush()
        return workorder

    async def get_aggregate_progress(self, workorder_id: uuid.UUID) -> tuple[int, int]:
        """Return (sum_completed_grids, sum_skipped_grids) across all child submissions."""
        query = select(
            func.coalesce(func.sum(Submission.completed_grids), 0),
            func.coalesce(func.sum(Submission.skipped_grids), 0),
        ).where(Submission.workorder_id == workorder_id)
        result = await self.session.execute(query)
        row = result.one()
        return int(row[0]), int(row[1])

    async def get_workorders_by_ids(
        self, workorder_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, Workorder]:
        if not workorder_ids:
            return {}
        query = select(Workorder).where(Workorder.id.in_(workorder_ids))
        result = await self.session.execute(query)
        rows = result.scalars().all()
        return {wo.id: wo for wo in rows}

    async def get_aggregate_progress_batch(
        self, workorder_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, tuple[int, int]]:
        if not workorder_ids:
            return {}
        query = (
            select(
                Submission.workorder_id,
                func.coalesce(func.sum(Submission.completed_grids), 0),
                func.coalesce(func.sum(Submission.skipped_grids), 0),
            )
            .where(Submission.workorder_id.in_(workorder_ids))
            .group_by(Submission.workorder_id)
        )
        result = await self.session.execute(query)
        rows = result.all()
        aggregates: dict[uuid.UUID, tuple[int, int]] = dict.fromkeys(workorder_ids, (0, 0))
        for row in rows:
            aggregates[row[0]] = (int(row[1]), int(row[2]))
        return aggregates
