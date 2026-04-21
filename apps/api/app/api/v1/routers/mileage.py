from datetime import UTC, date, datetime
from typing import Any

from fastapi import APIRouter, Depends, File, Form, Query, Request, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.responses import success_envelope
from app.core.security import get_current_auth_payload
from app.db.session import get_db_session
from app.integrations.storage.base import StorageProviderProtocol
from app.integrations.storage.supabase_storage import SupabaseStorageProvider
from app.repositories.mileage_repository import MileageRepository
from app.schemas.mileage import MileageEntryResponse
from app.services.mileage_service import MileageService, MileageUpload

router = APIRouter(prefix="/mileage", tags=["mileage"])


def get_storage_provider(
    settings: Settings = Depends(get_settings),
) -> StorageProviderProtocol:
    return SupabaseStorageProvider(
        supabase_url=str(settings.supabase_url) if settings.supabase_url is not None else None,
        service_role_key=settings.resolved_supabase_service_role_key,
    )


def get_mileage_service(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    storage: StorageProviderProtocol = Depends(get_storage_provider),
) -> MileageService:
    return MileageService(
        repository=MileageRepository(session),
        storage=storage,
        settings=settings,
    )


@router.get("")
async def get_mileage_for_date(
    request: Request,
    work_date: date = Query(...),
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: MileageService = Depends(get_mileage_service),
) -> dict[str, Any]:
    entry = await service.get_entry_for_date(auth_payload, work_date)
    return success_envelope(
        data=MileageEntryResponse.model_validate(entry).model_dump(mode="json") if entry else None,
        request_id=request.state.request_id,
    )


@router.post("/start")
async def start_mileage_shift(
    request: Request,
    response: Response,
    work_date: date = Form(...),
    start_mileage: int = Form(...),
    started_at: str | None = Form(default=None),
    odometer_image: UploadFile = File(...),
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: MileageService = Depends(get_mileage_service),
) -> dict[str, Any]:
    timestamp = datetime.fromisoformat(started_at) if started_at else datetime.now(UTC)
    upload = MileageUpload(
        file_name=odometer_image.filename or "",
        content_type=odometer_image.content_type or "",
        content=await odometer_image.read(),
    )
    entry = await service.start_shift(
        auth_payload,
        work_date=work_date,
        start_mileage=start_mileage,
        started_at=timestamp,
        upload=upload,
    )
    response.status_code = status.HTTP_201_CREATED
    return success_envelope(
        data=MileageEntryResponse.model_validate(entry).model_dump(mode="json"),
        request_id=request.state.request_id,
    )


@router.post("/end")
async def end_mileage_shift(
    request: Request,
    work_date: date = Form(...),
    end_mileage: int = Form(...),
    ended_at: str | None = Form(default=None),
    odometer_image: UploadFile = File(...),
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: MileageService = Depends(get_mileage_service),
) -> dict[str, Any]:
    timestamp = datetime.fromisoformat(ended_at) if ended_at else datetime.now(UTC)
    upload = MileageUpload(
        file_name=odometer_image.filename or "",
        content_type=odometer_image.content_type or "",
        content=await odometer_image.read(),
    )
    entry = await service.end_shift(
        auth_payload,
        work_date=work_date,
        end_mileage=end_mileage,
        ended_at=timestamp,
        upload=upload,
    )
    return success_envelope(
        data=MileageEntryResponse.model_validate(entry).model_dump(mode="json"),
        request_id=request.state.request_id,
    )
