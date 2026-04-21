from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, File, Form, Request, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.responses import success_envelope
from app.core.security import get_current_auth_payload
from app.db.session import get_db_session
from app.integrations.storage.base import StorageProviderProtocol
from app.integrations.storage.supabase_storage import SupabaseStorageProvider
from app.repositories.expense_repository import ExpenseRepository
from app.schemas.expenses import ExpenseEntryResponse
from app.services.expense_service import ExpenseService, ExpenseUpload

router = APIRouter(prefix="/expenses", tags=["expenses"])


def get_storage_provider(
    settings: Settings = Depends(get_settings),
) -> StorageProviderProtocol:
    return SupabaseStorageProvider(
        supabase_url=str(settings.supabase_url) if settings.supabase_url is not None else None,
        service_role_key=settings.resolved_supabase_service_role_key,
    )


def get_expense_service(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    storage: StorageProviderProtocol = Depends(get_storage_provider),
) -> ExpenseService:
    return ExpenseService(
        repository=ExpenseRepository(session),
        storage=storage,
        settings=settings,
    )


@router.get("")
async def list_expenses(
    request: Request,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: ExpenseService = Depends(get_expense_service),
) -> dict[str, Any]:
    items = await service.list_expenses(auth_payload)
    payload = [ExpenseEntryResponse.model_validate(item).model_dump(mode="json") for item in items]
    return success_envelope(
        data={"items": payload, "count": len(payload)},
        request_id=request.state.request_id,
    )


@router.post("")
async def create_expense(
    request: Request,
    response: Response,
    expense_date: date = Form(...),
    amount: float = Form(...),
    category: str = Form(...),
    receipt: UploadFile = File(...),
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: ExpenseService = Depends(get_expense_service),
) -> dict[str, Any]:
    upload = ExpenseUpload(
        file_name=receipt.filename or "",
        content_type=receipt.content_type or "",
        content=await receipt.read(),
    )
    entry = await service.create_expense(
        auth_payload,
        expense_date=expense_date,
        amount=amount,
        category=category,
        upload=upload,
    )
    response.status_code = status.HTTP_201_CREATED
    return success_envelope(
        data=ExpenseEntryResponse.model_validate(entry).model_dump(mode="json"),
        request_id=request.state.request_id,
    )
