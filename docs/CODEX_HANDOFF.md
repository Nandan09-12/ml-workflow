# Codex Handoff

## Project
ML Workflow

## Current Goal
Build V1 backend-first for the DT Check-in module.

## What Is Already Decided
- monorepo
- no microservices in v1
- FastAPI backend
- Next.js admin web
- Expo / React Native tester app
- Supabase Auth
- Supabase Postgres
- Supabase Storage
- audit logging required
- completion does not require attachment
- no roster in v1
- no edit approval in v1

## Locked Implementation Decisions
1. First admin bootstrap
   - use env var `BOOTSTRAP_ADMIN_EMAILS`
   - on `POST /api/v1/me/bootstrap`, if zero approved admins exist and caller email is allowlisted, auto-approve as `ADMIN`
   - write approval audit row with `reviewed_by_user_id = null` and `review_notes = BOOTSTRAP_ADMIN_AUTO_APPROVED`
   - disable bootstrap path once any approved admin exists
   - execute atomically/transactionally
2. `PATCH /me` editable fields
   - `full_name` only
3. Cluster normalization
   - Unicode NFKC
   - trim
   - replace `-` and `_` with space
   - collapse whitespace
   - uppercase
   - store in `cluster_name_normalized`
4. Pagination
   - default `page=1`
   - default `page_size=20`
   - max `page_size=100`
   - invalid values => `422`
5. Attachments
   - max size 25 MB per file
   - max 5 active attachments per submission
   - allowed extensions: `.csv`, `.xlsx`
   - `.xls` not allowed in v1
   - validate extension + MIME allowlist
6. Standard JSON response envelope
   - success: `{ success: true, data: ..., meta: ... }`
   - error: `{ success: false, error: { code, message, details }, meta: ... }`
   - no envelope for file streams or `204`
7. Future date validation
   - `NORTHEAST -> America/New_York`
   - `SOUTH_FLORIDA -> America/New_York`
   - `CENTRAL -> America/Chicago`
   - enforce `work_date <= current date` in zone timezone
8. Completion + file pending indicator
   - completion requires `pending_grids = 0`
   - completion does not require an attachment
   - expose computed `file_submission_pending` in submission detail/list responses
   - `file_submission_pending = true` when `status = COMPLETED` and active attachments = `0`
   - do not add a DB column for this in v1

## Immediate Priority
Implement the backend foundation and core submission workflow first.

## First Backend Features To Build
1. settings/config
2. JWT auth integration with Supabase
3. app_users model and bootstrap endpoint
4. admin approval endpoints
5. submissions model and create/list/update endpoints
6. submission audit logging

## Non-Negotiable Rules
- drive tester edits only own `ONGOING` submission
- `COMPLETED` requires `pending_grids = 0`
- expose computed `file_submission_pending` in submission list/detail responses
- duplicate submission prevented by owner + date + shift + normalized cluster
- all key mutations must be audit logged
- never edit an Alembic revision that has already been applied to a shared or
  persistent environment
- `apps/api/alembic/versions/0001_init_core_tables.py` is now immutable
- every schema change after `0001_init_core_tables` must be a new Alembic
  revision
- do not create or modify application tables directly in the Supabase dashboard

## Migration Guardrails
- read `docs/BACKEND_MIGRATION_POLICY.md` before making schema changes
- follow `apps/api/alembic/README.md` for migration discipline close to the code
- CI rejects edits to existing Alembic revision files and only allows newly
  added migration files

## Suggested Folder Layout For apps/api
```text
apps/api/
  app/
    api/
      v1/
        routers/
    core/
    db/
    models/
    repositories/
    schemas/
    services/
    main.py
  alembic/
  tests/
```

## Build Order
- backend models and migrations first
- user approval endpoints second
- submission endpoints third
- attachment flow fourth
- admin reporting after core CRUD is stable

## Do Not Change Without Reason
- role model
- submission uniqueness rule
- grid math rule
- computed `file_submission_pending` rule (derive from completed status + active attachments)
- audit-first architecture

## Hardening Defaults
- production-like environments must not run with `DATABASE_SSL_MODE=disable`
- Alembic and runtime DB sessions must use the same DB TLS settings source
- integration tests are opt-in (`RUN_INTEGRATION_TESTS=1`, `INTEGRATION_DATABASE_URL`) and isolated by schema
- mobile sync endpoint remains a v1 placeholder contract (`status = NOT_IMPLEMENTED`)
