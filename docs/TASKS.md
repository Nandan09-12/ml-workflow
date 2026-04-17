# Tasks

## Phase 1 - Repo and App Skeleton
- create monorepo structure
- create FastAPI app skeleton
- create Next.js admin app skeleton
- create Expo app skeleton
- add root docs and initial handoff pack

## Phase 2 - Backend Foundation
- configure settings and environment management
- connect FastAPI to Supabase Postgres
- add SQLAlchemy models
- add Alembic migrations
- add Supabase JWT auth verification
- implement app_users bootstrap flow
- implement standard response envelope utilities

## Phase 3 - User Approval Flow
- implement app user bootstrap endpoint
- implement current user endpoint
- implement `PATCH /me` (`full_name` only)
- implement admin list pending users
- implement approve / reject / suspend endpoints
- add user approval audit logging
- implement first-admin bootstrap logic with `BOOTSTRAP_ADMIN_EMAILS`

## Phase 4 - Workorder + Start Drive Core
- add `workorders` model and migration
- reshape `submissions` into daily child records
- implement workorder-code normalization contract
- implement `GET /workorders/lookup`
- implement `Start Drive` create/find flow
- enforce one daily submission per `workorder + work_date`
- enforce region-aware future date validation
- add `started_at` / `ended_at`
- add submission audit logging with workorder attach/create context

## Phase 5 - Daily Progress, Attachments, and Closeout
- implement update daily submission endpoint
- implement `End Drive` endpoint
- integrate Supabase Storage
- implement attachment upload endpoint
- implement attachment list endpoint
- implement signed download URL endpoint
- implement soft remove attachment endpoint
- enforce exactly one active attachment per daily submission
- enforce daily completion rule:
  - status must be `CHECKED_OUT`
  - exactly one active attachment is required
  - final daily fields must be present
- enforce aggregate workorder totals cannot exceed parent `total_grids`
- auto-complete parent workorder when aggregate child totals reach parent `total_grids`
- move parent workorder back to `ACTIVE` when a completed child is reopened or loses its last active file
- enforce file validation:
  - extension + MIME allowlist

## Phase 6 - Admin Workorder + Submission Console APIs
- implement admin workorder listing
- implement admin workorder detail
- implement admin workorder edit
- implement admin daily submission listing
- implement admin daily submission detail
- implement admin daily submission edit, including completed submissions
- implement admin daily submission reopen to `CHECKED_OUT`
- implement `file_submission_pending` filter for admin daily submissions list
- implement full daily submission audit history endpoint
- implement admin-only attachment history endpoint

## Phase 7 - Reporting APIs
- implement dashboard summary endpoint
- implement no-submission-yet endpoint
- implement CSV export endpoint for daily submissions
- add aggregate workorder progress read models

## Phase 8 - Frontend Screens
- admin login guard / session wiring
- pending users page
- workorders table
- workorder detail page
- daily submissions table
- daily submission detail page
- tester `Start Drive` screen with workorder lookup
- tester daily submission detail with `End Drive` and `Complete Submission`
- show warning in tester UI when daily submission is checked out and `file_submission_pending = true`
- show/filter `file_submission_pending` in admin daily submissions UI

## Phase 9 - Offline Preparation
- define mobile sync contract
- add mobile bootstrap endpoint
- add batch sync endpoint placeholder or initial implementation
- leave room for future structured 4-hour progress history without redesigning the core workorder + daily submission model

## Cross-Cutting Delivery Tasks
- apply standard pagination defaults and limits
- enforce consistent success/error envelope on JSON responses
- define and implement status/error mapping per endpoint
- add endpoint-level tests for all business rules

## Recommended First Coding Milestone
Deliver working backend for:
- bootstrap
- current user
- approve user
- workorder lookup
- `Start Drive` daily submission create/find
- list my daily submissions
- update in-progress daily submission
- audit logs for all these mutations
