import math
import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import Region, WorkorderStatus
from app.core.responses import success_envelope
from app.core.security import get_current_auth_payload
from app.db.session import get_db_session
from app.repositories.workorder_repository import WorkorderRepository
from app.schemas.workorders import (
    UpdateWorkorderRequest,
    WorkorderDetailResponse,
    WorkorderResponse,
)
from app.services.workorder_service import WorkorderService

router = APIRouter(prefix="/admin/workorders", tags=["admin-workorders"])


def get_workorder_service(
    session: AsyncSession = Depends(get_db_session),
) -> WorkorderService:
    return WorkorderService(repository=WorkorderRepository(session))


@router.get("")
async def list_workorders(
    request: Request,
    region: Region | None = Query(default=None),
    status: WorkorderStatus | None = Query(default=None),
    workorder_code: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: WorkorderService = Depends(get_workorder_service),
) -> dict[str, Any]:
    views, total = await service.list_workorders(
        auth_payload,
        region=region,
        status=status,
        workorder_code=workorder_code,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    items = [WorkorderResponse.model_validate(v.__dict__).model_dump(mode="json") for v in views]
    return success_envelope(
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 1,
        },
        request_id=request.state.request_id,
    )


@router.get("/{workorder_id}")
async def get_workorder(
    workorder_id: uuid.UUID,
    request: Request,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: WorkorderService = Depends(get_workorder_service),
) -> dict[str, Any]:
    detail = await service.get_workorder_admin(auth_payload, workorder_id)
    return success_envelope(
        data=WorkorderDetailResponse.model_validate(detail.__dict__).model_dump(mode="json"),
        request_id=request.state.request_id,
    )


@router.patch("/{workorder_id}")
async def update_workorder(
    workorder_id: uuid.UUID,
    body: UpdateWorkorderRequest,
    request: Request,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: WorkorderService = Depends(get_workorder_service),
) -> dict[str, Any]:
    view = await service.update_workorder(auth_payload, workorder_id, body)
    return success_envelope(
        data=WorkorderResponse.model_validate(view.__dict__).model_dump(mode="json"),
        request_id=request.state.request_id,
    )
