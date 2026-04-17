"""Introduce workorders parent table and daily submission uniqueness.

Revision ID: 0002_workorders_parent_daily_submissions
Revises: 0001_init_core_tables
Create Date: 2026-04-17 00:00:00
"""

from typing import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_workorders_parent_daily"
down_revision: str | None = "0001_init_core_tables"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_type
                WHERE typname = 'region_enum'
            ) THEN
                CREATE TYPE region_enum AS ENUM ('NE_UP', 'CENTRAL', 'SOUTH_FLORIDA');
            END IF;

            IF NOT EXISTS (
                SELECT 1
                FROM pg_type
                WHERE typname = 'workorder_status_enum'
            ) THEN
                CREATE TYPE workorder_status_enum AS ENUM ('ACTIVE', 'COMPLETED');
            END IF;
        END;
        $$;
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS workorders (
            id UUID PRIMARY KEY,
            workorder_code VARCHAR(255) NOT NULL,
            workorder_code_normalized VARCHAR(255) NOT NULL,
            region region_enum NOT NULL,
            total_grids INTEGER NOT NULL,
            status workorder_status_enum NOT NULL DEFAULT 'ACTIVE',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            created_by_user_id UUID NOT NULL REFERENCES app_users(id),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_by_user_id UUID NOT NULL REFERENCES app_users(id),
            completed_at TIMESTAMP WITH TIME ZONE,
            completed_by_user_id UUID REFERENCES app_users(id),
            CONSTRAINT ck_workorders_total_grids_positive CHECK (total_grids > 0),
            CONSTRAINT uq_workorders_code_normalized UNIQUE (workorder_code_normalized)
        );
        """
    )

    op.execute("ALTER TABLE submissions ADD COLUMN IF NOT EXISTS workorder_id UUID;")

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM submissions
                WHERE cluster_name_normalized IS NULL
                OR btrim(cluster_name_normalized) = ''
            ) THEN
                RAISE EXCEPTION
                    'Workorder migration blocked: submissions contain blank cluster_name_normalized values.';
            END IF;

            IF EXISTS (
                SELECT 1
                FROM submissions
                GROUP BY cluster_name_normalized, work_date
                HAVING COUNT(*) > 1
            ) THEN
                RAISE EXCEPTION
                    'Workorder migration blocked: duplicate submissions exist for the same normalized code and work_date.';
            END IF;

            IF EXISTS (
                SELECT 1
                FROM submissions
                GROUP BY cluster_name_normalized
                HAVING COUNT(DISTINCT zone) > 1
            ) THEN
                RAISE EXCEPTION
                    'Workorder migration blocked: mixed zone values exist for the same normalized code.';
            END IF;

            IF EXISTS (
                SELECT 1
                FROM submissions
                GROUP BY cluster_name_normalized
                HAVING COUNT(DISTINCT number_of_grids) > 1
            ) THEN
                RAISE EXCEPTION
                    'Workorder migration blocked: conflicting legacy number_of_grids values exist for the same normalized code.';
            END IF;

            IF EXISTS (
                SELECT 1
                FROM submissions
                GROUP BY cluster_name_normalized
                HAVING MAX(number_of_grids) <= 0
            ) THEN
                RAISE EXCEPTION
                    'Workorder migration blocked: legacy number_of_grids must be positive for workorder backfill.';
            END IF;

            IF EXISTS (
                SELECT 1
                FROM submission_attachments
                WHERE is_active IS TRUE
                GROUP BY submission_id
                HAVING COUNT(*) > 1
            ) THEN
                RAISE EXCEPTION
                    'Workorder migration blocked: submission_attachments contains multiple active rows for a single submission.';
            END IF;
        END;
        $$;
        """
    )

    op.execute(
        """
        -- backfill workorders from legacy submissions
        WITH ranked_legacy_submissions AS (
            SELECT
                id,
                cluster_name AS workorder_code,
                cluster_name_normalized AS workorder_code_normalized,
                CASE zone
                    WHEN 'NORTHEAST' THEN 'NE_UP'
                    WHEN 'CENTRAL' THEN 'CENTRAL'
                    WHEN 'SOUTH_FLORIDA' THEN 'SOUTH_FLORIDA'
                    ELSE NULL
                END::region_enum AS region,
                number_of_grids,
                completed_grids,
                skipped_grids,
                created_at,
                created_by_user_id,
                updated_at,
                updated_by_user_id,
                completed_at,
                completed_by_user_id,
                ROW_NUMBER() OVER (
                    PARTITION BY cluster_name_normalized
                    ORDER BY created_at ASC, id ASC
                ) AS created_rank,
                ROW_NUMBER() OVER (
                    PARTITION BY cluster_name_normalized
                    ORDER BY updated_at DESC, id DESC
                ) AS updated_rank,
                ROW_NUMBER() OVER (
                    PARTITION BY cluster_name_normalized
                    ORDER BY completed_at DESC NULLS LAST, id DESC
                ) AS completed_rank
            FROM submissions
        ),
        legacy_workorders AS (
            SELECT
                (
                    substring(md5(workorder_code_normalized), 1, 8) || '-' ||
                    substring(md5(workorder_code_normalized), 9, 4) || '-' ||
                    substring(md5(workorder_code_normalized), 13, 4) || '-' ||
                    substring(md5(workorder_code_normalized), 17, 4) || '-' ||
                    substring(md5(workorder_code_normalized), 21, 12)
                )::uuid AS id,
                MAX(CASE WHEN created_rank = 1 THEN workorder_code END) AS workorder_code,
                workorder_code_normalized,
                MAX(CASE WHEN created_rank = 1 THEN region::text END)::region_enum AS region,
                MAX(number_of_grids)::int AS total_grids,
                CASE
                    WHEN SUM(completed_grids + skipped_grids) >= MAX(number_of_grids)
                    THEN 'COMPLETED'::workorder_status_enum
                    ELSE 'ACTIVE'::workorder_status_enum
                END AS status,
                MIN(created_at) AS created_at,
                MAX(CASE WHEN created_rank = 1 THEN created_by_user_id::text END)::uuid AS created_by_user_id,
                MAX(updated_at) AS updated_at,
                MAX(CASE WHEN updated_rank = 1 THEN updated_by_user_id::text END)::uuid AS updated_by_user_id,
                CASE
                    WHEN SUM(completed_grids + skipped_grids) >= MAX(number_of_grids)
                    THEN MAX(completed_at)
                    ELSE NULL
                END AS completed_at,
                CASE
                    WHEN SUM(completed_grids + skipped_grids) >= MAX(number_of_grids)
                    THEN MAX(CASE WHEN completed_rank = 1 THEN completed_by_user_id::text END)::uuid
                    ELSE NULL
                END AS completed_by_user_id
            FROM ranked_legacy_submissions
            GROUP BY workorder_code_normalized
        )
        INSERT INTO workorders (
            id,
            workorder_code,
            workorder_code_normalized,
            region,
            total_grids,
            status,
            created_at,
            created_by_user_id,
            updated_at,
            updated_by_user_id,
            completed_at,
            completed_by_user_id
        )
        SELECT
            id,
            workorder_code,
            workorder_code_normalized,
            region,
            total_grids,
            status,
            created_at,
            created_by_user_id,
            updated_at,
            updated_by_user_id,
            completed_at,
            completed_by_user_id
        FROM legacy_workorders;
        """
    )

    op.execute(
        """
        -- attach legacy submissions to parent workorders
        UPDATE submissions AS s
        SET workorder_id = w.id
        FROM workorders AS w
        WHERE w.workorder_code_normalized = s.cluster_name_normalized;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM submissions
                WHERE workorder_id IS NULL
            ) THEN
                RAISE EXCEPTION
                    'Workorder migration blocked: some submissions were not assigned a workorder_id.';
            END IF;
        END;
        $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_submissions_workorder_id_workorders'
            ) THEN
                ALTER TABLE submissions
                ADD CONSTRAINT fk_submissions_workorder_id_workorders
                FOREIGN KEY (workorder_id)
                REFERENCES workorders(id);
            END IF;
        END;
        $$;
        """
    )

    op.execute("ALTER TABLE submissions ALTER COLUMN workorder_id SET NOT NULL;")

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'uq_submissions_workorder_date'
            ) THEN
                ALTER TABLE submissions
                ADD CONSTRAINT uq_submissions_workorder_date
                UNIQUE (workorder_id, work_date);
            END IF;
        END;
        $$;
        """
    )

    op.execute(
        """
        ALTER TABLE submissions
        DROP CONSTRAINT IF EXISTS uq_submissions_owner_date_shift_cluster;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'ck_submissions_skipped_grids_non_negative'
            ) THEN
                ALTER TABLE submissions
                ADD CONSTRAINT ck_submissions_skipped_grids_non_negative
                CHECK (skipped_grids >= 0);
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'ck_submissions_force_tested_grids_non_negative'
            ) THEN
                ALTER TABLE submissions
                ADD CONSTRAINT ck_submissions_force_tested_grids_non_negative
                CHECK (force_tested_grids >= 0);
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'ck_submissions_completed_grids_non_negative'
            ) THEN
                ALTER TABLE submissions
                ADD CONSTRAINT ck_submissions_completed_grids_non_negative
                CHECK (completed_grids >= 0);
            END IF;
        END;
        $$;
        """
    )

    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_submission_attachments_one_active_per_submission
        ON submission_attachments (submission_id)
        WHERE is_active IS TRUE;
        """
    )

    op.execute(
        """
        -- validate migration results
        DO $$
        DECLARE
            orphaned_submissions_count integer;
            duplicated_normalized_count integer;
            fk_coverage_count integer;
            submissions_count integer;
        BEGIN
            -- no orphaned submissions remain
            SELECT COUNT(*)
            INTO orphaned_submissions_count
            FROM submissions AS s
            LEFT JOIN workorders AS w
                ON w.id = s.workorder_id
            WHERE s.workorder_id IS NULL
                OR w.id IS NULL;

            IF orphaned_submissions_count > 0 THEN
                RAISE EXCEPTION
                    'Migration validation failed: orphaned submissions=%',
                    orphaned_submissions_count;
            END IF;

            SELECT COUNT(*)
            INTO duplicated_normalized_count
            FROM (
                SELECT workorder_code_normalized
                FROM workorders
                GROUP BY workorder_code_normalized
                HAVING COUNT(*) > 1
            ) AS dup;

            IF duplicated_normalized_count > 0 THEN
                RAISE EXCEPTION
                    'Migration validation failed: duplicated normalized codes=%',
                    duplicated_normalized_count;
            END IF;

            SELECT COUNT(*)
            INTO fk_coverage_count
            FROM submissions AS s
            INNER JOIN workorders AS w
                ON w.id = s.workorder_id;

            SELECT COUNT(*)
            INTO submissions_count
            FROM submissions;

            IF fk_coverage_count <> submissions_count THEN
                RAISE EXCEPTION
                    'Migration validation failed: foreign-key coverage mismatch joined=% total=%',
                    fk_coverage_count,
                    submissions_count;
            END IF;
        END;
        $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS uq_submission_attachments_one_active_per_submission;
        """
    )

    op.execute(
        """
        ALTER TABLE submissions
        DROP CONSTRAINT IF EXISTS uq_submissions_workorder_date;
        """
    )

    op.execute(
        """
        ALTER TABLE submissions
        DROP CONSTRAINT IF EXISTS fk_submissions_workorder_id_workorders;
        """
    )

    op.execute("ALTER TABLE submissions ALTER COLUMN workorder_id DROP NOT NULL;")

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'uq_submissions_owner_date_shift_cluster'
            ) THEN
                ALTER TABLE submissions
                ADD CONSTRAINT uq_submissions_owner_date_shift_cluster
                UNIQUE (owner_user_id, work_date, shift, cluster_name_normalized);
            END IF;
        END;
        $$;
        """
    )

    op.execute("ALTER TABLE submissions DROP COLUMN IF EXISTS workorder_id;")
    op.execute("DROP TABLE IF EXISTS workorders;")
    op.execute("DROP TYPE IF EXISTS workorder_status_enum;")
    op.execute("DROP TYPE IF EXISTS region_enum;")
