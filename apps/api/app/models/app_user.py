import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import AccountStatus, RequestedRole
from app.db.base import Base


class AppUser(Base):
    __tablename__ = "app_users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auth_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    requested_role: Mapped[RequestedRole] = mapped_column(
        Enum(RequestedRole, name="requested_role_enum"),
        nullable=False,
    )
    approved_role: Mapped[RequestedRole | None] = mapped_column(
        Enum(RequestedRole, name="approved_role_enum"),
        nullable=True,
    )
    account_status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus, name="account_status_enum"),
        nullable=False,
        default=AccountStatus.PENDING_APPROVAL,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_users.id"),
        nullable=True,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    submissions_owned: Mapped[list["Submission"]] = relationship(
        "Submission",
        back_populates="owner_user",
        foreign_keys="Submission.owner_user_id",
    )
    approvals_reviewed: Mapped[list["UserApprovalAudit"]] = relationship(
        "UserApprovalAudit",
        back_populates="reviewed_by_user",
        foreign_keys="UserApprovalAudit.reviewed_by_user_id",
    )
    approvals_received: Mapped[list["UserApprovalAudit"]] = relationship(
        "UserApprovalAudit",
        back_populates="user",
        foreign_keys="UserApprovalAudit.user_id",
    )
