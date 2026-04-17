# Testing

This document describes how backend tests are organized, how to run them locally,
and where to look for scenario expectations.

## Scope

The backend currently uses three practical test layers:

- unit tests for isolated service and helper logic
- API tests for HTTP contracts, auth, validation, and response shapes
- integration tests for repository and service behavior against a real Postgres database

These layers are complementary. Unit and API tests stay fast and run by default.
Integration tests are opt-in and validate behavior that is hard to trust with mocks,
especially SQL filtering, transactional updates, aggregate progress rules, and
parent-child lifecycle behavior.

## Source Of Truth

Behavioral expectations should come from the existing product and backend docs,
with executable tests acting as the final source of truth:

- `docs/API_SPEC.md` for request and response contracts
- `docs/BUSINESS_RULES.md` for lifecycle and computed-field rules
- `docs/BACKEND_API_DB_PRIORITY_TASKS.md` for backlog-driven coverage targets
- `docs/ARCHITECTURE.md` for model and data-flow context
- `docs/BACKEND_MIGRATION_POLICY.md` for migration safety expectations

Do not duplicate every assertion in prose. Add prose here only when the runbook,
test boundaries, or scenario grouping would otherwise be unclear.

## Local Runs

### Fast default backend suite

```bash
cd apps/api
PYTHONPATH=. pytest tests -m "not integration"
```

### Integration suite

Start the dedicated integration database:

```bash
docker compose -f docker-compose.integration.yml up -d integration-db
```

Run the integration tests from the API app directory:

```bash
cd apps/api
RUN_INTEGRATION_TESTS=1 \
INTEGRATION_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/ml_workflow_integration \
INTEGRATION_DATABASE_SSL_MODE=disable \
PYTHONPATH=. \
pytest tests/integration
```

Stop the dedicated integration database when finished:

```bash
docker compose -f docker-compose.integration.yml down
```

## Database Strategy

Integration tests use one shared local Postgres container and isolate each test with
a temporary schema. This keeps startup cost low while still exercising real SQL,
constraints, and async database behavior.

This integration database is intentionally separate from the normal dev stack.
It should not change the regular API workflow in `docker-compose.yml`.

## Current Integration Coverage

The current integration suite validates:

- Alembic upgrade/downgrade smoke across the workorder cutover revisions
- legacy submission backfill into parent workorders under real Postgres
- database-level uniqueness and foreign-key guarantees after migration
- workorder start-drive creation and duplicate same-day submission guards
- concurrent start-drive behavior for same-day conflicts and concurrent parent creation
- multi-day continuation for the same workorder across same-driver and different-driver days
- admin workorder updates, including duplicate normalized code conflicts, concurrent rename races, and status/progress reconciliation
- future-date rejection using workorder region rules
- submission completion and reopen lifecycle behavior, including parent cascade boundaries
- attachment upload, list, download, delete, and admin/owner access rules, including last-file parent-state handling
- reporting dashboard counts and no-submission-yet queries
- reporting CSV filtering, including `file_submission_pending`

## Next Wave Coverage

The next backend integration additions should focus on Wave 3 hardening scenarios:

- broader race and conflict translation around other non-happy-path admin edits and concurrent updates

## Maintenance Guidance

- Prefer shared builders and fixtures when the model evolves.
- Keep integration assertions business-focused rather than ORM-internal.
- When a contract changes, update the docs named above and the executable tests in the same change.
- If an issue is purely SQL or transaction behavior, add or adjust an integration test before relying on mocks.