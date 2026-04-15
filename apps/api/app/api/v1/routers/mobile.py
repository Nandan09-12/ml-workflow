from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_envelope
from app.core.security import get_current_auth_payload
from app.db.session import get_db_session
from app.repositories.mobile_repository import MobileRepository
from app.schemas.mobile import MobileBootstrapResponse, MobileSyncRequest, MobileSyncResponse
from app.services.mobile_service import MobileService

router = APIRouter(prefix="/mobile", tags=["mobile"])


def get_mobile_service(
    session: AsyncSession = Depends(get_db_session),
) -> MobileService:
    return MobileService(repository=MobileRepository(session))


@router.get("/bootstrap")
async def get_mobile_bootstrap(
    request: Request,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: MobileService = Depends(get_mobile_service),
) -> dict[str, Any]:
    payload = await service.get_bootstrap_payload(auth_payload)
    return success_envelope(
        data=MobileBootstrapResponse.model_validate(payload).model_dump(mode="json"),
        request_id=request.state.request_id,
    )


@router.post("/sync")
async def sync_mobile_data(
    sync_request: MobileSyncRequest,
    request: Request,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: MobileService = Depends(get_mobile_service),
) -> dict[str, Any]:
    payload = await service.sync_placeholder(auth_payload, sync_request)
    return success_envelope(
        data=MobileSyncResponse.model_validate(payload).model_dump(mode="json"),
        request_id=request.state.request_id,
    )

