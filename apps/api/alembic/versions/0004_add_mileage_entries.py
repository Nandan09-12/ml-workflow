"""Add mileage entries table.

Revision ID: 0004_add_mileage_entries
Revises: 0003_finalize_submission_schema
Create Date: 2026-04-21 12:00:00
"""

from typing import Sequence

from alembic import op

revision: str = "0004_add_mileage_entries"
down_revision: str | None = "0003_finalize_submission_schema"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS mileage_entries (
            id UUID PRIMARY KEY,
            owner_user_id UUID NOT NULL REFERENCES app_users(id),
            work_date DATE NOT NULL,
            start_mileage INTEGER NOT NULL CHECK (start_mileage >= 0),
            end_mileage INTEGER NULL CHECK (end_mileage IS NULL OR end_mileage >= 0),
            started_at TIMESTAMP WITH TIME ZONE NOT NULL,
            ended_at TIMESTAMP WITH TIME ZONE NULL,
            start_odometer_file_name VARCHAR(255) NOT NULL,
            start_odometer_bucket_name VARCHAR(255) NOT NULL,
            start_odometer_object_path VARCHAR(500) NOT NULL,
            start_odometer_mime_type VARCHAR(100) NOT NULL,
            end_odometer_file_name VARCHAR(255) NULL,
            end_odometer_bucket_name VARCHAR(255) NULL,
            end_odometer_object_path VARCHAR(500) NULL,
            end_odometer_mime_type VARCHAR(100) NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );
        """
    )

    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_mileage_entries_owner_work_date
        ON mileage_entries (owner_user_id, work_date);
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_mileage_entries_owner_work_date;")
    op.execute("DROP TABLE IF EXISTS mileage_entries;")
