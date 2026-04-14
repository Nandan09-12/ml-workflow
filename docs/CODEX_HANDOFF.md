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
- attachment required before completion
- no roster in v1
- no edit approval in v1

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
- drive tester edits only own ONGOING submission
- COMPLETED requires at least one active attachment
- COMPLETED requires pending_grids = 0
- duplicate submission prevented by owner + date + shift + normalized cluster
- all key mutations must be audit logged

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
Build Order
•	backend models and migrations first
•	user approval endpoints second
•	submission endpoints third
•	attachment flow fourth
•	admin reporting after core CRUD is stable
Do Not Change Without Reason
•	role model
•	submission uniqueness rule
•	grid math rule
•	attachment-before-complete rule
•	audit-first architecture ```
