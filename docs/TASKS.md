# Tasks

## Phase 1 — Repo and App Skeleton
- create monorepo structure
- create FastAPI app skeleton
- create Next.js admin app skeleton
- create Expo app skeleton
- add root docs and initial handoff pack

## Phase 2 — Backend Foundation
- configure settings and environment management
- connect FastAPI to Supabase Postgres
- add SQLAlchemy models
- add Alembic migrations
- add Supabase JWT auth verification
- implement app_users bootstrap flow

## Phase 3 — User Approval Flow
- implement app user bootstrap endpoint
- implement current user endpoint
- implement admin list pending users
- implement approve / reject endpoints
- add user approval audit logging

## Phase 4 — Submission Core
- implement create submission
- implement list my submissions
- implement get submission detail
- implement update ongoing submission
- enforce duplicate and grid math validation
- add submission audit logging

## Phase 5 — Attachments and Completion
- integrate Supabase Storage
- implement attachment upload endpoint
- implement attachment list endpoint
- implement signed download URL endpoint
- implement complete submission endpoint
- enforce attachment-before-complete rule

## Phase 6 — Admin Submission Console APIs
- implement admin submission listing
- implement admin submission detail
- implement admin edit submission
- implement admin reopen submission
- implement full audit history endpoint

## Phase 7 — Reporting APIs
- implement dashboard summary endpoint
- implement no-submission-yet endpoint
- implement CSV export endpoint

## Phase 8 — Frontend Screens
- admin login guard / session wiring
- pending users page
- submissions table
- submission detail page
- tester web-first submission screens

## Phase 9 — Offline Preparation
- define mobile sync contract
- add mobile bootstrap endpoint
- add batch sync endpoint placeholder or initial implementation

## Recommended First Coding Milestone
Deliver working backend for:
- bootstrap
- current user
- approve user
- create submission
- list my submissions
- update ongoing submission
