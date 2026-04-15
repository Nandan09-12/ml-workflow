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

## Phase 4 - Submission Core
- implement create submission
- implement list my submissions
- implement get submission detail
- implement update ongoing submission
- enforce duplicate and grid math validation
- enforce cluster normalization contract
- enforce zone-aware future date validation
- add submission audit logging

## Phase 5 - Attachments and Completion
- integrate Supabase Storage
- implement attachment upload endpoint
- implement attachment list endpoint
- implement signed download URL endpoint
- implement soft remove attachment endpoint
- enforce completion rule: `pending_grids = 0`
- allow completion without attachment
- compute and return `file_submission_pending` in submission list/detail responses
- enforce file validation:
  - max 25 MB
  - max 5 active attachments
  - extension + MIME allowlist

## Phase 6 - Admin Submission Console APIs
- implement admin submission listing
- implement admin submission detail
- implement admin edit submission
- implement admin reopen submission
- implement `file_submission_pending` filter for admin submissions list
- implement full audit history endpoint

## Phase 7 - Reporting APIs
- implement dashboard summary endpoint
- implement no-submission-yet endpoint
- implement CSV export endpoint

## Phase 8 - Frontend Screens
- admin login guard / session wiring
- pending users page
- submissions table
- submission detail page
- tester web-first submission screens
- show warning in tester UI when submission is completed and `file_submission_pending = true`
- show/filter `file_submission_pending` in admin submissions UI

## Phase 9 - Offline Preparation
- define mobile sync contract
- add mobile bootstrap endpoint
- add batch sync endpoint placeholder or initial implementation

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
- create submission
- list my submissions
- update ongoing submission
- audit logs for all these mutations
