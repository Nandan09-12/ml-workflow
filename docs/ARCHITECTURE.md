# Architecture

## High-Level Stack

### Backend
- FastAPI
- SQLAlchemy 2
- Alembic
- Supabase Postgres
- Supabase Storage
- Supabase Auth

### Admin Web
- Next.js
- TypeScript

### Tester App
- Expo / React Native
- TypeScript
- React Native Web for early web-based UI development
- SQLite on device later for offline sync

## Monorepo Structure

```text
ml-workflow/
  apps/
    api/
    admin-web/
    mobile/
  docs/
  README.md
```

## Why Monorepo
- single product
- shared documentation
- simpler development workflow
- easier API and frontend coordination
- no need for microservice complexity in v1

## Auth Model
- Supabase Auth handles signup, login, password reset, JWT
- FastAPI validates Supabase JWT
- business user state is stored in `app_users`
- approval and role decisions are managed by FastAPI and app tables

## First Admin Bootstrap Model
- use `BOOTSTRAP_ADMIN_EMAILS` env var for temporary first-admin allowlist
- during `POST /api/v1/me/bootstrap`, auto-approve only when:
  - no approved admins exist
  - caller email is allowlisted
  - requested role is `ADMIN`
- must write approval audit with `reviewed_by_user_id = null` and notes `BOOTSTRAP_ADMIN_AUTO_APPROVED`
- this path is disabled after first approved admin exists
- logic must execute in one DB transaction

## Data Model Ownership
- Supabase Auth stores auth identities
- app database stores business entities such as app users, workorders, daily submissions, attachment metadata, and audit logs
- `workorders` is the parent business entity for a multi-day job
- `submissions` is the child daily closeout entity under a workorder
- one workorder may span multiple days and different drivers, but only one driver may own a given workorder on a given day
- v1 stores only the latest cumulative progress for the current day on the daily submission row
- structured 4-hour checkpoint history is deferred to a future version as an additive table, not a replacement architecture

## File Storage Model
- actual file bytes stored in Supabase Storage
- file metadata stored in `submission_attachments`
- attachment rows link files to daily submissions and uploading users
- each daily submission has exactly one active file in v1
- attachment removal is soft-delete metadata, not hard-delete metadata
- bucket is private
- FastAPI generates signed download URLs after permission checks
- admins can review inactive attachment metadata as part of history/review workflows

## API Contract Pattern
- thin routers
- service layer for business rules
- repository layer for data access
- all mutation endpoints create audit logs
- separate tester routes from admin routes
- separate workorder concepts from daily submission concepts
- standard JSON response envelope for JSON endpoints
- daily submission list/detail responses include:
  - daily submission fields
  - `file_submission_pending`
  - a nested workorder summary with aggregate progress values

## Canonicalization and Validation
- `workorder_code` is the stable business identifier across days
- workorder code normalization is deterministic and stored in `workorder_code_normalized`
- normalization rules:
  - Unicode NFKC
  - trim
  - uppercase
  - remove whitespace
  - preserve `-`
- work date future validation is region-aware:
  - `NE_UP -> America/New_York`
  - `SOUTH_FLORIDA -> America/New_York`
  - `CENTRAL -> America/Chicago`
- `region` and `total_grids` belong to the parent workorder, not the daily submission
- daily submission grid counts are contribution counts for that one day only
- aggregate workorder progress is derived from child daily submissions
- pagination defaults:
  - `page=1`
  - `page_size=20`
  - `max page_size=100`
  - invalid values return `422`

## Core Flows

### Signup / Approval
1. user signs up via Supabase Auth
2. app calls bootstrap endpoint
3. app user row is created with requested role and pending status
4. admin approves, rejects, or suspends user

### Start Drive / Workorder Attach Flow
1. tester enters `workorder_code` and daily start fields
2. backend normalizes the code
3. if an active workorder exists for that normalized code, backend reuses it
4. if no active workorder exists, backend creates one using `region` and grand `total_grids`
5. backend creates the daily submission in `IN_PROGRESS` and stamps `started_at`

### Daily Progress / Closeout Flow
1. tester updates cumulative `completed_grids` during the day on the current daily submission
2. tester presses `End Drive`
3. backend stamps `ended_at` and moves the daily submission to `CHECKED_OUT`
4. tester receives the daily file and final `skipped_grids` / `force_tested_grids`
5. tester uploads the file and completes the daily submission
6. backend updates parent workorder aggregate progress

### Workorder Completion / Continuation Flow
1. if aggregate child `completed_grids + skipped_grids` is still below parent `total_grids`, the workorder remains `ACTIVE`
2. same driver or different driver on a later day enters the same `workorder_code`
3. backend attaches the new daily submission to the same active workorder
4. when aggregate child `completed_grids + skipped_grids = total_grids`, backend marks the parent workorder `COMPLETED`

### Reminder / Progress Note
- the 4-hour reminder cadence is part of the product workflow
- v1 backend stores only the latest cumulative progress for the current day on the daily submission row
- v1 does not yet include backend-managed reminder scheduling or a structured checkpoint history table

### Audit Flow
All create, edit, upload, remove, start-drive, end-drive, complete, reopen, approve, reject, and auto-bootstrap approval actions are audit logged. Workorder create/attach/complete/reopen effects are recorded in the related daily submission audit trail in v1.

## Deployment Approach

### V1 Local Dev
- API in Docker
- admin web in Docker
- mobile app developed on web first
- Android emulator later
- Supabase hosted services for auth, database, and storage

## Security and Hardening Notes
- TLS for public API traffic is terminated at the ingress/reverse-proxy layer in deployment environments.
- Database TLS is configurable via app settings and should not be disabled in production-like environments.
- Alembic migrations and runtime DB sessions share the same database SSL configuration source.
- Secrets are loaded from environment variables and must not be committed in source-controlled files.

## Test Isolation Notes
- fast default test runs include unit + API tests only.
- integration tests are opt-in and require:
  - `RUN_INTEGRATION_TESTS=1`
  - `INTEGRATION_DATABASE_URL`
- integration tests run against isolated per-test schemas and are skipped by default.
