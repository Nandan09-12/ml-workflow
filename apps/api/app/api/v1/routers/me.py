from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.responses import success_envelope
from app.core.security import get_current_auth_payload
from app.db.session import get_db_session
from app.repositories.me_repository import MeRepository
from app.schemas.me import AppUserResponse, BootstrapRequest, UpdateMeRequest
from app.services.me_service import MeService

router = APIRouter(prefix="/me", tags=["me"])


def get_me_service(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> MeService:
    return MeService(repository=MeRepository(session), settings=settings)


@router.get("")
async def get_me(
    request: Request,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: MeService = Depends(get_me_service),
) -> dict[str, Any]:
    me = await service.get_me(auth_payload)
    return success_envelope(
        data=AppUserResponse.model_validate(me).model_dump(mode="json"),
        request_id=request.state.request_id,
    )


@router.post("/bootstrap")
async def bootstrap_me(
    payload: BootstrapRequest,
    request: Request,
    response: Response,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: MeService = Depends(get_me_service),
) -> dict[str, Any]:
    me, created = await service.bootstrap(auth_payload, payload)
    response.status_code = 201 if created else 200
    return success_envelope(
        data=AppUserResponse.model_validate(me).model_dump(mode="json"),
        request_id=request.state.request_id,
        meta={"created": created},
    )


@router.patch("")
async def patch_me(
    payload: UpdateMeRequest,
    request: Request,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: MeService = Depends(get_me_service),
) -> dict[str, Any]:
    me = await service.update_me(auth_payload, payload)
    return success_envelope(
        data=AppUserResponse.model_validate(me).model_dump(mode="json"),
        request_id=request.state.request_id,
    )
