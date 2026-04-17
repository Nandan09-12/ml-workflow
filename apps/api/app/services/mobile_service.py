import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from app.core.enums import (
    AccountStatus,
    RequestedRole,
    Shift,
    SubmissionStatus,
    WorkorderStatus,
    Zone,
)
from app.core.errors import AppError, ErrorCode
from app.models.app_user import AppUser
from app.schemas.mobile import MobileSyncRequest


@dataclass(frozen=True)
class MobileUserStateView:
    id: uuid.UUID
    auth_user_id: uuid.UUID
    full_name: str
    email: str
    requested_role: RequestedRole
    approved_role: RequestedRole | None
    account_status: AccountStatus


@dataclass(frozen=True)
class MobileReferenceDataView:
    zones: list[str]
    shifts: list[str]
    submission_statuses: list[str]
    workorder_statuses: list[str]


@dataclass(frozen=True)
class MobileBootstrapView:
    contract_version: str
    offline_sync_enabled: bool
    server_time_utc: datetime
    user: MobileUserStateView
    reference_data: MobileReferenceDataView


@dataclass(frozen=True)
class MobileSyncResultView:
    contract_version: str
    accepted: bool
    status: str
    message: str
    received_operations_count: int
    processed_operations_count: int
    rejected_operations_count: int
    server_time_utc: datetime


class MobileRepositoryProtocol(Protocol):
    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None: ...


class MobileService:
    def __init__(self, repository: MobileRepositoryProtocol) -> None:
        self._repository = repository

    async def get_bootstrap_payload(
        self,
        auth_payload: dict[str, Any],
    ) -> MobileBootstrapView:
        user = await self._require_app_user(auth_payload)
        return MobileBootstrapView(
            contract_version="v1",
            offline_sync_enabled=False,
            server_time_utc=datetime.now(UTC),
            user=self._to_user_view(user),
            reference_data=self._reference_data(),
        )

    async def sync_placeholder(
        self,
        auth_payload: dict[str, Any],
        request: MobileSyncRequest,
    ) -> MobileSyncResultView:
        await self._require_app_user(auth_payload)
        operation_count = len(request.operations)
        return MobileSyncResultView(
            contract_version="v1",
            accepted=False,
            status="NOT_IMPLEMENTED",
            message="Mobile sync placeholder for future offline contract.",
            received_operations_count=operation_count,
            processed_operations_count=0,
            rejected_operations_count=operation_count,
            server_time_utc=datetime.now(UTC),
        )

    async def _require_app_user(self, auth_payload: dict[str, Any]) -> AppUser:
        auth_user_id = self._extract_auth_user_id(auth_payload)
        user = await self._repository.get_by_auth_user_id(auth_user_id)
        if user is None:
            raise AppError(
                ErrorCode.NOT_FOUND,
                "User profile was not found. Run bootstrap first.",
                status_code=404,
            )
        return user

    @staticmethod
    def _extract_auth_user_id(auth_payload: dict[str, Any]) -> uuid.UUID:
        raw_sub = auth_payload.get("sub")
        if raw_sub is None:
            raise AppError(
                ErrorCode.UNAUTHORIZED,
                "Authenticated user id is missing from token.",
                status_code=401,
            )
        try:
            return uuid.UUID(str(raw_sub))
        except (TypeError, ValueError) as exc:
            raise AppError(
                ErrorCode.UNAUTHORIZED,
                "Authenticated user id is invalid.",
                status_code=401,
            ) from exc

    @staticmethod
    def _reference_data() -> MobileReferenceDataView:
        return MobileReferenceDataView(
            zones=[zone.value for zone in Zone],
            shifts=[shift.value for shift in Shift],
            submission_statuses=[status.value for status in SubmissionStatus],
            workorder_statuses=[status.value for status in WorkorderStatus],
        )

    @staticmethod
    def _to_user_view(user: AppUser) -> MobileUserStateView:
        return MobileUserStateView(
            id=user.id,
            auth_user_id=user.auth_user_id,
            full_name=user.full_name,
            email=user.email,
            requested_role=user.requested_role,
            approved_role=user.approved_role,
            account_status=user.account_status,
        )

