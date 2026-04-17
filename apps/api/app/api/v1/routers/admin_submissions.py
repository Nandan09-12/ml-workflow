import math
import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.enums import Shift, SubmissionStatus
from app.core.responses import success_envelope
from app.core.security import get_current_auth_payload
from app.db.session import get_db_session
from app.integrations.storage.base import StorageProviderProtocol
from app.integrations.storage.supabase_storage import SupabaseStorageProvider
from app.repositories.attachment_repository import AttachmentRepository
from app.repositories.submission_repository import SubmissionRepository
from app.schemas.attachments import AttachmentResponse
from app.schemas.submissions import (
    SubmissionAuditResponse,
    SubmissionResponse,
    UpdateSubmissionRequest,
)
from app.services.attachment_service import AttachmentService
from app.services.submission_service import SubmissionService

router = APIRouter(prefix="/admin/submissions", tags=["admin-submissions"])


def get_admin_submission_service(
    session: AsyncSession = Depends(get_db_session),
) -> SubmissionService:
    return SubmissionService(repository=SubmissionRepository(session))


def get_storage_provider(
    settings: Settings = Depends(get_settings),
) -> StorageProviderProtocol:
    return SupabaseStorageProvider(
        supabase_url=str(settings.supabase_url) if settings.supabase_url is not None else None,
        service_role_key=settings.resolved_supabase_service_role_key,
    )


def get_attachment_service(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    storage: StorageProviderProtocol = Depends(get_storage_provider),
) -> AttachmentService:
    return AttachmentService(
        repository=AttachmentRepository(session),
        storage=storage,
        settings=settings,
    )


@router.post("/{submission_id}/reopen")
async def reopen_submission(
    submission_id: uuid.UUID,
    request: Request,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: SubmissionService = Depends(get_admin_submission_service),
) -> dict[str, Any]:
    submission = await service.reopen_submission(auth_payload, submission_id)
    return success_envelope(
        data=SubmissionResponse.model_validate(submission).model_dump(mode="json"),
        request_id=request.state.request_id,
    )


@router.get("")
async def list_admin_submissions(
    request: Request,
    work_date: date | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    status: SubmissionStatus | None = Query(default=None),
    shift: Shift | None = Query(default=None),
    owner_user_id: uuid.UUID | None = Query(default=None),
    ticket_number: str | None = Query(default=None),
    file_submission_pending: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: SubmissionService = Depends(get_admin_submission_service),
) -> dict[str, Any]:
    submissions, total = await service.list_admin_submissions(
        auth_payload,
        work_date=work_date,
        date_from=date_from,
        date_to=date_to,
        status=status,
        shift=shift,
        owner_user_id=owner_user_id,
        ticket_number=ticket_number,
        file_submission_pending=file_submission_pending,
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
async def get_admin_submission_detail(
    submission_id: uuid.UUID,
    request: Request,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: SubmissionService = Depends(get_admin_submission_service),
) -> dict[str, Any]:
    submission = await service.get_admin_submission(auth_payload, submission_id)
    return success_envelope(
        data=SubmissionResponse.model_validate(submission).model_dump(mode="json"),
        request_id=request.state.request_id,
    )


@router.patch("/{submission_id}")
async def update_admin_submission(
    submission_id: uuid.UUID,
    payload: UpdateSubmissionRequest,
    request: Request,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: SubmissionService = Depends(get_admin_submission_service),
) -> dict[str, Any]:
    submission = await service.update_admin_submission(auth_payload, submission_id, payload)
    return success_envelope(
        data=SubmissionResponse.model_validate(submission).model_dump(mode="json"),
        request_id=request.state.request_id,
    )


@router.get("/{submission_id}/audit")
async def get_admin_submission_audit(
    submission_id: uuid.UUID,
    request: Request,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: SubmissionService = Depends(get_admin_submission_service),
) -> dict[str, Any]:
    entries = await service.get_submission_audit(auth_payload, submission_id)
    items = [SubmissionAuditResponse.model_validate(item).model_dump(mode="json") for item in entries]
    return success_envelope(
        data={"items": items, "count": len(items)},
        request_id=request.state.request_id,
    )


@router.get("/{submission_id}/attachments/history")
async def get_attachment_history(
    submission_id: uuid.UUID,
    request: Request,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: AttachmentService = Depends(get_attachment_service),
) -> dict[str, Any]:
    attachments = await service.get_attachment_history(auth_payload, submission_id)
    items = [AttachmentResponse.model_validate(item.__dict__).model_dump(mode="json") for item in attachments]
    return success_envelope(
        data={"items": items, "count": len(items)},
        request_id=request.state.request_id,
    )
