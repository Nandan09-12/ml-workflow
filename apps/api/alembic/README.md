# Alembic Migration Rules

This directory contains persistent schema history for the ML Workflow API.

## Non-Negotiable Rules

- Never edit an Alembic revision that has already been applied to any shared or
  persistent environment.
- `0001_init_core_tables.py` is immutable now that it has been applied for real
  to the Supabase database.
- All future schema changes must be introduced as new Alembic revisions.
- Do not create or alter application tables manually in the Supabase dashboard.
- Do not use `alembic stamp` on shared environments unless you are explicitly
  repairing Alembic state and have verified the live schema situation first.
- New tables are not free-form. Only add schema objects that are explicitly
  required by approved product and backend decisions.

## Expected Workflow

1. Update SQLAlchemy models only for an approved schema change.
2. Create a new Alembic revision for that change.
3. Review the generated migration carefully before applying it.
4. Apply the revision to the target environment.
5. Update schema docs if the persistent contract changed.

## Why This Matters

Editing an already-applied revision can leave Alembic history and the live
database out of sync, which risks missing tables, drift between environments,
and avoidable data loss.
