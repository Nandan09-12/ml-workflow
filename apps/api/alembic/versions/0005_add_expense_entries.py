"""add expense entries

Revision ID: 0005_add_expense_entries
Revises: 0004_add_mileage_entries
Create Date: 2026-04-21 14:25:00.000000
"""

from alembic import op


revision = "0005_add_expense_entries"
down_revision = "0004_add_mileage_entries"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE expense_entries (
            id UUID PRIMARY KEY,
            owner_user_id UUID NOT NULL REFERENCES app_users(id),
            expense_date DATE NOT NULL,
            amount NUMERIC(12, 2) NOT NULL,
            category VARCHAR(50) NOT NULL,
            receipt_file_name VARCHAR(255) NOT NULL,
            receipt_bucket_name VARCHAR(255) NOT NULL,
            receipt_object_path VARCHAR(500) NOT NULL,
            receipt_mime_type VARCHAR(100) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX ix_expense_entries_owner_user_id
        ON expense_entries (owner_user_id)
        """
    )
    op.execute(
        """
        CREATE INDEX ix_expense_entries_expense_date
        ON expense_entries (expense_date)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_expense_entries_expense_date")
    op.execute("DROP INDEX IF EXISTS ix_expense_entries_owner_user_id")
    op.execute("DROP TABLE IF EXISTS expense_entries")
