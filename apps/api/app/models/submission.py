import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import Shift, SubmissionStatus
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.app_user import AppUser
    from app.models.submission_attachment import SubmissionAttachment
    from app.models.submission_audit_log import SubmissionAuditLog
    from app.models.workorder import Workorder


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        UniqueConstraint(
            "workorder_id",
            "work_date",
            name="uq_submissions_workorder_date",
        ),
        CheckConstraint("skipped_grids >= 0", name="ck_submissions_skipped_grids_non_negative"),
        CheckConstraint(
            "force_tested_grids >= 0",
            name="ck_submissions_force_tested_grids_non_negative",
        ),
        CheckConstraint(
            "completed_grids >= 0",
            name="ck_submissions_completed_grids_non_negative",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_generated_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        default=uuid.uuid4,
    )
    workorder_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workorders.id"),
        nullable=False,
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_users.id"),
        nullable=False,
    )
    submitter_name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    submitter_email_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    shift: Mapped[Shift] = mapped_column(Enum(Shift, name="shift_enum"), nullable=False)
    team_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ticket_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    skipped_grids: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    force_tested_grids: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_grids: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, name="submission_status_enum"),
        nullable=False,
        default=SubmissionStatus.IN_PROGRESS,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_users.id"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    updated_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_users.id"),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_users.id"),
        nullable=True,
    )
    reopened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reopened_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_users.id"),
        nullable=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    owner_user: Mapped["AppUser"] = relationship(
        "AppUser",
        back_populates="submissions_owned",
        foreign_keys=[owner_user_id],
    )
    workorder: Mapped["Workorder | None"] = relationship(
        "Workorder",
        back_populates="submissions",
    )
    attachments: Mapped[list["SubmissionAttachment"]] = relationship(
        "SubmissionAttachment",
        back_populates="submission",
    )
    audit_logs: Mapped[list["SubmissionAuditLog"]] = relationship(
        "SubmissionAuditLog",
        back_populates="submission",
    )
