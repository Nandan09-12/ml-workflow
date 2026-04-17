import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import Region, WorkorderStatus
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.submission import Submission


class Workorder(Base):
    __tablename__ = "workorders"
    __table_args__ = (
        UniqueConstraint("workorder_code_normalized", name="uq_workorders_code_normalized"),
        CheckConstraint("total_grids > 0", name="ck_workorders_total_grids_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workorder_code: Mapped[str] = mapped_column(String(255), nullable=False)
    workorder_code_normalized: Mapped[str] = mapped_column(String(255), nullable=False)
    region: Mapped[Region] = mapped_column(Enum(Region, name="region_enum"), nullable=False)
    total_grids: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[WorkorderStatus] = mapped_column(
        Enum(WorkorderStatus, name="workorder_status_enum"),
        nullable=False,
        default=WorkorderStatus.ACTIVE,
    )
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

    submissions: Mapped[list["Submission"]] = relationship(
        "Submission",
        back_populates="workorder",
    )
