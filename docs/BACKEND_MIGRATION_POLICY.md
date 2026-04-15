# Backend Migration Policy

## Purpose

Protect the persistent Supabase schema from drift, accidental resets, and data
loss caused by mutable migration history.

## Hard Rules

- Never edit an Alembic revision that has already been applied to any shared or
  persistent environment.
- `apps/api/alembic/versions/0001_init_core_tables.py` is immutable.
- Every schema change after `0001_init_core_tables` must be a new Alembic
  revision.
- Do not create, alter, or drop application tables manually in the Supabase
  dashboard.
- Do not add speculative tables or columns "just in case". New schema objects
  must be tied to an approved product or backend requirement.

## Safe Process

1. Confirm the schema change is actually required.
2. Update SQLAlchemy models for the approved change.
3. Generate a new Alembic revision.
4. Review the migration carefully before applying it.
5. Apply the migration to the target environment.
6. Update schema-related docs if the persistent contract changed.

## Guardrails In This Repo

- A warning is embedded in `0001_init_core_tables.py`.
- `apps/api/alembic/README.md` explains migration discipline close to the code.
- CI rejects modifications to existing files under `apps/api/alembic/versions/`
  while still allowing newly added migration files.

## Shared Environment Recovery Rule

If Alembic history and the live schema ever disagree, do not guess. First
inspect the actual database state, then repair Alembic state with explicit,
minimal actions.
