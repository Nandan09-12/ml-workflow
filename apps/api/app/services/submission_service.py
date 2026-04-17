import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, Protocol

from sqlalchemy.exc import IntegrityError

from app.core.enums import (
    AccountStatus,
    AuditActionType,
    AuditSource,
    RequestedRole,
    Shift,
    SubmissionStatus,
    WorkorderStatus,
)
from app.core.errors import AppError, ErrorCode
from app.models.app_user import AppUser
from app.models.submission import Submission
from app.models.submission_audit_log import SubmissionAuditLog
from app.models.workorder import Workorder
from app.schemas.submissions import CreateSubmissionRequest, UpdateSubmissionRequest
from app.schemas.workorders import WorkorderSummary


@dataclass(frozen=True)
class SubmissionView:
    id: uuid.UUID
    client_generated_id: uuid.UUID
    workorder_id: uuid.UUID
    owner_user_id: uuid.UUID
    submitter_name_snapshot: str
    submitter_email_snapshot: str
    work_date: date
    shift: Shift
    team_number: str | None
    ticket_number: str | None
    skipped_grids: int
    force_tested_grids: int
    completed_grids: int
    status: SubmissionStatus
    version_number: int
    started_at: datetime
    ended_at: datetime | None
    created_at: datetime
    updated_at: datetime
    file_submission_pending: bool
    workorder_summary: WorkorderSummary | None = None


@dataclass(frozen=True)
class SubmissionAuditView:
    id: uuid.UUID
    submission_id: uuid.UUID
    action_type: AuditActionType
    actor_user_id: uuid.UUID
    actor_role: str
    source: AuditSource
    changed_fields_json: dict[str, Any] | None
    before_snapshot_json: dict[str, Any] | None
    after_snapshot_json: dict[str, Any] | None
    created_at: datetime


class SubmissionRepositoryProtocol(Protocol):
    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None: ...

    async def get_submission_by_workorder_date(
        self,
        *,
        workorder_id: uuid.UUID,
        work_date: date,
        exclude_submission_id: uuid.UUID | None = None,
    ) -> Submission | None: ...

    async def create_submission(self, submission: Submission) -> Submission: ...

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
    ) -> tuple[list[Submission], int]: ...

    async def list_admin_submissions(
        self,
        *,
        work_date: date | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        status: SubmissionStatus | None = None,
        shift: Shift | None = None,
        workorder_status: WorkorderStatus | None = None,
        owner_user_id: uuid.UUID | None = None,
        ticket_number: str | None = None,
        file_submission_pending: bool | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Submission], int]: ...

    async def get_submission_by_id(self, submission_id: uuid.UUID) -> Submission | None: ...

    async def save_submission(self, submission: Submission) -> Submission: ...

    async def create_audit_log(self, log: SubmissionAuditLog) -> SubmissionAuditLog: ...

    async def get_submission_audit_logs(self, submission_id: uuid.UUID) -> list[SubmissionAuditLog]: ...

    async def count_active_attachments(self, submission_id: uuid.UUID) -> int: ...

    async def count_active_attachments_for_submissions(
        self,
        submission_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, int]: ...

    async def get_workorder_by_id(self, workorder_id: uuid.UUID) -> Workorder | None: ...

    async def save_workorder(self, workorder: Workorder) -> Workorder: ...

    async def get_aggregate_progress(self, workorder_id: uuid.UUID) -> tuple[int, int]: ...

    async def get_workorders_by_ids(
        self, workorder_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, Workorder]: ...

    async def get_aggregate_progress_batch(
        self, workorder_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, tuple[int, int]]: ...

    def transaction(self) -> Any: ...


class SubmissionService:
    def __init__(self, repository: SubmissionRepositoryProtocol) -> None:
        self._repository = repository

    async def create_submission(
        self,
        auth_payload: dict[str, Any],
        request: CreateSubmissionRequest,
    ) -> SubmissionView:
        actor = await self._require_approved_user(auth_payload)
        self._validate_grids(
            skipped_grids=request.skipped_grids,
            force_tested_grids=request.force_tested_grids,
            completed_grids=request.completed_grids,
        )

        duplicate = await self._repository.get_submission_by_workorder_date(
            workorder_id=request.workorder_id,
            work_date=request.work_date,
        )
        if duplicate is not None:
            raise AppError(
                ErrorCode.SUBMISSION_ALREADY_EXISTS,
                "A submission already exists for this workorder on that date.",
                status_code=409,
            )

        now = datetime.now(UTC)
        submission = Submission(
            id=uuid.uuid4(),
            client_generated_id=request.client_generated_id or uuid.uuid4(),
            workorder_id=request.workorder_id,
            owner_user_id=actor.id,
            submitter_name_snapshot=actor.full_name,
            submitter_email_snapshot=actor.email,
            work_date=request.work_date,
            shift=request.shift,
            team_number=self._normalize_optional_text(request.team_number),
            ticket_number=self._normalize_optional_text(request.ticket_number),
            skipped_grids=request.skipped_grids,
            force_tested_grids=request.force_tested_grids,
            completed_grids=request.completed_grids,
            status=SubmissionStatus.IN_PROGRESS,
            started_at=now,
            ended_at=None,
            created_at=now,
            created_by_user_id=actor.id,
            updated_at=now,
            updated_by_user_id=actor.id,
            version_number=1,
        )

        try:
            async with self._repository.transaction():
                created = await self._repository.create_submission(submission)
                await self._repository.create_audit_log(
                    self._build_audit_log(
                        submission_id=created.id,
                        action_type=AuditActionType.CREATED,
                        actor=actor,
                        changed_fields=[
                            "workorder_id",
                            "work_date",
                            "shift",
                            "team_number",
                            "ticket_number",
                            "skipped_grids",
                            "force_tested_grids",
                            "completed_grids",
                            "status",
                            "started_at",
                            "version_number",
                        ],
                    )
                )
        except IntegrityError as exc:
            raise AppError(
                ErrorCode.SUBMISSION_ALREADY_EXISTS,
                "A submission already exists for this workorder on that date.",
                status_code=409,
            ) from exc

        active_attachments = await self._repository.count_active_attachments(created.id)
        return self._to_view(created, active_attachment_count=active_attachments)

    async def end_drive(
        self,
        auth_payload: dict[str, Any],
        submission_id: uuid.UUID,
    ) -> SubmissionView:
        actor = await self._require_approved_user(auth_payload)
        async with self._repository.transaction():
            submission = await self._repository.get_submission_by_id(submission_id)
            if submission is None:
                raise AppError(ErrorCode.NOT_FOUND, "Submission was not found.", status_code=404)
            self._assert_owner(actor, submission)
            if submission.status != SubmissionStatus.IN_PROGRESS:
                raise AppError(
                    ErrorCode.SUBMISSION_NOT_CHECKED_OUT,
                    "Only in-progress submissions can be ended.",
                    status_code=400,
                )

            now = datetime.now(UTC)
            submission.status = SubmissionStatus.CHECKED_OUT
            submission.ended_at = now
            submission.updated_at = now
            submission.updated_by_user_id = actor.id
            submission.version_number += 1
            await self._repository.save_submission(submission)
            await self._repository.create_audit_log(
                self._build_audit_log(
                    submission_id=submission.id,
                    action_type=AuditActionType.STATUS_CHANGED,
                    actor=actor,
                    changed_fields=["status", "ended_at", "version_number"],
                )
            )

        active_attachments = await self._repository.count_active_attachments(submission.id)
        return self._to_view(submission, active_attachment_count=active_attachments)

    async def list_my_submissions(
        self,
        auth_payload: dict[str, Any],
        *,
        work_date: date | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        status: SubmissionStatus | None = None,
        shift: Shift | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SubmissionView], int]:
        actor = await self._require_approved_user(auth_payload)
        offset = (page - 1) * page_size
        submissions, total = await self._repository.list_submissions(
            owner_user_id=actor.id,
            work_date=work_date,
            date_from=date_from,
            date_to=date_to,
            status=status,
            shift=shift,
            offset=offset,
            limit=page_size,
        )

        submission_ids = [submission.id for submission in submissions]
        attachment_counts = await self._repository.count_active_attachments_for_submissions(submission_ids)

        workorder_ids = list({s.workorder_id for s in submissions})
        workorders_map = await self._repository.get_workorders_by_ids(workorder_ids)
        agg_map = await self._repository.get_aggregate_progress_batch(workorder_ids)

        views = [
            self._to_view(
                submission,
                active_attachment_count=attachment_counts.get(submission.id, 0),
                workorder_summary=self._to_workorder_summary(
                    workorders_map[submission.workorder_id],
                    agg_map.get(submission.workorder_id, (0, 0)),
                )
                if submission.workorder_id in workorders_map
                else None,
            )
            for submission in submissions
        ]
        return views, total

    async def get_submission(
        self,
        auth_payload: dict[str, Any],
        submission_id: uuid.UUID,
    ) -> SubmissionView:
        actor = await self._require_approved_user(auth_payload)
        submission = await self._repository.get_submission_by_id(submission_id)
        if submission is None:
            raise AppError(ErrorCode.NOT_FOUND, "Submission was not found.", status_code=404)
        self._assert_owner(actor, submission)
        active_attachments = await self._repository.count_active_attachments(submission.id)
        workorder = await self._repository.get_workorder_by_id(submission.workorder_id)
        workorder_summary: WorkorderSummary | None = None
        if workorder is not None:
            agg = await self._repository.get_aggregate_progress(submission.workorder_id)
            workorder_summary = self._to_workorder_summary(workorder, agg)
        return self._to_view(submission, active_attachment_count=active_attachments, workorder_summary=workorder_summary)

    async def update_submission(
        self,
        auth_payload: dict[str, Any],
        submission_id: uuid.UUID,
        request: UpdateSubmissionRequest,
    ) -> SubmissionView:
        actor = await self._require_approved_user(auth_payload)
        async with self._repository.transaction():
            submission = await self._repository.get_submission_by_id(submission_id)
            if submission is None:
                raise AppError(ErrorCode.NOT_FOUND, "Submission was not found.", status_code=404)
            self._assert_owner(actor, submission)
            if submission.status not in (SubmissionStatus.IN_PROGRESS, SubmissionStatus.CHECKED_OUT):
                raise AppError(
                    ErrorCode.SUBMISSION_ALREADY_COMPLETED,
                    "Only in-progress or checked-out submissions can be edited.",
                    status_code=400,
                )
            if submission.version_number != request.version_number:
                raise AppError(
                    ErrorCode.VERSION_CONFLICT,
                    "Submission version is stale. Refresh and retry.",
                    status_code=409,
                )

            old_completed = submission.completed_grids
            old_skipped = submission.skipped_grids
            changed_fields = self._apply_updates(submission, request)
            if changed_fields:
                self._validate_grids(
                    skipped_grids=submission.skipped_grids,
                    force_tested_grids=submission.force_tested_grids,
                    completed_grids=submission.completed_grids,
                )
                duplicate = await self._repository.get_submission_by_workorder_date(
                    workorder_id=submission.workorder_id,
                    work_date=submission.work_date,
                    exclude_submission_id=submission.id,
                )
                if duplicate is not None:
                    raise AppError(
                        ErrorCode.SUBMISSION_ALREADY_EXISTS,
                        "A submission already exists for this workorder on that date.",
                        status_code=409,
                    )

                # Aggregate cap check
                workorder = await self._repository.get_workorder_by_id(submission.workorder_id)
                if workorder is not None:
                    agg = await self._repository.get_aggregate_progress(submission.workorder_id)
                    old_sum = old_completed + old_skipped
                    new_sum = submission.completed_grids + submission.skipped_grids
                    if (agg[0] + agg[1]) - old_sum + new_sum > workorder.total_grids:
                        raise AppError(
                            ErrorCode.WORKORDER_PROGRESS_EXCEEDS_TOTAL,
                            "Updated grid values would exceed the workorder total.",
                            status_code=400,
                        )

                now = datetime.now(UTC)
                submission.version_number += 1
                submission.updated_at = now
                submission.updated_by_user_id = actor.id
                await self._repository.save_submission(submission)
                await self._repository.create_audit_log(
                    self._build_audit_log(
                        submission_id=submission.id,
                        action_type=AuditActionType.UPDATED,
                        actor=actor,
                        changed_fields=sorted(changed_fields),
                    )
                )

        active_attachments = await self._repository.count_active_attachments(submission.id)
        return self._to_view(submission, active_attachment_count=active_attachments)

    async def complete_submission(
        self,
        auth_payload: dict[str, Any],
        submission_id: uuid.UUID,
    ) -> SubmissionView:
        actor = await self._require_approved_user(auth_payload)
        async with self._repository.transaction():
            submission = await self._repository.get_submission_by_id(submission_id)
            if submission is None:
                raise AppError(ErrorCode.NOT_FOUND, "Submission was not found.", status_code=404)
            self._assert_owner(actor, submission)
            if submission.status != SubmissionStatus.CHECKED_OUT:
                raise AppError(
                    ErrorCode.SUBMISSION_NOT_CHECKED_OUT,
                    "Only checked-out submissions can be completed.",
                    status_code=400,
                )

            # Attachment required
            active_attachments = await self._repository.count_active_attachments(submission.id)
            if active_attachments == 0:
                raise AppError(
                    ErrorCode.ATTACHMENT_REQUIRED,
                    "At least one attachment is required before completing a submission.",
                    status_code=400,
                )

            # Aggregate cap check
            workorder = await self._repository.get_workorder_by_id(submission.workorder_id)
            agg_total = 0
            if workorder is not None:
                agg = await self._repository.get_aggregate_progress(submission.workorder_id)
                agg_total = agg[0] + agg[1]
                if agg_total > workorder.total_grids:
                    raise AppError(
                        ErrorCode.WORKORDER_PROGRESS_EXCEEDS_TOTAL,
                        "Submission grids exceed the workorder total.",
                        status_code=400,
                    )

            now = datetime.now(UTC)
            submission.status = SubmissionStatus.COMPLETED
            submission.ended_at = now
            submission.completed_at = now
            submission.completed_by_user_id = actor.id
            submission.updated_at = now
            submission.updated_by_user_id = actor.id
            submission.version_number += 1
            await self._repository.save_submission(submission)
            await self._repository.create_audit_log(
                self._build_audit_log(
                    submission_id=submission.id,
                    action_type=AuditActionType.COMPLETED,
                    actor=actor,
                    changed_fields=[
                        "status",
                        "ended_at",
                        "completed_at",
                        "completed_by_user_id",
                        "version_number",
                    ],
                )
            )

            # Auto-complete parent workorder when grids are fully accounted for
            if workorder is not None and agg_total >= workorder.total_grids:
                now2 = datetime.now(UTC)
                workorder.status = WorkorderStatus.COMPLETED
                workorder.completed_at = now2
                workorder.completed_by_user_id = actor.id
                await self._repository.save_workorder(workorder)

        return self._to_view(submission, active_attachment_count=active_attachments)

    async def reopen_submission(
        self,
        auth_payload: dict[str, Any],
        submission_id: uuid.UUID,
    ) -> SubmissionView:
        actor = await self._require_approved_admin(auth_payload)
        async with self._repository.transaction():
            submission = await self._repository.get_submission_by_id(submission_id)
            if submission is None:
                raise AppError(ErrorCode.NOT_FOUND, "Submission was not found.", status_code=404)
            if submission.status != SubmissionStatus.COMPLETED:
                raise AppError(
                    ErrorCode.SUBMISSION_NOT_COMPLETED,
                    "Only completed submissions can be reopened.",
                    status_code=400,
                )

            now = datetime.now(UTC)
            submission.status = SubmissionStatus.CHECKED_OUT
            submission.reopened_at = now
            submission.reopened_by_user_id = actor.id
            submission.updated_at = now
            submission.updated_by_user_id = actor.id
            submission.version_number += 1
            await self._repository.save_submission(submission)
            await self._repository.create_audit_log(
                self._build_audit_log(
                    submission_id=submission.id,
                    action_type=AuditActionType.REOPENED,
                    actor=actor,
                    changed_fields=[
                        "status",
                        "reopened_at",
                        "reopened_by_user_id",
                        "version_number",
                    ],
                )
            )

            # Cascade: if parent workorder was COMPLETED, revert to ACTIVE
            workorder = await self._repository.get_workorder_by_id(submission.workorder_id)
            if workorder is not None and workorder.status == WorkorderStatus.COMPLETED:
                now2 = datetime.now(UTC)
                workorder.status = WorkorderStatus.ACTIVE
                workorder.completed_at = None
                workorder.completed_by_user_id = None
                workorder.updated_at = now2
                workorder.updated_by_user_id = actor.id
                await self._repository.save_workorder(workorder)

        active_attachments = await self._repository.count_active_attachments(submission.id)
        return self._to_view(submission, active_attachment_count=active_attachments)

    async def list_admin_submissions(
        self,
        auth_payload: dict[str, Any],
        *,
        work_date: date | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        status: SubmissionStatus | None = None,
        shift: Shift | None = None,
        workorder_status: WorkorderStatus | None = None,
        owner_user_id: uuid.UUID | None = None,
        ticket_number: str | None = None,
        file_submission_pending: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SubmissionView], int]:
        await self._require_approved_admin(auth_payload)
        offset = (page - 1) * page_size
        submissions, total = await self._repository.list_admin_submissions(
            work_date=work_date,
            date_from=date_from,
            date_to=date_to,
            status=status,
            shift=shift,
            workorder_status=workorder_status,
            owner_user_id=owner_user_id,
            ticket_number=ticket_number,
            file_submission_pending=file_submission_pending,
            offset=offset,
            limit=page_size,
        )
        submission_ids = [submission.id for submission in submissions]
        attachment_counts = await self._repository.count_active_attachments_for_submissions(submission_ids)

        workorder_ids = list({s.workorder_id for s in submissions})
        workorders_map = await self._repository.get_workorders_by_ids(workorder_ids)
        agg_map = await self._repository.get_aggregate_progress_batch(workorder_ids)

        views = [
            self._to_view(
                submission,
                active_attachment_count=attachment_counts.get(submission.id, 0),
                workorder_summary=self._to_workorder_summary(
                    workorders_map[submission.workorder_id],
                    agg_map.get(submission.workorder_id, (0, 0)),
                )
                if submission.workorder_id in workorders_map
                else None,
            )
            for submission in submissions
        ]
        return views, total

    async def get_admin_submission(
        self,
        auth_payload: dict[str, Any],
        submission_id: uuid.UUID,
    ) -> SubmissionView:
        await self._require_approved_admin(auth_payload)
        submission = await self._repository.get_submission_by_id(submission_id)
        if submission is None:
            raise AppError(ErrorCode.NOT_FOUND, "Submission was not found.", status_code=404)
        active_attachments = await self._repository.count_active_attachments(submission.id)
        workorder = await self._repository.get_workorder_by_id(submission.workorder_id)
        workorder_summary: WorkorderSummary | None = None
        if workorder is not None:
            agg = await self._repository.get_aggregate_progress(submission.workorder_id)
            workorder_summary = self._to_workorder_summary(workorder, agg)
        return self._to_view(submission, active_attachment_count=active_attachments, workorder_summary=workorder_summary)

    async def update_admin_submission(
        self,
        auth_payload: dict[str, Any],
        submission_id: uuid.UUID,
        request: UpdateSubmissionRequest,
    ) -> SubmissionView:
        actor = await self._require_approved_admin(auth_payload)
        async with self._repository.transaction():
            submission = await self._repository.get_submission_by_id(submission_id)
            if submission is None:
                raise AppError(ErrorCode.NOT_FOUND, "Submission was not found.", status_code=404)
            if submission.version_number != request.version_number:
                raise AppError(
                    ErrorCode.VERSION_CONFLICT,
                    "Submission version is stale. Refresh and retry.",
                    status_code=409,
                )

            changed_fields = self._apply_updates(submission, request)
            if changed_fields:
                self._validate_grids(
                    skipped_grids=submission.skipped_grids,
                    force_tested_grids=submission.force_tested_grids,
                    completed_grids=submission.completed_grids,
                )
                duplicate = await self._repository.get_submission_by_workorder_date(
                    workorder_id=submission.workorder_id,
                    work_date=submission.work_date,
                    exclude_submission_id=submission.id,
                )
                if duplicate is not None:
                    raise AppError(
                        ErrorCode.SUBMISSION_ALREADY_EXISTS,
                        "A submission already exists for this workorder on that date.",
                        status_code=409,
                    )
                now = datetime.now(UTC)
                submission.version_number += 1
                submission.updated_at = now
                submission.updated_by_user_id = actor.id
                await self._repository.save_submission(submission)
                await self._repository.create_audit_log(
                    self._build_audit_log(
                        submission_id=submission.id,
                        action_type=AuditActionType.UPDATED,
                        actor=actor,
                        changed_fields=sorted(changed_fields),
                    )
                )

                # Auto-complete parent workorder if aggregate meets total
                workorder = await self._repository.get_workorder_by_id(submission.workorder_id)
                if workorder is not None and workorder.status != WorkorderStatus.COMPLETED:
                    agg = await self._repository.get_aggregate_progress(submission.workorder_id)
                    if agg[0] + agg[1] >= workorder.total_grids:
                        now2 = datetime.now(UTC)
                        workorder.status = WorkorderStatus.COMPLETED
                        workorder.completed_at = now2
                        workorder.completed_by_user_id = actor.id
                        workorder.updated_at = now2
                        workorder.updated_by_user_id = actor.id
                        await self._repository.save_workorder(workorder)

        active_attachments = await self._repository.count_active_attachments(submission.id)
        return self._to_view(submission, active_attachment_count=active_attachments)

    async def get_submission_audit(
        self,
        auth_payload: dict[str, Any],
        submission_id: uuid.UUID,
    ) -> list[SubmissionAuditView]:
        await self._require_approved_admin(auth_payload)
        submission = await self._repository.get_submission_by_id(submission_id)
        if submission is None:
            raise AppError(ErrorCode.NOT_FOUND, "Submission was not found.", status_code=404)
        logs = await self._repository.get_submission_audit_logs(submission_id)
        return [self._to_audit_view(entry) for entry in logs]

    def _apply_updates(self, submission: Submission, request: UpdateSubmissionRequest) -> set[str]:
        changed_fields: set[str] = set()
        fields_set = set(request.model_fields_set)
        fields_set.discard("version_number")

        if "work_date" in fields_set:
            assert request.work_date is not None
            if request.work_date != submission.work_date:
                submission.work_date = request.work_date
                changed_fields.add("work_date")

        if "shift" in fields_set:
            assert request.shift is not None
            if request.shift != submission.shift:
                submission.shift = request.shift
                changed_fields.add("shift")

        if "team_number" in fields_set:
            normalized_team = self._normalize_optional_text(request.team_number)
            if normalized_team != submission.team_number:
                submission.team_number = normalized_team
                changed_fields.add("team_number")

        if "ticket_number" in fields_set:
            normalized_ticket = self._normalize_optional_text(request.ticket_number)
            if normalized_ticket != submission.ticket_number:
                submission.ticket_number = normalized_ticket
                changed_fields.add("ticket_number")

        for field in ("skipped_grids", "force_tested_grids", "completed_grids"):
            if field not in fields_set:
                continue
            value = getattr(request, field)
            if value is None:
                raise AppError(
                    ErrorCode.VALIDATION_ERROR,
                    f"{field} cannot be null.",
                    status_code=400,
                )
            if value != getattr(submission, field):
                setattr(submission, field, value)
                changed_fields.add(field)

        return changed_fields

    async def _require_approved_user(self, auth_payload: dict[str, Any]) -> AppUser:
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
                "Account is not approved for submission actions.",
                status_code=403,
            )
        return actor

    async def _require_approved_admin(self, auth_payload: dict[str, Any]) -> AppUser:
        actor = await self._require_approved_user(auth_payload)
        if actor.approved_role != RequestedRole.ADMIN:
            raise AppError(
                ErrorCode.ADMIN_ONLY,
                "Admin access required.",
                status_code=403,
            )
        return actor

    @staticmethod
    def _assert_owner(actor: AppUser, submission: Submission) -> None:
        if submission.owner_user_id != actor.id:
            raise AppError(
                ErrorCode.NOT_OWNER,
                "Submission does not belong to the authenticated user.",
                status_code=403,
            )

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
    def _normalize_optional_text(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized if normalized else None

    @staticmethod
    def _validate_grids(
        *,
        skipped_grids: int,
        force_tested_grids: int,
        completed_grids: int,
    ) -> None:
        for field, value in (
            ("skipped_grids", skipped_grids),
            ("force_tested_grids", force_tested_grids),
            ("completed_grids", completed_grids),
        ):
            if value < 0:
                raise AppError(
                    ErrorCode.INVALID_GRID_MATH,
                    "Grid values must be non-negative.",
                    status_code=400,
                    details={"field": field, "value": value},
                )

    @staticmethod
    def _is_file_submission_pending(
        *,
        status: SubmissionStatus,
        active_attachment_count: int,
    ) -> bool:
        return status == SubmissionStatus.CHECKED_OUT and active_attachment_count == 0

    @staticmethod
    def _build_audit_log(
        *,
        submission_id: uuid.UUID,
        action_type: AuditActionType,
        actor: AppUser,
        changed_fields: list[str] | None = None,
    ) -> SubmissionAuditLog:
        return SubmissionAuditLog(
            id=uuid.uuid4(),
            submission_id=submission_id,
            action_type=action_type,
            actor_user_id=actor.id,
            actor_role=(
                actor.approved_role.value
                if actor.approved_role is not None
                else actor.requested_role.value
            ),
            source=AuditSource.WEB,
            changed_fields_json={"fields": changed_fields} if changed_fields else None,
            before_snapshot_json=None,
            after_snapshot_json=None,
            created_at=datetime.now(UTC),
        )

    def _to_view(
        self,
        submission: Submission,
        *,
        active_attachment_count: int,
        workorder_summary: WorkorderSummary | None = None,
    ) -> SubmissionView:
        return SubmissionView(
            id=submission.id,
            client_generated_id=submission.client_generated_id,
            workorder_id=submission.workorder_id,
            owner_user_id=submission.owner_user_id,
            submitter_name_snapshot=submission.submitter_name_snapshot,
            submitter_email_snapshot=submission.submitter_email_snapshot,
            work_date=submission.work_date,
            shift=submission.shift,
            team_number=submission.team_number,
            ticket_number=submission.ticket_number,
            skipped_grids=submission.skipped_grids,
            force_tested_grids=submission.force_tested_grids,
            completed_grids=submission.completed_grids,
            status=submission.status,
            version_number=submission.version_number,
            started_at=submission.started_at,
            ended_at=submission.ended_at,
            created_at=submission.created_at,
            updated_at=submission.updated_at,
            file_submission_pending=self._is_file_submission_pending(
                status=submission.status,
                active_attachment_count=active_attachment_count,
            ),
            workorder_summary=workorder_summary,
        )

    @staticmethod
    def _to_workorder_summary(
        workorder: Workorder, aggregate: tuple[int, int]
    ) -> WorkorderSummary:
        completed_grids, skipped_grids = aggregate
        done = completed_grids + skipped_grids
        remaining = max(workorder.total_grids - done, 0)
        progress = (done / workorder.total_grids * 100) if workorder.total_grids > 0 else 0.0
        return WorkorderSummary(
            workorder_code=workorder.workorder_code,
            region=workorder.region,
            status=workorder.status,
            total_grids=workorder.total_grids,
            completed_grids=completed_grids,
            skipped_grids=skipped_grids,
            remaining_grids=remaining,
            progress_percent=round(progress, 2),
        )

    @staticmethod
    def _to_audit_view(entry: SubmissionAuditLog) -> SubmissionAuditView:
        return SubmissionAuditView(
            id=entry.id,
            submission_id=entry.submission_id,
            action_type=entry.action_type,
            actor_user_id=entry.actor_user_id,
            actor_role=entry.actor_role,
            source=entry.source,
            changed_fields_json=entry.changed_fields_json,
            before_snapshot_json=entry.before_snapshot_json,
            after_snapshot_json=entry.after_snapshot_json,
            created_at=entry.created_at,
        )
