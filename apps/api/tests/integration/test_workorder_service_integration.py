import asyncio
from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.enums import (
    AccountStatus,
    RequestedRole,
    SubmissionStatus,
    WorkorderStatus,
)
from app.core.errors import AppError
from app.models.workorder import Workorder
from app.repositories.workorder_repository import WorkorderRepository
from app.schemas.workorders import UpdateWorkorderRequest
from app.services.workorder_service import WorkorderService
from tests.integration.helpers import (
    auth_payload,
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
        wait_on_save: _AsyncBarrier | None = None,
    ) -> None:
        super().__init__(session)
        self._wait_on_save = wait_on_save

    async def save_workorder(self, workorder: Workorder) -> Workorder:
        if self._wait_on_save is not None:
            await self._wait_on_save.wait()
        return await super().save_workorder(workorder)


async def test_update_workorder_rejects_duplicate_normalized_code(
    integration_session: AsyncSession,
) -> None:
    admin = build_user(
        email="admin-workorder-dup@example.com",
        requested_role=RequestedRole.ADMIN,
        approved_role=RequestedRole.ADMIN,
        account_status=AccountStatus.APPROVED,
    )
    first = build_workorder(owner=admin, workorder_code="WO FIRST")
    second = build_workorder(owner=admin, workorder_code="WO-SECOND")
    integration_session.add_all([admin, first, second])
    await integration_session.commit()

    service = WorkorderService(
        repository=WorkorderRepository(integration_session)
    )
    with pytest.raises(AppError) as exc:
        await service.update_workorder(
            auth_payload(admin),
            second.id,
            UpdateWorkorderRequest(workorder_code="wo   first"),
        )

    assert exc.value.code.value == "CONFLICT"
    assert exc.value.status_code == 409


async def test_update_workorder_total_grids_equal_to_aggregate_marks_parent_completed(
    integration_session: AsyncSession,
) -> None:
    admin = build_user(
        email="admin-workorder-equal@example.com",
        requested_role=RequestedRole.ADMIN,
        approved_role=RequestedRole.ADMIN,
        account_status=AccountStatus.APPROVED,
    )
    owner = build_user(
        email="owner-workorder-equal@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    workorder = build_workorder(
        owner=owner,
        workorder_code="WO-EQUAL-AGG",
        total_grids=12,
        status=WorkorderStatus.ACTIVE,
    )
    submission = build_submission(
        owner=owner,
        workorder=workorder,
        work_date=date(2026, 4, 14),
        status=SubmissionStatus.COMPLETED,
        skipped_grids=1,
        completed_grids=8,
    )
    integration_session.add_all([admin, owner, workorder, submission])
    await integration_session.commit()

    service = WorkorderService(
        repository=WorkorderRepository(integration_session)
    )
    updated = await service.update_workorder(
        auth_payload(admin),
        workorder.id,
        UpdateWorkorderRequest(total_grids=9),
    )

    saved_workorder = (
        await integration_session.execute(
            select(Workorder).where(Workorder.id == workorder.id)
        )
    ).scalar_one()

    assert updated.total_grids == 9
    assert updated.status == WorkorderStatus.COMPLETED
    assert saved_workorder.status == WorkorderStatus.COMPLETED
    assert saved_workorder.completed_at is not None
    assert saved_workorder.completed_by_user_id == admin.id


async def test_update_workorder_increasing_total_grids_reopens_completed_parent(
    integration_session: AsyncSession,
) -> None:
    admin = build_user(
        email="admin-workorder-reopen@example.com",
        requested_role=RequestedRole.ADMIN,
        approved_role=RequestedRole.ADMIN,
        account_status=AccountStatus.APPROVED,
    )
    owner = build_user(
        email="owner-workorder-reopen@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    workorder = build_workorder(
        owner=owner,
        workorder_code="WO-REOPEN-ADMIN",
        total_grids=9,
        status=WorkorderStatus.COMPLETED,
    )
    submission = build_submission(
        owner=owner,
        workorder=workorder,
        work_date=date(2026, 4, 14),
        status=SubmissionStatus.COMPLETED,
        skipped_grids=1,
        completed_grids=8,
    )
    integration_session.add_all([admin, owner, workorder, submission])
    await integration_session.commit()

    service = WorkorderService(
        repository=WorkorderRepository(integration_session)
    )
    updated = await service.update_workorder(
        auth_payload(admin),
        workorder.id,
        UpdateWorkorderRequest(total_grids=12),
    )

    saved_workorder = (
        await integration_session.execute(
            select(Workorder).where(Workorder.id == workorder.id)
        )
    ).scalar_one()

    assert updated.total_grids == 12
    assert updated.status == WorkorderStatus.ACTIVE
    assert saved_workorder.status == WorkorderStatus.ACTIVE
    assert saved_workorder.completed_at is None
    assert saved_workorder.completed_by_user_id is None


async def test_update_workorder_preserves_existing_completion_actor_when_still_completed(
    integration_session: AsyncSession,
) -> None:
    admin = build_user(
        email="admin-workorder-preserve@example.com",
        requested_role=RequestedRole.ADMIN,
        approved_role=RequestedRole.ADMIN,
        account_status=AccountStatus.APPROVED,
    )
    owner = build_user(
        email="owner-workorder-preserve@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    workorder = build_workorder(
        owner=owner,
        workorder_code="WO-PRESERVE-COMPLETE",
        total_grids=9,
        status=WorkorderStatus.COMPLETED,
    )
    original_completed_at = workorder.completed_at
    original_completed_by_user_id = workorder.completed_by_user_id
    submission = build_submission(
        owner=owner,
        workorder=workorder,
        work_date=date(2026, 4, 14),
        status=SubmissionStatus.COMPLETED,
        skipped_grids=1,
        completed_grids=8,
    )
    integration_session.add_all([admin, owner, workorder, submission])
    await integration_session.commit()

    service = WorkorderService(
        repository=WorkorderRepository(integration_session)
    )
    updated = await service.update_workorder(
        auth_payload(admin),
        workorder.id,
        UpdateWorkorderRequest(region=workorder.region),
    )

    saved_workorder = (
        await integration_session.execute(
            select(Workorder).where(Workorder.id == workorder.id)
        )
    ).scalar_one()

    assert updated.status == WorkorderStatus.COMPLETED
    assert saved_workorder.completed_at == original_completed_at
    assert saved_workorder.completed_by_user_id == original_completed_by_user_id


async def test_update_workorder_concurrent_duplicate_rename_returns_conflict(
    integration_session: AsyncSession,
) -> None:
    admin = build_user(
        email="admin-workorder-race@example.com",
        requested_role=RequestedRole.ADMIN,
        approved_role=RequestedRole.ADMIN,
        account_status=AccountStatus.APPROVED,
    )
    first = build_workorder(owner=admin, workorder_code="WO-ALPHA")
    second = build_workorder(owner=admin, workorder_code="WO-BETA")
    third = build_workorder(owner=admin, workorder_code="WO-GAMMA")
    integration_session.add_all([admin, first, second, third])
    await integration_session.commit()

    bind = integration_session.bind
    assert bind is not None
    barrier = _AsyncBarrier(2)
    session_factory = async_sessionmaker(
        bind=bind,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session_one:
        async with session_factory() as session_two:
            service_one = WorkorderService(
                repository=_CoordinatedWorkorderRepository(
                    session_one,
                    wait_on_save=barrier,
                )
            )
            service_two = WorkorderService(
                repository=_CoordinatedWorkorderRepository(
                    session_two,
                    wait_on_save=barrier,
                )
            )

            results = await asyncio.gather(
                service_one.update_workorder(
                    auth_payload(admin),
                    second.id,
                    UpdateWorkorderRequest(workorder_code="WO SHARED"),
                ),
                service_two.update_workorder(
                    auth_payload(admin),
                    third.id,
                    UpdateWorkorderRequest(workorder_code="wo   shared"),
                ),
                return_exceptions=True,
            )

    successes = [result for result in results if not isinstance(result, Exception)]
    failures = [result for result in results if isinstance(result, Exception)]

    assert len(successes) == 1
    assert len(failures) == 1
    assert isinstance(failures[0], AppError)
    assert failures[0].code.value == "CONFLICT"
    assert failures[0].status_code == 409

    async with session_factory() as verification_session:
        saved_workorders = (
            await verification_session.execute(
                select(Workorder).order_by(Workorder.workorder_code.asc())
            )
        ).scalars().all()
    normalized_codes = [workorder.workorder_code_normalized for workorder in saved_workorders]

    assert normalized_codes.count("WOSHARED") == 1
    assert normalized_codes.count("WO-BETA") + normalized_codes.count("WO-GAMMA") == 1
