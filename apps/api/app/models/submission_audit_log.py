import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import AuditActionType, AuditSource
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.submission import Submission


class SubmissionAuditLog(Base):
    __tablename__ = "submission_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id"),
        nullable=False,
    )
    action_type: Mapped[AuditActionType] = mapped_column(
        Enum(AuditActionType, name="audit_action_type_enum"),
        nullable=False,
    )
    actor_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_users.id"),
        nullable=False,
    )
    actor_role: Mapped[str] = mapped_column(String(50), nullable=False)
    source: Mapped[AuditSource] = mapped_column(
        Enum(AuditSource, name="audit_source_enum"),
        nullable=False,
    )
    changed_fields_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    before_snapshot_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    after_snapshot_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    submission: Mapped["Submission"] = relationship(
        "Submission",
        back_populates="audit_logs",
    )
