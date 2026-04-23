"""
RED tests for WorkorderService.

All tests in this file are expected to FAIL until WorkorderService is implemented.
"""
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from app.core.enums import (
    AccountStatus,
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
from app.schemas.workorders import StartDriveRequest, UpdateWorkorderRequest
from app.services.workorder_service import WorkorderService

# ---------------------------------------------------------------------------
# Timezone-aware "today" helper — matches _today_for_region(NE_UP/SOUTH_FLORIDA)
# Using UTC _today() breaks at midnight UTC when Eastern is still the
# previous day, causing "work_date cannot be in the future" failures in CI.
# ---------------------------------------------------------------------------
_EASTERN = ZoneInfo("America/New_York")


def _today() -> date:
    return datetime.now(_EASTERN).date()


# ---------------------------------------------------------------------------
# Fake repository
# ---------------------------------------------------------------------------


class FakeWorkorderRepository:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.approved_user = AppUser(
            id=uuid.uuid4(),
            auth_user_id=uuid.uuid4(),
            full_name="Drive Tester",
            email="tester@example.com",
            requested_role=RequestedRole.DRIVE_TESTER,
            approved_role=RequestedRole.DRIVE_TESTER,
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
        self.users = [self.approved_user, self.pending_user, self.admin_user]
        self.workorders: list[Workorder] = []
        self.submissions: list[Submission] = []
        self.audit_logs: list[SubmissionAuditLog] = []
        # override per-test: (sum_completed, sum_skipped)
        self._aggregate: dict[uuid.UUID, tuple[int, int]] = {}
        self.transaction_entries = 0

    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None:
        return next((u for u in self.users if u.auth_user_id == auth_user_id), None)

    async def get_workorder_by_normalized_code(self, code: str) -> Workorder | None:
        return next(
            (w for w in self.workorders if w.workorder_code_normalized == code),
            None,
        )

    async def create_workorder(self, workorder: Workorder) -> Workorder:
        self.workorders.append(workorder)
        return workorder

    async def get_workorder_by_id(self, workorder_id: uuid.UUID) -> Workorder | None:
        return next((w for w in self.workorders if w.id == workorder_id), None)

    async def save_workorder(self, workorder: Workorder) -> Workorder:
        return workorder

    async def create_submission(self, submission: Submission) -> Submission:
        self.submissions.append(submission)
        return submission

    async def get_submission_by_workorder_date(
        self,
        *,
        workorder_id: uuid.UUID,
        work_date: date,
        exclude_submission_id: uuid.UUID | None = None,
    ) -> Submission | None:
        return next(
            (
                s
                for s in self.submissions
                if s.workorder_id == workorder_id
                and s.work_date == work_date
                and s.id != exclude_submission_id
            ),
            None,
        )

    async def create_audit_log(self, log: SubmissionAuditLog) -> SubmissionAuditLog:
        self.audit_logs.append(log)
        return log

    async def get_aggregate_progress(self, workorder_id: uuid.UUID) -> tuple[int, int]:
        return self._aggregate.get(workorder_id, (0, 0))

    async def list_workorders(
        self,
        *,
        region: Region | None = None,
        status: WorkorderStatus | None = None,
        workorder_code: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Workorder], int]:
        results = list(self.workorders)
        if region is not None:
            results = [w for w in results if w.region == region]
        if status is not None:
            results = [w for w in results if w.status == status]
        if workorder_code is not None:
            term = workorder_code.upper()
            results = [w for w in results if term in w.workorder_code_normalized]
        total = len(results)
        return results[offset : offset + limit], total

    async def list_submissions_by_workorder(
        self,
        workorder_id: uuid.UUID,
    ) -> list[Submission]:
        return [s for s in self.submissions if s.workorder_id == workorder_id]

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        self.transaction_entries += 1
        yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth(user: AppUser) -> dict[str, Any]:
    return {"sub": str(user.auth_user_id), "email": user.email}


def _workorder(
    code: str = "WO-001",
    *,
    normalized_code: str | None = None,
    region: Region = Region.NE_UP,
    total_grids: int = 10,
    status: WorkorderStatus = WorkorderStatus.ACTIVE,
    created_by: uuid.UUID | None = None,
) -> Workorder:
    now = datetime.now(UTC)
    creator = created_by or uuid.uuid4()
    return Workorder(
        id=uuid.uuid4(),
        workorder_code=code,
        workorder_code_normalized=normalized_code or code.upper(),
        region=region,
        total_grids=total_grids,
        status=status,
        created_at=now,
        created_by_user_id=creator,
        updated_at=now,
        updated_by_user_id=creator,
        completed_at=None,
        completed_by_user_id=None,
    )


def _submission(
    owner_user_id: uuid.UUID,
    workorder_id: uuid.UUID,
    *,
    work_date: date | None = None,
    status: SubmissionStatus = SubmissionStatus.COMPLETED,
    completed_grids: int = 3,
    skipped_grids: int = 1,
) -> Submission:
    now = datetime.now(UTC)
    return Submission(
        id=uuid.uuid4(),
        client_generated_id=uuid.uuid4(),
        owner_user_id=owner_user_id,
        workorder_id=workorder_id,
        submitter_name_snapshot="Snapshot Name",
        submitter_email_snapshot="snapshot@example.com",
        work_date=work_date or _today(),
        shift=Shift.AM,
        team_number=None,
        ticket_number=None,
        skipped_grids=skipped_grids,
        force_tested_grids=0,
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
        version_number=1,
    )


# ---------------------------------------------------------------------------
# Normalization tests
# ---------------------------------------------------------------------------


def test_normalize_trims_and_uppercases() -> None:
    assert WorkorderService.normalize_code("  wo-001  ") == "WO-001"


def test_normalize_removes_interior_spaces() -> None:
    assert WorkorderService.normalize_code("WO 001") == "WO001"


def test_normalize_preserves_hyphen() -> None:
    assert WorkorderService.normalize_code("wo-abc-12") == "WO-ABC-12"


def test_normalize_empty_string_after_normalization_raises() -> None:
    with pytest.raises(AppError) as exc:
        WorkorderService.normalize_code("   ")
    assert exc.value.status_code == 400


# ---------------------------------------------------------------------------
# start_drive — account guard
# ---------------------------------------------------------------------------


async def test_start_drive_requires_approved_account() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)

    with pytest.raises(AppError) as exc:
        await service.start_drive(
            _auth(repo.pending_user),
            StartDriveRequest(
                workorder_code="WO-001",
                region=Region.NE_UP,
                total_grids=10,
                work_date=_today(),
                shift=Shift.AM,
            ),
        )

    assert exc.value.code.value == "ACCOUNT_NOT_APPROVED"


# ---------------------------------------------------------------------------
# start_drive — new workorder path
# ---------------------------------------------------------------------------


async def test_start_drive_creates_new_workorder_when_none_exists() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)

    view = await service.start_drive(
        _auth(repo.approved_user),
        StartDriveRequest(
            workorder_code="WO-001",
            region=Region.NE_UP,
            total_grids=10,
            work_date=_today(),
            shift=Shift.AM,
        ),
    )

    assert len(repo.workorders) == 1
    assert repo.workorders[0].workorder_code_normalized == "WO-001"
    assert view.workorder.workorder_code == "WO-001"
    assert view.workorder.total_grids == 10
    assert view.workorder.region == Region.NE_UP


async def test_start_drive_requires_region_when_creating_new_workorder() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)

    with pytest.raises(AppError) as exc:
        await service.start_drive(
            _auth(repo.approved_user),
            StartDriveRequest(
                workorder_code="WO-MISSING-REGION",
                # region intentionally omitted
                total_grids=10,
                work_date=_today(),
                shift=Shift.AM,
            ),
        )

    assert exc.value.code.value == "WORKORDER_REGION_MISMATCH"


async def test_start_drive_requires_total_grids_when_creating_new_workorder() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)

    with pytest.raises(AppError) as exc:
        await service.start_drive(
            _auth(repo.approved_user),
            StartDriveRequest(
                workorder_code="WO-MISSING-GRIDS",
                region=Region.NE_UP,
                # total_grids intentionally omitted
                work_date=_today(),
                shift=Shift.AM,
            ),
        )

    assert exc.value.code.value == "WORKORDER_TOTAL_GRIDS_MISMATCH"


async def test_start_drive_creates_submission_as_in_progress() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)

    view = await service.start_drive(
        _auth(repo.approved_user),
        StartDriveRequest(
            workorder_code="WO-001",
            region=Region.NE_UP,
            total_grids=10,
            work_date=_today(),
            shift=Shift.AM,
        ),
    )

    assert view.status == SubmissionStatus.IN_PROGRESS
    assert view.started_at is not None


async def test_start_drive_creates_audit_log() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)

    await service.start_drive(
        _auth(repo.approved_user),
        StartDriveRequest(
            workorder_code="WO-001",
            region=Region.NE_UP,
            total_grids=10,
            work_date=_today(),
            shift=Shift.AM,
        ),
    )

    assert len(repo.audit_logs) == 1


async def test_start_drive_is_atomic() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)

    await service.start_drive(
        _auth(repo.approved_user),
        StartDriveRequest(
            workorder_code="WO-001",
            region=Region.NE_UP,
            total_grids=10,
            work_date=_today(),
            shift=Shift.AM,
        ),
    )

    assert repo.transaction_entries == 1


# ---------------------------------------------------------------------------
# start_drive — attach to existing workorder
# ---------------------------------------------------------------------------


async def test_start_drive_reuses_active_workorder() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    existing = _workorder("WO-EXIST", region=Region.CENTRAL, total_grids=5)
    repo.workorders.append(existing)

    view = await service.start_drive(
        _auth(repo.approved_user),
        StartDriveRequest(
            workorder_code="WO-EXIST",
            work_date=_today(),
            shift=Shift.AM,
        ),
    )

    assert len(repo.workorders) == 1  # no new workorder created
    assert view.workorder.total_grids == 5
    assert view.workorder.region == Region.CENTRAL


async def test_start_drive_rejects_completed_workorder() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    existing = _workorder("WO-DONE", status=WorkorderStatus.COMPLETED)
    repo.workorders.append(existing)

    with pytest.raises(AppError) as exc:
        await service.start_drive(
            _auth(repo.approved_user),
            StartDriveRequest(
                workorder_code="WO-DONE",
                work_date=_today(),
                shift=Shift.AM,
            ),
        )

    assert exc.value.code.value == "WORKORDER_ALREADY_COMPLETED"


async def test_start_drive_rejects_region_mismatch_when_attaching() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    existing = _workorder("WO-REG", region=Region.CENTRAL, total_grids=5)
    repo.workorders.append(existing)

    with pytest.raises(AppError) as exc:
        await service.start_drive(
            _auth(repo.approved_user),
            StartDriveRequest(
                workorder_code="WO-REG",
                region=Region.NE_UP,  # mismatch
                total_grids=5,
                work_date=_today(),
                shift=Shift.AM,
            ),
        )

    assert exc.value.code.value == "WORKORDER_REGION_MISMATCH"


async def test_start_drive_rejects_total_grids_mismatch_when_attaching() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    existing = _workorder("WO-GRIDS", region=Region.CENTRAL, total_grids=5)
    repo.workorders.append(existing)

    with pytest.raises(AppError) as exc:
        await service.start_drive(
            _auth(repo.approved_user),
            StartDriveRequest(
                workorder_code="WO-GRIDS",
                total_grids=99,  # mismatch
                work_date=_today(),
                shift=Shift.AM,
            ),
        )

    assert exc.value.code.value == "WORKORDER_TOTAL_GRIDS_MISMATCH"


async def test_start_drive_allows_omit_region_and_grids_when_attaching() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    existing = _workorder("WO-ATTACH", region=Region.SOUTH_FLORIDA, total_grids=7)
    repo.workorders.append(existing)

    view = await service.start_drive(
        _auth(repo.approved_user),
        StartDriveRequest(
            workorder_code="WO-ATTACH",
            # region and total_grids omitted — should be fine when attaching
            work_date=_today(),
            shift=Shift.AM,
        ),
    )

    assert view.workorder.region == Region.SOUTH_FLORIDA
    assert view.workorder.total_grids == 7


async def test_start_drive_rejects_duplicate_workorder_date_submission() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    existing = _workorder("WO-DUP")
    repo.workorders.append(existing)
    dupe_sub = _submission(repo.approved_user.id, existing.id, work_date=_today())
    repo.submissions.append(dupe_sub)

    with pytest.raises(AppError) as exc:
        await service.start_drive(
            _auth(repo.approved_user),
            StartDriveRequest(
                workorder_code="WO-DUP",
                work_date=_today(),
                shift=Shift.AM,
            ),
        )

    assert exc.value.code.value == "SUBMISSION_ALREADY_EXISTS"


# ---------------------------------------------------------------------------
# lookup_workorder
# ---------------------------------------------------------------------------


async def test_lookup_finds_workorder_by_normalized_code() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    existing = _workorder("wo-lookup", normalized_code="WO-LOOKUP", total_grids=20)
    repo.workorders.append(existing)
    repo._aggregate[existing.id] = (5, 2)

    view = await service.lookup_workorder(_auth(repo.approved_user), "wo-lookup")

    assert view.workorder_code == "wo-lookup"
    assert view.completed_grids == 5
    assert view.skipped_grids == 2
    assert view.remaining_grids == 13
    assert view.total_grids == 20


async def test_lookup_returns_not_found_for_missing_code() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)

    with pytest.raises(AppError) as exc:
        await service.lookup_workorder(_auth(repo.approved_user), "GHOST-CODE")

    assert exc.value.code.value == "WORKORDER_NOT_FOUND"
    assert exc.value.status_code == 404


async def test_lookup_requires_approved_account() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)

    with pytest.raises(AppError) as exc:
        await service.lookup_workorder(_auth(repo.pending_user), "WO-001")

    assert exc.value.code.value == "ACCOUNT_NOT_APPROVED"


async def test_lookup_returns_aggregate_progress() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    wo = _workorder("WO-AGG", total_grids=10)
    repo.workorders.append(wo)
    repo._aggregate[wo.id] = (4, 3)

    view = await service.lookup_workorder(_auth(repo.approved_user), "WO-AGG")

    assert view.completed_grids == 4
    assert view.skipped_grids == 3
    assert view.remaining_grids == 3  # 10 - (4+3)
    assert abs(view.progress_percent - 70.0) < 0.01


# ---------------------------------------------------------------------------
# auto-complete parent workorder
# ---------------------------------------------------------------------------


async def test_auto_complete_parent_does_not_trigger_below_total() -> None:
    """After a submission completes, if sum(completed+skipped) < total_grids, workorder stays ACTIVE."""
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    wo = _workorder("WO-PARTIAL", total_grids=10)
    repo.workorders.append(wo)
    repo._aggregate[wo.id] = (3, 2)  # sum = 5, total = 10

    completed = await service.maybe_auto_complete_workorder(
        workorder=wo,
        actor=repo.approved_user,
    )

    assert completed is False
    assert wo.status == WorkorderStatus.ACTIVE


async def test_auto_complete_parent_triggers_when_sum_reaches_total() -> None:
    """When sum(completed+skipped) >= total_grids, workorder should be set COMPLETED."""
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    wo = _workorder("WO-FULL", total_grids=10)
    repo.workorders.append(wo)
    repo._aggregate[wo.id] = (7, 3)  # sum = 10 = total

    completed = await service.maybe_auto_complete_workorder(
        workorder=wo,
        actor=repo.approved_user,
    )

    assert completed is True
    assert wo.status == WorkorderStatus.COMPLETED
    assert wo.completed_at is not None
    assert wo.completed_by_user_id == repo.approved_user.id


async def test_auto_complete_parent_triggers_when_sum_exceeds_total() -> None:
    """Even if somehow sum > total (edge case), workorder should be marked COMPLETED."""
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    wo = _workorder("WO-OVER", total_grids=8)
    repo.workorders.append(wo)
    repo._aggregate[wo.id] = (6, 4)  # sum = 10 > 8

    completed = await service.maybe_auto_complete_workorder(
        workorder=wo,
        actor=repo.approved_user,
    )

    assert completed is True
    assert wo.status == WorkorderStatus.COMPLETED


# ---------------------------------------------------------------------------
# RED tests — start_drive: future work_date validation
# ---------------------------------------------------------------------------


async def test_start_drive_rejects_future_work_date() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo, _today_override=date(2026, 4, 17))

    with pytest.raises(AppError) as exc:
        await service.start_drive(
            _auth(repo.approved_user),
            StartDriveRequest(
                workorder_code="WO-2026",
                region=Region.NE_UP,
                total_grids=10,
                work_date=date(2026, 4, 18),  # tomorrow → INVALID
                shift=Shift.AM,
            ),
        )

    assert exc.value.code.value == "VALIDATION_ERROR"
    assert exc.value.status_code == 422


async def test_start_drive_accepts_today_work_date() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo, _today_override=date(2026, 4, 17))

    result = await service.start_drive(
        _auth(repo.approved_user),
        StartDriveRequest(
            workorder_code="WO-2026",
            region=Region.NE_UP,
            total_grids=10,
            work_date=date(2026, 4, 17),  # today → OK
            shift=Shift.AM,
        ),
    )

    assert result.status == SubmissionStatus.IN_PROGRESS


async def test_start_drive_accepts_past_work_date() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo, _today_override=date(2026, 4, 17))

    result = await service.start_drive(
        _auth(repo.approved_user),
        StartDriveRequest(
            workorder_code="WO-PAST",
            region=Region.NE_UP,
            total_grids=10,
            work_date=date(2026, 4, 16),  # yesterday → OK
            shift=Shift.AM,
        ),
    )

    assert result.status == SubmissionStatus.IN_PROGRESS


# ---------------------------------------------------------------------------
# Wave 2 — list_workorders (item 45)
# ---------------------------------------------------------------------------


async def test_list_workorders_requires_admin() -> None:
    """Non-admin approved users cannot list workorders via admin endpoint."""
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)

    with pytest.raises(AppError) as exc:
        await service.list_workorders(_auth(repo.approved_user))

    assert exc.value.code.value == "ADMIN_ONLY"
    assert exc.value.status_code == 403


async def test_list_workorders_returns_all_when_no_filters() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    repo.workorders.extend([
        _workorder("WO-A", region=Region.NE_UP),
        _workorder("WO-B", region=Region.CENTRAL),
        _workorder("WO-C", region=Region.SOUTH_FLORIDA),
    ])

    views, total = await service.list_workorders(_auth(repo.admin_user))

    assert total == 3
    assert len(views) == 3


async def test_list_workorders_filters_by_region() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    repo.workorders.extend([
        _workorder("WO-NE", region=Region.NE_UP),
        _workorder("WO-CENTRAL", region=Region.CENTRAL),
    ])

    views, total = await service.list_workorders(
        _auth(repo.admin_user), region=Region.NE_UP
    )

    assert total == 1
    assert views[0].workorder_code == "WO-NE"


async def test_list_workorders_filters_by_status() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    repo.workorders.extend([
        _workorder("WO-ACTIVE", status=WorkorderStatus.ACTIVE),
        _workorder("WO-DONE", status=WorkorderStatus.COMPLETED),
    ])

    views, total = await service.list_workorders(
        _auth(repo.admin_user), status=WorkorderStatus.ACTIVE
    )

    assert total == 1
    assert views[0].workorder_code == "WO-ACTIVE"


async def test_list_workorders_filters_by_code_substring() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    repo.workorders.extend([
        _workorder("WO-ALPHA-01", normalized_code="WO-ALPHA-01"),
        _workorder("WO-BETA-01", normalized_code="WO-BETA-01"),
    ])

    views, total = await service.list_workorders(
        _auth(repo.admin_user), workorder_code="ALPHA"
    )

    assert total == 1
    assert views[0].workorder_code == "WO-ALPHA-01"


async def test_list_workorders_paginates() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    for i in range(5):
        repo.workorders.append(_workorder(f"WO-{i:02d}"))

    views, total = await service.list_workorders(
        _auth(repo.admin_user), page=1, page_size=2
    )

    assert total == 5
    assert len(views) == 2


async def test_list_workorders_includes_aggregate_progress() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    wo = _workorder("WO-AGG", total_grids=10)
    repo.workorders.append(wo)
    repo._aggregate[wo.id] = (6, 2)

    views, _ = await service.list_workorders(_auth(repo.admin_user))

    assert views[0].completed_grids == 6
    assert views[0].skipped_grids == 2
    assert views[0].remaining_grids == 2
    assert abs(views[0].progress_percent - 80.0) < 0.01


# ---------------------------------------------------------------------------
# Wave 2 — get_workorder_admin (item 46)
# ---------------------------------------------------------------------------


async def test_get_workorder_admin_requires_admin() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    wo = _workorder("WO-DETAIL")
    repo.workorders.append(wo)

    with pytest.raises(AppError) as exc:
        await service.get_workorder_admin(_auth(repo.approved_user), wo.id)

    assert exc.value.code.value == "ADMIN_ONLY"


async def test_get_workorder_admin_returns_not_found() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)

    with pytest.raises(AppError) as exc:
        await service.get_workorder_admin(_auth(repo.admin_user), uuid.uuid4())

    assert exc.value.code.value == "WORKORDER_NOT_FOUND"
    assert exc.value.status_code == 404


async def test_get_workorder_admin_returns_detail_with_submissions() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    wo = _workorder("WO-FULL", total_grids=10)
    repo.workorders.append(wo)
    sub1 = _submission(repo.approved_user.id, wo.id, work_date=date(2026, 4, 14))
    sub2 = _submission(repo.approved_user.id, wo.id, work_date=date(2026, 4, 15))
    repo.submissions.extend([sub1, sub2])
    repo._aggregate[wo.id] = (6, 0)

    detail = await service.get_workorder_admin(_auth(repo.admin_user), wo.id)

    assert detail.id == wo.id
    assert detail.workorder_code == "WO-FULL"
    assert detail.total_grids == 10
    assert detail.completed_grids == 6
    assert len(detail.submissions) == 2


async def test_get_workorder_admin_has_empty_submissions_list() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    wo = _workorder("WO-EMPTY")
    repo.workorders.append(wo)

    detail = await service.get_workorder_admin(_auth(repo.admin_user), wo.id)

    assert detail.submissions == []


# ---------------------------------------------------------------------------
# Wave 2 — update_workorder (item 47)
# ---------------------------------------------------------------------------


async def test_update_workorder_requires_admin() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    wo = _workorder("WO-UPD")
    repo.workorders.append(wo)

    with pytest.raises(AppError) as exc:
        await service.update_workorder(
            _auth(repo.approved_user),
            wo.id,
            UpdateWorkorderRequest(total_grids=20),
        )

    assert exc.value.code.value == "ADMIN_ONLY"


async def test_update_workorder_returns_not_found() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)

    with pytest.raises(AppError) as exc:
        await service.update_workorder(
            _auth(repo.admin_user),
            uuid.uuid4(),
            UpdateWorkorderRequest(total_grids=20),
        )

    assert exc.value.code.value == "WORKORDER_NOT_FOUND"


async def test_update_workorder_total_grids_below_current_progress_raises() -> None:
    """total_grids cannot be set below current aggregate (completed + skipped)."""
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    wo = _workorder("WO-CAP", total_grids=10)
    repo.workorders.append(wo)
    repo._aggregate[wo.id] = (7, 2)  # sum = 9

    with pytest.raises(AppError) as exc:
        await service.update_workorder(
            _auth(repo.admin_user),
            wo.id,
            UpdateWorkorderRequest(total_grids=8),  # 8 < 9 → invalid
        )

    assert exc.value.code.value == "WORKORDER_PROGRESS_EXCEEDS_TOTAL"


async def test_update_workorder_total_grids_equal_to_progress_allowed() -> None:
    """total_grids == current aggregate is allowed (already complete)."""
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    wo = _workorder("WO-EQ", total_grids=10)
    repo.workorders.append(wo)
    repo._aggregate[wo.id] = (5, 4)  # sum = 9

    view = await service.update_workorder(
        _auth(repo.admin_user),
        wo.id,
        UpdateWorkorderRequest(total_grids=9),  # exactly equal → OK
    )

    assert view.total_grids == 9


async def test_update_workorder_updates_region() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    wo = _workorder("WO-REG-UPD", region=Region.NE_UP)
    repo.workorders.append(wo)

    view = await service.update_workorder(
        _auth(repo.admin_user),
        wo.id,
        UpdateWorkorderRequest(region=Region.CENTRAL),
    )

    assert view.region == Region.CENTRAL


async def test_update_workorder_updates_code_and_normalizes() -> None:
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    wo = _workorder("WO-OLD", normalized_code="WO-OLD")
    repo.workorders.append(wo)

    view = await service.update_workorder(
        _auth(repo.admin_user),
        wo.id,
        UpdateWorkorderRequest(workorder_code="wo new code"),
    )

    assert view.workorder_code == "wo new code"
    assert wo.workorder_code_normalized == "WONEWCODE"


async def test_update_workorder_no_op_when_nothing_set() -> None:
    """If request has no fields set, workorder is returned unchanged."""
    repo = FakeWorkorderRepository()
    service = WorkorderService(repository=repo)
    wo = _workorder("WO-NOOP", total_grids=10)
    repo.workorders.append(wo)

    view = await service.update_workorder(
        _auth(repo.admin_user),
        wo.id,
        UpdateWorkorderRequest(),  # nothing set
    )

    assert view.total_grids == 10
    assert view.workorder_code == "WO-NOOP"

