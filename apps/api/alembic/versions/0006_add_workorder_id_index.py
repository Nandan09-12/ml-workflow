"""Add index on submissions.workorder_id for aggregate query performance.

Revision ID: 0006_add_workorder_id_index
Revises: 0005_add_expense_entries
Create Date: 2026-04-26 12:00:00
"""

from typing import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006_add_workorder_id_index"
down_revision: str | None = "0005_add_expense_entries"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_submissions_workorder_id",
        "submissions",
        ["workorder_id"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_submissions_workorder_id",
        table_name="submissions",
        if_exists=True,
    )
