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
- `docs/TESTING.md`
- `CONTRIBUTING.md`

## V1 Summary

Drive testers create daily closeout submissions under multi-day workorders. Admins approve
users, review workorders and daily submissions, audit changes, reopen completed daily
records if needed, and export data.

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
  docker compose -f docker-compose.integration.yml up -d integration-db
  cd apps/api
  RUN_INTEGRATION_TESTS=1 INTEGRATION_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/ml_workflow_integration INTEGRATION_DATABASE_SSL_MODE=disable PYTHONPATH=. pytest tests/integration
  docker compose -f docker-compose.integration.yml down
  ```

## Integration DB
- dedicated Docker stack file: `docker-compose.integration.yml`
- default local Postgres port: `5433`
- example env template: `apps/api/.env.integration.example`
- integration tests run against one Postgres instance and isolate each test with a temporary schema
- this setup does not change the normal API dev workflow in `docker-compose.yml`
- backend testing strategy and scenario sources are documented in `docs/TESTING.md`

