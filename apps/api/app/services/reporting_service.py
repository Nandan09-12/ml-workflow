import csv
import io
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, Protocol

from app.core.enums import (
    AccountStatus,
    RequestedRole,
    Shift,
    SubmissionStatus,
    WorkorderStatus,
)
from app.core.errors import AppError, ErrorCode
from app.models.app_user import AppUser
from app.models.submission import Submission


@dataclass(frozen=True)
class DashboardSummaryView:
    approved_drive_testers: int
    ongoing_submissions: int
    completed_submissions: int
    no_submission_yet: int
    active_workorders: int
    completed_workorders: int
    reference_date: date
    date_from: date | None
    date_to: date | None


@dataclass(frozen=True)
class NoSubmissionYetUserView:
    id: uuid.UUID
    full_name: str
    email: str


class ReportingRepositoryProtocol(Protocol):
    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None: ...

    async def count_approved_drive_testers(self) -> int: ...

    async def count_submissions_by_status(
        self,
        *,
        status: SubmissionStatus,
        work_date: date | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> int: ...

    async def count_approved_drive_testers_without_submission(
        self,
        *,
        work_date: date,
    ) -> int: ...

    async def list_approved_drive_testers_without_submission(
        self,
        *,
        work_date: date,
        offset: int,
        limit: int,
    ) -> tuple[list[AppUser], int]: ...

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
    ) -> list[Submission]: ...

    async def count_active_attachments_for_submissions(
        self,
        submission_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, int]: ...

    async def count_workorders_by_status(self, *, status: WorkorderStatus) -> int: ...

    async def get_workorders_by_submission_ids(
        self, submission_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, Any]: ...


class ReportingService:
    def __init__(self, repository: ReportingRepositoryProtocol) -> None:
        self._repository = repository

    async def get_dashboard_summary(
        self,
        auth_payload: dict[str, Any],
        *,
        work_date: date | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> DashboardSummaryView:
        await self._require_approved_admin(auth_payload)
        approved_drive_testers = await self._repository.count_approved_drive_testers()
        ongoing_submissions = await self._repository.count_submissions_by_status(
            status=SubmissionStatus.IN_PROGRESS,
            work_date=work_date,
            date_from=date_from,
            date_to=date_to,
        )
        completed_submissions = await self._repository.count_submissions_by_status(
            status=SubmissionStatus.COMPLETED,
            work_date=work_date,
            date_from=date_from,
            date_to=date_to,
        )
        reference_date = self._resolve_reference_date(
            work_date=work_date,
            date_from=date_from,
            date_to=date_to,
        )
        no_submission_yet = await self._repository.count_approved_drive_testers_without_submission(
            work_date=reference_date
        )
        active_workorders = await self._repository.count_workorders_by_status(
            status=WorkorderStatus.ACTIVE
        )
        completed_workorders = await self._repository.count_workorders_by_status(
            status=WorkorderStatus.COMPLETED
        )
        return DashboardSummaryView(
            approved_drive_testers=approved_drive_testers,
            ongoing_submissions=ongoing_submissions,
            completed_submissions=completed_submissions,
            no_submission_yet=no_submission_yet,
            active_workorders=active_workorders,
            completed_workorders=completed_workorders,
            reference_date=reference_date,
            date_from=date_from,
            date_to=date_to,
        )

    async def list_no_submission_yet(
        self,
        auth_payload: dict[str, Any],
        *,
        work_date: date,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[NoSubmissionYetUserView], int]:
        await self._require_approved_admin(auth_payload)
        offset = (page - 1) * page_size
        users, total = await self._repository.list_approved_drive_testers_without_submission(
            work_date=work_date,
            offset=offset,
            limit=page_size,
        )
        return [self._to_no_submission_view(user) for user in users], total

    async def export_submissions_csv(
        self,
        auth_payload: dict[str, Any],
        *,
        work_date: date | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        status: SubmissionStatus | None = None,
        shift: Shift | None = None,
        owner_user_id: uuid.UUID | None = None,
        ticket_number: str | None = None,
        file_submission_pending: bool | None = None,
    ) -> str:
        await self._require_approved_admin(auth_payload)
        submissions = await self._repository.list_admin_submissions_for_export(
            work_date=work_date,
            date_from=date_from,
            date_to=date_to,
            status=status,
            shift=shift,
            owner_user_id=owner_user_id,
            ticket_number=ticket_number,
            file_submission_pending=file_submission_pending,
        )
        attachment_counts = await self._repository.count_active_attachments_for_submissions(
            [submission.id for submission in submissions]
        )
        workorders_map = await self._repository.get_workorders_by_submission_ids(
            [submission.id for submission in submissions]
        )
        return self._build_csv(submissions, attachment_counts, workorders_map)

    async def _require_approved_admin(self, auth_payload: dict[str, Any]) -> AppUser:
        auth_user_id = self._extract_auth_user_id(auth_payload)
        actor = await self._repository.get_by_auth_user_id(auth_user_id)
        if actor is None:
            raise AppError(
                ErrorCode.NOT_FOUND,
                "Authenticated app user profile not found.",
                status_code=404,
            )
        if actor.account_status != AccountStatus.APPROVED:
            raise AppError(
                ErrorCode.ACCOUNT_NOT_APPROVED,
                "Account is not approved for admin actions.",
                status_code=403,
            )
        if actor.approved_role != RequestedRole.ADMIN:
            raise AppError(
                ErrorCode.ADMIN_ONLY,
                "Admin access required.",
                status_code=403,
            )
        return actor

    @staticmethod
    def _extract_auth_user_id(auth_payload: dict[str, Any]) -> uuid.UUID:
        raw_sub = auth_payload.get("sub")
        if raw_sub is None:
            raise AppError(
                ErrorCode.UNAUTHORIZED,
                "Authenticated user id is missing from token.",
                status_code=401,
            )
        try:
            return uuid.UUID(str(raw_sub))
        except (TypeError, ValueError) as exc:
            raise AppError(
                ErrorCode.UNAUTHORIZED,
                "Authenticated user id is invalid.",
                status_code=401,
            ) from exc

    @staticmethod
    def _resolve_reference_date(
        *,
        work_date: date | None,
        date_from: date | None,
        date_to: date | None,
    ) -> date:
        if work_date is not None:
            return work_date
        if date_to is not None:
            return date_to
        if date_from is not None:
            return date_from
        return datetime.now(UTC).date()

    @staticmethod
    def _to_no_submission_view(user: AppUser) -> NoSubmissionYetUserView:
        return NoSubmissionYetUserView(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
        )

    @staticmethod
    def _build_csv(
        submissions: list[Submission],
        attachment_counts: dict[uuid.UUID, int],
        workorders_map: dict[uuid.UUID, Any] | None = None,
    ) -> str:
        if workorders_map is None:
            workorders_map = {}
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "submission_id",
                "client_generated_id",
                "workorder_id",
                "owner_user_id",
                "submitter_name",
                "submitter_email",
                "work_date",
                "shift",
                "team_number",
                "ticket_number",
                "skipped_grids",
                "force_tested_grids",
                "completed_grids",
                "status",
                "version_number",
                "started_at",
                "ended_at",
                "created_at",
                "updated_at",
                "file_submission_pending",
                "workorder_code",
                "workorder_region",
                "workorder_status",
                "workorder_progress_percent",
            ]
        )
        for submission in submissions:
            active_attachments = attachment_counts.get(submission.id, 0)
            wo = workorders_map.get(submission.id)
            writer.writerow(
                [
                    str(submission.id),
                    str(submission.client_generated_id),
                    str(submission.workorder_id),
                    str(submission.owner_user_id),
                    submission.submitter_name_snapshot,
                    submission.submitter_email_snapshot,
                    submission.work_date.isoformat(),
                    submission.shift.value,
                    submission.team_number or "",
                    submission.ticket_number or "",
                    submission.skipped_grids,
                    submission.force_tested_grids,
                    submission.completed_grids,
                    submission.status.value,
                    submission.version_number,
                    submission.started_at.isoformat(),
                    submission.ended_at.isoformat() if submission.ended_at else "",
                    submission.created_at.isoformat(),
                    submission.updated_at.isoformat(),
                    "true"
                    if ReportingService._is_file_submission_pending(
                        status=submission.status,
                        active_attachment_count=active_attachments,
                    )
                    else "false",
                    getattr(wo, "workorder_code", "") if wo else "",
                    getattr(wo, "region", "") if wo else "",
                    getattr(wo, "status", "") if wo else "",
                    getattr(wo, "progress_percent", "") if wo else "",
                ]
            )
        return buffer.getvalue()

    @staticmethod
    def _is_file_submission_pending(
        *,
        status: SubmissionStatus,
        active_attachment_count: int,
    ) -> bool:
        return status == SubmissionStatus.COMPLETED and active_attachment_count == 0

