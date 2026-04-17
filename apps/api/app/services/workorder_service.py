import unicodedata
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, Protocol

from app.core.enums import (
    AccountStatus,
    AuditActionType,
    AuditSource,
    Region,
    SubmissionStatus,
    WorkorderStatus,
)
from app.core.errors import AppError, ErrorCode
from app.models.app_user import AppUser
from app.models.submission import Submission
from app.models.submission_audit_log import SubmissionAuditLog
from app.models.workorder import Workorder
from app.schemas.workorders import StartDriveRequest, WorkorderSummary, WorkorderView
from app.services.submission_service import SubmissionView


@dataclass(frozen=True)
class SubmissionWithWorkorderView(SubmissionView):
    workorder: WorkorderSummary = None  # type: ignore[assignment]


class WorkorderRepositoryProtocol(Protocol):
    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None: ...

    async def get_workorder_by_normalized_code(self, code: str) -> Workorder | None: ...

    async def create_workorder(self, workorder: Workorder) -> Workorder: ...

    async def get_workorder_by_id(self, workorder_id: uuid.UUID) -> Workorder | None: ...

    async def save_workorder(self, workorder: Workorder) -> Workorder: ...

    async def create_submission(self, submission: Submission) -> Submission: ...

    async def get_submission_by_workorder_date(
        self,
        *,
        workorder_id: uuid.UUID,
        work_date: date,
        exclude_submission_id: uuid.UUID | None = None,
    ) -> Submission | None: ...

    async def create_audit_log(self, log: SubmissionAuditLog) -> SubmissionAuditLog: ...

    async def get_aggregate_progress(self, workorder_id: uuid.UUID) -> tuple[int, int]: ...

    def transaction(self) -> Any: ...


class WorkorderService:
    def __init__(
        self,
        repository: WorkorderRepositoryProtocol,
        *,
        _today_override: date | None = None,
    ) -> None:
        self._repository = repository
        self._today_override = _today_override

    def _today_for_region(self, region: Region) -> date:
        if self._today_override is not None:
            return self._today_override
        from zoneinfo import ZoneInfo

        tz_map: dict[Region, str] = {
            Region.NE_UP: "America/New_York",
            Region.SOUTH_FLORIDA: "America/New_York",
            Region.CENTRAL: "America/Chicago",
        }
        tz = ZoneInfo(tz_map.get(region, "America/New_York"))
        return datetime.now(tz).date()

    @staticmethod
    def normalize_code(code: str) -> str:
        normalized = unicodedata.normalize("NFKC", code)
        normalized = normalized.strip().upper().replace(" ", "")
        if not normalized:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "workorder_code cannot be blank after normalization.",
                status_code=400,
            )
        return normalized

    async def start_drive(
        self,
        auth_payload: dict[str, Any],
        request: StartDriveRequest,
    ) -> SubmissionWithWorkorderView:
        actor = await self._require_approved_user(auth_payload)
        normalized = self.normalize_code(request.workorder_code)

        async with self._repository.transaction():
            workorder = await self._repository.get_workorder_by_normalized_code(normalized)

            if workorder is None:
                # Creating a new workorder — region and total_grids are required
                if request.region is None:
                    raise AppError(
                        ErrorCode.WORKORDER_REGION_MISMATCH,
                        "region is required when creating a new workorder.",
                        status_code=400,
                    )
                if request.total_grids is None:
                    raise AppError(
                        ErrorCode.WORKORDER_TOTAL_GRIDS_MISMATCH,
                        "total_grids is required when creating a new workorder.",
                        status_code=400,
                    )
                now = datetime.now(UTC)
                workorder = Workorder(
                    id=uuid.uuid4(),
                    workorder_code=request.workorder_code.strip(),
                    workorder_code_normalized=normalized,
                    region=request.region,
                    total_grids=request.total_grids,
                    status=WorkorderStatus.ACTIVE,
                    created_at=now,
                    created_by_user_id=actor.id,
                    updated_at=now,
                    updated_by_user_id=actor.id,
                    completed_at=None,
                    completed_by_user_id=None,
                )
                workorder = await self._repository.create_workorder(workorder)
            else:
                # Attaching to existing — validate provided fields match
                if workorder.status == WorkorderStatus.COMPLETED:
                    raise AppError(
                        ErrorCode.WORKORDER_ALREADY_COMPLETED,
                        "Cannot start a drive for a completed workorder.",
                        status_code=400,
                    )
                if request.region is not None and request.region != workorder.region:
                    raise AppError(
                        ErrorCode.WORKORDER_REGION_MISMATCH,
                        "Provided region does not match the existing workorder.",
                        status_code=409,
                    )
                if request.total_grids is not None and request.total_grids != workorder.total_grids:
                    raise AppError(
                        ErrorCode.WORKORDER_TOTAL_GRIDS_MISMATCH,
                        "Provided total_grids does not match the existing workorder.",
                        status_code=409,
                    )

            # Future work_date guard
            today = self._today_for_region(workorder.region)
            if request.work_date > today:
                raise AppError(
                    ErrorCode.VALIDATION_ERROR,
                    "work_date cannot be in the future.",
                    status_code=422,
                )

            # Check for duplicate submission on same workorder+date
            duplicate = await self._repository.get_submission_by_workorder_date(
                workorder_id=workorder.id,
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
                workorder_id=workorder.id,
                owner_user_id=actor.id,
                submitter_name_snapshot=actor.full_name,
                submitter_email_snapshot=actor.email,
                work_date=request.work_date,
                shift=request.shift,
                team_number=_normalize_optional_text(request.team_number),
                ticket_number=_normalize_optional_text(request.ticket_number),
                skipped_grids=0,
                force_tested_grids=0,
                completed_grids=0,
                status=SubmissionStatus.IN_PROGRESS,
                started_at=now,
                ended_at=None,
                created_at=now,
                created_by_user_id=actor.id,
                updated_at=now,
                updated_by_user_id=actor.id,
                completed_at=None,
                completed_by_user_id=None,
                reopened_at=None,
                reopened_by_user_id=None,
                version_number=1,
            )
            created = await self._repository.create_submission(submission)
            await self._repository.create_audit_log(
                _build_audit_log(
                    submission_id=created.id,
                    action_type=AuditActionType.CREATED,
                    actor=actor,
                    changed_fields=["workorder_id", "work_date", "shift", "status", "started_at"],
                )
            )

        agg = await self._repository.get_aggregate_progress(workorder.id)
        summary = _to_workorder_summary(workorder, agg)
        return _to_submission_with_workorder_view(created, summary, active_attachment_count=0)

    async def lookup_workorder(
        self,
        auth_payload: dict[str, Any],
        workorder_code: str,
    ) -> WorkorderView:
        await self._require_approved_user(auth_payload)
        normalized = self.normalize_code(workorder_code)
        workorder = await self._repository.get_workorder_by_normalized_code(normalized)
        if workorder is None:
            raise AppError(
                ErrorCode.WORKORDER_NOT_FOUND,
                "Workorder not found.",
                status_code=404,
            )
        agg = await self._repository.get_aggregate_progress(workorder.id)
        return _to_workorder_view(workorder, agg)

    async def maybe_auto_complete_workorder(
        self,
        *,
        workorder: Workorder,
        actor: AppUser,
    ) -> bool:
        """Mark workorder COMPLETED if aggregate progress meets or exceeds total_grids.

        Returns True if the workorder was completed, False otherwise.
        """
        if workorder.status == WorkorderStatus.COMPLETED:
            return False
        completed_grids, skipped_grids = await self._repository.get_aggregate_progress(workorder.id)
        if completed_grids + skipped_grids >= workorder.total_grids:
            now = datetime.now(UTC)
            workorder.status = WorkorderStatus.COMPLETED
            workorder.completed_at = now
            workorder.completed_by_user_id = actor.id
            workorder.updated_at = now
            workorder.updated_by_user_id = actor.id
            await self._repository.save_workorder(workorder)
            return True
        return False

    async def _require_approved_user(self, auth_payload: dict[str, Any]) -> AppUser:
        raw_sub = auth_payload.get("sub")
        if raw_sub is None:
            raise AppError(ErrorCode.UNAUTHORIZED, "Missing token subject.", status_code=401)
        try:
            auth_user_id = uuid.UUID(str(raw_sub))
        except (TypeError, ValueError) as exc:
            raise AppError(ErrorCode.UNAUTHORIZED, "Invalid token subject.", status_code=401) from exc
        actor = await self._repository.get_by_auth_user_id(auth_user_id)
        if actor is None:
            raise AppError(ErrorCode.NOT_FOUND, "User profile not found.", status_code=404)
        if actor.account_status != AccountStatus.APPROVED:
            raise AppError(
                ErrorCode.ACCOUNT_NOT_APPROVED,
                "Account is not approved.",
                status_code=403,
            )
        return actor


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized if normalized else None


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


def _to_workorder_summary(workorder: Workorder, aggregate: tuple[int, int]) -> WorkorderSummary:
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


def _to_workorder_view(workorder: Workorder, aggregate: tuple[int, int]) -> WorkorderView:
    completed_grids, skipped_grids = aggregate
    done = completed_grids + skipped_grids
    remaining = max(workorder.total_grids - done, 0)
    progress = (done / workorder.total_grids * 100) if workorder.total_grids > 0 else 0.0
    return WorkorderView(
        id=workorder.id,
        workorder_code=workorder.workorder_code,
        region=workorder.region,
        status=workorder.status,
        total_grids=workorder.total_grids,
        completed_grids=completed_grids,
        skipped_grids=skipped_grids,
        remaining_grids=remaining,
        progress_percent=round(progress, 2),
        created_at=workorder.created_at,
        updated_at=workorder.updated_at,
    )


def _to_submission_with_workorder_view(
    submission: Submission,
    workorder_summary: WorkorderSummary,
    *,
    active_attachment_count: int,
) -> SubmissionWithWorkorderView:
    file_pending = (
        submission.status == SubmissionStatus.COMPLETED and active_attachment_count == 0
    )
    return SubmissionWithWorkorderView(
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
        file_submission_pending=file_pending,
        workorder=workorder_summary,
    )
