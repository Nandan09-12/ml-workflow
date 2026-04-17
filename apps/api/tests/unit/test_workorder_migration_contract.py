from pathlib import Path


def _migration_text() -> str:
    migration_path = Path("alembic/versions/0002_workorders_parent_daily_submissions.py")
    assert migration_path.exists(), "Expected new migration file to exist."
    return migration_path.read_text(encoding="utf-8")


def test_migration_adds_workorders_parent_table_and_status_enum() -> None:
    content = _migration_text()

    assert "workorder_status_enum" in content
    assert "region_enum" in content
    assert "CREATE TYPE region_enum AS ENUM ('NE_UP', 'CENTRAL', 'SOUTH_FLORIDA')" in content
    assert "CREATE TABLE IF NOT EXISTS workorders" in content
    assert "workorder_code_normalized" in content
    assert "uq_workorders_code_normalized" in content
    assert "created_by_user_id UUID NOT NULL REFERENCES app_users(id)" in content
    assert "updated_by_user_id UUID NOT NULL REFERENCES app_users(id)" in content
    assert "completed_at TIMESTAMP WITH TIME ZONE" in content
    assert "completed_by_user_id UUID REFERENCES app_users(id)" in content
    assert "ck_workorders_total_grids_positive" in content


def test_migration_adds_workorder_fk_and_daily_uniqueness() -> None:
    content = _migration_text()

    assert "ADD COLUMN IF NOT EXISTS workorder_id UUID" in content
    assert "fk_submissions_workorder_id_workorders" in content
    assert "uq_submissions_workorder_date" in content


def test_migration_replaces_legacy_submission_uniqueness_and_adds_active_attachment_guard() -> None:
    content = _migration_text()

    assert "DROP CONSTRAINT IF EXISTS uq_submissions_owner_date_shift_cluster" in content
    assert "uq_submission_attachments_one_active_per_submission" in content
    assert "WHERE is_active IS TRUE" in content


def test_migration_contains_backfill_mapping_and_validation_queries() -> None:
    content = _migration_text()

    assert "backfill workorders from legacy submissions" in content
    assert "attach legacy submissions to parent workorders" in content
    assert "cluster_name AS workorder_code" in content
    assert "cluster_name_normalized AS workorder_code_normalized" in content
    assert "CASE zone" in content
    assert "WHEN 'NORTHEAST' THEN 'NE_UP'" in content
    assert "WHEN 'CENTRAL' THEN 'CENTRAL'" in content
    assert "WHEN 'SOUTH_FLORIDA' THEN 'SOUTH_FLORIDA'" in content
    assert "validate migration results" in content
    assert "no orphaned submissions remain" in content


def test_migration_contains_cutover_blockers_for_irrecoverable_conflicts() -> None:
    content = _migration_text()

    assert "blank cluster_name_normalized values" in content
    assert "duplicate submissions exist for the same normalized code and work_date" in content
    assert "mixed zone values exist for the same normalized code" in content
    assert "conflicting legacy number_of_grids values exist for the same normalized code" in content
