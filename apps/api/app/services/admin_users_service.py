import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from app.core.enums import AccountStatus, ApprovalDecision, RequestedRole
from app.core.errors import AppError, ErrorCode
from app.models.app_user import AppUser
from app.models.user_approval_audit import UserApprovalAudit


@dataclass(frozen=True)
class AdminUserView:
    id: uuid.UUID
    auth_user_id: uuid.UUID
    full_name: str
    email: str
    requested_role: RequestedRole
    approved_role: RequestedRole | None
    account_status: AccountStatus
    approved_at: datetime | None
    approved_by_user_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ApprovalAuditView:
    id: uuid.UUID
    user_id: uuid.UUID
    requested_role: RequestedRole
    decision: ApprovalDecision
    reviewed_by_user_id: uuid.UUID | None
    reviewed_at: datetime | None
    review_notes: str | None
    created_at: datetime


class AdminUsersRepositoryProtocol(Protocol):
    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None: ...

    async def list_pending_users(
        self,
        *,
        requested_role: RequestedRole | None = None,
    ) -> list[AppUser]: ...

    async def list_users(
        self,
        *,
        requested_role: RequestedRole | None = None,
        account_status: AccountStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[AppUser], int]: ...

    async def get_by_id(self, user_id: uuid.UUID) -> AppUser | None: ...

    async def save_user(self, user: AppUser) -> AppUser: ...

    async def create_approval_audit(self, audit: UserApprovalAudit) -> UserApprovalAudit: ...

    async def get_approval_history(self, user_id: uuid.UUID) -> list[UserApprovalAudit]: ...

    def transaction(self) -> Any: ...


class AdminUsersService:
    def __init__(self, repository: AdminUsersRepositoryProtocol) -> None:
        self._repository = repository

    async def list_pending_users(
        self,
        auth_payload: dict[str, Any],
        *,
        requested_role: RequestedRole | None = None,
    ) -> list[AdminUserView]:
        await self._require_approved_admin(auth_payload)
        users = await self._repository.list_pending_users(requested_role=requested_role)
        return [self._to_admin_user_view(user) for user in users]

    async def list_users(
        self,
        auth_payload: dict[str, Any],
        *,
        requested_role: RequestedRole | None = None,
        account_status: AccountStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AdminUserView], int]:
        await self._require_approved_admin(auth_payload)
        offset = (page - 1) * page_size
        users, total = await self._repository.list_users(
            requested_role=requested_role,
            account_status=account_status,
            offset=offset,
            limit=page_size,
        )
        return [self._to_admin_user_view(user) for user in users], total

    async def get_user(self, auth_payload: dict[str, Any], user_id: uuid.UUID) -> AdminUserView:
        await self._require_approved_admin(auth_payload)
        user = await self._repository.get_by_id(user_id)
        if user is None:
            raise AppError(ErrorCode.NOT_FOUND, "User was not found.", status_code=404)
        return self._to_admin_user_view(user)

    async def approve_user(
        self,
        auth_payload: dict[str, Any],
        user_id: uuid.UUID,
    ) -> AdminUserView:
        actor = await self._require_approved_admin(auth_payload)
        async with self._repository.transaction():
            target = await self._repository.get_by_id(user_id)
            if target is None:
                raise AppError(ErrorCode.NOT_FOUND, "User was not found.", status_code=404)
            if target.account_status != AccountStatus.PENDING_APPROVAL:
                raise AppError(
                    ErrorCode.INVALID_ACCOUNT_STATE,
                    "Only pending users can be approved.",
                    status_code=400,
                )
            now = datetime.now(UTC)
            target.account_status = AccountStatus.APPROVED
            target.approved_role = target.requested_role
            target.approved_at = now
            target.approved_by_user_id = actor.id
            target.updated_at = now
            await self._repository.save_user(target)
            await self._repository.create_approval_audit(
                UserApprovalAudit(
                    id=uuid.uuid4(),
                    user_id=target.id,
                    requested_role=target.requested_role,
                    decision=ApprovalDecision.APPROVED,
                    reviewed_by_user_id=actor.id,
                    reviewed_at=now,
                    review_notes=None,
                    created_at=now,
                )
            )
        return self._to_admin_user_view(target)

    async def reject_user(
        self,
        auth_payload: dict[str, Any],
        user_id: uuid.UUID,
    ) -> AdminUserView:
        actor = await self._require_approved_admin(auth_payload)
        async with self._repository.transaction():
            target = await self._repository.get_by_id(user_id)
            if target is None:
                raise AppError(ErrorCode.NOT_FOUND, "User was not found.", status_code=404)
            if target.account_status != AccountStatus.PENDING_APPROVAL:
                raise AppError(
                    ErrorCode.INVALID_ACCOUNT_STATE,
                    "Only pending users can be rejected.",
                    status_code=400,
                )
            now = datetime.now(UTC)
            target.account_status = AccountStatus.REJECTED
            target.approved_role = None
            target.approved_at = None
            target.approved_by_user_id = None
            target.updated_at = now
            await self._repository.save_user(target)
            await self._repository.create_approval_audit(
                UserApprovalAudit(
                    id=uuid.uuid4(),
                    user_id=target.id,
                    requested_role=target.requested_role,
                    decision=ApprovalDecision.REJECTED,
                    reviewed_by_user_id=actor.id,
                    reviewed_at=now,
                    review_notes=None,
                    created_at=now,
                )
            )
        return self._to_admin_user_view(target)

    async def suspend_user(
        self,
        auth_payload: dict[str, Any],
        user_id: uuid.UUID,
    ) -> AdminUserView:
        await self._require_approved_admin(auth_payload)
        async with self._repository.transaction():
            target = await self._repository.get_by_id(user_id)
            if target is None:
                raise AppError(ErrorCode.NOT_FOUND, "User was not found.", status_code=404)
            if target.account_status != AccountStatus.APPROVED:
                raise AppError(
                    ErrorCode.INVALID_ACCOUNT_STATE,
                    "Only approved users can be suspended.",
                    status_code=400,
                )
            target.account_status = AccountStatus.SUSPENDED
            target.updated_at = datetime.now(UTC)
            await self._repository.save_user(target)
        return self._to_admin_user_view(target)

    async def get_approval_history(
        self,
        auth_payload: dict[str, Any],
        user_id: uuid.UUID,
    ) -> list[ApprovalAuditView]:
        await self._require_approved_admin(auth_payload)
        history = await self._repository.get_approval_history(user_id)
        return [self._to_approval_view(entry) for entry in history]

    async def _require_approved_admin(self, auth_payload: dict[str, Any]) -> AppUser:
        auth_user_id = self._extract_auth_user_id(auth_payload)
        actor = await self._repository.get_by_auth_user_id(auth_user_id)
        if actor is None:
            raise AppError(
                ErrorCode.NOT_FOUND,
                "Authenticated app user profile not found.",
                status_code=404,
            )
        if actor.account_status != AccountStatus.APPROVED:
            raise AppError(
                ErrorCode.ACCOUNT_NOT_APPROVED,
                "Account is not approved for admin actions.",
                status_code=403,
            )
        if actor.approved_role != RequestedRole.ADMIN:
            raise AppError(
                ErrorCode.ADMIN_ONLY,
                "Admin access required.",
                status_code=403,
            )
        return actor

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
    def _to_admin_user_view(user: AppUser) -> AdminUserView:
        return AdminUserView(
            id=user.id,
            auth_user_id=user.auth_user_id,
            full_name=user.full_name,
            email=user.email,
            requested_role=user.requested_role,
            approved_role=user.approved_role,
            account_status=user.account_status,
            approved_at=user.approved_at,
            approved_by_user_id=user.approved_by_user_id,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    @staticmethod
    def _to_approval_view(entry: UserApprovalAudit) -> ApprovalAuditView:
        return ApprovalAuditView(
            id=entry.id,
            user_id=entry.user_id,
            requested_role=entry.requested_role,
            decision=entry.decision,
            reviewed_by_user_id=entry.reviewed_by_user_id,
            reviewed_at=entry.reviewed_at,
            review_notes=entry.review_notes,
            created_at=entry.created_at,
        )
