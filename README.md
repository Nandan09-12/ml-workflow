# ml-workflow

ML Workflow is a modular field-operations platform.

V1 includes the **DT Check-in** module for drive testers and admins.

## Current Apps

- `apps/api` — FastAPI backend
- `apps/admin-web` — Next.js admin console
- `apps/mobile` — Expo / React Native tester app (web-first initially, mobile later)

## Docs

- `docs/PRD.md`
- `docs/ARCHITECTURE.md`
- `docs/DB_SCHEMA.md`
- `docs/API_SPEC.md`
- `docs/BUSINESS_RULES.md`
- `docs/USER_FLOWS.md`
- `docs/UI_SCREENS.md`
- `docs/TASKS.md`
- `docs/CODEX_HANDOFF.md`

## V1 Summary

Drive testers submit daily cluster/grid progress records.
Admins approve users, review submissions, audit changes, reopen completed records if needed, and export data.

## Key V1 Decisions

- Monorepo
- FastAPI backend
- Next.js admin web
- Expo / React Native tester app
- Supabase Auth + Postgres + Storage
- No microservices in v1
- No roster/assignment in v1
- Full audit history for all submission changes

## Proposed Repo Structure

```text

ml-workflow/
  apps/
    api/
    admin-web/
    mobile/
  docs/
    PRD.md
    ARCHITECTURE.md
    DB_SCHEMA.md
    API_SPEC.md
    BUSINESS_RULES.md
    USER_FLOWS.md
    UI_SCREENS.md
    TASKS.md
    CODEX_HANDOFF.md
  README.md

