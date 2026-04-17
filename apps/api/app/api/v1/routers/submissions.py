import math
import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import Shift, SubmissionStatus
from app.core.responses import success_envelope
from app.core.security import get_current_auth_payload
from app.db.session import get_db_session
from app.repositories.submission_repository import SubmissionRepository
from app.repositories.workorder_repository import WorkorderRepository
from app.schemas.submissions import (
    SubmissionResponse,
    UpdateSubmissionRequest,
)
from app.schemas.workorders import StartDriveRequest
from app.services.submission_service import SubmissionService
from app.services.workorder_service import WorkorderService

router = APIRouter(prefix="/submissions", tags=["submissions"])


def get_submission_service(
    session: AsyncSession = Depends(get_db_session),
) -> SubmissionService:
    return SubmissionService(repository=SubmissionRepository(session))


def get_workorder_service_for_submissions(
    session: AsyncSession = Depends(get_db_session),
) -> WorkorderService:
    return WorkorderService(repository=WorkorderRepository(session))


@router.post("")
async def start_drive(
    payload: StartDriveRequest,
    request: Request,
    response: Response,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: WorkorderService = Depends(get_workorder_service_for_submissions),
) -> dict[str, Any]:
    submission = await service.start_drive(auth_payload, payload)
    response.status_code = 201
    return success_envelope(
        data=SubmissionResponse.model_validate(submission.__dict__).model_dump(mode="json"),
        request_id=request.state.request_id,
    )


@router.get("")
async def list_my_submissions(
    request: Request,
    work_date: date | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    status: SubmissionStatus | None = Query(default=None),
    shift: Shift | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: SubmissionService = Depends(get_submission_service),
) -> dict[str, Any]:
    submissions, total = await service.list_my_submissions(
        auth_payload,
        work_date=work_date,
        date_from=date_from,
        date_to=date_to,
        status=status,
        shift=shift,
        page=page,
        page_size=page_size,
    )
    items = [SubmissionResponse.model_validate(item).model_dump(mode="json") for item in submissions]
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return success_envelope(
        data={
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
            },
        },
        request_id=request.state.request_id,
    )


@router.get("/{submission_id}")
async def get_submission_detail(
    submission_id: uuid.UUID,
    request: Request,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: SubmissionService = Depends(get_submission_service),
) -> dict[str, Any]:
    submission = await service.get_submission(auth_payload, submission_id)
    return success_envelope(
        data=SubmissionResponse.model_validate(submission).model_dump(mode="json"),
        request_id=request.state.request_id,
    )


@router.patch("/{submission_id}")
async def update_submission(
    submission_id: uuid.UUID,
    payload: UpdateSubmissionRequest,
    request: Request,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: SubmissionService = Depends(get_submission_service),
) -> dict[str, Any]:
    submission = await service.update_submission(auth_payload, submission_id, payload)
    return success_envelope(
        data=SubmissionResponse.model_validate(submission).model_dump(mode="json"),
        request_id=request.state.request_id,
    )


@router.post("/{submission_id}/end-drive")
async def end_drive(
    submission_id: uuid.UUID,
    request: Request,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: SubmissionService = Depends(get_submission_service),
) -> dict[str, Any]:
    submission = await service.end_drive(auth_payload, submission_id)
    return success_envelope(
        data=SubmissionResponse.model_validate(submission).model_dump(mode="json"),
        request_id=request.state.request_id,
    )


@router.post("/{submission_id}/complete")
async def complete_submission(
    submission_id: uuid.UUID,
    request: Request,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: SubmissionService = Depends(get_submission_service),
) -> dict[str, Any]:
    submission = await service.complete_submission(auth_payload, submission_id)
    return success_envelope(
        data=SubmissionResponse.model_validate(submission).model_dump(mode="json"),
        request_id=request.state.request_id,
    )
