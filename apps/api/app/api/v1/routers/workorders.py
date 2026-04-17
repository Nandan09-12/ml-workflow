from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_envelope
from app.core.security import get_current_auth_payload
from app.db.session import get_db_session
from app.repositories.workorder_repository import WorkorderRepository
from app.schemas.workorders import WorkorderResponse
from app.services.workorder_service import WorkorderService

router = APIRouter(prefix="/workorders", tags=["workorders"])


def get_workorder_service(
    session: AsyncSession = Depends(get_db_session),
) -> WorkorderService:
    return WorkorderService(repository=WorkorderRepository(session))


@router.get("/lookup")
async def lookup_workorder(
    request: Request,
    workorder_code: str = Query(min_length=1),
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: WorkorderService = Depends(get_workorder_service),
) -> dict[str, Any]:
    workorder = await service.lookup_workorder(auth_payload, workorder_code)
    return success_envelope(
        data=WorkorderResponse.model_validate(workorder.__dict__).model_dump(mode="json"),
        request_id=request.state.request_id,
    )
