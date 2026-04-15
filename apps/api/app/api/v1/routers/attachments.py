import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.responses import success_envelope
from app.core.security import get_current_auth_payload
from app.db.session import get_db_session
from app.integrations.storage.base import StorageProviderProtocol
from app.integrations.storage.supabase_storage import SupabaseStorageProvider
from app.repositories.attachment_repository import AttachmentRepository
from app.schemas.attachments import AttachmentResponse, DownloadUrlResponse
from app.services.attachment_service import AttachmentService, AttachmentUpload

router = APIRouter(tags=["attachments"])


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


@router.post("/submissions/{submission_id}/attachments")
async def upload_attachment(
    submission_id: uuid.UUID,
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: AttachmentService = Depends(get_attachment_service),
) -> dict[str, Any]:
    content = await file.read()
    upload = AttachmentUpload(
        file_name=file.filename or "",
        content_type=file.content_type or "",
        content=content,
    )
    attachment = await service.upload_attachment(auth_payload, submission_id, upload)
    response.status_code = status.HTTP_201_CREATED
    return success_envelope(
        data=AttachmentResponse.model_validate(attachment).model_dump(mode="json"),
        request_id=request.state.request_id,
    )


@router.get("/submissions/{submission_id}/attachments")
async def list_submission_attachments(
    submission_id: uuid.UUID,
    request: Request,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: AttachmentService = Depends(get_attachment_service),
) -> dict[str, Any]:
    attachments = await service.list_attachments(auth_payload, submission_id)
    items = [AttachmentResponse.model_validate(item).model_dump(mode="json") for item in attachments]
    return success_envelope(
        data={"items": items, "count": len(items)},
        request_id=request.state.request_id,
    )


@router.get("/attachments/{attachment_id}")
async def get_attachment_metadata(
    attachment_id: uuid.UUID,
    request: Request,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: AttachmentService = Depends(get_attachment_service),
) -> dict[str, Any]:
    attachment = await service.get_attachment(auth_payload, attachment_id)
    return success_envelope(
        data=AttachmentResponse.model_validate(attachment).model_dump(mode="json"),
        request_id=request.state.request_id,
    )


@router.post("/attachments/{attachment_id}/download-url")
async def create_download_url(
    attachment_id: uuid.UUID,
    request: Request,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: AttachmentService = Depends(get_attachment_service),
) -> dict[str, Any]:
    payload = await service.create_download_url(auth_payload, attachment_id)
    return success_envelope(
        data=DownloadUrlResponse.model_validate(payload).model_dump(mode="json"),
        request_id=request.state.request_id,
    )


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    attachment_id: uuid.UUID,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: AttachmentService = Depends(get_attachment_service),
) -> Response:
    await service.delete_attachment(auth_payload, attachment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
