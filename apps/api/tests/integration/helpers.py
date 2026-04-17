import unicodedata
import uuid
from datetime import UTC, date, datetime
from pathlib import Path

from app.core.enums import (
    AccountStatus,
    Region,
    RequestedRole,
    Shift,
    SubmissionStatus,
    WorkorderStatus,
)
from app.models.app_user import AppUser
from app.models.submission import Submission
from app.models.submission_attachment import SubmissionAttachment
from app.models.workorder import Workorder


def build_user(
    *,
    email: str,
    requested_role: RequestedRole,
    approved_role: RequestedRole | None,
    account_status: AccountStatus,
    full_name: str | None = None,
) -> AppUser:
    now = datetime.now(UTC)
    return AppUser(
        id=uuid.uuid4(),
        auth_user_id=uuid.uuid4(),
        full_name=full_name or email.split("@")[0],
        email=email,
        requested_role=requested_role,
        approved_role=approved_role,
        account_status=account_status,
        approved_at=now if account_status == AccountStatus.APPROVED else None,
        approved_by_user_id=None,
        created_at=now,
        updated_at=now,
    )


def auth_payload(user: AppUser) -> dict[str, str]:
    return {"sub": str(user.auth_user_id), "email": user.email}


def normalize_workorder_code(code: str) -> str:
    return unicodedata.normalize("NFKC", code).strip().upper().replace(" ", "")


def build_workorder(
    *,
    owner: AppUser,
    workorder_code: str,
    region: Region = Region.NE_UP,
    total_grids: int = 10,
    status: WorkorderStatus = WorkorderStatus.ACTIVE,
) -> Workorder:
    now = datetime.now(UTC)
    return Workorder(
        id=uuid.uuid4(),
        workorder_code=workorder_code,
        workorder_code_normalized=normalize_workorder_code(workorder_code),
        region=region,
        total_grids=total_grids,
        status=status,
        created_at=now,
        created_by_user_id=owner.id,
        updated_at=now,
        updated_by_user_id=owner.id,
        completed_at=now if status == WorkorderStatus.COMPLETED else None,
        completed_by_user_id=owner.id if status == WorkorderStatus.COMPLETED else None,
    )


def build_submission(
    *,
    owner: AppUser,
    workorder: Workorder,
    work_date: date,
    shift: Shift = Shift.AM,
    team_number: str | None = "11",
    ticket_number: str | None = "TKT-1",
    skipped_grids: int = 0,
    force_tested_grids: int = 0,
    completed_grids: int = 0,
    status: SubmissionStatus = SubmissionStatus.IN_PROGRESS,
    version_number: int = 1,
) -> Submission:
    now = datetime.now(UTC)
    ended_at = now if status in {SubmissionStatus.CHECKED_OUT, SubmissionStatus.COMPLETED} else None
    completed_at = now if status == SubmissionStatus.COMPLETED else None
    completed_by_user_id = owner.id if status == SubmissionStatus.COMPLETED else None
    return Submission(
        id=uuid.uuid4(),
        client_generated_id=uuid.uuid4(),
        workorder_id=workorder.id,
        owner_user_id=owner.id,
        submitter_name_snapshot=owner.full_name,
        submitter_email_snapshot=owner.email,
        work_date=work_date,
        shift=shift,
        team_number=team_number,
        ticket_number=ticket_number,
        skipped_grids=skipped_grids,
        force_tested_grids=force_tested_grids,
        completed_grids=completed_grids,
        status=status,
        started_at=now,
        ended_at=ended_at,
        created_at=now,
        created_by_user_id=owner.id,
        updated_at=now,
        updated_by_user_id=owner.id,
        completed_at=completed_at,
        completed_by_user_id=completed_by_user_id,
        reopened_at=None,
        reopened_by_user_id=None,
        version_number=version_number,
    )


def build_attachment(
    *,
    submission: Submission,
    uploader: AppUser,
    file_name: str = "report.csv",
    bucket_name: str = "attachments",
    mime_type: str = "text/csv",
    file_size_bytes: int = 128,
    is_active: bool = True,
) -> SubmissionAttachment:
    now = datetime.now(UTC)
    extension = Path(file_name).suffix.lower()
    return SubmissionAttachment(
        id=uuid.uuid4(),
        submission_id=submission.id,
        file_name=file_name,
        bucket_name=bucket_name,
        object_path=f"{submission.id}/{uuid.uuid4().hex}{extension}",
        mime_type=mime_type,
        file_extension=extension,
        file_size_bytes=file_size_bytes,
        uploaded_by_user_id=uploader.id,
        uploaded_at=now,
        is_active=is_active,
    )
