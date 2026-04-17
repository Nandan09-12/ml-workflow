import asyncio
import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

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
from app.models.submission import Submission
from app.models.submission_audit_log import SubmissionAuditLog
from app.models.workorder import Workorder
from app.repositories.submission_repository import SubmissionRepository
from app.repositories.workorder_repository import WorkorderRepository
from app.schemas.submissions import UpdateSubmissionRequest
from app.schemas.workorders import StartDriveRequest
from app.services.submission_service import SubmissionService
from app.services.workorder_service import WorkorderService
from tests.integration.helpers import (
    auth_payload,
    build_attachment,
    build_submission,
    build_user,
    build_workorder,
)

pytestmark = pytest.mark.integration


class _AsyncBarrier:
    def __init__(self, parties: int) -> None:
        self._parties = parties
        self._waiting = 0
        self._event = asyncio.Event()
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        async with self._lock:
            self._waiting += 1
            if self._waiting >= self._parties:
                self._event.set()
        await self._event.wait()


class _CoordinatedWorkorderRepository(WorkorderRepository):
    def __init__(
        self,
        session: AsyncSession,
        *,
        wait_on_missing_workorder: _AsyncBarrier | None = None,
        wait_on_missing_submission: _AsyncBarrier | None = None,
    ) -> None:
        super().__init__(session)
        self._wait_on_missing_workorder = wait_on_missing_workorder
        self._wait_on_missing_submission = wait_on_missing_submission

    async def get_workorder_by_normalized_code(self, code: str) -> Workorder | None:
        workorder = await super().get_workorder_by_normalized_code(code)
        if workorder is None and self._wait_on_missing_workorder is not None:
            await self._wait_on_missing_workorder.wait()
        return workorder

    async def get_submission_by_workorder_date(
        self,
        *,
        workorder_id: uuid.UUID,
        work_date: date,
        exclude_submission_id: uuid.UUID | None = None,
    ) -> Submission | None:
        submission = await super().get_submission_by_workorder_date(
            workorder_id=workorder_id,
            work_date=work_date,
            exclude_submission_id=exclude_submission_id,
        )
        if submission is None and self._wait_on_missing_submission is not None:
            await self._wait_on_missing_submission.wait()
        return submission


async def test_start_drive_creates_workorder_submission_and_audit(
    integration_session: AsyncSession,
) -> None:
    owner = build_user(
        email="owner-create@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    integration_session.add(owner)
    await integration_session.commit()

    selected_date = date(2026, 4, 14)
    service = WorkorderService(
        repository=WorkorderRepository(integration_session),
        _today_override=selected_date,
    )

    created = await service.start_drive(
        auth_payload(owner),
        StartDriveRequest(
            workorder_code="  Wo-100  ",
            region=Region.NE_UP,
            total_grids=10,
            work_date=selected_date,
            shift=Shift.AM,
            team_number=" 11 ",
            ticket_number=" TKT-1 ",
        ),
    )

    assert created.status == SubmissionStatus.IN_PROGRESS
    assert created.file_submission_pending is False
    assert created.workorder.workorder_code == "Wo-100"
    assert created.workorder.total_grids == 10
    assert created.team_number == "11"
    assert created.ticket_number == "TKT-1"

    saved_workorder = (
        await integration_session.execute(
            select(Workorder).where(Workorder.id == created.workorder_id)
        )
    ).scalar_one()
    assert saved_workorder.workorder_code_normalized == "WO-100"

    logs = (
        await integration_session.execute(
            select(SubmissionAuditLog).where(
                SubmissionAuditLog.submission_id == created.id
            )
        )
    ).scalars().all()
    assert len(logs) == 1
    assert logs[0].action_type == AuditActionType.CREATED


async def test_start_drive_rejects_duplicate_submission_for_same_workorder_day(
    integration_session: AsyncSession,
) -> None:
    owner = build_user(
        email="owner-dup@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    selected_date = date(2026, 4, 14)
    workorder = build_workorder(owner=owner, workorder_code="WO-DUP")
    existing = build_submission(
        owner=owner,
        workorder=workorder,
        work_date=selected_date,
    )
    integration_session.add_all([owner, workorder, existing])
    await integration_session.commit()

    service = WorkorderService(
        repository=WorkorderRepository(integration_session),
        _today_override=selected_date,
    )
    with pytest.raises(AppError) as exc:
        await service.start_drive(
            auth_payload(owner),
            StartDriveRequest(
                workorder_code="WO-DUP",
                work_date=selected_date,
                shift=Shift.AM,
                team_number="11",
                ticket_number="TKT-1",
            ),
        )

    assert exc.value.code.value == "SUBMISSION_ALREADY_EXISTS"
    assert exc.value.status_code == 409


async def test_start_drive_concurrent_same_day_returns_conflict_and_keeps_one_row(
    integration_session: AsyncSession,
) -> None:
    owner = build_user(
        email="owner-race-same-day@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    integration_session.add(owner)
    await integration_session.commit()

    bind = integration_session.bind
    assert bind is not None
    barrier = _AsyncBarrier(2)
    session_factory = async_sessionmaker(
        bind=bind,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session_one, session_factory() as session_two:
        service_one = WorkorderService(
            repository=_CoordinatedWorkorderRepository(
                session_one,
                wait_on_missing_workorder=barrier,
            ),
            _today_override=date(2026, 4, 14),
        )
        service_two = WorkorderService(
            repository=_CoordinatedWorkorderRepository(
                session_two,
                wait_on_missing_workorder=barrier,
            ),
            _today_override=date(2026, 4, 14),
        )

        results = await asyncio.gather(
            service_one.start_drive(
                auth_payload(owner),
                StartDriveRequest(
                    workorder_code="WO-RACE-SAME-DAY",
                    region=Region.NE_UP,
                    total_grids=10,
                    work_date=date(2026, 4, 14),
                    shift=Shift.AM,
                    team_number="11",
                    ticket_number="TKT-1",
                ),
            ),
            service_two.start_drive(
                auth_payload(owner),
                StartDriveRequest(
                    workorder_code="WO-RACE-SAME-DAY",
                    region=Region.NE_UP,
                    total_grids=10,
                    work_date=date(2026, 4, 14),
                    shift=Shift.AM,
                    team_number="11",
                    ticket_number="TKT-1",
                ),
            ),
            return_exceptions=True,
        )

    successes = [result for result in results if not isinstance(result, Exception)]
    failures = [result for result in results if isinstance(result, Exception)]

    assert len(successes) == 1
    assert len(failures) == 1
    assert isinstance(failures[0], AppError)
    assert failures[0].code.value == "SUBMISSION_ALREADY_EXISTS"
    assert failures[0].status_code == 409

    workorders = (
        await integration_session.execute(
            select(Workorder).where(
                Workorder.workorder_code_normalized == "WO-RACE-SAME-DAY"
            )
        )
    ).scalars().all()
    submissions = (
        await integration_session.execute(
            select(Submission)
            .join(Workorder, Submission.workorder_id == Workorder.id)
            .where(Workorder.workorder_code_normalized == "WO-RACE-SAME-DAY")
        )
    ).scalars().all()

    assert len(workorders) == 1
    assert len(submissions) == 1


async def test_start_drive_concurrent_new_workorder_different_days_reuses_parent(
    integration_session: AsyncSession,
) -> None:
    owner = build_user(
        email="owner-race-different-days@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    integration_session.add(owner)
    await integration_session.commit()

    bind = integration_session.bind
    assert bind is not None
    barrier = _AsyncBarrier(2)
    session_factory = async_sessionmaker(
        bind=bind,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session_one, session_factory() as session_two:
        service_one = WorkorderService(
            repository=_CoordinatedWorkorderRepository(
                session_one,
                wait_on_missing_workorder=barrier,
            ),
            _today_override=date(2026, 4, 15),
        )
        service_two = WorkorderService(
            repository=_CoordinatedWorkorderRepository(
                session_two,
                wait_on_missing_workorder=barrier,
            ),
            _today_override=date(2026, 4, 15),
        )

        first_day, second_day = await asyncio.gather(
            service_one.start_drive(
                auth_payload(owner),
                StartDriveRequest(
                    workorder_code="WO-RACE-MULTI",
                    region=Region.NE_UP,
                    total_grids=12,
                    work_date=date(2026, 4, 14),
                    shift=Shift.AM,
                    team_number="11",
                    ticket_number="TKT-1",
                ),
            ),
            service_two.start_drive(
                auth_payload(owner),
                StartDriveRequest(
                    workorder_code="WO-RACE-MULTI",
                    region=Region.NE_UP,
                    total_grids=12,
                    work_date=date(2026, 4, 15),
                    shift=Shift.AM,
                    team_number="11",
                    ticket_number="TKT-2",
                ),
            ),
        )

    submissions = (
        await integration_session.execute(
            select(Submission)
            .join(Workorder, Submission.workorder_id == Workorder.id)
            .where(Workorder.workorder_code_normalized == "WO-RACE-MULTI")
            .order_by(Submission.work_date.asc())
        )
    ).scalars().all()

    assert first_day.workorder_id == second_day.workorder_id
    assert [submission.work_date for submission in submissions] == [
        date(2026, 4, 14),
        date(2026, 4, 15),
    ]


async def test_start_drive_allows_multi_day_continuation_for_same_and_different_driver(
    integration_session: AsyncSession,
) -> None:
    first_driver = build_user(
        email="driver-one@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    second_driver = build_user(
        email="driver-two@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    integration_session.add_all([first_driver, second_driver])
    await integration_session.commit()

    service = WorkorderService(
        repository=WorkorderRepository(integration_session),
        _today_override=date(2026, 4, 16),
    )

    day_one = await service.start_drive(
        auth_payload(first_driver),
        StartDriveRequest(
            workorder_code="WO-CONTINUE",
            region=Region.NE_UP,
            total_grids=12,
            work_date=date(2026, 4, 14),
            shift=Shift.AM,
            team_number="11",
            ticket_number="TKT-1",
        ),
    )
    day_two_same_driver = await service.start_drive(
        auth_payload(first_driver),
        StartDriveRequest(
            workorder_code="WO-CONTINUE",
            work_date=date(2026, 4, 15),
            shift=Shift.AM,
            team_number="11",
            ticket_number="TKT-2",
        ),
    )
    day_three_different_driver = await service.start_drive(
        auth_payload(second_driver),
        StartDriveRequest(
            workorder_code="WO-CONTINUE",
            work_date=date(2026, 4, 16),
            shift=Shift.AM,
            team_number="22",
            ticket_number="TKT-3",
        ),
    )

    submissions = (
        await integration_session.execute(
            select(Submission)
            .where(Submission.workorder_id == day_one.workorder_id)
            .order_by(Submission.work_date.asc())
        )
    ).scalars().all()

    assert day_one.workorder_id == day_two_same_driver.workorder_id
    assert day_one.workorder_id == day_three_different_driver.workorder_id
    assert day_one.owner_user_id == first_driver.id
    assert day_two_same_driver.owner_user_id == first_driver.id
    assert day_three_different_driver.owner_user_id == second_driver.id
    assert [submission.work_date for submission in submissions] == [
        date(2026, 4, 14),
        date(2026, 4, 15),
        date(2026, 4, 16),
    ]


async def test_start_drive_rejects_future_work_date_for_workorder_region(
    integration_session: AsyncSession,
) -> None:
    owner = build_user(
        email="owner-future@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    integration_session.add(owner)
    await integration_session.commit()

    today = date(2026, 4, 14)
    future_date = today + timedelta(days=1)
    service = WorkorderService(
        repository=WorkorderRepository(integration_session),
        _today_override=today,
    )
    with pytest.raises(AppError) as exc:
        await service.start_drive(
            auth_payload(owner),
            StartDriveRequest(
                workorder_code="WO-FUTURE",
                region=Region.CENTRAL,
                total_grids=10,
                work_date=future_date,
                shift=Shift.AM,
                team_number="11",
                ticket_number="TKT-2",
            ),
        )

    assert exc.value.code.value == "VALIDATION_ERROR"
    assert exc.value.status_code == 422


async def test_submission_complete_requires_attachment(
    integration_session: AsyncSession,
) -> None:
    owner = build_user(
        email="owner-complete-fail@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    workorder = build_workorder(owner=owner, workorder_code="WO-COMPLETE")
    submission = build_submission(
        owner=owner,
        workorder=workorder,
        work_date=date(2026, 4, 14),
        status=SubmissionStatus.CHECKED_OUT,
        skipped_grids=1,
        completed_grids=8,
    )
    integration_session.add_all([owner, workorder, submission])
    await integration_session.commit()

    service = SubmissionService(
        repository=SubmissionRepository(integration_session)
    )
    with pytest.raises(AppError) as exc:
        await service.complete_submission(auth_payload(owner), submission.id)

    assert exc.value.code.value == "ATTACHMENT_REQUIRED"
    assert exc.value.status_code == 400


async def test_submission_complete_keeps_parent_active_until_aggregate_reaches_total(
    integration_session: AsyncSession,
) -> None:
    owner = build_user(
        email="owner-complete-partial@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    workorder = build_workorder(
        owner=owner,
        workorder_code="WO-PARTIAL-COMPLETE",
        total_grids=10,
    )
    first_submission = build_submission(
        owner=owner,
        workorder=workorder,
        work_date=date(2026, 4, 13),
        status=SubmissionStatus.COMPLETED,
        skipped_grids=1,
        completed_grids=4,
    )
    second_submission = build_submission(
        owner=owner,
        workorder=workorder,
        work_date=date(2026, 4, 14),
        status=SubmissionStatus.CHECKED_OUT,
        skipped_grids=0,
        completed_grids=2,
    )
    attachment = build_attachment(submission=second_submission, uploader=owner)
    integration_session.add_all(
        [owner, workorder, first_submission, second_submission, attachment]
    )
    await integration_session.commit()

    service = SubmissionService(repository=SubmissionRepository(integration_session))
    completed = await service.complete_submission(
        auth_payload(owner),
        second_submission.id,
    )

    saved_workorder = (
        await integration_session.execute(
            select(Workorder).where(Workorder.id == workorder.id)
        )
    ).scalar_one()

    assert completed.status == SubmissionStatus.COMPLETED
    assert saved_workorder.status == WorkorderStatus.ACTIVE
    assert saved_workorder.completed_at is None


async def test_submission_complete_marks_parent_completed_when_multi_day_total_is_met(
    integration_session: AsyncSession,
) -> None:
    owner = build_user(
        email="owner-complete-full@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    workorder = build_workorder(
        owner=owner,
        workorder_code="WO-FULL-COMPLETE",
        total_grids=10,
    )
    first_submission = build_submission(
        owner=owner,
        workorder=workorder,
        work_date=date(2026, 4, 13),
        status=SubmissionStatus.COMPLETED,
        skipped_grids=1,
        completed_grids=4,
    )
    second_submission = build_submission(
        owner=owner,
        workorder=workorder,
        work_date=date(2026, 4, 14),
        status=SubmissionStatus.CHECKED_OUT,
        skipped_grids=1,
        completed_grids=4,
    )
    attachment = build_attachment(submission=second_submission, uploader=owner)
    integration_session.add_all(
        [owner, workorder, first_submission, second_submission, attachment]
    )
    await integration_session.commit()

    service = SubmissionService(repository=SubmissionRepository(integration_session))
    await service.complete_submission(auth_payload(owner), second_submission.id)

    saved_workorder = (
        await integration_session.execute(
            select(Workorder).where(Workorder.id == workorder.id)
        )
    ).scalar_one()

    assert saved_workorder.status == WorkorderStatus.COMPLETED
    assert saved_workorder.completed_at is not None
    assert saved_workorder.completed_by_user_id == owner.id


async def test_submission_complete_then_reopen_updates_parent_and_audit(
    integration_session: AsyncSession,
) -> None:
    owner = build_user(
        email="owner-lifecycle@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    admin = build_user(
        email="admin-lifecycle@example.com",
        requested_role=RequestedRole.ADMIN,
        approved_role=RequestedRole.ADMIN,
        account_status=AccountStatus.APPROVED,
    )
    workorder = build_workorder(
        owner=owner,
        workorder_code="WO-LIFECYCLE",
        total_grids=10,
    )
    submission = build_submission(
        owner=owner,
        workorder=workorder,
        work_date=date(2026, 4, 14),
        status=SubmissionStatus.CHECKED_OUT,
        skipped_grids=1,
        completed_grids=9,
    )
    attachment = build_attachment(submission=submission, uploader=owner)
    integration_session.add_all(
        [owner, admin, workorder, submission, attachment]
    )
    await integration_session.commit()

    service = SubmissionService(
        repository=SubmissionRepository(integration_session)
    )
    completed = await service.complete_submission(
        auth_payload(owner),
        submission.id,
    )
    reopened = await service.reopen_submission(
        auth_payload(admin),
        submission.id,
    )

    assert completed.status == SubmissionStatus.COMPLETED
    assert reopened.status == SubmissionStatus.CHECKED_OUT
    assert reopened.file_submission_pending is False

    saved_submission = (
        await integration_session.execute(
            select(Submission).where(Submission.id == submission.id)
        )
    ).scalar_one()
    saved_workorder = (
        await integration_session.execute(
            select(Workorder).where(Workorder.id == workorder.id)
        )
    ).scalar_one()
    assert saved_submission.status == SubmissionStatus.CHECKED_OUT
    assert saved_submission.completed_by_user_id == owner.id
    assert saved_submission.reopened_by_user_id == admin.id
    assert saved_workorder.status == WorkorderStatus.ACTIVE

    logs = (
        await integration_session.execute(
            select(SubmissionAuditLog)
            .where(SubmissionAuditLog.submission_id == submission.id)
            .order_by(SubmissionAuditLog.created_at.asc())
        )
    ).scalars().all()
    action_types = [entry.action_type for entry in logs]
    assert AuditActionType.COMPLETED in action_types
    assert AuditActionType.REOPENED in action_types


async def test_reopen_one_completed_child_reverts_parent_without_changing_sibling(
    integration_session: AsyncSession,
) -> None:
    owner = build_user(
        email="owner-reopen-sibling@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    admin = build_user(
        email="admin-reopen-sibling@example.com",
        requested_role=RequestedRole.ADMIN,
        approved_role=RequestedRole.ADMIN,
        account_status=AccountStatus.APPROVED,
    )
    workorder = build_workorder(
        owner=owner,
        workorder_code="WO-REOPEN-SIBLING",
        status=WorkorderStatus.COMPLETED,
        total_grids=10,
    )
    first_submission = build_submission(
        owner=owner,
        workorder=workorder,
        work_date=date(2026, 4, 13),
        status=SubmissionStatus.COMPLETED,
        skipped_grids=1,
        completed_grids=4,
    )
    second_submission = build_submission(
        owner=owner,
        workorder=workorder,
        work_date=date(2026, 4, 14),
        status=SubmissionStatus.COMPLETED,
        skipped_grids=1,
        completed_grids=4,
    )
    first_attachment = build_attachment(submission=first_submission, uploader=owner)
    second_attachment = build_attachment(submission=second_submission, uploader=owner)
    integration_session.add_all(
        [
            owner,
            admin,
            workorder,
            first_submission,
            second_submission,
            first_attachment,
            second_attachment,
        ]
    )
    await integration_session.commit()

    service = SubmissionService(repository=SubmissionRepository(integration_session))
    reopened = await service.reopen_submission(
        auth_payload(admin),
        second_submission.id,
    )

    saved_workorder = (
        await integration_session.execute(
            select(Workorder).where(Workorder.id == workorder.id)
        )
    ).scalar_one()
    saved_first_submission = (
        await integration_session.execute(
            select(Submission).where(Submission.id == first_submission.id)
        )
    ).scalar_one()

    assert reopened.status == SubmissionStatus.CHECKED_OUT
    assert saved_workorder.status == WorkorderStatus.ACTIVE
    assert saved_workorder.completed_at is None
    assert saved_first_submission.status == SubmissionStatus.COMPLETED


async def test_submission_admin_list_supports_file_submission_pending_filter(
    integration_session: AsyncSession,
) -> None:
    admin = build_user(
        email="admin-filter@example.com",
        requested_role=RequestedRole.ADMIN,
        approved_role=RequestedRole.ADMIN,
        account_status=AccountStatus.APPROVED,
    )
    owner = build_user(
        email="owner-filter@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    pending_workorder = build_workorder(
        owner=owner,
        workorder_code="WO-PENDING",
    )
    with_file_workorder = build_workorder(
        owner=owner,
        workorder_code="WO-WITHFILE",
    )
    pending_file = build_submission(
        owner=owner,
        workorder=pending_workorder,
        work_date=date(2026, 4, 14),
        status=SubmissionStatus.CHECKED_OUT,
    )
    with_file = build_submission(
        owner=owner,
        workorder=with_file_workorder,
        work_date=date(2026, 4, 14),
        status=SubmissionStatus.CHECKED_OUT,
        ticket_number="TKT-2",
    )
    attachment = build_attachment(
        submission=with_file,
        uploader=owner,
        file_name="evidence.csv",
    )
    integration_session.add_all(
        [
            admin,
            owner,
            pending_workorder,
            with_file_workorder,
            pending_file,
            with_file,
            attachment,
        ]
    )
    await integration_session.commit()

    service = SubmissionService(
        repository=SubmissionRepository(integration_session)
    )
    items, total = await service.list_admin_submissions(
        auth_payload(admin),
        file_submission_pending=True,
        page=1,
        page_size=20,
    )

    assert total == 1
    assert len(items) == 1
    assert items[0].id == pending_file.id
    assert items[0].file_submission_pending is True


async def test_submission_update_requires_matching_version(
    integration_session: AsyncSession,
) -> None:
    owner = build_user(
        email="owner-version@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    workorder = build_workorder(owner=owner, workorder_code="WO-VERSION")
    submission = build_submission(
        owner=owner,
        workorder=workorder,
        work_date=date(2026, 4, 14),
        version_number=2,
    )
    integration_session.add_all([owner, workorder, submission])
    await integration_session.commit()

    service = SubmissionService(
        repository=SubmissionRepository(integration_session)
    )
    with pytest.raises(AppError) as exc:
        await service.update_submission(
            auth_payload(owner),
            submission.id,
            UpdateSubmissionRequest(version_number=1, team_number="22"),
        )

    assert exc.value.code.value == "VERSION_CONFLICT"
    assert exc.value.status_code == 409


async def test_submission_get_requires_owner(
    integration_session: AsyncSession,
) -> None:
    owner = build_user(
        email="owner-a@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    other = build_user(
        email="owner-b@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    workorder = build_workorder(owner=other, workorder_code="WO-OTHER")
    submission = build_submission(
        owner=other,
        workorder=workorder,
        work_date=date(2026, 4, 14),
    )
    integration_session.add_all([owner, other, workorder, submission])
    await integration_session.commit()

    service = SubmissionService(
        repository=SubmissionRepository(integration_session)
    )
    with pytest.raises(AppError) as exc:
        await service.get_submission(auth_payload(owner), submission.id)

    assert exc.value.code.value == "NOT_OWNER"
    assert exc.value.status_code == 403
