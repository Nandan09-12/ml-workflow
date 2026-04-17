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
- no roster in v1
- no edit approval in v1
- V1 stores the latest daily progress state only, not structured 4-hour checkpoint history

## Locked Implementation Decisions
1. First admin bootstrap
   - use env var `BOOTSTRAP_ADMIN_EMAILS`
   - on `POST /api/v1/me/bootstrap`, if zero approved admins exist and caller email is allowlisted, auto-approve as `ADMIN`
   - write approval audit row with `reviewed_by_user_id = null` and `review_notes = BOOTSTRAP_ADMIN_AUTO_APPROVED`
   - disable bootstrap path once any approved admin exists
   - execute atomically/transactionally
2. `PATCH /me` editable fields
   - `full_name` only
3. Parent/child domain model
   - `workorders` is the parent multi-day business record
   - `submissions` is the child daily closeout record
   - one workorder can span multiple days and different drivers
   - one daily submission per `workorder + work_date`
4. Workorder code identity
   - use `workorder_code` as the real stable business identifier
   - store raw `workorder_code` for display
   - store normalized `workorder_code_normalized` for lookup/search/uniqueness
   - normalization:
     - Unicode NFKC
     - trim
     - uppercase
     - remove whitespace
     - preserve `-`
5. Parent workorder fields
   - `region` belongs to the parent workorder
   - `total_grids` belongs to the parent workorder and is the grand total across all days
   - workorder statuses: `ACTIVE`, `COMPLETED`
6. Daily submission fields
   - `completed_grids`, `skipped_grids`, and `force_tested_grids` are that day's contribution only
   - tester progress updates use cumulative `completed_grids` within the day
   - `skipped_grids` are permanent for the workorder
7. Submission lifecycle
   - `Start Drive` finds or creates the parent workorder and creates `IN_PROGRESS`
   - backend stamps `started_at` automatically
   - `End Drive` moves daily submission to `CHECKED_OUT`
   - backend stamps `ended_at` automatically
   - `Complete Submission` requires `CHECKED_OUT`
8. Aggregate workorder rules
   - aggregate child `completed_grids + skipped_grids` cannot exceed parent `total_grids`
   - workorder auto-completes when aggregate child `completed_grids + skipped_grids = total_grids`
   - reopening the relevant child or removing its last active file may move the parent back to `ACTIVE`
9. Attachments
   - exactly one active file per daily submission
   - allowed extensions: `.csv`, `.xlsx`
   - `.xls` not allowed in v1
   - validate extension + MIME allowlist
   - inactive attachment history is admin-only
10. Completion + file pending indicator
   - daily completion requires exactly one active attachment
   - expose computed `file_submission_pending` in daily submission detail/list responses
   - `file_submission_pending = true` when `daily submission status = CHECKED_OUT` and active attachments = `0`
   - do not add a DB column for this in v1
11. Post-completion edits
   - testers do not edit completed daily submission data
   - admins can edit completed daily submissions
   - admins can edit workorders
   - testers can still manage files after completion

## Immediate Priority
Implement the backend foundation and the workorder + daily submission workflow first.

## First Backend Features To Build
1. settings/config
2. JWT auth integration with Supabase
3. app_users model and bootstrap endpoint
4. admin approval endpoints
5. workorders model and lookup/create flow
6. daily submissions model and create/list/update endpoints
7. submission audit logging

## Non-Negotiable Rules
- drive tester edits only own `IN_PROGRESS` or `CHECKED_OUT` daily submission
- `COMPLETED` daily submission requires exactly one active attachment
- expose computed `file_submission_pending` and workorder aggregate progress in read models
- duplicate daily submission prevented by `workorder_id + work_date`
- aggregate child progress must never exceed parent `total_grids`
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
- workorder lookup/start-drive flow third
- daily submission endpoints fourth
- attachment flow fifth
- admin reporting after core CRUD is stable

## Do Not Change Without Reason
- role model
- parent `workorders` + child `submissions` architecture
- workorder code normalization rule
- one-daily-submission-per-workorder-per-date rule
- one-active-file-per-daily-submission rule
- aggregate workorder progress rule
- audit-first architecture

## Hardening Defaults
- production-like environments must not run with `DATABASE_SSL_MODE=disable`
- Alembic and runtime DB sessions must use the same database SSL configuration source
- integration tests are opt-in (`RUN_INTEGRATION_TESTS=1`, `INTEGRATION_DATABASE_URL`) and isolated by schema
- mobile sync endpoint remains a v1 placeholder contract (`status = NOT_IMPLEMENTED`)
