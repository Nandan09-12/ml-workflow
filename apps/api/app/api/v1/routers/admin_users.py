import math
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AccountStatus, RequestedRole
from app.core.responses import success_envelope
from app.core.security import get_current_auth_payload
from app.db.session import get_db_session
from app.repositories.admin_users_repository import AdminUsersRepository
from app.schemas.admin_users import AdminUserResponse, ApprovalAuditResponse
from app.services.admin_users_service import AdminUsersService

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


def get_admin_users_service(
    session: AsyncSession = Depends(get_db_session),
) -> AdminUsersService:
    return AdminUsersService(repository=AdminUsersRepository(session))


@router.get("/pending")
async def list_pending_users(
    request: Request,
    requested_role: RequestedRole | None = Query(default=None),
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: AdminUsersService = Depends(get_admin_users_service),
) -> dict[str, Any]:
    users = await service.list_pending_users(auth_payload, requested_role=requested_role)
    items = [AdminUserResponse.model_validate(user).model_dump(mode="json") for user in users]
    return success_envelope(
        data={"items": items, "count": len(items)},
        request_id=request.state.request_id,
    )


@router.get("")
async def list_users(
    request: Request,
    requested_role: RequestedRole | None = Query(default=None),
    account_status: AccountStatus | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: AdminUsersService = Depends(get_admin_users_service),
) -> dict[str, Any]:
    users, total = await service.list_users(
        auth_payload,
        requested_role=requested_role,
        account_status=account_status,
        page=page,
        page_size=page_size,
    )
    items = [AdminUserResponse.model_validate(user).model_dump(mode="json") for user in users]
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


@router.get("/{user_id}")
async def get_user_detail(
    user_id: uuid.UUID,
    request: Request,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: AdminUsersService = Depends(get_admin_users_service),
) -> dict[str, Any]:
    user = await service.get_user(auth_payload, user_id)
    return success_envelope(
        data=AdminUserResponse.model_validate(user).model_dump(mode="json"),
        request_id=request.state.request_id,
    )


@router.post("/{user_id}/approve")
async def approve_user(
    user_id: uuid.UUID,
    request: Request,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: AdminUsersService = Depends(get_admin_users_service),
) -> dict[str, Any]:
    user = await service.approve_user(auth_payload, user_id)
    return success_envelope(
        data=AdminUserResponse.model_validate(user).model_dump(mode="json"),
        request_id=request.state.request_id,
    )


@router.post("/{user_id}/reject")
async def reject_user(
    user_id: uuid.UUID,
    request: Request,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: AdminUsersService = Depends(get_admin_users_service),
) -> dict[str, Any]:
    user = await service.reject_user(auth_payload, user_id)
    return success_envelope(
        data=AdminUserResponse.model_validate(user).model_dump(mode="json"),
        request_id=request.state.request_id,
    )


@router.post("/{user_id}/suspend")
async def suspend_user(
    user_id: uuid.UUID,
    request: Request,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: AdminUsersService = Depends(get_admin_users_service),
) -> dict[str, Any]:
    user = await service.suspend_user(auth_payload, user_id)
    return success_envelope(
        data=AdminUserResponse.model_validate(user).model_dump(mode="json"),
        request_id=request.state.request_id,
    )


@router.get("/{user_id}/approval-history")
async def get_approval_history(
    user_id: uuid.UUID,
    request: Request,
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: AdminUsersService = Depends(get_admin_users_service),
) -> dict[str, Any]:
    history = await service.get_approval_history(auth_payload, user_id)
    items = [ApprovalAuditResponse.model_validate(entry).model_dump(mode="json") for entry in history]
    return success_envelope(
        data={"items": items, "count": len(items)},
        request_id=request.state.request_id,
    )
