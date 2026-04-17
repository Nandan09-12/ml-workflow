Act as a senior staff engineer and build the backend for this project using a strict, production-grade TDD workflow.

First, read these repo files and treat them as the source of truth:

- README.md
- docs/PRD.md
- docs/ARCHITECTURE.md
- docs/DB_SCHEMA.md
- docs/API_SPEC.md
- docs/BUSINESS_RULES.md
- docs/USER_FLOWS.md
- docs/TASKS.md
- docs/CODEX_HANDOFF.md

Also apply these resolved implementation decisions if they are not yet reflected in code/docs:

- First admin bootstrap:
  - Use env var BOOTSTRAP_ADMIN_EMAILS
  - On POST /api/v1/me/bootstrap, if zero approved admins exist and caller email is allowlisted, auto-approve as ADMIN
  - Write approval audit row with reviewed_by_user_id = null and review_notes = 'BOOTSTRAP_ADMIN_AUTO_APPROVED'
  - Disable bootstrap path once any approved admin exists
  - Must be atomic / transactional

- PATCH /api/v1/me editable fields:
  - full_name only

- Parent/child domain model:
  - workorders is the parent multi-day business record
  - submissions is the child daily closeout record
  - one daily submission per workorder + work_date
  - same or different driver may continue the same workorder on a later day with a new daily submission

- Workorder code normalization:
  - Unicode NFKC
  - trim
  - uppercase
  - remove whitespace
  - preserve '-'
  - store in workorder_code_normalized

- Parent workorder fields:
  - region belongs to the parent workorder
  - total_grids belongs to the parent workorder and is the grand total across all days
  - workorder statuses: ACTIVE, COMPLETED

- Daily submission fields:
  - completed_grids, skipped_grids, and force_tested_grids are that day's contribution only
  - tester progress updates use cumulative completed_grids within the day
  - skipped_grids are permanent for the workorder
  - force_tested_grids is informational only

- Attachments:
  - exactly one active file per daily submission
  - allowed extensions: .csv, .xlsx
  - allowed MIME:
    - text/csv
    - application/csv
    - application/vnd.ms-excel
    - application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
  - validate extension + MIME
  - .xls not allowed in v1
  - inactive attachment history is admin-only

- Submission lifecycle:
  - Start Drive finds or creates the parent workorder and creates the daily submission as IN_PROGRESS
  - Start Drive stamps started_at
  - End Drive stamps ended_at and moves the daily submission to CHECKED_OUT
  - daily completion requires CHECKED_OUT

- Aggregate workorder progress:
  - aggregate child completed_grids + skipped_grids cannot exceed parent total_grids
  - workorder auto-completes when aggregate child completed_grids + skipped_grids = total_grids
  - if the last active file is removed from the relevant completed child, the child moves back to CHECKED_OUT and the parent may move back to ACTIVE

- Completion + file submission pending:
  - daily completion requires exactly one active attachment
  - expose computed file_submission_pending in daily submission list/detail responses
  - file_submission_pending = true when daily submission status = CHECKED_OUT and active attachments = 0
  - do not add DB columns for this in v1

- Standard JSON response envelope:
  - success: { success: true, data: ..., meta: ... }
  - error: { success: false, error: { code, message, details }, meta: ... }
  - no envelope for file streams or 204 responses

- Future date validation:
  - region-to-timezone mapping:
    - NE_UP -> America/New_York
    - SOUTH_FLORIDA -> America/New_York
    - CENTRAL -> America/Chicago
  - UI labels:
    - NE-UP
    - South/Florida
    - Central
  - enforce work_date <= current date in the parent workorder region timezone

- Edit rules:
  - testers do not edit completed daily submission data
  - admins can edit completed daily submissions
  - admins can edit workorders
  - testers can still manage files after completion

Tech context:
- Backend: FastAPI
- Testing: pytest
- API tests: FastAPI TestClient
- Async tests: httpx.AsyncClient + ASGITransport when needed
- Database backend: Supabase Postgres
- Object storage: Supabase Storage
- Auth provider: Supabase Auth
- Code location: apps/api
- I want productionizable code, not demo code

Follow these engineering rules exactly:

1. TDD workflow
- Work feature by feature in this order:
  - test
  - minimal implementation
  - refactor
- For every endpoint, service, repository, auth rule, validation rule, and storage workflow:
  - first write failing tests
  - then implement the smallest amount of code needed to pass
  - then refactor safely
- Before writing implementation for each slice, briefly state:
  - the test cases you will add
  - whether they are unit, API, or integration tests
  - what dependencies will be mocked or overridden

2. Testing strategy
- Unit tests:
  - no network
  - no real Supabase calls
  - mock repository, auth, and storage boundaries
  - test business logic thoroughly
- API tests:
  - use TestClient against the FastAPI app
  - override dependencies cleanly
  - verify status codes, response envelope, validation, and auth failures
- Integration tests:
  - place separately
  - may target a dedicated test Supabase project/schema/bucket only if explicitly enabled
  - never run by default in local fast test runs

3. Architecture constraints
Use this structure inside apps/api:
- app/api/v1/routers
- app/schemas
- app/services
- app/repositories
- app/core
- app/integrations/storage
- app/models
- app/db
- tests/unit
- tests/api
- tests/integration

Keep business rules in services, not in route handlers.

4. Dependency injection
Design the app so all external dependencies are injectable:
- current user / auth dependency
- settings/config
- repositories
- storage service
- Supabase adapters
- DB/session layer

Do not hardcode clients inside route handlers or services.

5. Auth testing
Simulate auth in tests by overriding FastAPI dependencies.
Do not rely on real JWT verification in most unit/API tests.
Create fixtures for:
- anonymous user
- authenticated drive tester
- authenticated admin
- pending approval user

Add tests for:
- unauthenticated
- authenticated but unauthorized
- authenticated and authorized

6. Supabase testing rules
- do not use production Supabase project in tests
- do not call real storage or real DB from unit tests
- wrap Supabase access behind adapters so they can be mocked
- for storage, unit test path generation, validation, metadata handling, and failure mapping without real uploads
- keep real Supabase integration tests explicitly marked and isolated

7. Pytest conventions
Use:
- fixtures in tests/conftest.py
- parametrization where useful
- markers for integration / slow / storage
- factories or fixtures for test data

8. Code quality bar
The code must be:
- typed
- modular
- easy to extend
- explicit about boundaries
- ready for CI
- safe for future auth and storage hardening

9. Output style
Do not dump everything at once.
Work in small vertical slices.
For each slice:
- show failing tests first
- then implementation
- then refactor notes
- then stop

10. Guardrails
- never use production secrets in tests
- never commit real Supabase credentials
- never mix network/storage behavior into pure unit tests
- prefer dependency overrides and fixtures over patching internals
- keep business rules in services, not routes

Now start with only Slice 1:

Slice 1 goals:
- propose the exact apps/api folder structure
- create pytest.ini
- create tests/conftest.py with core fixtures
- create a minimal FastAPI app factory or main app
- write the first failing health-check API test
- write one failing authenticated GET /api/v1/me API test
- then implement the minimum code needed to pass
- then stop and summarize what was added

Do not move to the next slice until Slice 1 is complete.
