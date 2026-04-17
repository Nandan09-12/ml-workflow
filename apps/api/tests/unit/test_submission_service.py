import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from typing import Any

import pytest

from app.core.enums import (
    AccountStatus,
    AuditActionType,
    Region,
    RequestedRole,
    Shift,
    SubmissionStatus,
    WorkorderStatus,
)
from app.core.errors import AppError
from app.models.app_user import AppUser
from app.models.submission import Submission
from app.models.submission_audit_log import SubmissionAuditLog
from app.models.workorder import Workorder
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
        self.workorders: dict[uuid.UUID, Workorder] = {}
        self.transaction_entries = 0

    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None:
        return next((user for user in self.users if user.auth_user_id == auth_user_id), None)

    async def get_submission_by_workorder_date(
        self,
        *,
        workorder_id: uuid.UUID,
        work_date: date,
        exclude_submission_id: uuid.UUID | None = None,
    ) -> Submission | None:
        return next(
            (
                submission
                for submission in self.submissions
                if submission.workorder_id == workorder_id
                and submission.work_date == work_date
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
        shift: Shift | None = None,
        owner_user_id: uuid.UUID | None = None,
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
        if shift is not None:
            items = [submission for submission in items if submission.shift == shift]
        if owner_user_id is not None:
            items = [submission for submission in items if submission.owner_user_id == owner_user_id]
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
                    submission.status == SubmissionStatus.CHECKED_OUT
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

    async def get_workorder_by_id(self, workorder_id: uuid.UUID) -> Workorder | None:
        return self.workorders.get(workorder_id)

    async def save_workorder(self, workorder: Workorder) -> Workorder:
        self.workorders[workorder.id] = workorder
        return workorder

    async def get_aggregate_progress(self, workorder_id: uuid.UUID) -> tuple[int, int]:
        relevant = [s for s in self.submissions if s.workorder_id == workorder_id]
        return (
            sum(s.completed_grids for s in relevant),
            sum(s.skipped_grids for s in relevant),
        )

    async def get_workorders_by_ids(self, workorder_ids: list[uuid.UUID]) -> dict[uuid.UUID, Workorder]:
        return {wid: self.workorders[wid] for wid in workorder_ids if wid in self.workorders}

    async def get_aggregate_progress_batch(
        self, workorder_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, tuple[int, int]]:
        result: dict[uuid.UUID, tuple[int, int]] = dict.fromkeys(workorder_ids, (0, 0))
        for s in self.submissions:
            if s.workorder_id in result:
                c, sk = result[s.workorder_id]
                result[s.workorder_id] = (c + s.completed_grids, sk + s.skipped_grids)
        return result

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        self.transaction_entries += 1
        yield


def _auth_payload(user: AppUser) -> dict[str, Any]:
    return {"sub": str(user.auth_user_id), "email": user.email}


def _workorder(
    owner_user_id: uuid.UUID,
    *,
    total_grids: int = 20,
    status: WorkorderStatus = WorkorderStatus.ACTIVE,
) -> Workorder:
    now = datetime.now(UTC)
    return Workorder(
        id=uuid.uuid4(),
        workorder_code="WO-UNIT",
        workorder_code_normalized="WO-UNIT",
        region=Region.NE_UP,
        total_grids=total_grids,
        status=status,
        created_at=now,
        created_by_user_id=owner_user_id,
        updated_at=now,
        updated_by_user_id=owner_user_id,
        completed_at=None,
        completed_by_user_id=None,
    )


def _submission(
    owner_user_id: uuid.UUID,
    *,
    workorder_id: uuid.UUID | None = None,
    work_date: date | None = None,
    shift: Shift = Shift.AM,
    status: SubmissionStatus = SubmissionStatus.IN_PROGRESS,
    version_number: int = 1,
    completed_grids: int = 7,
    skipped_grids: int = 1,
    force_tested_grids: int = 0,
) -> Submission:
    now = datetime.now(UTC)
    return Submission(
        id=uuid.uuid4(),
        client_generated_id=uuid.uuid4(),
        owner_user_id=owner_user_id,
        workorder_id=workorder_id or uuid.uuid4(),
        submitter_name_snapshot="Snapshot Name",
        submitter_email_snapshot="snapshot@example.com",
        work_date=work_date or date.today(),
        shift=shift,
        team_number="11",
        ticket_number="TKT-100",
        skipped_grids=skipped_grids,
        force_tested_grids=force_tested_grids,
        completed_grids=completed_grids,
        status=status,
        started_at=now,
        ended_at=None,
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


async def test_create_submission_creates_and_audits() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    workorder_id = uuid.uuid4()

    created = await service.create_submission(
        _auth_payload(repo.owner_user),
        CreateSubmissionRequest(
            workorder_id=workorder_id,
            work_date=date.today(),
            shift=Shift.AM,
            team_number=" 11 ",
            ticket_number=" TKT-1 ",
            skipped_grids=1,
            force_tested_grids=0,
            completed_grids=7,
        ),
    )

    assert created.owner_user_id == repo.owner_user.id
    assert created.workorder_id == workorder_id
    assert created.status == SubmissionStatus.IN_PROGRESS
    assert created.version_number == 1
    assert created.file_submission_pending is False
    assert repo.transaction_entries == 1
    assert len(repo.audit_logs) == 1
    assert repo.audit_logs[0].action_type == AuditActionType.CREATED


async def test_create_submission_rejects_negative_force_tested_grids() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)

    with pytest.raises(AppError) as exc:
        await service.create_submission(
            _auth_payload(repo.owner_user),
            CreateSubmissionRequest(
                workorder_id=uuid.uuid4(),
                work_date=date.today(),
                shift=Shift.AM,
                team_number="11",
                ticket_number="TKT-1",
                skipped_grids=1,
                force_tested_grids=-1,
                completed_grids=7,
            ),
        )

    assert exc.value.code.value == "INVALID_GRID_MATH"
    assert exc.value.status_code == 400


async def test_create_submission_rejects_duplicate_for_same_workorder_date() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    workorder_id = uuid.uuid4()
    existing = _submission(repo.owner_user.id, workorder_id=workorder_id)
    repo.submissions.append(existing)

    with pytest.raises(AppError) as exc:
        await service.create_submission(
            _auth_payload(repo.owner_user),
            CreateSubmissionRequest(
                workorder_id=workorder_id,
                work_date=existing.work_date,
                shift=existing.shift,
                team_number="11",
                ticket_number="TKT-1",
                skipped_grids=1,
                force_tested_grids=0,
                completed_grids=7,
            ),
        )

    assert exc.value.code.value == "SUBMISSION_ALREADY_EXISTS"
    assert exc.value.status_code == 409


async def test_list_submissions_returns_computed_file_submission_pending() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    # file_submission_pending = CHECKED_OUT + no attachment
    checked_out_no_file = _submission(
        repo.owner_user.id,
        status=SubmissionStatus.CHECKED_OUT,
    )
    checked_out_with_file = _submission(
        repo.owner_user.id,
        status=SubmissionStatus.CHECKED_OUT,
    )
    ongoing = _submission(repo.owner_user.id, status=SubmissionStatus.IN_PROGRESS)
    other_owner = _submission(repo.other_user.id, status=SubmissionStatus.CHECKED_OUT)
    repo.submissions.extend([checked_out_no_file, checked_out_with_file, ongoing, other_owner])
    repo.attachment_counts = {
        checked_out_no_file.id: 0,
        checked_out_with_file.id: 1,
        ongoing.id: 0,
        other_owner.id: 0,
    }

    items, total = await service.list_my_submissions(_auth_payload(repo.owner_user), page=1, page_size=20)

    assert total == 3
    by_id = {item.id: item for item in items}
    assert by_id[checked_out_no_file.id].file_submission_pending is True
    assert by_id[checked_out_with_file.id].file_submission_pending is False
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
            skipped_grids=2,
            force_tested_grids=1,
            completed_grids=10,
        ),
    )

    assert updated.version_number == 2
    assert repo.transaction_entries == 1
    assert len(repo.audit_logs) == 1
    assert repo.audit_logs[0].action_type == AuditActionType.UPDATED


async def test_update_submission_rejects_non_in_progress_submission() -> None:
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


async def test_complete_submission_with_attachment_marks_completed_and_audits() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    wo = _workorder(repo.owner_user.id, total_grids=20)
    submission = _submission(repo.owner_user.id, workorder_id=wo.id, status=SubmissionStatus.CHECKED_OUT, version_number=1)
    repo.workorders[wo.id] = wo
    repo.submissions.append(submission)
    repo.attachment_counts[submission.id] = 1  # required attachment present

    completed = await service.complete_submission(_auth_payload(repo.owner_user), submission.id)

    assert completed.status == SubmissionStatus.COMPLETED
    assert completed.version_number == 2
    assert completed.file_submission_pending is False  # COMPLETED → always False
    assert submission.completed_at is not None
    assert submission.completed_by_user_id == repo.owner_user.id
    assert repo.transaction_entries == 1
    assert len(repo.audit_logs) == 1
    assert repo.audit_logs[0].action_type == AuditActionType.COMPLETED


async def test_complete_submission_rejects_already_completed() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, status=SubmissionStatus.COMPLETED, version_number=1)
    repo.submissions.append(submission)

    with pytest.raises(AppError) as exc:
        await service.complete_submission(_auth_payload(repo.owner_user), submission.id)

    assert exc.value.code.value == "SUBMISSION_NOT_CHECKED_OUT"
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
    submission = _submission(repo.owner_user.id, status=SubmissionStatus.IN_PROGRESS, version_number=1)
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

    assert reopened.status == SubmissionStatus.CHECKED_OUT
    assert reopened.version_number == 2
    assert reopened.file_submission_pending is True  # CHECKED_OUT + no attachment → pending
    assert submission.reopened_at is not None
    assert submission.reopened_by_user_id == repo.admin_user.id
    assert repo.transaction_entries == 1
    assert len(repo.audit_logs) == 1
    assert repo.audit_logs[0].action_type == AuditActionType.REOPENED


async def test_admin_list_submissions_supports_file_pending_filter() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    # file_submission_pending is CHECKED_OUT + no attachment
    checked_out_no_file = _submission(repo.owner_user.id, status=SubmissionStatus.CHECKED_OUT)
    checked_out_with_file = _submission(repo.owner_user.id, status=SubmissionStatus.CHECKED_OUT)
    ongoing = _submission(repo.other_user.id, status=SubmissionStatus.IN_PROGRESS)
    repo.submissions.extend([checked_out_no_file, checked_out_with_file, ongoing])
    repo.attachment_counts = {
        checked_out_no_file.id: 0,
        checked_out_with_file.id: 1,
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
    assert items[0].id == checked_out_no_file.id
    assert items[0].file_submission_pending is True


async def test_admin_get_submission_can_access_any_owner() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id)
    repo.submissions.append(submission)

    found = await service.get_admin_submission(_auth_payload(repo.admin_user), submission.id)

    assert found.id == submission.id


async def test_admin_update_submission_writes_updated_audit() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, status=SubmissionStatus.IN_PROGRESS, version_number=1)
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
    submission = _submission(repo.owner_user.id, status=SubmissionStatus.IN_PROGRESS, version_number=1)
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


# ---------------------------------------------------------------------------
# RED tests — end_drive
# ---------------------------------------------------------------------------


async def test_end_drive_transitions_in_progress_to_checked_out() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, status=SubmissionStatus.IN_PROGRESS)
    repo.submissions.append(submission)

    view = await service.end_drive(_auth_payload(repo.owner_user), submission.id)

    assert view.status == SubmissionStatus.CHECKED_OUT


async def test_end_drive_stamps_ended_at() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, status=SubmissionStatus.IN_PROGRESS)
    repo.submissions.append(submission)

    view = await service.end_drive(_auth_payload(repo.owner_user), submission.id)

    assert view.ended_at is not None


async def test_end_drive_requires_in_progress_status() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, status=SubmissionStatus.CHECKED_OUT)
    repo.submissions.append(submission)

    with pytest.raises(AppError) as exc:
        await service.end_drive(_auth_payload(repo.owner_user), submission.id)

    assert exc.value.code.value == "SUBMISSION_NOT_CHECKED_OUT"
    assert exc.value.status_code == 400


async def test_end_drive_creates_audit_log() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, status=SubmissionStatus.IN_PROGRESS)
    repo.submissions.append(submission)

    await service.end_drive(_auth_payload(repo.owner_user), submission.id)

    assert len(repo.audit_logs) == 1


async def test_end_drive_increments_version() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, status=SubmissionStatus.IN_PROGRESS, version_number=1)
    repo.submissions.append(submission)

    view = await service.end_drive(_auth_payload(repo.owner_user), submission.id)

    assert view.version_number == 2


async def test_end_drive_rejects_non_owner() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.other_user.id, status=SubmissionStatus.IN_PROGRESS)
    repo.submissions.append(submission)

    with pytest.raises(AppError) as exc:
        await service.end_drive(_auth_payload(repo.owner_user), submission.id)

    assert exc.value.code.value == "NOT_OWNER"


# ---------------------------------------------------------------------------
# RED tests — complete_submission bug fixes
# (currently: checks status==COMPLETED to block; should require CHECKED_OUT)
# ---------------------------------------------------------------------------


async def test_complete_submission_requires_checked_out_status() -> None:
    """complete_submission must REJECT IN_PROGRESS submissions (only CHECKED_OUT allowed)."""
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, status=SubmissionStatus.IN_PROGRESS, version_number=1)
    repo.submissions.append(submission)

    with pytest.raises(AppError) as exc:
        await service.complete_submission(_auth_payload(repo.owner_user), submission.id)

    assert exc.value.code.value == "SUBMISSION_NOT_CHECKED_OUT"
    assert exc.value.status_code == 400


async def test_complete_submission_succeeds_from_checked_out_with_attachment() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    wo = _workorder(repo.owner_user.id, total_grids=20)
    submission = _submission(repo.owner_user.id, workorder_id=wo.id, status=SubmissionStatus.CHECKED_OUT, version_number=1)
    repo.workorders[wo.id] = wo
    repo.submissions.append(submission)
    repo.attachment_counts[submission.id] = 1

    view = await service.complete_submission(_auth_payload(repo.owner_user), submission.id)

    assert view.status == SubmissionStatus.COMPLETED


# ---------------------------------------------------------------------------
# RED tests — reopen_submission bug fix
# (currently: sets status=IN_PROGRESS; should set CHECKED_OUT)
# ---------------------------------------------------------------------------


async def test_reopen_submission_sets_checked_out_not_in_progress() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, status=SubmissionStatus.COMPLETED, version_number=1)
    repo.submissions.append(submission)

    reopened = await service.reopen_submission(_auth_payload(repo.admin_user), submission.id)

    assert reopened.status == SubmissionStatus.CHECKED_OUT


# ---------------------------------------------------------------------------
# RED tests — update_submission bug fix
# (currently: blocks if status != IN_PROGRESS; should also allow CHECKED_OUT)
# ---------------------------------------------------------------------------


async def test_update_submission_allows_edits_on_checked_out() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, status=SubmissionStatus.CHECKED_OUT, version_number=1)
    repo.submissions.append(submission)

    updated = await service.update_submission(
        _auth_payload(repo.owner_user),
        submission.id,
        UpdateSubmissionRequest(version_number=1, ticket_number="NEW-TICKET"),
    )

    assert updated.ticket_number == "NEW-TICKET"


# ---------------------------------------------------------------------------
# RED tests — file_submission_pending formula (CHECKED_OUT + no attachment)
# ---------------------------------------------------------------------------


async def test_file_submission_pending_true_when_checked_out_no_attachment() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, status=SubmissionStatus.CHECKED_OUT)
    repo.submissions.append(submission)
    repo.attachment_counts[submission.id] = 0

    view = await service.get_submission(_auth_payload(repo.owner_user), submission.id)

    assert view.file_submission_pending is True


async def test_file_submission_pending_false_when_checked_out_with_attachment() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, status=SubmissionStatus.CHECKED_OUT)
    repo.submissions.append(submission)
    repo.attachment_counts[submission.id] = 1

    view = await service.get_submission(_auth_payload(repo.owner_user), submission.id)

    assert view.file_submission_pending is False


async def test_file_submission_pending_false_when_completed() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, status=SubmissionStatus.COMPLETED)
    repo.submissions.append(submission)
    repo.attachment_counts[submission.id] = 0  # even with no attachment, COMPLETED is never pending

    view = await service.get_submission(_auth_payload(repo.owner_user), submission.id)

    assert view.file_submission_pending is False


async def test_file_submission_pending_false_when_in_progress() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    submission = _submission(repo.owner_user.id, status=SubmissionStatus.IN_PROGRESS)
    repo.submissions.append(submission)
    repo.attachment_counts[submission.id] = 0

    view = await service.get_submission(_auth_payload(repo.owner_user), submission.id)

    assert view.file_submission_pending is False


# ---------------------------------------------------------------------------
# RED tests — complete_submission: attachment required
# ---------------------------------------------------------------------------


async def test_complete_submission_requires_attachment() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    wo = _workorder(repo.owner_user.id, total_grids=20)
    submission = _submission(repo.owner_user.id, workorder_id=wo.id, status=SubmissionStatus.CHECKED_OUT)
    repo.workorders[wo.id] = wo
    repo.submissions.append(submission)
    repo.attachment_counts[submission.id] = 0  # no attachment

    with pytest.raises(AppError) as exc:
        await service.complete_submission(_auth_payload(repo.owner_user), submission.id)

    assert exc.value.code.value == "ATTACHMENT_REQUIRED"
    assert exc.value.status_code == 400


# ---------------------------------------------------------------------------
# RED tests — complete_submission: aggregate cap
# ---------------------------------------------------------------------------


async def test_complete_submission_rejects_if_aggregate_exceeds_total_grids() -> None:
    """If grids are already over cap (data integrity issue), block completion."""
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    wo = _workorder(repo.owner_user.id, total_grids=5)
    submission = _submission(
        repo.owner_user.id, workorder_id=wo.id, status=SubmissionStatus.CHECKED_OUT,
        completed_grids=6, skipped_grids=0,
    )
    repo.workorders[wo.id] = wo
    repo.submissions.append(submission)
    repo.attachment_counts[submission.id] = 1

    with pytest.raises(AppError) as exc:
        await service.complete_submission(_auth_payload(repo.owner_user), submission.id)

    assert exc.value.code.value == "WORKORDER_PROGRESS_EXCEEDS_TOTAL"
    assert exc.value.status_code == 400


# ---------------------------------------------------------------------------
# RED tests — complete_submission: auto-complete parent workorder
# ---------------------------------------------------------------------------


async def test_complete_submission_auto_completes_parent_workorder() -> None:
    """When aggregate reaches total_grids at completion, parent becomes COMPLETED."""
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    wo = _workorder(repo.owner_user.id, total_grids=10)
    submission = _submission(
        repo.owner_user.id, workorder_id=wo.id, status=SubmissionStatus.CHECKED_OUT,
        completed_grids=10, skipped_grids=0,
    )
    repo.workorders[wo.id] = wo
    repo.submissions.append(submission)
    repo.attachment_counts[submission.id] = 1

    await service.complete_submission(_auth_payload(repo.owner_user), submission.id)

    assert wo.status == WorkorderStatus.COMPLETED
    assert wo.completed_at is not None
    assert wo.completed_by_user_id == repo.owner_user.id


async def test_complete_submission_does_not_auto_complete_parent_below_total() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    wo = _workorder(repo.owner_user.id, total_grids=10)
    submission = _submission(
        repo.owner_user.id, workorder_id=wo.id, status=SubmissionStatus.CHECKED_OUT,
        completed_grids=4, skipped_grids=2,  # sum=6, total=10 → stays ACTIVE
    )
    repo.workorders[wo.id] = wo
    repo.submissions.append(submission)
    repo.attachment_counts[submission.id] = 1

    await service.complete_submission(_auth_payload(repo.owner_user), submission.id)

    assert wo.status == WorkorderStatus.ACTIVE


# ---------------------------------------------------------------------------
# RED tests — update_submission: aggregate cap
# ---------------------------------------------------------------------------


async def test_update_submission_rejects_if_aggregate_would_exceed_total_grids() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    wo = _workorder(repo.owner_user.id, total_grids=10)
    # Two submissions: other (3 grids) + this (5 grids) = 8 total
    other_sub = _submission(
        repo.owner_user.id, workorder_id=wo.id,
        completed_grids=3, skipped_grids=0,
    )
    this_sub = _submission(
        repo.owner_user.id, workorder_id=wo.id, status=SubmissionStatus.IN_PROGRESS,
        completed_grids=5, skipped_grids=0, work_date=date(2026, 3, 1),
    )
    repo.workorders[wo.id] = wo
    repo.submissions.extend([other_sub, this_sub])

    # Proposing to update to 8 grids — total would be 3 + 8 = 11 > 10
    with pytest.raises(AppError) as exc:
        await service.update_submission(
            _auth_payload(repo.owner_user),
            this_sub.id,
            UpdateSubmissionRequest(version_number=1, completed_grids=8),
        )

    assert exc.value.code.value == "WORKORDER_PROGRESS_EXCEEDS_TOTAL"
    assert exc.value.status_code == 400


async def test_update_submission_allows_edit_within_total_grids() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    wo = _workorder(repo.owner_user.id, total_grids=10)
    other_sub = _submission(
        repo.owner_user.id, workorder_id=wo.id,
        completed_grids=3, skipped_grids=0,
    )
    this_sub = _submission(
        repo.owner_user.id, workorder_id=wo.id, status=SubmissionStatus.IN_PROGRESS,
        completed_grids=5, skipped_grids=0, work_date=date(2026, 3, 1),
    )
    repo.workorders[wo.id] = wo
    repo.submissions.extend([other_sub, this_sub])

    # Proposing 6 — total would be 3 + 6 = 9 ≤ 10 → OK
    updated = await service.update_submission(
        _auth_payload(repo.owner_user),
        this_sub.id,
        UpdateSubmissionRequest(version_number=1, completed_grids=6),
    )

    assert updated.completed_grids == 6


# ---------------------------------------------------------------------------
# RED tests — reopen_submission: parent workorder cascade
# ---------------------------------------------------------------------------


async def test_reopen_submission_sets_parent_workorder_back_to_active() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    wo = _workorder(repo.owner_user.id, status=WorkorderStatus.COMPLETED)
    submission = _submission(repo.owner_user.id, workorder_id=wo.id, status=SubmissionStatus.COMPLETED)
    repo.workorders[wo.id] = wo
    repo.submissions.append(submission)

    await service.reopen_submission(_auth_payload(repo.admin_user), submission.id)

    assert wo.status == WorkorderStatus.ACTIVE


async def test_reopen_submission_parent_stays_active_if_already_active() -> None:
    repo = FakeSubmissionRepository()
    service = SubmissionService(repository=repo)
    wo = _workorder(repo.owner_user.id, status=WorkorderStatus.ACTIVE)
    submission = _submission(repo.owner_user.id, workorder_id=wo.id, status=SubmissionStatus.COMPLETED)
    repo.workorders[wo.id] = wo
    repo.submissions.append(submission)

    await service.reopen_submission(_auth_payload(repo.admin_user), submission.id)

    assert wo.status == WorkorderStatus.ACTIVE  # unchanged
