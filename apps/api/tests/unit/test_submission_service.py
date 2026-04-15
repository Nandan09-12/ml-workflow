import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from app.core.enums import (
    AccountStatus,
    AuditActionType,
    RequestedRole,
    Shift,
    SubmissionStatus,
    Zone,
)
from app.core.errors import AppError
from app.models.app_user import AppUser
from app.models.submission import Submission
from app.models.submission_audit_log import SubmissionAuditLog
from app.schemas.submissions import CreateSubmissionRequest, UpdateSubmissionRequest
from app.services.submission_service import SubmissionService


class FakeSubmissionRepository:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.owner_user = AppUser(
            id=uuid.uuid4(),
            auth_user_id=uuid.uuid4(),
            full_name="Owner User",
            email="owner@example.com",
            requested_role=RequestedRole.DRIVE_TESTER,
            approved_role=RequestedRole.DRIVE_TESTER,
            account_status=AccountStatus.APPROVED,
            approved_at=now,
            approved_by_user_id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
        )
        self.other_user = AppUser(
            id=uuid.uuid4(),
            auth_user_id=uuid.uuid4(),
            full_name="Other User",
            email="other@example.com",
            requested_role=RequestedRole.DRIVE_TESTER,
            approved_role=RequestedRole.DRIVE_TESTER,
            account_status=AccountStatus.APPROVED,
            approved_at=now,
            approved_by_user_id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
        )
        self.admin_user = AppUser(
            id=uuid.uuid4(),
            auth_user_id=uuid.uuid4(),
            full_name="Admin User",
            email="admin@example.com",
            requested_role=RequestedRole.ADMIN,
            approved_role=RequestedRole.ADMIN,
            account_status=AccountStatus.APPROVED,
            approved_at=now,
            approved_by_user_id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
        )
        self.pending_user = AppUser(
            id=uuid.uuid4(),
            auth_user_id=uuid.uuid4(),
            full_name="Pending User",
            email="pending@example.com",
            requested_role=RequestedRole.DRIVE_TESTER,
            approved_role=None,
            account_status=AccountStatus.PENDING_APPROVAL,
            approved_at=None,
            approved_by_user_id=None,
            created_at=now,
            updated_at=now,
        )
        self.users = [self.owner_user, self.other_user, self.admin_user, self.pending_user]
        self.submissions: list[Submission] = []
        self.audit_logs: list[SubmissionAuditLog] = []
        self.attachment_counts: dict[uuid.UUID, int] = {}
        self.transaction_entries = 0

    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None:
        return next((user for user in self.users if user.auth_user_id == auth_user_id), None)

    async def get_duplicate_for_owner(
        self,
        *,
        owner_user_id: uuid.UUID,
        work_date: date,
        shift: Shift,
        cluster_name_normalized: str,
        exclude_submission_id: uuid.UUID | None = None,
    ) -> Submission | None:
        return next(
            (
                submission
                for submission in self.submissions
                if submission.owner_user_id == owner_user_id
                and submission.work_date == work_date
                and submission.shift == shift
                and submission.cluster_name_normalized == cluster_name_normalized
                and submission.id != exclude_submission_id
            ),
            None,
        )

    async def create_submission(self, submission: Submission) -> Submission:
        self.submissions.append(submission)
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
        items = [submission for submission in self.submissions if submission.owner_user_id == owner_user_id]
        if work_date is not None:
            items = [submission for submission in items if submission.work_date == work_date]
        if date_from is not None:
            items = [submission for submission in items if submission.work_date >= date_from]
        if date_to is not None:
            items = [submission for submission in items if submission.work_date <= date_to]
        if status is not None:
            items = [submission for submission in items if submission.status == status]
        if zone is not None:
            items = [submission for submission in items if submission.zone == zone]
        if shift is not None:
            items = [submission for submission in items if submission.shift == shift]
        total = len(items)
        return items[offset : offset + limit], total

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
        items = list(self.submissions)
        if work_date is not None:
            items = [submission for submission in items if submission.work_date == work_date]
        if date_from is not None:
            items = [submission for submission in items if submission.work_date >= date_from]
        if date_to is not None:
            items = [submission for submission in items if submission.work_date <= date_to]
        if status is not None:
            items = [submission for submission in items if submission.status == status]
        if zone is not None:
            items = [submission for submission in items if submission.zone == zone]
        if shift is not None:
            items = [submission for submission in items if submission.shift == shift]
        if owner_user_id is not None:
            items = [submission for submission in items if submission.owner_user_id == owner_user_id]
        if cluster_name is not None:
            needle = cluster_name.strip().lower()
            items = [submission for submission in items if needle in submission.cluster_name.lower()]
        if ticket_number is not None:
            needle = ticket_number.strip().lower()
            items = [
                submission
                for submission in items
                if submission.ticket_number is not None and needle in submission.ticket_number.lower()
            ]
        if file_submission_pending is not None:
            items = [
                submission
                for submission in items
                if (
                    submission.status == SubmissionStatus.COMPLETED
                    and self.attachment_counts.get(submission.id, 0) == 0
                )
                == file_submission_pending
            ]
        total = len(items)
        return items[offset : offset + limit], total

    async def get_submission_by_id(self, submission_id: uuid.UUID) -> Submission | None:
        return next((submission for submission in self.submissions if submission.id == submission_id), None)

    async def save_submission(self, submission: Submission) -> Submission:
        return submission

    async def create_audit_log(self, log: SubmissionAuditLog) -> SubmissionAuditLog:
        self.audit_logs.append(log)
        return log

    async def get_submission_audit_logs(self, submission_id: uuid.UUID) -> list[SubmissionAuditLog]:
        return [log for log in self.audit_logs if log.submission_id == submission_id]

    async def count_active_attachments(self, submission_id: uuid.UUID) -> int:
        return self.attachment_counts.get(submission_id, 0)

    async def count_active_attachments_for_submissions(
        self,
        submission_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, int]:
        return {submission_id: self.attachment_counts.get(submission_id, 0) for submission_id in submission_ids}

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        self.transaction_entries += 1
        yield


def _auth_payload(user: AppUser) -> dict[str, Any]:
    return {"sub": str(user.auth_user_id), "email": user.email}


def _today_for_zone(zone: Zone) -> date:
    timezone_map = {
        Zone.NORTHEAST: "America/New_York",
        Zone.SOUTH_FLORIDA: "America/New_York",
        Zone.CENTRAL: "America/Chicago",
    }
    return datetime.now(ZoneInfo(timezone_map[zone])).date()


def _submission(
    owner_user_id: uuid.UUID,
    *,
    cluster_name: str = "North Cluster",
    cluster_name_normalized: str = "NORTH CLUSTER",
    work_date: date | None = None,
    shift: Shift = Shift.AM,
    status: SubmissionStatus = SubmissionStatus.ONGOING,
    version_number: int = 1,
) -> Submission:
    now = datetime.now(UTC)
    final_work_date = work_date or _today_for_zone(Zone.NORTHEAST)
    return Submission(
        id=uuid.uuid4(),
        client_generated_id=uuid.uuid4(),
        owner_user_id=owner_user_id,
        submitter_name_snapshot="Snapshot Name",
        submitter_email_snapshot="snapshot@example.com",
        zone=Zone.NORTHEAST,
        work_date=final_work_date,
        shift=shift,
        team_number="11",
        ticket_number="TKT-100",
        cluster_name=cluster_name,
        cluster_name_normalized=cluster_name_normalized,
        number_of_grids=10,
        skipped_grids=1,
        force_tested_grids=0,
        pending_grids=2,
        completed_grids=7,
        status=status,
        created_at=now,
        created_by_user_id=owner_user_id,
        updated_at=now,
        updated_by_user_id=owner_user_id,
        completed_at=None,
        completed_by_user_id=None,
        reopened_at=None,
        reopened_by_user_id=None,
        version_number=version_number,
    )


async def test_create_submission_applies_normalization_and_audit() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)

    created = await service.create_submission(
        _auth_payload(repo.owner_user),
        CreateSubmissionRequest(
            zone=Zone.NORTHEAST,
            work_date=_today_for_zone(Zone.NORTHEAST),
            shift=Shift.AM,
            team_number=" 11 ",
            ticket_number=" TKT-1 ",
            cluster_name="  Clu-ster__One  ",
            number_of_grids=10,
            skipped_grids=1,
            force_tested_grids=0,
            pending_grids=2,
            completed_grids=7,
        ),
    )

    assert created.owner_user_id == repo.owner_user.id
    assert created.cluster_name == "Clu-ster__One"
    assert created.cluster_name_normalized == "CLU STER ONE"
    assert created.status == SubmissionStatus.ONGOING
    assert created.version_number == 1
    assert created.file_submission_pending is False
    assert repo.transaction_entries == 1
    assert len(repo.audit_logs) == 1
    assert repo.audit_logs[0].action_type == AuditActionType.CREATED


async def test_create_submission_rejects_future_work_date() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    future_date = _today_for_zone(Zone.CENTRAL) + timedelta(days=1)

    with pytest.raises(AppError) as exc:
        await service.create_submission(
            _auth_payload(repo.owner_user),
            CreateSubmissionRequest(
                zone=Zone.CENTRAL,
                work_date=future_date,
                shift=Shift.AM,
                team_number="11",
                ticket_number="TKT-1",
                cluster_name="Cluster A",
                number_of_grids=10,
                skipped_grids=1,
                force_tested_grids=0,
                pending_grids=2,
                completed_grids=7,
            ),
        )

    assert exc.value.code.value == "VALIDATION_ERROR"
    assert exc.value.status_code == 400


async def test_create_submission_rejects_negative_force_tested_grids() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)

    with pytest.raises(AppError) as exc:
        await service.create_submission(
            _auth_payload(repo.owner_user),
            CreateSubmissionRequest(
                zone=Zone.NORTHEAST,
                work_date=_today_for_zone(Zone.NORTHEAST),
                shift=Shift.AM,
                team_number="11",
                ticket_number="TKT-1",
                cluster_name="Cluster A",
                number_of_grids=10,
                skipped_grids=1,
                force_tested_grids=-1,
                pending_grids=2,
                completed_grids=7,
            ),
        )

    assert exc.value.code.value == "INVALID_GRID_MATH"
    assert exc.value.status_code == 400


async def test_create_submission_rejects_duplicate_for_same_owner_date_shift_cluster() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    existing = _submission(
        repo.owner_user.id,
        cluster_name="Alpha-Cluster",
        cluster_name_normalized="ALPHA CLUSTER",
    )
    repo.submissions.append(existing)

    with pytest.raises(AppError) as exc:
        await service.create_submission(
            _auth_payload(repo.owner_user),
            CreateSubmissionRequest(
                zone=Zone.NORTHEAST,
                work_date=existing.work_date,
                shift=existing.shift,
                team_number="11",
                ticket_number="TKT-1",
                cluster_name=" alpha__cluster ",
                number_of_grids=10,
                skipped_grids=1,
                force_tested_grids=0,
                pending_grids=2,
                completed_grids=7,
            ),
        )

    assert exc.value.code.value == "SUBMISSION_ALREADY_EXISTS"
    assert exc.value.status_code == 409


async def test_list_submissions_returns_computed_file_submission_pending() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    completed_missing_file = _submission(
        repo.owner_user.id,
        status=SubmissionStatus.COMPLETED,
    )
    completed_with_file = _submission(
        repo.owner_user.id,
        status=SubmissionStatus.COMPLETED,
    )
    ongoing = _submission(repo.owner_user.id, status=SubmissionStatus.ONGOING)
    other_owner = _submission(repo.other_user.id, status=SubmissionStatus.COMPLETED)
    repo.submissions.extend([completed_missing_file, completed_with_file, ongoing, other_owner])
    repo.attachment_counts = {
        completed_missing_file.id: 0,
        completed_with_file.id: 2,
        ongoing.id: 0,
        other_owner.id: 0,
    }

    items, total = await service.list_my_submissions(_auth_payload(repo.owner_user), page=1, page_size=20)

    assert total == 3
    by_id = {item.id: item for item in items}
    assert by_id[completed_missing_file.id].file_submission_pending is True
    assert by_id[completed_with_file.id].file_submission_pending is False
    assert by_id[ongoing.id].file_submission_pending is False


async def test_get_submission_rejects_non_owner() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.other_user.id)
    repo.submissions.append(submission)

    with pytest.raises(AppError) as exc:
        await service.get_submission(_auth_payload(repo.owner_user), submission.id)

    assert exc.value.code.value == "NOT_OWNER"
    assert exc.value.status_code == 403


async def test_update_submission_requires_matching_version_number() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, version_number=2)
    repo.submissions.append(submission)

    with pytest.raises(AppError) as exc:
        await service.update_submission(
            _auth_payload(repo.owner_user),
            submission.id,
            UpdateSubmissionRequest(version_number=1, team_number="22"),
        )

    assert exc.value.code.value == "VERSION_CONFLICT"
    assert exc.value.status_code == 409


async def test_update_submission_applies_changes_revalidates_and_audits() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, version_number=1)
    repo.submissions.append(submission)

    updated = await service.update_submission(
        _auth_payload(repo.owner_user),
        submission.id,
        UpdateSubmissionRequest(
            version_number=1,
            cluster_name="  north-east_cluster  ",
            number_of_grids=12,
            skipped_grids=2,
            force_tested_grids=1,
            pending_grids=0,
            completed_grids=10,
        ),
    )

    assert updated.cluster_name == "north-east_cluster"
    assert updated.cluster_name_normalized == "NORTH EAST CLUSTER"
    assert updated.version_number == 2
    assert repo.transaction_entries == 1
    assert len(repo.audit_logs) == 1
    assert repo.audit_logs[0].action_type == AuditActionType.UPDATED


async def test_update_submission_rejects_completed_submission() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, status=SubmissionStatus.COMPLETED, version_number=1)
    repo.submissions.append(submission)

    with pytest.raises(AppError) as exc:
        await service.update_submission(
            _auth_payload(repo.owner_user),
            submission.id,
            UpdateSubmissionRequest(version_number=1, team_number="22"),
        )

    assert exc.value.code.value == "SUBMISSION_ALREADY_COMPLETED"
    assert exc.value.status_code == 400


async def test_submission_endpoints_require_approved_account() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)

    with pytest.raises(AppError) as exc:
        await service.list_my_submissions(_auth_payload(repo.pending_user), page=1, page_size=20)

    assert exc.value.code.value == "ACCOUNT_NOT_APPROVED"
    assert exc.value.status_code == 403


async def test_complete_submission_marks_completed_without_attachment_and_audits() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, version_number=1)
    submission.pending_grids = 0
    submission.completed_grids = 9
    repo.submissions.append(submission)
    repo.attachment_counts[submission.id] = 0

    completed = await service.complete_submission(_auth_payload(repo.owner_user), submission.id)

    assert completed.status == SubmissionStatus.COMPLETED
    assert completed.version_number == 2
    assert completed.file_submission_pending is True
    assert submission.completed_at is not None
    assert submission.completed_by_user_id == repo.owner_user.id
    assert repo.transaction_entries == 1
    assert len(repo.audit_logs) == 1
    assert repo.audit_logs[0].action_type == AuditActionType.COMPLETED


async def test_complete_submission_requires_pending_grids_zero() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, version_number=1)
    repo.submissions.append(submission)

    with pytest.raises(AppError) as exc:
        await service.complete_submission(_auth_payload(repo.owner_user), submission.id)

    assert exc.value.code.value == "PENDING_GRIDS_MUST_BE_ZERO"
    assert exc.value.status_code == 400


async def test_complete_submission_rejects_already_completed() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, status=SubmissionStatus.COMPLETED, version_number=1)
    repo.submissions.append(submission)

    with pytest.raises(AppError) as exc:
        await service.complete_submission(_auth_payload(repo.owner_user), submission.id)

    assert exc.value.code.value == "SUBMISSION_ALREADY_COMPLETED"
    assert exc.value.status_code == 400


async def test_reopen_submission_requires_admin_role() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, status=SubmissionStatus.COMPLETED, version_number=1)
    repo.submissions.append(submission)

    with pytest.raises(AppError) as exc:
        await service.reopen_submission(_auth_payload(repo.owner_user), submission.id)

    assert exc.value.code.value == "ADMIN_ONLY"
    assert exc.value.status_code == 403


async def test_reopen_submission_requires_completed_status() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, status=SubmissionStatus.ONGOING, version_number=1)
    repo.submissions.append(submission)

    with pytest.raises(AppError) as exc:
        await service.reopen_submission(_auth_payload(repo.admin_user), submission.id)

    assert exc.value.code.value == "SUBMISSION_NOT_COMPLETED"
    assert exc.value.status_code == 400


async def test_reopen_submission_sets_ongoing_and_audits() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, status=SubmissionStatus.COMPLETED, version_number=1)
    repo.submissions.append(submission)

    reopened = await service.reopen_submission(_auth_payload(repo.admin_user), submission.id)

    assert reopened.status == SubmissionStatus.ONGOING
    assert reopened.version_number == 2
    assert reopened.file_submission_pending is False
    assert submission.reopened_at is not None
    assert submission.reopened_by_user_id == repo.admin_user.id
    assert repo.transaction_entries == 1
    assert len(repo.audit_logs) == 1
    assert repo.audit_logs[0].action_type == AuditActionType.REOPENED


async def test_admin_list_submissions_supports_file_pending_filter() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    completed_missing_file = _submission(repo.owner_user.id, status=SubmissionStatus.COMPLETED)
    completed_with_file = _submission(repo.owner_user.id, status=SubmissionStatus.COMPLETED)
    ongoing = _submission(repo.other_user.id, status=SubmissionStatus.ONGOING)
    repo.submissions.extend([completed_missing_file, completed_with_file, ongoing])
    repo.attachment_counts = {
        completed_missing_file.id: 0,
        completed_with_file.id: 2,
        ongoing.id: 0,
    }

    items, total = await service.list_admin_submissions(
        _auth_payload(repo.admin_user),
        file_submission_pending=True,
        page=1,
        page_size=20,
    )

    assert total == 1
    assert len(items) == 1
    assert items[0].id == completed_missing_file.id
    assert items[0].file_submission_pending is True


async def test_admin_get_submission_can_access_any_owner() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id)
    repo.submissions.append(submission)

    found = await service.get_admin_submission(_auth_payload(repo.admin_user), submission.id)

    assert found.id == submission.id


async def test_admin_update_completed_submission_enforces_pending_zero() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, status=SubmissionStatus.COMPLETED, version_number=1)
    submission.pending_grids = 0
    submission.completed_grids = 9
    repo.submissions.append(submission)

    with pytest.raises(AppError) as exc:
        await service.update_admin_submission(
            _auth_payload(repo.admin_user),
            submission.id,
            UpdateSubmissionRequest(version_number=1, pending_grids=1, completed_grids=8),
        )

    assert exc.value.code.value == "PENDING_GRIDS_MUST_BE_ZERO"
    assert exc.value.status_code == 400


async def test_admin_update_submission_writes_updated_audit() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, status=SubmissionStatus.ONGOING, version_number=1)
    repo.submissions.append(submission)

    updated = await service.update_admin_submission(
        _auth_payload(repo.admin_user),
        submission.id,
        UpdateSubmissionRequest(version_number=1, ticket_number="NEW-TICKET"),
    )

    assert updated.ticket_number == "NEW-TICKET"
    assert updated.version_number == 2
    assert len(repo.audit_logs) == 1
    assert repo.audit_logs[0].action_type == AuditActionType.UPDATED


async def test_admin_get_submission_audit_returns_items() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, status=SubmissionStatus.ONGOING, version_number=1)
    repo.submissions.append(submission)
    repo.audit_logs.append(
        SubmissionAuditLog(
            id=uuid.uuid4(),
            submission_id=submission.id,
            action_type=AuditActionType.UPDATED,
            actor_user_id=repo.admin_user.id,
            actor_role="ADMIN",
            source="ADMIN_CONSOLE",
            changed_fields_json={"fields": ["ticket_number"]},
            before_snapshot_json=None,
            after_snapshot_json=None,
            created_at=datetime.now(UTC),
        )
    )

    entries = await service.get_submission_audit(_auth_payload(repo.admin_user), submission.id)

    assert len(entries) == 1
    assert entries[0].submission_id == submission.id
    assert entries[0].action_type == AuditActionType.UPDATED
