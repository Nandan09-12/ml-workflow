import uuid
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.models.submission_attachment import SubmissionAttachment
from app.models.submission_audit_log import SubmissionAuditLog
from app.repositories.submission_repository import SubmissionRepository
from app.schemas.submissions import CreateSubmissionRequest, UpdateSubmissionRequest
from app.services.submission_service import SubmissionService

pytestmark = pytest.mark.integration


def _build_user(
    *,
    email: str,
    requested_role: RequestedRole,
    approved_role: RequestedRole | None,
    account_status: AccountStatus,
) -> AppUser:
    now = datetime.now(UTC)
    return AppUser(
        id=uuid.uuid4(),
        auth_user_id=uuid.uuid4(),
        full_name=email.split("@")[0],
        email=email,
        requested_role=requested_role,
        approved_role=approved_role,
        account_status=account_status,
        approved_at=now if account_status == AccountStatus.APPROVED else None,
        approved_by_user_id=None,
        created_at=now,
        updated_at=now,
    )


def _auth_payload(user: AppUser) -> dict[str, str]:
    return {"sub": str(user.auth_user_id), "email": user.email}


def _today_for_zone(zone: Zone) -> date:
    timezone_map = {
        Zone.NORTHEAST: "America/New_York",
        Zone.SOUTH_FLORIDA: "America/New_York",
        Zone.CENTRAL: "America/Chicago",
    }
    return datetime.now(ZoneInfo(timezone_map[zone])).date()


def _build_submission(
    *,
    owner: AppUser,
    work_date: date,
    cluster_name: str,
    cluster_name_normalized: str,
    status: SubmissionStatus = SubmissionStatus.IN_PROGRESS,
    pending_grids: int = 2,
    completed_grids: int = 7,
    version_number: int = 1,
) -> Submission:
    now = datetime.now(UTC)
    return Submission(
        id=uuid.uuid4(),
        client_generated_id=uuid.uuid4(),
        owner_user_id=owner.id,
        submitter_name_snapshot=owner.full_name,
        submitter_email_snapshot=owner.email,
        zone=Zone.NORTHEAST,
        work_date=work_date,
        shift=Shift.AM,
        team_number="11",
        ticket_number="TKT-1",
        cluster_name=cluster_name,
        cluster_name_normalized=cluster_name_normalized,
        number_of_grids=10,
        skipped_grids=1,
        force_tested_grids=0,
        pending_grids=pending_grids,
        completed_grids=completed_grids,
        status=status,
        created_at=now,
        created_by_user_id=owner.id,
        updated_at=now,
        updated_by_user_id=owner.id,
        completed_at=now if status == SubmissionStatus.COMPLETED else None,
        completed_by_user_id=owner.id if status == SubmissionStatus.COMPLETED else None,
        reopened_at=None,
        reopened_by_user_id=None,
        version_number=version_number,
    )


async def test_submission_create_persists_normalized_cluster_and_audit(
    integration_session: AsyncSession,
) -> None:
    owner = _build_user(
        email="owner-create@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    integration_session.add(owner)
    await integration_session.commit()

    service = SubmissionService(repository=SubmissionRepository(integration_session))
    created = await service.create_submission(
        _auth_payload(owner),
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

    assert created.cluster_name == "Clu-ster__One"
    assert created.cluster_name_normalized == "CLU STER ONE"
    assert created.status == SubmissionStatus.IN_PROGRESS
    assert created.file_submission_pending is False

    saved = (
        await integration_session.execute(select(Submission).where(Submission.id == created.id))
    ).scalar_one()
    assert saved.cluster_name_normalized == "CLU STER ONE"

    logs = (
        await integration_session.execute(
            select(SubmissionAuditLog).where(SubmissionAuditLog.submission_id == created.id)
        )
    ).scalars().all()
    assert len(logs) == 1
    assert logs[0].action_type == AuditActionType.CREATED


async def test_submission_create_rejects_duplicate_by_normalized_key(
    integration_session: AsyncSession,
) -> None:
    owner = _build_user(
        email="owner-dup@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    selected_date = _today_for_zone(Zone.NORTHEAST)
    existing = _build_submission(
        owner=owner,
        work_date=selected_date,
        cluster_name="Alpha Cluster",
        cluster_name_normalized="ALPHA CLUSTER",
    )
    integration_session.add_all([owner, existing])
    await integration_session.commit()

    service = SubmissionService(repository=SubmissionRepository(integration_session))
    with pytest.raises(AppError) as exc:
        await service.create_submission(
            _auth_payload(owner),
            CreateSubmissionRequest(
                zone=Zone.NORTHEAST,
                work_date=selected_date,
                shift=Shift.AM,
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


async def test_submission_create_rejects_future_work_date_for_zone(
    integration_session: AsyncSession,
) -> None:
    owner = _build_user(
        email="owner-future@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    integration_session.add(owner)
    await integration_session.commit()
    future_date = _today_for_zone(Zone.CENTRAL) + timedelta(days=1)

    service = SubmissionService(repository=SubmissionRepository(integration_session))
    with pytest.raises(AppError) as exc:
        await service.create_submission(
            _auth_payload(owner),
            CreateSubmissionRequest(
                zone=Zone.CENTRAL,
                work_date=future_date,
                shift=Shift.AM,
                team_number="11",
                ticket_number="TKT-2",
                cluster_name="Future Cluster",
                number_of_grids=10,
                skipped_grids=1,
                force_tested_grids=0,
                pending_grids=2,
                completed_grids=7,
            ),
        )

    assert exc.value.code.value == "VALIDATION_ERROR"
    assert exc.value.status_code == 400


async def test_submission_complete_requires_pending_grids_zero(
    integration_session: AsyncSession,
) -> None:
    owner = _build_user(
        email="owner-complete-fail@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    submission = _build_submission(
        owner=owner,
        work_date=_today_for_zone(Zone.NORTHEAST),
        cluster_name="Cluster Pending",
        cluster_name_normalized="CLUSTER PENDING",
        pending_grids=1,
        completed_grids=8,
    )
    integration_session.add_all([owner, submission])
    await integration_session.commit()

    service = SubmissionService(repository=SubmissionRepository(integration_session))
    with pytest.raises(AppError) as exc:
        await service.complete_submission(_auth_payload(owner), submission.id)

    assert exc.value.code.value == "PENDING_GRIDS_MUST_BE_ZERO"
    assert exc.value.status_code == 400


async def test_submission_complete_then_reopen_updates_status_flags_and_audit(
    integration_session: AsyncSession,
) -> None:
    owner = _build_user(
        email="owner-lifecycle@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    admin = _build_user(
        email="admin-lifecycle@example.com",
        requested_role=RequestedRole.ADMIN,
        approved_role=RequestedRole.ADMIN,
        account_status=AccountStatus.APPROVED,
    )
    submission = _build_submission(
        owner=owner,
        work_date=_today_for_zone(Zone.NORTHEAST),
        cluster_name="Cluster Lifecycle",
        cluster_name_normalized="CLUSTER LIFECYCLE",
        pending_grids=0,
        completed_grids=9,
    )
    integration_session.add_all([owner, admin, submission])
    await integration_session.commit()

    service = SubmissionService(repository=SubmissionRepository(integration_session))
    completed = await service.complete_submission(_auth_payload(owner), submission.id)
    reopened = await service.reopen_submission(_auth_payload(admin), submission.id)

    assert completed.status == SubmissionStatus.COMPLETED
    assert completed.file_submission_pending is True
    assert reopened.status == SubmissionStatus.IN_PROGRESS
    assert reopened.file_submission_pending is False

    saved = (
        await integration_session.execute(select(Submission).where(Submission.id == submission.id))
    ).scalar_one()
    assert saved.reopened_by_user_id == admin.id
    assert saved.completed_by_user_id == owner.id

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


async def test_submission_admin_list_supports_file_submission_pending_filter(
    integration_session: AsyncSession,
) -> None:
    admin = _build_user(
        email="admin-filter@example.com",
        requested_role=RequestedRole.ADMIN,
        approved_role=RequestedRole.ADMIN,
        account_status=AccountStatus.APPROVED,
    )
    owner = _build_user(
        email="owner-filter@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    selected_date = _today_for_zone(Zone.NORTHEAST)
    pending_file = _build_submission(
        owner=owner,
        work_date=selected_date,
        cluster_name="Pending File",
        cluster_name_normalized="PENDING FILE",
        status=SubmissionStatus.COMPLETED,
        pending_grids=0,
        completed_grids=9,
    )
    with_file = _build_submission(
        owner=owner,
        work_date=selected_date,
        cluster_name="Has File",
        cluster_name_normalized="HAS FILE",
        status=SubmissionStatus.COMPLETED,
        pending_grids=0,
        completed_grids=9,
    )
    integration_session.add_all([admin, owner, pending_file, with_file])
    await integration_session.flush()
    integration_session.add(
        SubmissionAttachment(
            id=uuid.uuid4(),
            submission_id=with_file.id,
            file_name="evidence.csv",
            bucket_name="attachments",
            object_path=f"{with_file.id}/evidence.csv",
            mime_type="text/csv",
            file_extension=".csv",
            file_size_bytes=100,
            uploaded_by_user_id=owner.id,
            uploaded_at=datetime.now(UTC),
            is_active=True,
        )
    )
    await integration_session.commit()

    service = SubmissionService(repository=SubmissionRepository(integration_session))
    items, total = await service.list_admin_submissions(
        _auth_payload(admin),
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
    owner = _build_user(
        email="owner-version@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    submission = _build_submission(
        owner=owner,
        work_date=_today_for_zone(Zone.NORTHEAST),
        cluster_name="Versioned",
        cluster_name_normalized="VERSIONED",
        version_number=2,
    )
    integration_session.add_all([owner, submission])
    await integration_session.commit()

    service = SubmissionService(repository=SubmissionRepository(integration_session))
    with pytest.raises(AppError) as exc:
        await service.update_submission(
            _auth_payload(owner),
            submission.id,
            UpdateSubmissionRequest(version_number=1, team_number="22"),
        )

    assert exc.value.code.value == "VERSION_CONFLICT"
    assert exc.value.status_code == 409


async def test_submission_get_requires_owner(
    integration_session: AsyncSession,
) -> None:
    owner = _build_user(
        email="owner-a@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    other = _build_user(
        email="owner-b@example.com",
        requested_role=RequestedRole.DRIVE_TESTER,
        approved_role=RequestedRole.DRIVE_TESTER,
        account_status=AccountStatus.APPROVED,
    )
    submission = _build_submission(
        owner=other,
        work_date=_today_for_zone(Zone.NORTHEAST),
        cluster_name="Other Owner",
        cluster_name_normalized="OTHER OWNER",
    )
    integration_session.add_all([owner, other, submission])
    await integration_session.commit()

    service = SubmissionService(repository=SubmissionRepository(integration_session))
    with pytest.raises(AppError) as exc:
        await service.get_submission(_auth_payload(owner), submission.id)

    assert exc.value.code.value == "NOT_OWNER"
    assert exc.value.status_code == 403
