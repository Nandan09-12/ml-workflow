import re
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError

from app.core.enums import (
    AccountStatus,
    AuditActionType,
    AuditSource,
    RequestedRole,
    Shift,
    SubmissionStatus,
    Zone,
)
from app.core.errors import AppError, ErrorCode
from app.models.app_user import AppUser
from app.models.submission import Submission
from app.models.submission_audit_log import SubmissionAuditLog
from app.schemas.submissions import CreateSubmissionRequest, UpdateSubmissionRequest


@dataclass(frozen=True)
class SubmissionView:
    id: uuid.UUID
    client_generated_id: uuid.UUID
    owner_user_id: uuid.UUID
    submitter_name_snapshot: str
    submitter_email_snapshot: str
    zone: Zone
    work_date: date
    shift: Shift
    team_number: str | None
    ticket_number: str | None
    cluster_name: str
    cluster_name_normalized: str
    number_of_grids: int
    skipped_grids: int
    force_tested_grids: int
    pending_grids: int
    completed_grids: int
    status: SubmissionStatus
    version_number: int
    created_at: datetime
    updated_at: datetime
    file_submission_pending: bool


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

    async def get_duplicate_for_owner(
        self,
        *,
        owner_user_id: uuid.UUID,
        work_date: date,
        shift: Shift,
        cluster_name_normalized: str,
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
        zone: Zone | None = None,
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
        zone: Zone | None = None,
        shift: Shift | None = None,
        owner_user_id: uuid.UUID | None = None,
        cluster_name: str | None = None,
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

    def transaction(self) -> Any: ...


class SubmissionService:
    _ZONE_TIMEZONES: dict[Zone, str] = {
        Zone.NORTHEAST: "America/New_York",
        Zone.SOUTH_FLORIDA: "America/New_York",
        Zone.CENTRAL: "America/Chicago",
    }

    def __init__(self, repository: SubmissionRepositoryProtocol) -> None:
        self._repository = repository

    async def create_submission(
        self,
        auth_payload: dict[str, Any],
        request: CreateSubmissionRequest,
    ) -> SubmissionView:
        actor = await self._require_approved_user(auth_payload)
        cluster_name = request.cluster_name.strip()
        cluster_name_normalized = self._normalize_cluster_name(cluster_name)
        self._validate_work_date(zone=request.zone, work_date=request.work_date)
        self._validate_grid_math(
            number_of_grids=request.number_of_grids,
            skipped_grids=request.skipped_grids,
            force_tested_grids=request.force_tested_grids,
            pending_grids=request.pending_grids,
            completed_grids=request.completed_grids,
        )

        duplicate = await self._repository.get_duplicate_for_owner(
            owner_user_id=actor.id,
            work_date=request.work_date,
            shift=request.shift,
            cluster_name_normalized=cluster_name_normalized,
        )
        if duplicate is not None:
            raise AppError(
                ErrorCode.SUBMISSION_ALREADY_EXISTS,
                "Submission already exists for the same owner, date, shift, and cluster.",
                status_code=409,
            )

        now = datetime.now(UTC)
        submission = Submission(
            id=uuid.uuid4(),
            client_generated_id=request.client_generated_id or uuid.uuid4(),
            owner_user_id=actor.id,
            submitter_name_snapshot=actor.full_name,
            submitter_email_snapshot=actor.email,
            zone=request.zone,
            work_date=request.work_date,
            shift=request.shift,
            team_number=self._normalize_optional_text(request.team_number),
            ticket_number=self._normalize_optional_text(request.ticket_number),
            cluster_name=cluster_name,
            cluster_name_normalized=cluster_name_normalized,
            number_of_grids=request.number_of_grids,
            skipped_grids=request.skipped_grids,
            force_tested_grids=request.force_tested_grids,
            pending_grids=request.pending_grids,
            completed_grids=request.completed_grids,
            status=SubmissionStatus.ONGOING,
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
                            "zone",
                            "work_date",
                            "shift",
                            "team_number",
                            "ticket_number",
                            "cluster_name",
                            "cluster_name_normalized",
                            "number_of_grids",
                            "skipped_grids",
                            "force_tested_grids",
                            "pending_grids",
                            "completed_grids",
                            "status",
                            "version_number",
                        ],
                    )
                )
        except IntegrityError as exc:
            raise AppError(
                ErrorCode.SUBMISSION_ALREADY_EXISTS,
                "Submission already exists for the same owner, date, shift, and cluster.",
                status_code=409,
            ) from exc

        active_attachments = await self._repository.count_active_attachments(created.id)
        return self._to_view(created, active_attachment_count=active_attachments)

    async def list_my_submissions(
        self,
        auth_payload: dict[str, Any],
        *,
        work_date: date | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        status: SubmissionStatus | None = None,
        zone: Zone | None = None,
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
            zone=zone,
            shift=shift,
            offset=offset,
            limit=page_size,
        )

        submission_ids = [submission.id for submission in submissions]
        attachment_counts = await self._repository.count_active_attachments_for_submissions(submission_ids)
        views = [
            self._to_view(submission, active_attachment_count=attachment_counts.get(submission.id, 0))
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
        return self._to_view(submission, active_attachment_count=active_attachments)

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
            if submission.status != SubmissionStatus.ONGOING:
                raise AppError(
                    ErrorCode.SUBMISSION_ALREADY_COMPLETED,
                    "Completed submissions cannot be edited.",
                    status_code=400,
                )
            if submission.version_number != request.version_number:
                raise AppError(
                    ErrorCode.VERSION_CONFLICT,
                    "Submission version is stale. Refresh and retry.",
                    status_code=409,
                )

            changed_fields = self._apply_updates(submission, request)
            if changed_fields:
                self._validate_work_date(zone=submission.zone, work_date=submission.work_date)
                self._validate_grid_math(
                    number_of_grids=submission.number_of_grids,
                    skipped_grids=submission.skipped_grids,
                    force_tested_grids=submission.force_tested_grids,
                    pending_grids=submission.pending_grids,
                    completed_grids=submission.completed_grids,
                )
                duplicate = await self._repository.get_duplicate_for_owner(
                    owner_user_id=submission.owner_user_id,
                    work_date=submission.work_date,
                    shift=submission.shift,
                    cluster_name_normalized=submission.cluster_name_normalized,
                    exclude_submission_id=submission.id,
                )
                if duplicate is not None:
                    raise AppError(
                        ErrorCode.SUBMISSION_ALREADY_EXISTS,
                        "Submission already exists for the same owner, date, shift, and cluster.",
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
            if submission.status == SubmissionStatus.COMPLETED:
                raise AppError(
                    ErrorCode.SUBMISSION_ALREADY_COMPLETED,
                    "Submission is already completed.",
                    status_code=400,
                )
            if submission.pending_grids != 0:
                raise AppError(
                    ErrorCode.PENDING_GRIDS_MUST_BE_ZERO,
                    "pending_grids must be 0 before completion.",
                    status_code=400,
                )

            now = datetime.now(UTC)
            submission.status = SubmissionStatus.COMPLETED
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
                        "completed_at",
                        "completed_by_user_id",
                        "version_number",
                    ],
                )
            )

        active_attachments = await self._repository.count_active_attachments(submission.id)
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
            submission.status = SubmissionStatus.ONGOING
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
        zone: Zone | None = None,
        shift: Shift | None = None,
        owner_user_id: uuid.UUID | None = None,
        cluster_name: str | None = None,
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
            zone=zone,
            shift=shift,
            owner_user_id=owner_user_id,
            cluster_name=cluster_name,
            ticket_number=ticket_number,
            file_submission_pending=file_submission_pending,
            offset=offset,
            limit=page_size,
        )
        submission_ids = [submission.id for submission in submissions]
        attachment_counts = await self._repository.count_active_attachments_for_submissions(submission_ids)
        views = [
            self._to_view(submission, active_attachment_count=attachment_counts.get(submission.id, 0))
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
        return self._to_view(submission, active_attachment_count=active_attachments)

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
                self._validate_work_date(zone=submission.zone, work_date=submission.work_date)
                self._validate_grid_math(
                    number_of_grids=submission.number_of_grids,
                    skipped_grids=submission.skipped_grids,
                    force_tested_grids=submission.force_tested_grids,
                    pending_grids=submission.pending_grids,
                    completed_grids=submission.completed_grids,
                )
                if (
                    submission.status == SubmissionStatus.COMPLETED
                    and submission.pending_grids != 0
                ):
                    raise AppError(
                        ErrorCode.PENDING_GRIDS_MUST_BE_ZERO,
                        "pending_grids must remain 0 while submission is completed.",
                        status_code=400,
                    )
                duplicate = await self._repository.get_duplicate_for_owner(
                    owner_user_id=submission.owner_user_id,
                    work_date=submission.work_date,
                    shift=submission.shift,
                    cluster_name_normalized=submission.cluster_name_normalized,
                    exclude_submission_id=submission.id,
                )
                if duplicate is not None:
                    raise AppError(
                        ErrorCode.SUBMISSION_ALREADY_EXISTS,
                        "Submission already exists for the same owner, date, shift, and cluster.",
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

        if "zone" in fields_set:
            assert request.zone is not None
            if request.zone != submission.zone:
                submission.zone = request.zone
                changed_fields.add("zone")

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

        if "cluster_name" in fields_set:
            if request.cluster_name is None:
                raise AppError(
                    ErrorCode.VALIDATION_ERROR,
                    "cluster_name cannot be null.",
                    status_code=400,
                )
            cluster_name = request.cluster_name.strip()
            normalized_cluster = self._normalize_cluster_name(cluster_name)
            if cluster_name != submission.cluster_name:
                submission.cluster_name = cluster_name
                changed_fields.add("cluster_name")
            if normalized_cluster != submission.cluster_name_normalized:
                submission.cluster_name_normalized = normalized_cluster
                changed_fields.add("cluster_name_normalized")

        numeric_fields = (
            "number_of_grids",
            "skipped_grids",
            "force_tested_grids",
            "pending_grids",
            "completed_grids",
        )
        for field in numeric_fields:
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
    def _normalize_cluster_name(cluster_name: str) -> str:
        normalized = unicodedata.normalize("NFKC", cluster_name)
        normalized = normalized.strip()
        normalized = normalized.replace("-", " ").replace("_", " ")
        normalized = re.sub(r"\s+", " ", normalized)
        normalized = normalized.upper()
        if not normalized:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "cluster_name cannot be empty.",
                status_code=400,
            )
        return normalized

    def _validate_work_date(self, *, zone: Zone, work_date: date) -> None:
        timezone = ZoneInfo(self._ZONE_TIMEZONES[zone])
        zone_today = datetime.now(timezone).date()
        if work_date > zone_today:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "work_date cannot be in the future for the selected zone.",
                status_code=400,
                details={
                    "zone": zone.value,
                    "zone_current_date": zone_today.isoformat(),
                    "work_date": work_date.isoformat(),
                },
            )

    @staticmethod
    def _validate_grid_math(
        *,
        number_of_grids: int,
        skipped_grids: int,
        force_tested_grids: int,
        pending_grids: int,
        completed_grids: int,
    ) -> None:
        values = {
            "number_of_grids": number_of_grids,
            "skipped_grids": skipped_grids,
            "force_tested_grids": force_tested_grids,
            "pending_grids": pending_grids,
            "completed_grids": completed_grids,
        }
        for field, value in values.items():
            if value < 0:
                raise AppError(
                    ErrorCode.INVALID_GRID_MATH,
                    "Grid values must be non-negative.",
                    status_code=400,
                    details={"field": field, "value": value},
                )

        if skipped_grids > number_of_grids:
            raise AppError(
                ErrorCode.INVALID_GRID_MATH,
                "skipped_grids cannot exceed number_of_grids.",
                status_code=400,
            )
        if pending_grids > number_of_grids:
            raise AppError(
                ErrorCode.INVALID_GRID_MATH,
                "pending_grids cannot exceed number_of_grids.",
                status_code=400,
            )
        if completed_grids > number_of_grids:
            raise AppError(
                ErrorCode.INVALID_GRID_MATH,
                "completed_grids cannot exceed number_of_grids.",
                status_code=400,
            )
        if completed_grids + pending_grids + skipped_grids != number_of_grids:
            raise AppError(
                ErrorCode.INVALID_GRID_MATH,
                "completed_grids + pending_grids + skipped_grids must equal number_of_grids.",
                status_code=400,
            )

    @staticmethod
    def _is_file_submission_pending(
        *,
        status: SubmissionStatus,
        active_attachment_count: int,
    ) -> bool:
        return status == SubmissionStatus.COMPLETED and active_attachment_count == 0

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
    ) -> SubmissionView:
        return SubmissionView(
            id=submission.id,
            client_generated_id=submission.client_generated_id,
            owner_user_id=submission.owner_user_id,
            submitter_name_snapshot=submission.submitter_name_snapshot,
            submitter_email_snapshot=submission.submitter_email_snapshot,
            zone=submission.zone,
            work_date=submission.work_date,
            shift=submission.shift,
            team_number=submission.team_number,
            ticket_number=submission.ticket_number,
            cluster_name=submission.cluster_name,
            cluster_name_normalized=submission.cluster_name_normalized,
            number_of_grids=submission.number_of_grids,
            skipped_grids=submission.skipped_grids,
            force_tested_grids=submission.force_tested_grids,
            pending_grids=submission.pending_grids,
            completed_grids=submission.completed_grids,
            status=submission.status,
            version_number=submission.version_number,
            created_at=submission.created_at,
            updated_at=submission.updated_at,
            file_submission_pending=self._is_file_submission_pending(
                status=submission.status,
                active_attachment_count=active_attachment_count,
            ),
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
