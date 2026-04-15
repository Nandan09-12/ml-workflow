# ml-workflow

ML Workflow is a modular field-operations platform.

V1 includes the **DT Check-in** module for drive testers and admins.

## Current Apps

- `apps/api` - FastAPI backend
- `apps/admin-web` - Next.js admin console
- `apps/mobile` - Expo / React Native tester app (web-first initially, mobile later)

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
- `docs/BACKEND_MIGRATION_POLICY.md`

## V1 Summary

Drive testers submit daily cluster/grid progress records. Admins approve users, review
submissions, audit changes, reopen completed records if needed, and export data.

## Key V1 Decisions

- Monorepo
- FastAPI backend
- Next.js admin web
- Expo / React Native tester app
- Supabase Auth + Postgres + Storage
- No microservices in v1
- No roster/assignment in v1
- Full audit history for all submission changes

## Repo Structure

```text
ml-workflow/
  apps/
    api/
      app/
      alembic/
      tests/
    admin-web/
    mobile/
  docs/
  docker-compose.yml
  README.md
```

## Local API Quickstart

```bash
docker compose up --build
```

Environment template for API settings:

```bash
apps/api/.env.example
```

API health endpoint:

```bash
GET http://localhost:8000/api/v1/health
```

## Security Notes
- Do not commit real secrets (`SUPABASE_SERVICE_ROLE_KEY`, DB credentials, JWT secrets) to git.
- In production-like environments, database SSL must be enabled via API settings.
- Public HTTPS termination is expected at ingress/reverse proxy.

## Tests
- Fast default run (unit + API):
  ```bash
  cd apps/api
  PYTHONPATH=. pytest tests -m "not integration"
  ```
- Opt-in integration tests:
  ```bash
  cd apps/api
  RUN_INTEGRATION_TESTS=1 INTEGRATION_DATABASE_URL=<test-db-url> PYTHONPATH=. pytest tests/integration
  ```
