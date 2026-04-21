import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.app_user import AppUser


class MileageEntry(Base):
    __tablename__ = "mileage_entries"
    __table_args__ = (
        Index(
            "uq_mileage_entries_owner_work_date",
            "owner_user_id",
            "work_date",
            unique=True,
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_users.id"),
        nullable=False,
    )
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_mileage: Mapped[int] = mapped_column(Integer, nullable=False)
    end_mileage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    start_odometer_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_odometer_bucket_name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_odometer_object_path: Mapped[str] = mapped_column(String(500), nullable=False)
    start_odometer_mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    end_odometer_file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    end_odometer_bucket_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    end_odometer_object_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    end_odometer_mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
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

    owner_user: Mapped["AppUser"] = relationship("AppUser")
