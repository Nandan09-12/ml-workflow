"""Finalize submission schema for the workorder model.

Revision ID: 0003_finalize_submission_schema
Revises: 0002_workorders_parent_daily
Create Date: 2026-04-17 00:30:00
"""

from typing import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_finalize_submission_schema"
down_revision: str | None = "0002_workorders_parent_daily"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE submissions
        ADD COLUMN IF NOT EXISTS started_at TIMESTAMP WITH TIME ZONE,
        ADD COLUMN IF NOT EXISTS ended_at TIMESTAMP WITH TIME ZONE;
        """
    )

    op.execute(
        """
        UPDATE submissions
        SET started_at = COALESCE(started_at, created_at)
        WHERE started_at IS NULL;
        """
    )

    op.execute(
        """
        UPDATE submissions
        SET ended_at = COALESCE(ended_at, completed_at)
        WHERE ended_at IS NULL
          AND completed_at IS NOT NULL;
        """
    )

    op.execute(
        """
        ALTER TABLE submissions
        ALTER COLUMN started_at SET NOT NULL;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t
                    ON t.oid = e.enumtypid
                WHERE t.typname = 'submission_status_enum'
                  AND e.enumlabel = 'ONGOING'
            ) THEN
                CREATE TYPE submission_status_enum_v2 AS ENUM ('IN_PROGRESS', 'CHECKED_OUT', 'COMPLETED');

                ALTER TABLE submissions
                ALTER COLUMN status DROP DEFAULT;

                ALTER TABLE submissions
                ALTER COLUMN status TYPE submission_status_enum_v2
                USING (
                    CASE status::text
                        WHEN 'ONGOING' THEN 'IN_PROGRESS'
                        WHEN 'COMPLETED' THEN 'COMPLETED'
                        ELSE status::text
                    END
                )::submission_status_enum_v2;

                DROP TYPE submission_status_enum;
                ALTER TYPE submission_status_enum_v2 RENAME TO submission_status_enum;
            END IF;
        END;
        $$;
        """
    )

    op.execute(
        """
        ALTER TABLE submissions
        ALTER COLUMN status SET DEFAULT 'IN_PROGRESS';
        """
    )

    op.execute(
        """
        ALTER TABLE submissions
        DROP CONSTRAINT IF EXISTS ck_submissions_number_of_grids_non_negative,
        DROP CONSTRAINT IF EXISTS ck_submissions_pending_grids_non_negative,
        DROP CONSTRAINT IF EXISTS ck_submissions_grid_math,
        DROP CONSTRAINT IF EXISTS ck_submissions_skipped_lte_total,
        DROP CONSTRAINT IF EXISTS ck_submissions_pending_lte_total,
        DROP CONSTRAINT IF EXISTS ck_submissions_completed_lte_total;
        """
    )

    op.execute(
        """
        ALTER TABLE submissions DROP COLUMN IF EXISTS zone;
        ALTER TABLE submissions DROP COLUMN IF EXISTS cluster_name;
        ALTER TABLE submissions DROP COLUMN IF EXISTS cluster_name_normalized;
        ALTER TABLE submissions DROP COLUMN IF EXISTS number_of_grids;
        ALTER TABLE submissions DROP COLUMN IF EXISTS pending_grids;
        """
    )

    op.execute(
        """
        DROP TYPE IF EXISTS zone_enum;
        """
    )

    op.execute(
        """
        DO $$
        DECLARE
            started_at_missing_count integer;
            legacy_columns_remaining_count integer;
            submission_status_enum_values_count integer;
        BEGIN
            SELECT COUNT(*)
            INTO started_at_missing_count
            FROM submissions
            WHERE started_at IS NULL;

            IF started_at_missing_count > 0 THEN
                RAISE EXCEPTION
                    'Submission schema finalization validation failed: started_at missing rows=%',
                    started_at_missing_count;
            END IF;

            SELECT COUNT(*)
            INTO legacy_columns_remaining_count
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'submissions'
              AND column_name IN (
                  'zone',
                  'cluster_name',
                  'cluster_name_normalized',
                  'number_of_grids',
                  'pending_grids'
              );

            IF legacy_columns_remaining_count > 0 THEN
                RAISE EXCEPTION
                    'Submission schema finalization validation failed: legacy columns remaining=%',
                    legacy_columns_remaining_count;
            END IF;

            SELECT COUNT(*)
            INTO submission_status_enum_values_count
            FROM pg_enum e
            JOIN pg_type t
                ON t.oid = e.enumtypid
            WHERE t.typname = 'submission_status_enum'
              AND e.enumlabel IN ('IN_PROGRESS', 'CHECKED_OUT', 'COMPLETED');

            IF submission_status_enum_values_count <> 3 THEN
                RAISE EXCEPTION
                    'Submission schema finalization validation failed: submission_status_enum values count=%',
                    submission_status_enum_values_count;
            END IF;
        END;
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_type
                WHERE typname = 'zone_enum'
            ) THEN
                CREATE TYPE zone_enum AS ENUM ('NORTHEAST', 'CENTRAL', 'SOUTH_FLORIDA');
            END IF;
        END;
        $$;
        """
    )

    op.execute(
        """
        ALTER TABLE submissions
        ADD COLUMN IF NOT EXISTS zone zone_enum,
        ADD COLUMN IF NOT EXISTS cluster_name VARCHAR(255),
        ADD COLUMN IF NOT EXISTS cluster_name_normalized VARCHAR(255),
        ADD COLUMN IF NOT EXISTS number_of_grids INTEGER,
        ADD COLUMN IF NOT EXISTS pending_grids INTEGER;
        """
    )

    op.execute(
        """
        UPDATE submissions AS s
        SET zone = CASE w.region::text
                WHEN 'NE_UP' THEN 'NORTHEAST'::zone_enum
                WHEN 'CENTRAL' THEN 'CENTRAL'::zone_enum
                WHEN 'SOUTH_FLORIDA' THEN 'SOUTH_FLORIDA'::zone_enum
                ELSE NULL
            END,
            cluster_name = w.workorder_code,
            cluster_name_normalized = w.workorder_code_normalized,
            number_of_grids = w.total_grids,
            pending_grids = GREATEST(w.total_grids - (s.completed_grids + s.skipped_grids), 0)
        FROM workorders AS w
        WHERE w.id = s.workorder_id;
        """
    )

    op.execute(
        """
        ALTER TABLE submissions
        ALTER COLUMN zone SET NOT NULL,
        ALTER COLUMN cluster_name SET NOT NULL,
        ALTER COLUMN cluster_name_normalized SET NOT NULL,
        ALTER COLUMN number_of_grids SET NOT NULL,
        ALTER COLUMN pending_grids SET NOT NULL;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t
                    ON t.oid = e.enumtypid
                WHERE t.typname = 'submission_status_enum'
                  AND e.enumlabel = 'CHECKED_OUT'
            ) THEN
                CREATE TYPE submission_status_enum_v1 AS ENUM ('ONGOING', 'COMPLETED');

                ALTER TABLE submissions
                ALTER COLUMN status DROP DEFAULT;

                ALTER TABLE submissions
                ALTER COLUMN status TYPE submission_status_enum_v1
                USING (
                    CASE status::text
                        WHEN 'COMPLETED' THEN 'COMPLETED'
                        ELSE 'ONGOING'
                    END
                )::submission_status_enum_v1;

                DROP TYPE submission_status_enum;
                ALTER TYPE submission_status_enum_v1 RENAME TO submission_status_enum;
            END IF;
        END;
        $$;
        """
    )

    op.execute(
        """
        ALTER TABLE submissions
        ALTER COLUMN status SET DEFAULT 'ONGOING';
        """
    )

    op.execute(
        """
        ALTER TABLE submissions
        DROP COLUMN IF EXISTS started_at,
        DROP COLUMN IF EXISTS ended_at;
        """
    )

    op.execute(
        """
        ALTER TABLE submissions
        ADD CONSTRAINT ck_submissions_number_of_grids_non_negative CHECK (number_of_grids >= 0),
        ADD CONSTRAINT ck_submissions_pending_grids_non_negative CHECK (pending_grids >= 0),
        ADD CONSTRAINT ck_submissions_grid_math CHECK (completed_grids + pending_grids + skipped_grids = number_of_grids),
        ADD CONSTRAINT ck_submissions_skipped_lte_total CHECK (skipped_grids <= number_of_grids),
        ADD CONSTRAINT ck_submissions_pending_lte_total CHECK (pending_grids <= number_of_grids),
        ADD CONSTRAINT ck_submissions_completed_lte_total CHECK (completed_grids <= number_of_grids);
        """
    )
