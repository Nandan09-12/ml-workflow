import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from app.core.config import Settings
from app.core.enums import AccountStatus, ApprovalDecision, RequestedRole
from app.core.errors import AppError, ErrorCode
from app.models.app_user import AppUser
from app.models.user_approval_audit import UserApprovalAudit
from app.schemas.me import BootstrapRequest, UpdateMeRequest


@dataclass(frozen=True)
class MeUserView:
    id: uuid.UUID
    auth_user_id: uuid.UUID
    full_name: str
    email: str
    requested_role: RequestedRole
    approved_role: RequestedRole | None
    account_status: AccountStatus
    approved_at: datetime | None
    approved_by_user_id: uuid.UUID | None


class MeRepositoryProtocol(Protocol):
    async def get_by_auth_user_id(self, auth_user_id: uuid.UUID) -> AppUser | None: ...

    async def count_approved_admins(self) -> int: ...

    async def create_user(self, user: AppUser) -> AppUser: ...

    async def create_approval_audit(self, audit: UserApprovalAudit) -> UserApprovalAudit: ...

    async def acquire_bootstrap_lock(self) -> None: ...

    async def update_full_name(self, user: AppUser, full_name: str) -> AppUser: ...

    def transaction(self) -> Any: ...


class MeService:
    def __init__(
        self,
        repository: MeRepositoryProtocol,
        settings: Settings,
    ) -> None:
        self._repository = repository
        self._settings = settings

    async def get_me(self, auth_payload: dict[str, Any]) -> MeUserView:
        auth_user_id = self._extract_auth_user_id(auth_payload)
        user = await self._repository.get_by_auth_user_id(auth_user_id)
        if user is None:
            raise AppError(
                ErrorCode.NOT_FOUND,
                "User profile was not found. Run bootstrap first.",
                status_code=404,
            )
        return self._to_view(user)

    async def bootstrap(
        self,
        auth_payload: dict[str, Any],
        request: BootstrapRequest,
    ) -> tuple[MeUserView, bool]:
        auth_user_id = self._extract_auth_user_id(auth_payload)
        email = self._extract_email(auth_payload)
        requested_role = request.requested_role
        async with self._repository.transaction():
            await self._repository.acquire_bootstrap_lock()
            existing = await self._repository.get_by_auth_user_id(auth_user_id)
            if existing is not None:
                return self._to_view(existing), False

            approved_admin_count = await self._repository.count_approved_admins()
            should_auto_approve = (
                approved_admin_count == 0
                and requested_role == RequestedRole.ADMIN
                and self._normalize_email(email) in self._normalized_allowlist()
            )

            now = datetime.now(UTC)
            user = AppUser(
                id=uuid.uuid4(),
                auth_user_id=auth_user_id,
                full_name=request.full_name.strip(),
                email=email,
                requested_role=requested_role,
                approved_role=RequestedRole.ADMIN if should_auto_approve else None,
                account_status=(
                    AccountStatus.APPROVED
                    if should_auto_approve
                    else AccountStatus.PENDING_APPROVAL
                ),
                approved_at=now if should_auto_approve else None,
                approved_by_user_id=None,
                created_at=now,
                updated_at=now,
            )
            created_user = await self._repository.create_user(user)
            if should_auto_approve:
                approval_audit = UserApprovalAudit(
                    id=uuid.uuid4(),
                    user_id=created_user.id,
                    requested_role=RequestedRole.ADMIN,
                    decision=ApprovalDecision.APPROVED,
                    reviewed_by_user_id=None,
                    reviewed_at=now,
                    review_notes="BOOTSTRAP_ADMIN_AUTO_APPROVED",
                    created_at=now,
                )
                await self._repository.create_approval_audit(approval_audit)

        return self._to_view(created_user), True

    async def update_me(
        self,
        auth_payload: dict[str, Any],
        request: UpdateMeRequest,
    ) -> MeUserView:
        auth_user_id = self._extract_auth_user_id(auth_payload)
        user = await self._repository.get_by_auth_user_id(auth_user_id)
        if user is None:
            raise AppError(
                ErrorCode.NOT_FOUND,
                "User profile was not found. Run bootstrap first.",
                status_code=404,
            )
        async with self._repository.transaction():
            updated_user = await self._repository.update_full_name(user, request.full_name.strip())
        return self._to_view(updated_user)

    def _normalized_allowlist(self) -> set[str]:
        emails = self._settings.bootstrap_admin_emails
        if not emails:
            return set()
        parsed: Iterable[str] = (part.strip().lower() for part in emails.split(","))
        return {value for value in parsed if value}

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
    def _extract_email(auth_payload: dict[str, Any]) -> str:
        raw_email = auth_payload.get("email")
        if not isinstance(raw_email, str) or not raw_email.strip():
            raise AppError(
                ErrorCode.UNAUTHORIZED,
                "Authenticated email is missing from token.",
                status_code=401,
            )
        return raw_email.strip()

    @staticmethod
    def _normalize_email(value: str) -> str:
        return value.strip().lower()

    @staticmethod
    def _to_view(user: AppUser) -> MeUserView:
        return MeUserView(
            id=user.id,
            auth_user_id=user.auth_user_id,
            full_name=user.full_name,
            email=user.email,
            requested_role=user.requested_role,
            approved_role=user.approved_role,
            account_status=user.account_status,
            approved_at=user.approved_at,
            approved_by_user_id=user.approved_by_user_id,
        )
