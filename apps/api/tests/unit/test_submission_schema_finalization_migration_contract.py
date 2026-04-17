from pathlib import Path


def _migration_text() -> str:
    migration_path = Path("alembic/versions/0003_finalize_submission_schema.py")
    assert migration_path.exists(), "Expected submission finalization migration file to exist."
    return migration_path.read_text(encoding="utf-8")


def test_migration_finalizes_submission_status_enum_and_timestamps() -> None:
    content = _migration_text()

    assert "submission_status_enum_v2" in content
    assert "'IN_PROGRESS', 'CHECKED_OUT', 'COMPLETED'" in content
    assert "ADD COLUMN IF NOT EXISTS started_at TIMESTAMP WITH TIME ZONE" in content
    assert "ADD COLUMN IF NOT EXISTS ended_at TIMESTAMP WITH TIME ZONE" in content
    assert "SET started_at = COALESCE(started_at, created_at)" in content
    assert "ALTER COLUMN started_at SET NOT NULL" in content


def test_migration_drops_legacy_submission_columns_and_constraints() -> None:
    content = _migration_text()

    assert "DROP CONSTRAINT IF EXISTS ck_submissions_number_of_grids_non_negative" in content
    assert "DROP CONSTRAINT IF EXISTS ck_submissions_pending_grids_non_negative" in content
    assert "DROP CONSTRAINT IF EXISTS ck_submissions_grid_math" in content
    assert "DROP CONSTRAINT IF EXISTS ck_submissions_skipped_lte_total" in content
    assert "DROP CONSTRAINT IF EXISTS ck_submissions_pending_lte_total" in content
    assert "DROP CONSTRAINT IF EXISTS ck_submissions_completed_lte_total" in content
    assert "DROP COLUMN IF EXISTS zone" in content
    assert "DROP COLUMN IF EXISTS cluster_name" in content
    assert "DROP COLUMN IF EXISTS cluster_name_normalized" in content
    assert "DROP COLUMN IF EXISTS number_of_grids" in content
    assert "DROP COLUMN IF EXISTS pending_grids" in content


def test_migration_validates_final_submission_contract() -> None:
    content = _migration_text()

    assert "started_at_missing_count" in content
    assert "legacy_columns_remaining_count" in content
    assert "submission_status_enum_values_count" in content
    assert "Submission schema finalization validation failed" in content
