import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date

from sqlalchemy import and_, func, not_, select

from app.core.enums import Shift, SubmissionStatus, Zone
from app.models.app_user import AppUser
from app.models.submission import Submission
from app.models.submission_attachment import SubmissionAttachment
from app.models.submission_audit_log import SubmissionAuditLog
from app.repositories.base import BaseRepository


class SubmissionRepository(BaseRepository):
    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None:
        query = select(AppUser).where(AppUser.auth_user_id == auth_user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_duplicate_for_owner(
        self,
        *,
        owner_user_id: uuid.UUID,
        work_date: date,
        shift: Shift,
        cluster_name_normalized: str,
        exclude_submission_id: uuid.UUID | None = None,
    ) -> Submission | None:
        query = select(Submission).where(
            Submission.owner_user_id == owner_user_id,
            Submission.work_date == work_date,
            Submission.shift == shift,
            Submission.cluster_name_normalized == cluster_name_normalized,
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
        zone: Zone | None = None,
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
        if zone is not None:
            users_query = users_query.where(Submission.zone == zone)
            count_query = count_query.where(Submission.zone == zone)
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
        zone: Zone | None = None,
        shift: Shift | None = None,
        owner_user_id: uuid.UUID | None = None,
        cluster_name: str | None = None,
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
            zone=zone,
            shift=shift,
            owner_user_id=owner_user_id,
            cluster_name=cluster_name,
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
        counts: dict[uuid.UUID, int] = {submission_id: 0 for submission_id in submission_ids}
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
        zone: Zone | None,
        shift: Shift | None,
        owner_user_id: uuid.UUID | None,
        cluster_name: str | None,
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
        if zone is not None:
            items_query = items_query.where(Submission.zone == zone)
            count_query = count_query.where(Submission.zone == zone)
        if shift is not None:
            items_query = items_query.where(Submission.shift == shift)
            count_query = count_query.where(Submission.shift == shift)
        if owner_user_id is not None:
            items_query = items_query.where(Submission.owner_user_id == owner_user_id)
            count_query = count_query.where(Submission.owner_user_id == owner_user_id)
        if cluster_name:
            pattern = f"%{cluster_name.strip()}%"
            items_query = items_query.where(Submission.cluster_name.ilike(pattern))
            count_query = count_query.where(Submission.cluster_name.ilike(pattern))
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
                Submission.status == SubmissionStatus.COMPLETED,
                active_attachment_count == 0,
            )
            if file_submission_pending:
                items_query = items_query.where(pending_predicate)
                count_query = count_query.where(pending_predicate)
            else:
                items_query = items_query.where(not_(pending_predicate))
                count_query = count_query.where(not_(pending_predicate))

        return items_query, count_query
