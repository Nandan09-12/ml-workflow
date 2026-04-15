import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ApprovalDecision, RequestedRole
from app.db.base import Base


class UserApprovalAudit(Base):
    __tablename__ = "user_approval_audit"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_users.id"),
        nullable=False,
    )
    requested_role: Mapped[RequestedRole] = mapped_column(
        Enum(RequestedRole, name="approval_requested_role_enum"),
        nullable=False,
    )
    decision: Mapped[ApprovalDecision] = mapped_column(
        Enum(ApprovalDecision, name="approval_decision_enum"),
        nullable=False,
        default=ApprovalDecision.PENDING,
    )
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_users.id"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped["AppUser"] = relationship(
        "AppUser",
        back_populates="approvals_received",
        foreign_keys=[user_id],
    )
    reviewed_by_user: Mapped["AppUser | None"] = relationship(
        "AppUser",
        back_populates="approvals_reviewed",
        foreign_keys=[reviewed_by_user_id],
    )
