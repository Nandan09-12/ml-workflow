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
- app database stores business entities such as app users, submissions, attachment metadata, and audit logs

## File Storage Model
- actual file bytes stored in Supabase Storage
- file metadata stored in `submission_attachments`
- attachment rows link files to submissions and uploading users
- bucket is private
- FastAPI generates signed download URLs after permission checks

## API Contract Pattern
- thin routers
- service layer for business rules
- repository layer for data access
- all mutation endpoints create audit logs
- separate admin routes from tester routes
- standard JSON response envelope for JSON endpoints
- submission list/detail responses include computed `file_submission_pending`

## Canonicalization and Validation
- cluster normalization is deterministic and stored in `cluster_name_normalized`
- work date future validation is zone-aware:
  - `NORTHEAST -> America/New_York`
  - `SOUTH_FLORIDA -> America/New_York`
  - `CENTRAL -> America/Chicago`
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

### Submission Flow
1. tester creates ongoing submission
2. tester edits while ongoing
3. tester marks submission completed when `pending_grids = 0`
4. tester uploads CSV/XLSX attachment before or after completion
5. admin may reopen if correction is needed

### Audit Flow
All create, edit, upload, complete, reopen, approve, reject, and auto-bootstrap approval actions are audit logged.

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
