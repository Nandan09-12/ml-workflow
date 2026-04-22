import uuid
from datetime import date
from typing import Any

from sqlalchemy import and_, func, not_, or_, select

from app.core.enums import Region, Shift, SubmissionStatus, WorkorderStatus
from app.models.submission import Submission
from app.models.submission_attachment import SubmissionAttachment
from app.models.workorder import Workorder


def apply_admin_submission_filters(
    items_query: Any,
    count_query: Any,
    *,
    work_date: date | None,
    date_from: date | None,
    date_to: date | None,
    status: SubmissionStatus | None,
    shift: Shift | None,
    workorder_status: WorkorderStatus | None = None,
    region: Region | None = None,
    workorder_code: str | None = None,
    tester: str | None = None,
    owner_user_id: uuid.UUID | None,
    ticket_number: str | None,
    file_submission_pending: bool | None,
) -> tuple[Any, Any]:
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
    if workorder_status is not None:
        items_query = items_query.where(
            Submission.workorder_id == Workorder.id,
            Workorder.status == workorder_status,
        )
        count_query = count_query.where(
            Submission.workorder_id == Workorder.id,
            Workorder.status == workorder_status,
        )
    if region is not None:
        items_query = items_query.where(
            Submission.workorder_id == Workorder.id,
            Workorder.region == region,
        )
        count_query = count_query.where(
            Submission.workorder_id == Workorder.id,
            Workorder.region == region,
        )
    if workorder_code:
        normalized_workorder_code = workorder_code.strip()
        if normalized_workorder_code:
            workorder_pattern = f"%{normalized_workorder_code}%"
            items_query = items_query.where(
                Submission.workorder_id == Workorder.id,
                Workorder.workorder_code.ilike(workorder_pattern),
            )
            count_query = count_query.where(
                Submission.workorder_id == Workorder.id,
                Workorder.workorder_code.ilike(workorder_pattern),
            )
    if tester:
        normalized_tester = tester.strip()
        if normalized_tester:
            tester_pattern = f"%{normalized_tester}%"
            tester_predicate = or_(
                Submission.submitter_name_snapshot.ilike(tester_pattern),
                Submission.submitter_email_snapshot.ilike(tester_pattern),
            )
            items_query = items_query.where(tester_predicate)
            count_query = count_query.where(tester_predicate)
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
