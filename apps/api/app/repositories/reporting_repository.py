import uuid
from datetime import date
from typing import Any

from sqlalchemy import func, select

from app.core.enums import AccountStatus, RequestedRole, Shift, SubmissionStatus
from app.models.app_user import AppUser
from app.models.submission import Submission
from app.models.submission_attachment import SubmissionAttachment
from app.repositories.base import BaseRepository
from app.repositories.submission_repository import SubmissionRepository


class ReportingRepository(BaseRepository):
    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None:
        query = select(AppUser).where(AppUser.auth_user_id == auth_user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def count_approved_drive_testers(self) -> int:
        query = select(func.count(AppUser.id)).where(*self._approved_drive_tester_predicates())
        result = await self.session.execute(query)
        return int(result.scalar_one())

    async def count_submissions_by_status(
        self,
        *,
        status: SubmissionStatus,
        work_date: date | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> int:
        query = select(func.count(Submission.id)).where(Submission.status == status)
        query = self._apply_submission_date_filters(
            query,
            work_date=work_date,
            date_from=date_from,
            date_to=date_to,
        )
        result = await self.session.execute(query)
        return int(result.scalar_one())

    async def count_approved_drive_testers_without_submission(
        self,
        *,
        work_date: date,
    ) -> int:
        query = select(func.count(AppUser.id)).where(
            *self._approved_drive_tester_predicates(),
            ~self._submission_exists_for_work_date(work_date),
        )
        result = await self.session.execute(query)
        return int(result.scalar_one())

    async def list_approved_drive_testers_without_submission(
        self,
        *,
        work_date: date,
        offset: int,
        limit: int,
    ) -> tuple[list[AppUser], int]:
        items_query = (
            select(AppUser)
            .where(
                *self._approved_drive_tester_predicates(),
                ~self._submission_exists_for_work_date(work_date),
            )
            .order_by(AppUser.full_name.asc(), AppUser.email.asc())
            .offset(offset)
            .limit(limit)
        )
        count_query = select(func.count(AppUser.id)).where(
            *self._approved_drive_tester_predicates(),
            ~self._submission_exists_for_work_date(work_date),
        )
        items_result = await self.session.execute(items_query)
        count_result = await self.session.execute(count_query)
        items = list(items_result.scalars().all())
        total = int(count_result.scalar_one())
        return items, total

    async def list_admin_submissions_for_export(
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
    ) -> list[Submission]:
        items_query = select(Submission)
        count_query = select(func.count(Submission.id))
        items_query, _ = SubmissionRepository._apply_admin_filters(  # noqa: SLF001
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
        items_result = await self.session.execute(items_query)
        return list(items_result.scalars().all())

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
        counts = dict.fromkeys(submission_ids, 0)
        for submission_id, count in result.all():
            counts[submission_id] = int(count)
        return counts

    @staticmethod
    def _approved_drive_tester_predicates() -> tuple[Any, ...]:
        return (
            AppUser.account_status == AccountStatus.APPROVED,
            AppUser.approved_role == RequestedRole.DRIVE_TESTER,
        )

    @staticmethod
    def _submission_exists_for_work_date(work_date: date) -> Any:
        return (
            select(Submission.id)
            .where(
                Submission.owner_user_id == AppUser.id,
                Submission.work_date == work_date,
            )
            .exists()
        )

    @staticmethod
    def _apply_submission_date_filters(
        query: Any,
        *,
        work_date: date | None,
        date_from: date | None,
        date_to: date | None,
    ) -> Any:
        if work_date is not None:
            query = query.where(Submission.work_date == work_date)
        if date_from is not None:
            query = query.where(Submission.work_date >= date_from)
        if date_to is not None:
            query = query.where(Submission.work_date <= date_to)
        return query
